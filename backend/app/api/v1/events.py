from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.event import Event
from app.models.audit import AuditLog
from app.models.user import User
from app.api.deps import require_operator, require_observer
from app.schemas.event import (
    EventDetailResponse,
    EventListResponse,
    EventReviewRequest,
    EventReviewResponse,
    SupportingFrameItem,
)

router = APIRouter(prefix="/events", tags=["VisionX Crowd Events"])

VALID_REVIEW_ACTIONS = {
    "acknowledge": "acknowledged",
    "dismiss": "dismissed",
    "resolve": "resolved",
}

@router.get("", response_model=EventListResponse)
def list_events(
    status_filter: Optional[str] = Query(None, alias="status"),
    zone_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List crowd events with optional status, zone, and severity filters."""
    query = db.query(Event)

    if status_filter:
        query = query.filter(Event.status == status_filter)
    if zone_id:
        query = query.filter(Event.zone_id == zone_id)
    if severity:
        query = query.filter(Event.severity == severity)

    total = query.count()
    events = query.order_by(desc(Event.created_at)).offset(offset).limit(limit).all()

    return EventListResponse(
        events=[build_event_response(ev) for ev in events],
        total=total,
        limit=limit,
        offset=offset,
    )

@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed information and supporting evidence for a single event."""
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found",
        )
    return build_event_response(event)

@router.put("/{event_id}/review", response_model=EventReviewResponse)
def review_event(
    event_id: str,
    payload: EventReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Operator human-in-the-loop review action for crowd-count events.
    Permitted actions: 'acknowledge', 'dismiss', 'resolve'.
    Enforces valid state lifecycle transitions and creates audit records.
    """
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found",
        )

    action = payload.action.lower().strip()
    if action not in VALID_REVIEW_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid review action '{payload.action}'. Allowed actions: {', '.join(sorted(VALID_REVIEW_ACTIONS.keys()))}",
        )

    # State transition checks
    if event.status in ("dismissed", "resolved"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event '{event_id}' is already in terminal state '{event.status}'. Cannot perform '{action}'.",
        )

    old_status = event.status
    new_status = VALID_REVIEW_ACTIONS[action]

    # Apply review decision
    now_utc = datetime.now(timezone.utc)
    event.status = new_status
    event.review_notes = payload.notes
    event.reviewed_by = current_user.username
    event.reviewed_at = now_utc

    # Record to immutable audit log with verified principal
    db.add(
        AuditLog(
            actor_id=current_user.username,
            actor_role=current_user.role,
            action_type="EVENT_REVIEWED",
            entity_type="EVENT",
            entity_id=event.id,
            details={
                "action": action,
                "previous_status": old_status,
                "new_status": new_status,
                "review_notes": payload.notes,
                "person_count": event.person_count,
                "rule_name": event.rule_name,
            },
        )
    )

    db.commit()
    db.refresh(event)

    return EventReviewResponse(
        id=event.id,
        status=event.status,
        reviewed_by=event.reviewed_by,
        reviewed_at=event.reviewed_at.isoformat() if event.reviewed_at else None,
        review_notes=event.review_notes,
        message=f"Event status transitioned from '{old_status}' to '{new_status}' successfully.",
    )

def build_event_response(event: Event) -> EventDetailResponse:
    """Helper to convert Event ORM entity to EventDetailResponse with safe evidence URLs."""
    evidence_url = None
    if event.evidence_image_path:
        norm_path = event.evidence_image_path.replace("\\", "/")
        parts = norm_path.split("/")
        if len(parts) >= 2:
            job_id_part = parts[0]
            filename_part = parts[-1]
            evidence_url = f"/api/v1/evidence/{job_id_part}/{filename_part}"

    supporting_items: List[SupportingFrameItem] = []
    if event.supporting_frames_data and isinstance(event.supporting_frames_data, list):
        for item in event.supporting_frames_data:
            frame_ev_url = None
            if item.get("evidence_image_path"):
                f_norm = item["evidence_image_path"].replace("\\", "/")
                f_parts = f_norm.split("/")
                if len(f_parts) >= 2:
                    frame_ev_url = f"/api/v1/evidence/{f_parts[0]}/{f_parts[-1]}"

            supporting_items.append(
                SupportingFrameItem(
                    frame_index=item.get("frame_index", 0),
                    timestamp_seconds=item.get("timestamp_seconds", 0.0),
                    person_count=item.get("person_count", 0),
                    evidence_image_path=item.get("evidence_image_path"),
                    evidence_image_url=frame_ev_url,
                )
            )

    return EventDetailResponse(
        id=event.id,
        video_id=event.video_id,
        job_id=event.job_id,
        detection_id=event.detection_id,
        rule_id=event.rule_id,
        zone_id=event.zone_id,
        camera_id=event.camera_id,
        event_type=event.event_type,
        severity=event.severity,
        person_count=event.person_count,
        rule_name=event.rule_name,
        rule_threshold=event.rule_threshold,
        sustained_frames=event.sustained_frames,
        sustained_duration_sec=event.sustained_duration_sec,
        window_start_sec=event.window_start_sec,
        window_end_sec=event.window_end_sec,
        description=event.description,
        evidence_image_path=event.evidence_image_path,
        evidence_image_url=evidence_url,
        supporting_frames=supporting_items,
        status=event.status,
        review_notes=event.review_notes,
        reviewed_by=event.reviewed_by,
        reviewed_at=event.reviewed_at.isoformat() if event.reviewed_at else None,
        created_at=event.created_at.isoformat() if event.created_at else "",
    )
