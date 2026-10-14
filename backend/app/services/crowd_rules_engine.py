import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.job import Job
from app.models.detection import Detection
from app.models.event import Event
from app.models.rule import CrowdRule
from app.models.audit import AuditLog

DEFAULT_RULES = [
    {
        "id": "RULE-SURGE-DEFAULT",
        "name": "Crowd Surge Alert",
        "description": "Decision-support alert triggered when detected persons in a single sampled frame reach or exceed the surge threshold.",
        "rule_type": "threshold",
        "operator": ">=",
        "threshold_count": 15,
        "sustained_seconds": 0.0,
        "min_consecutive_frames": 1,
        "zone_id": None,
        "severity": "high",
        "cooldown_seconds": 10.0,
        "is_active": True,
        "created_by": "system",
    },
    {
        "id": "RULE-SUSTAINED-DEFAULT",
        "name": "Sustained High Crowd Presence",
        "description": "Decision-support alert triggered when detected person counts equal or exceed the threshold across at least 3 consecutive sampled frames spanning at least 4.0 seconds.",
        "rule_type": "sustained",
        "operator": ">=",
        "threshold_count": 10,
        "sustained_seconds": 4.0,
        "min_consecutive_frames": 3,
        "zone_id": None,
        "severity": "critical",
        "cooldown_seconds": 15.0,
        "is_active": True,
        "created_by": "system",
    },
]

def seed_default_rules(db: Session) -> None:
    """
    Ensure standard default crowd-count rules exist in the database on startup.
    Idempotent: will not overwrite existing customized rules.
    """
    for r_data in DEFAULT_RULES:
        existing = db.query(CrowdRule).filter_by(id=r_data["id"]).first()
        if not existing:
            new_rule = CrowdRule(**r_data)
            db.add(new_rule)
    db.commit()

def calculate_event_severity(peak_count: int, threshold: int, base_severity: str = "medium") -> str:
    """
    Calculate alert severity following the approved ratio scale in VisionX design:
    ratio = peak_count / threshold
    ≥ 2.0 -> critical
    ≥ 1.5 -> high
    ≥ 1.0 -> medium (or base_severity)
    < 1.0 -> low
    """
    if threshold <= 0:
        return base_severity
    ratio = peak_count / threshold
    if ratio >= 2.0:
        return "critical"
    elif ratio >= 1.5:
        return "high"
    elif ratio >= 1.0:
        # Honor base_severity if it was already high or critical
        if base_severity in ("high", "critical"):
            return base_severity
        return "medium"
    return "low"

