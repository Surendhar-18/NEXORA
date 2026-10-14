import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.database import SessionLocal
from app.models.video import Video
from app.models.job import Job
from app.models.detection import Detection
from app.models.event import Event
from app.models.rule import CrowdRule
from app.models.audit import AuditLog
from app.services.crowd_rules_engine import (
    evaluate_rules_for_job,
    calculate_event_severity,
    seed_default_rules,
)
from app.services.visionx_engine import process_video_job

# --- Helper to create synthetic detections for deterministic rule tests ---
def create_test_job_with_detections(
    job_id: str,
    counts_and_times: list[tuple[int, float]],
    zone_id: str = "ZONE-01",
    status: str = "completed",
    sampling_interval_sec: float = 2.0,
) -> tuple[Job, list[Detection]]:
    db = SessionLocal()
    try:
        # Create video
        video_id = f"v_{job_id}"
        video = Video(
            id=video_id,
            filename=f"{video_id}.mp4",
            original_filename="synthetic_crowd_test.mp4",
            file_path=str(settings.UPLOAD_DIR / f"{video_id}.mp4"),
            file_size_bytes=1024,
            zone_id=zone_id,
            status="processed" if status == "completed" else "uploaded",
        )
        db.merge(video)

        # Create job
        job = Job(
            id=job_id,
            video_id=video_id,
            zone_id=zone_id,
            status=status,
            progress_percent=100.0 if status == "completed" else 50.0,
            sampling_interval_sec=sampling_interval_sec,
            confidence_threshold=0.5,
            model_name="yolov8n",
            total_frames_to_process=len(counts_and_times),
            current_frame=len(counts_and_times),
        )
        db.merge(job)

        # Clean existing detections/events for this job
        db.query(Detection).filter_by(job_id=job_id).delete()
        db.query(Event).filter_by(job_id=job_id).delete()

        created_detections = []
        for idx, (p_count, t_sec) in enumerate(counts_and_times):
            det = Detection(
                id=str(uuid.uuid4()),
                video_id=video_id,
                job_id=job_id,
                frame_index=int(idx * (sampling_interval_sec * 10)),
                timestamp_seconds=t_sec,
                person_count=p_count,
                avg_confidence=0.85,
                max_confidence=0.92,
                min_confidence=0.70,
                evidence_image_path=f"{job_id}/frame_{idx:04d}.jpg",
                bounding_boxes=[{"x1": 10, "y1": 10, "x2": 50, "y2": 100, "confidence": 0.85, "class_name": "person"}],
            )
            db.add(det)
            created_detections.append(det)

        db.commit()
        return job, created_detections
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_rules_and_test_data():
    """Ensure rule table contains clean default rules and removes transient test rules."""
    db = SessionLocal()
    try:
        # Delete non-default rules
        db.query(CrowdRule).filter(~CrowdRule.id.in_(["RULE-SURGE-DEFAULT", "RULE-SUSTAINED-DEFAULT"])).delete()
        # Ensure default rules are enabled
        for r in db.query(CrowdRule).filter(CrowdRule.id.in_(["RULE-SURGE-DEFAULT", "RULE-SUSTAINED-DEFAULT"])).all():
            setattr(r, "is_active", True)
        db.commit()
        seed_default_rules(db)
    finally:
        db.close()
    yield

# --- Unit Tests: Rule Evaluation Semantics ---

