from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.deps import require_operator, require_observer
from app.schemas.venue import (
    VenueDetailResponse,
    VenueSummaryResponse,
    VenueZoneResponse,
    VenueNodeResponse,
    VenueEdgeResponse,
    WalkwayBlockRequest,
    WalkwayBlockResponse
)
from app.services.venue_service import VenueService

router = APIRouter(tags=["venue"])

@router.get("/venue", response_model=VenueDetailResponse)
def get_default_venue(
    venue_id: Optional[str] = Query(None, description="Optional specific venue identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """
    Get full venue structure (zones, nodes, edges, cameras).
    Defaults to the active demo venue.
    """
    if venue_id:
        return VenueService.get_venue_by_id(db, venue_id)
    return VenueService.get_default_venue(db)

@router.get("/venues", response_model=List[VenueSummaryResponse])
def list_venues(db: Session = Depends(get_db)):
    """List configured venues."""
    return VenueService.list_venues(db)

@router.get("/venues/{venue_id}", response_model=VenueDetailResponse)
def get_venue_details(venue_id: str, db: Session = Depends(get_db)):
    """Get complete venue configuration by venue ID."""
    return VenueService.get_venue_by_id(db, venue_id)

@router.get("/venues/{venue_id}/zones")
def get_venue_zones(venue_id: str, db: Session = Depends(get_db)):
    """List zones for a venue."""
    return VenueService.get_venue_zones(db, venue_id)

@router.get("/venues/{venue_id}/nodes")
def get_venue_nodes(venue_id: str, db: Session = Depends(get_db)):
    """List nodes for a venue."""
    return VenueService.get_venue_nodes(db, venue_id)

@router.get("/venues/{venue_id}/edges")
def get_venue_edges(venue_id: str, db: Session = Depends(get_db)):
    """List edges (walkways) for a venue."""
    return VenueService.get_venue_edges(db, venue_id)

@router.put("/venue/edges/{edge_id}/block", response_model=WalkwayBlockResponse)
@router.put("/walkways/{edge_id}/block", response_model=WalkwayBlockResponse)
def block_edge(
    edge_id: str,
    payload: Optional[WalkwayBlockRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Block a walkway, eliminating it from candidate routing paths.
    Creates an immutable audit log entry.
    """
    reason = payload.reason if payload else None
    edge = VenueService.block_walkway(db, edge_id, reason=reason, operator=current_user.username)
    return WalkwayBlockResponse(
        id=edge.id,
        name=edge.name,
        is_blocked=edge.is_blocked,
        blocked_at=edge.blocked_at,
        blocked_by=edge.blocked_by,
        blockage_reason=edge.blockage_reason,
        message="Walkway blocked successfully. Route calculations will exclude this walkway."
    )

@router.put("/venue/edges/{edge_id}/reopen", response_model=WalkwayBlockResponse)
@router.put("/walkways/{edge_id}/reopen", response_model=WalkwayBlockResponse)
def reopen_edge(
    edge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Reopen a blocked walkway, restoring candidate routing eligibility.
    Creates an immutable audit log entry.
    """
    edge = VenueService.reopen_walkway(db, edge_id, operator=current_user.username)
    return WalkwayBlockResponse(
        id=edge.id,
        name=edge.name,
        is_blocked=edge.is_blocked,
        blocked_at=None,
        blocked_by=None,
        blockage_reason=None,
        message="Walkway reopened successfully."
    )
