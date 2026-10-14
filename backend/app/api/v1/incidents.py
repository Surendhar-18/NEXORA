from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.resource import Resource
from app.schemas.incident import (
    IncidentCreateRequest,
    IncidentStatusUpdateRequest,
    IncidentAssignResourceRequest,
    IncidentNoteCreateRequest,
    IncidentLocationUpdateRequest,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentSummaryItem,
    IncidentHistoryItem,
    IncidentNoteItem,
)
from app.schemas.resource import ResourceResponse
from app.services.incident_service import IncidentService
from app.models.user import User
from app.api.deps import require_operator, require_observer

router = APIRouter(prefix="/incidents", tags=["Incident Management"])

def _build_detail_response(incident: Incident) -> IncidentDetailResponse:
    evidence_url = None
    if incident.event and incident.event.evidence_image_path:
        f_norm = incident.event.evidence_image_path.replace("\\", "/")
        f_parts = f_norm.split("/")
        if len(f_parts) >= 2:
            evidence_url = f"/api/v1/evidence/{f_parts[0]}/{f_parts[-1]}"

    assigned_resource_resp = None
    if incident.assigned_resource:
        assigned_resource_resp = ResourceResponse.model_validate(incident.assigned_resource)

    history_items = [IncidentHistoryItem.model_validate(h) for h in incident.history]
    note_items = [IncidentNoteItem.model_validate(n) for n in incident.notes]

    return IncidentDetailResponse(
        id=incident.id,
        incident_number=incident.incident_number,
        title=incident.title,
        description=incident.description,
        venue_id=incident.venue_id,
        zone_id=incident.zone_id,
        location_status=incident.location_status,
        severity=incident.severity,
        status=incident.status,
        event_id=incident.event_id,
        assigned_resource=assigned_resource_resp,
        created_by=incident.created_by,
        acknowledged_at=incident.acknowledged_at,
        acknowledged_by=incident.acknowledged_by,
        resolved_at=incident.resolved_at,
        resolved_by=incident.resolved_by,
        resolution_notes=incident.resolution_notes,
        closed_at=incident.closed_at,
        closed_by=incident.closed_by,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        evidence_image_url=evidence_url,
        history=history_items,
        notes=note_items,
    )

@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (open, acknowledged, in_progress, resolved, closed)"),
    severity_filter: Optional[str] = Query(None, alias="severity", description="Filter by severity (low, medium, high, critical)"),
    venue_id: Optional[str] = Query(None, description="Filter by venue ID"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List operational incidents with status and severity filters."""
    result = IncidentService.list_incidents(
        db=db,
        status_filter=status_filter,
        severity_filter=severity_filter,
        venue_filter=venue_id,
        zone_filter=zone_id,
        limit=limit,
        offset=offset,
    )
    items = [IncidentSummaryItem.model_validate(inc) for inc in result["incidents"]]
    return IncidentListResponse(
        incidents=items,
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )

@router.post("", response_model=IncidentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Create an incident manually or link to a reviewed crowd event."""
    incident = IncidentService.create_incident(
        db=db,
        title=payload.title,
        description=payload.description,
        venue_id=payload.venue_id,
        zone_id=payload.zone_id,
        event_id=payload.event_id,
        severity=payload.priority,
        created_by=current_user.username
    )
    return _build_detail_response(incident)

@router.post("/from-event/{event_id}", response_model=IncidentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_incident_from_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Escalate a human-reviewed crowd event into an operational incident.
    Enforces review status eligibility and duplicate prevention (idempotency).
    """
    incident = IncidentService.create_incident_from_event(
        db=db,
        event_id=event_id,
        operator=current_user.username
    )
    return _build_detail_response(incident)

@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident_detail(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer)
):
    """Retrieve full incident detail including notes, audit history, and assigned resource."""
    incident = IncidentService.get_incident_detail(db, incident_id)
    return _build_detail_response(incident)

@router.put("/{incident_id}/status", response_model=IncidentDetailResponse)
@router.patch("/{incident_id}/status", response_model=IncidentDetailResponse)
def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Apply a validated state transition to an incident.
    Resolution requires mandatory resolution summary notes.
    """
    incident = IncidentService.update_incident_status(
        db=db,
        incident_id=incident_id,
        new_status=payload.status,
        notes=payload.notes,
        operator=current_user.username
    )
    return _build_detail_response(incident)

@router.post("/{incident_id}/assign", response_model=IncidentDetailResponse)
def assign_resource(
    incident_id: str,
    payload: IncidentAssignResourceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Atomically assign a simulated response resource to an incident.
    Transitions incident to 'in_progress' and sets resource status to 'assigned'.
    """
    incident = IncidentService.assign_resource(
        db=db,
        incident_id=incident_id,
        resource_id=payload.resource_id,
        operator=current_user.username
    )
    return _build_detail_response(incident)

@router.post("/{incident_id}/release", response_model=IncidentDetailResponse)
def release_resource(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Release the currently assigned resource from the incident, returning it to 'available'.
    """
    incident = IncidentService.release_resource(
        db=db,
        incident_id=incident_id,
        operator=current_user.username
    )
    return _build_detail_response(incident)

@router.post("/{incident_id}/notes", response_model=IncidentNoteItem, status_code=status.HTTP_201_CREATED)
def add_incident_note(
    incident_id: str,
    payload: IncidentNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Add an operational note to the incident audit thread."""
    note = IncidentService.add_incident_note(
        db=db,
        incident_id=incident_id,
        note_text=payload.note_text,
        author=current_user.username
    )
    return IncidentNoteItem.model_validate(note)

@router.put("/{incident_id}/location", response_model=IncidentDetailResponse)
@router.patch("/{incident_id}/location", response_model=IncidentDetailResponse)
def update_incident_location(
    incident_id: str,
    payload: IncidentLocationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Update incident venue and zone association, validating against GIS records."""
    incident = IncidentService.update_location(
        db=db,
        incident_id=incident_id,
        venue_id=payload.venue_id,
        zone_id=payload.zone_id,
        operator=current_user.username
    )
    return _build_detail_response(incident)

@router.get("/{incident_id}/history", response_model=List[IncidentHistoryItem])
def get_incident_history(incident_id: str, db: Session = Depends(get_db)):
    """Retrieve full chronological audit history for an incident."""
    incident = IncidentService.get_incident_detail(db, incident_id)
    return [IncidentHistoryItem.model_validate(h) for h in incident.history]