def evaluate_rules_for_job(job_id: str, db: Session, dry_run: bool = False) -> List[Event]:
    """
    Core deterministic crowd-count rule evaluation engine.
    
    Semantics & Invariants:
    1. Evaluates ONLY against persisted genuine detection records for a completed job.
       Incomplete or failed jobs raise an exception or abort without creating events.
    2. Sorts sampled frames strictly by frame_index and verified timestamp_seconds.
    3. Identifies contiguous sequences of qualifying samples meeting rule.operator & threshold_count.
    4. Detects sampling gaps (> 2.5x sampling_interval_sec) and resets sustained continuity.
    5. Sustained condition requires both min_consecutive_frames AND sustained_seconds duration.
    6. Selects the peak-count frame as the primary event evidence frame.
    7. Prevents duplicate events across repeated evaluations via idempotency controls.
    """
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise ValueError(f"Job with ID '{job_id}' not found.")

    if job.status != "completed":
        # Incomplete, queued, or failed jobs cannot generate events
        return []

    detections = (
        db.query(Detection)
        .filter_by(job_id=job.id)
        .order_by(Detection.frame_index.asc())
        .all()
    )

    if not detections:
        # Zero detection records = insufficient evidence
        return []

    active_rules = db.query(CrowdRule).filter_by(is_active=True).all()
    if not active_rules:
        return []

    sampling_interval = max(0.5, float(job.sampling_interval_sec))
    max_tolerated_gap = sampling_interval * 2.5

    generated_events: List[Event] = []

    for rule in active_rules:
        # Check venue zone applicability
        if rule.zone_id and job.zone_id and rule.zone_id != job.zone_id:
            continue

        # Helper to test threshold condition
        def is_qualifying(det: Detection) -> bool:
            if rule.operator == ">":
                return det.person_count > rule.threshold_count
            return det.person_count >= rule.threshold_count

        # Partition detections into contiguous qualifying runs
        qualifying_runs: List[List[Detection]] = []
        current_run: List[Detection] = []

        for i, det in enumerate(detections):
            if is_qualifying(det):
                if not current_run:
                    current_run.append(det)
                else:
                    prev_det = current_run[-1]
                    time_gap = det.timestamp_seconds - prev_det.timestamp_seconds
                    if time_gap > max_tolerated_gap:
                        # Interrupted by an irregular/missing frame gap
                        qualifying_runs.append(current_run)
                        current_run = [det]
                    else:
                        current_run.append(det)
            else:
                if current_run:
                    qualifying_runs.append(current_run)
                    current_run = []

        if current_run:
            qualifying_runs.append(current_run)

        # Evaluate each qualifying run against rule condition
        for run in qualifying_runs:
            consecutive_frames = len(run)
            start_ts = run[0].timestamp_seconds
            end_ts = run[-1].timestamp_seconds
            duration_sec = end_ts - start_ts

            is_condition_met = False
            if rule.rule_type == "threshold":
                if consecutive_frames >= rule.min_consecutive_frames:
                    is_condition_met = True
            elif rule.rule_type == "sustained":
                # Must satisfy both consecutive count and duration window
                if consecutive_frames >= rule.min_consecutive_frames and duration_sec >= rule.sustained_seconds:
                    is_condition_met = True

            if not is_condition_met:
                continue

            # Identify peak frame in this qualifying window
            peak_det = max(run, key=lambda d: d.person_count)
            severity = calculate_event_severity(peak_det.person_count, rule.threshold_count, rule.severity)

            # Idempotency / Deduplication check:
            # Prevent duplicate event if an event for this job and rule already exists within cooldown window
            existing = (
                db.query(Event)
                .filter(
                    Event.job_id == job.id,
                    Event.rule_id == rule.id,
                    Event.window_start_sec <= end_ts,
                    Event.window_end_sec >= start_ts,
                )
                .first()
            )

            if existing:
                # Already captured by an existing event record
                continue

            # Supporting frames metadata for operator inspection
            supporting_data = [
                {
                    "frame_index": d.frame_index,
                    "timestamp_seconds": d.timestamp_seconds,
                    "person_count": d.person_count,
                    "evidence_image_path": d.evidence_image_path,
                }
                for d in run
            ]

            desc_text = (
                f"{rule.name}: Observed {peak_det.person_count} persons in frame (threshold: {rule.threshold_count})"
                + (f" sustained over {consecutive_frames} frames ({duration_sec:.1f}s)" if rule.rule_type == "sustained" else "")
            )

            event = Event(
                id=str(uuid.uuid4()),
                video_id=job.video_id,
                job_id=job.id,
                detection_id=peak_det.id,
                rule_id=rule.id,
                zone_id=job.zone_id or "ZONE-01",
                camera_id=None,
                event_type=rule.rule_type,
                severity=severity,
                person_count=peak_det.person_count,
                rule_name=rule.name,
                rule_threshold=rule.threshold_count,
                sustained_frames=consecutive_frames if rule.rule_type == "sustained" else None,
                sustained_duration_sec=round(duration_sec, 2) if rule.rule_type == "sustained" else None,
                window_start_sec=round(start_ts, 2),
                window_end_sec=round(end_ts, 2),
                description=desc_text,
                evidence_image_path=peak_det.evidence_image_path,
                supporting_frames_data=supporting_data,
                status="pending_review",
                created_at=datetime.now(timezone.utc),
            )

            if not dry_run:
                db.add(event)
                db.add(
                    AuditLog(
                        actor_id="crowd_rules_engine",
                        actor_role="system",
                        action_type="EVENT_GENERATED",
                        entity_type="EVENT",
                        entity_id=event.id,
                        details={
                            "job_id": job.id,
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "peak_person_count": peak_det.person_count,
                            "threshold": rule.threshold_count,
                            "severity": severity,
                            "window_start_sec": start_ts,
                            "window_end_sec": end_ts,
                        },
                    )
                )

            generated_events.append(event)

    if not dry_run and generated_events:
        db.commit()
        for ev in generated_events:
            db.refresh(ev)

    return generated_events