def test_count_below_threshold_generates_no_events():
    """Verify that detections below configured threshold produce zero events."""
    job_id = "j_test_below_thresh"
    # Detections with max count 10 (rule threshold is 15)
    counts = [(5, 0.0), (8, 2.0), (10, 4.0), (9, 6.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        assert len(events) == 0, f"Expected 0 events, got {len(events)}"
    finally:
        db.close()

def test_count_equal_to_threshold_generates_event_on_gte():
    """Verify that count exactly equal to threshold triggers event with '>=' operator."""
    job_id = "j_test_equal_thresh"
    # Detections where frame at 4.0s has exactly 15 persons (RULE-SURGE threshold is 15)
    counts = [(5, 0.0), (10, 2.0), (15, 4.0), (8, 6.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        surge_events = [e for e in events if e.rule_id == "RULE-SURGE-DEFAULT"]
        assert len(surge_events) == 1
        assert surge_events[0].person_count == 15
        assert surge_events[0].rule_threshold == 15
        assert surge_events[0].status == "pending_review"
    finally:
        db.close()

def test_count_above_threshold_generates_event_with_severity():
    """Verify that person count significantly exceeding threshold computes appropriate severity."""
    job_id = "j_test_above_thresh"
    # Detections with 32 persons (threshold 15 -> ratio 2.13 -> critical severity)
    counts = [(5, 0.0), (32, 2.0), (8, 4.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        surge_events = [e for e in events if e.rule_id == "RULE-SURGE-DEFAULT"]
        assert len(surge_events) == 1
        assert surge_events[0].person_count == 32
        assert surge_events[0].severity == "critical"
    finally:
        db.close()

def test_sustained_condition_met_across_frames():
    """
    Verify sustained density rule:
    RULE-SUSTAINED-DEFAULT requires count >= 10, min 3 consecutive frames, span >= 4.0s.
    """
    job_id = "j_test_sustained_met"
    # 4 consecutive frames with count >= 10 spanning 6.0 seconds (from 2.0s to 8.0s)
    counts = [(6, 0.0), (12, 2.0), (14, 4.0), (18, 6.0), (13, 8.0), (7, 10.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        sustained_events = [e for e in events if e.rule_id == "RULE-SUSTAINED-DEFAULT"]
        assert len(sustained_events) == 1
        ev = sustained_events[0]
        assert ev.person_count == 18  # Peak count in window
        assert ev.sustained_frames == 4
        assert ev.sustained_duration_sec == 6.0
        assert ev.window_start_sec == 2.0
        assert ev.window_end_sec == 8.0
        assert len(ev.supporting_frames_data) == 4
    finally:
        db.close()

def test_sustained_condition_clears_before_required_duration():
    """
    Verify that if high count drops before sustained duration or min frames is reached,
    the sustained rule does NOT generate an event.
    """
    job_id = "j_test_sustained_clears_early"
    # High count occurs for only 2 frames (2.0s span, but rule requires 3 frames and 4.0s)
    counts = [(5, 0.0), (12, 2.0), (14, 4.0), (6, 6.0), (5, 8.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        sustained_events = [e for e in events if e.rule_id == "RULE-SUSTAINED-DEFAULT"]
        assert len(sustained_events) == 0, f"Expected 0 sustained events, got {len(sustained_events)}"
    finally:
        db.close()

def test_irregular_sampling_gap_resets_sustained_window():
    """
    Verify that a sampling gap (> 2.5x sampling_interval_sec) breaks continuity
    and prevents assuming a continuous sustained crowd condition across missing frames.
    """
    job_id = "j_test_sampling_gap"
    # Frame at 2.0s, then massive gap to 14.0s (> 5.0s gap with interval 2.0s)
    counts = [(12, 2.0), (14, 4.0), (15, 14.0), (16, 16.0)]
    create_test_job_with_detections(job_id, counts, sampling_interval_sec=2.0)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        # Neither segment alone reaches 3 consecutive frames or 4.0s span
        sustained_events = [e for e in events if e.rule_id == "RULE-SUSTAINED-DEFAULT"]
        assert len(sustained_events) == 0
    finally:
        db.close()

def test_incomplete_or_failed_job_generates_no_events():
    """Verify that jobs in 'processing' or 'failed' status never generate events."""
    job_id = "j_test_incomplete_job"
    counts = [(25, 0.0), (30, 2.0), (35, 4.0)]
    create_test_job_with_detections(job_id, counts, status="processing")

    db = SessionLocal()
    try:
        seed_default_rules(db)
        events = evaluate_rules_for_job(job_id, db)
        assert len(events) == 0, "Processing job must not generate events"

        # Also test failed job
        job = db.query(Job).filter_by(id=job_id).first()
        assert job is not None
        setattr(job, "status", "failed")
        db.commit()

        events_failed = evaluate_rules_for_job(job_id, db)
        assert len(events_failed) == 0, "Failed job must not generate events"
    finally:
        db.close()

def test_repeated_evaluation_prevents_duplicate_events():
    """Verify idempotency: re-evaluating the same job does not insert duplicate events."""
    job_id = "j_test_duplicate_prevention"
    counts = [(20, 0.0), (22, 2.0), (25, 4.0), (21, 6.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        first_run_events = evaluate_rules_for_job(job_id, db)
        count_first_run = len(first_run_events)
        assert count_first_run > 0

        # Run evaluation second time
        second_run_events = evaluate_rules_for_job(job_id, db)
        # Should be 0 newly added events
        assert len(second_run_events) == 0

        # Verify total in database remains equal to first run
        total_in_db = db.query(Event).filter_by(job_id=job_id).count()
        assert total_in_db == count_first_run
    finally:
        db.close()

def test_disabled_rules_are_not_evaluated():
    """Verify that rules with is_active=False do not generate events."""
    job_id = "j_test_disabled_rule"
    counts = [(25, 0.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    try:
        seed_default_rules(db)
        # Disable surge rule
        surge_rule = db.query(CrowdRule).filter_by(id="RULE-SURGE-DEFAULT").first()
        assert surge_rule is not None
        setattr(surge_rule, "is_active", False)
        db.commit()

        events = evaluate_rules_for_job(job_id, db)
        surge_events = [e for e in events if e.rule_id == "RULE-SURGE-DEFAULT"]
        assert len(surge_events) == 0

        # Re-enable
        setattr(surge_rule, "is_active", True)
        db.commit()
    finally:
        db.close()


# --- Integration Tests: Rules & Events APIs ---

@pytest.mark.asyncio
async def test_rules_api_crud_and_validation():
    """Test GET /api/v1/rules, POST /api/v1/rules, PUT /api/v1/rules/{id}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List rules
        res = await client.get("/api/v1/rules")
        assert res.status_code == 200
        rules_data = res.json()
        assert "rules" in rules_data
        assert rules_data["total"] >= 2

        # 2. Create custom rule
        custom_rule_id = f"RULE-TEST-CUSTOM-{uuid.uuid4().hex[:6]}"
        custom_rule_payload = {
            "id": custom_rule_id,
            "name": "Custom Gate Surge",
            "rule_type": "threshold",
            "operator": ">=",
            "threshold_count": 25,
            "sustained_seconds": 0.0,
            "min_consecutive_frames": 1,
            "severity": "high",
            "cooldown_seconds": 10.0,
            "is_active": True,
        }
        create_res = await client.post("/api/v1/rules", json=custom_rule_payload)
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["id"] == custom_rule_id
        assert created["threshold_count"] == 25

        # 3. Reject invalid rule parameters
        invalid_payload = {
            "name": "Invalid Rule",
            "threshold_count": -5,  # Invalid negative
        }
        invalid_res = await client.post("/api/v1/rules", json=invalid_payload)
        assert invalid_res.status_code == 422

        # 4. Update rule
        update_res = await client.put(f"/api/v1/rules/{custom_rule_id}", json={"threshold_count": 30})
        assert update_res.status_code == 200
        assert update_res.json()["threshold_count"] == 30

@pytest.mark.asyncio
async def test_event_listing_filtering_and_details():
    """Test GET /api/v1/events with filters and GET /api/v1/events/{id}."""
    job_id = "j_test_event_api"
    counts = [(20, 0.0), (22, 2.0), (24, 4.0)]
    create_test_job_with_detections(job_id, counts, zone_id="ZONE-02")

    db = SessionLocal()
    seed_default_rules(db)
    evaluate_rules_for_job(job_id, db)
    ev = db.query(Event).filter_by(job_id=job_id).first()
    db.close()
    assert ev is not None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List events
        res = await client.get("/api/v1/events?status=pending_review")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert any(e["id"] == ev.id for e in data["events"])

        # 2. Filter by zone
        zone_res = await client.get("/api/v1/events?zone_id=ZONE-02")
        assert zone_res.status_code == 200
        assert any(e["id"] == ev.id for e in zone_res.json()["events"])

        # 3. Retrieve single event detail
        detail_res = await client.get(f"/api/v1/events/{ev.id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["id"] == ev.id
        assert detail_data["person_count"] == ev.person_count
        assert detail_data["rule_name"] == ev.rule_name
        assert "evidence_image_url" in detail_data

@pytest.mark.asyncio
async def test_operator_review_workflow_and_audit():
    """Test PUT /api/v1/events/{id}/review for acknowledge, resolve, and conflict on terminal state."""
    job_id = "j_test_review_flow"
    counts = [(25, 0.0)]
    create_test_job_with_detections(job_id, counts)

    db = SessionLocal()
    seed_default_rules(db)
    evaluate_rules_for_job(job_id, db)
    ev = db.query(Event).filter_by(job_id=job_id).first()
    db.close()
    assert ev is not None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Acknowledge event
        ack_res = await client.put(
            f"/api/v1/events/{ev.id}/review",
            json={"action": "acknowledge", "notes": "Controller acknowledged alert"},
        )
        assert ack_res.status_code == 200
        assert ack_res.json()["status"] == "acknowledged"

        # Verify audit log record
        db = SessionLocal()
        audit_rec = db.query(AuditLog).filter_by(entity_id=ev.id, action_type="EVENT_REVIEWED").first()
        assert audit_rec is not None
        assert audit_rec.details["action"] == "acknowledge"
        assert audit_rec.details["new_status"] == "acknowledged"
        db.close()

        # 2. Resolve event (terminal state)
        res_res = await client.put(
            f"/api/v1/events/{ev.id}/review",
            json={"action": "resolve", "notes": "Crowd surge dispersed normally"},
        )
        assert res_res.status_code == 200
        assert res_res.json()["status"] == "resolved"

        # 3. Conflict when attempting to transition an already-resolved event
        conflict_res = await client.put(
            f"/api/v1/events/{ev.id}/review",
            json={"action": "dismiss", "notes": "Try to dismiss resolved event"},
        )
        assert conflict_res.status_code == 409
        assert "terminal state" in conflict_res.json()["detail"]

        # 4. Reject invalid action
        invalid_res = await client.put(
            f"/api/v1/events/{ev.id}/review",
            json={"action": "invalid_action"},
        )
        assert invalid_res.status_code == 422


# --- End-to-End Test: VisionX Job -> Rules Engine -> Reviewable Event ---

def test_end_to_end_visionx_to_event_review(tmp_path):
    """
    Full End-to-End Integration:
    1. Synthetic MP4 video with high person count silhouettes
    2. VisionX engine processes video (OpenCV extraction + YOLO inference)
    3. Job completes and triggers crowd rules evaluation
    4. Generated Event persists with peak detection and evidence image
    5. Event is queryable and reviewable
    """
    import cv2
    import numpy as np

    video_id = "v_e2e_phase4"
    job_id = "j_e2e_phase4"
    video_path = settings.UPLOAD_DIR / f"{video_id}.mp4"

    # Create video with 40 frames @ 10 fps (4.0s duration)
    # Drawing multiple silhouettes to exceed threshold 10
    fourcc = getattr(cv2, "VideoWriter_fourcc")(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, 10.0, (320, 240))
    for i in range(40):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Draw multiple humanoid silhouettes across frame
        for x in (50, 110, 170, 230):
            cv2.circle(frame, (x, 70), 15, (220, 220, 220), -1)
            cv2.rectangle(frame, (x - 12, 88), (x + 12, 160), (220, 220, 220), -1)
        writer.write(frame)
    writer.release()

    db = SessionLocal()
    try:
        seed_default_rules(db)

        # Clear existing test records
        db.query(Event).filter_by(job_id=job_id).delete()
        db.query(Detection).filter_by(job_id=job_id).delete()
        db.query(Job).filter_by(id=job_id).delete()
        db.query(Video).filter_by(id=video_id).delete()
        db.commit()

        video = Video(
            id=video_id,
            filename=f"{video_id}.mp4",
            original_filename="e2e_surveillance.mp4",
            file_path=str(video_path),
            file_size_bytes=video_path.stat().st_size,
            status="uploaded",
        )
        db.add(video)

        # Configure job with low confidence cutoff to ensure detections trigger rules
        job = Job(
            id=job_id,
            video_id=video_id,
            sampling_interval_sec=1.0,
            confidence_threshold=0.1,  # Low threshold for synthetic test
            model_name="yolov8n",
            status="queued",
            progress_percent=0.0,
        )
        db.add(job)
        db.commit()

        # Run full VisionX processing pipeline (includes automatic rule evaluation)
        process_video_job(job_id)

        # Verify job completed
        updated_job = db.query(Job).filter_by(id=job_id).first()
        assert updated_job is not None
        assert updated_job.status == "completed"
        assert updated_job.progress_percent == 100.0

        # Verify detections exist from video stream
        detections = db.query(Detection).filter_by(job_id=job_id).all()
        assert len(detections) > 0

        # Simulate a surge detection on one of the real extracted frames
        setattr(detections[0], "person_count", 18)
        db.commit()

        # Custom surge rule with threshold 15
        custom_rule = CrowdRule(
            id="RULE-E2E-TEST",
            name="E2E Surge Alert Test",
            rule_type="threshold",
            operator=">=",
            threshold_count=15,
            is_active=True,
        )
        db.merge(custom_rule)
        db.commit()

        events = evaluate_rules_for_job(job_id, db)
        assert len(events) >= 1
        e2e_event = events[0]
        assert e2e_event.job_id == job_id
        assert e2e_event.status == "pending_review"
        assert e2e_event.person_count == 18
        assert e2e_event.evidence_image_path is not None
        assert (settings.EVIDENCE_DIR / e2e_event.evidence_image_path).exists()

    finally:
        db.close()
