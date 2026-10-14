from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.route import RouteComparisonResponse, RouteCalculationRequest
from app.services.routing_engine import RoutingEngine

router = APIRouter(tags=["routing"])

@router.get("/routes/compare", response_model=RouteComparisonResponse)
def compare_routes(
    from_node: str = Query(..., description="Origin node identifier"),
    to_node: str = Query(..., description="Destination node identifier"),
    max_routes: int = Query(3, ge=1, le=10, description="Max alternative routes"),
    venue_id: Optional[str] = Query(None, description="Target venue ID"),
    db: Session = Depends(get_db)
):
    """
    Calculate and compare up to max_routes alternatives between two nodes.
    Excludes all currently blocked walkways.
    """
    return RoutingEngine.calculate_routes(
        db=db,
        from_node=from_node,
        to_node=to_node,
        max_routes=max_routes,
        venue_id=venue_id
    )

@router.post("/routes/calculate", response_model=RouteComparisonResponse)
def calculate_routes_post(
    payload: RouteCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate alternative routes using POST payload.
    Excludes all currently blocked walkways.
    """
    return RoutingEngine.calculate_routes(
        db=db,
        from_node=payload.from_node,
        to_node=payload.to_node,
        max_routes=payload.max_routes,
        venue_id=payload.venue_id
    )
