from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RouteSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    edge_id: str
    name: Optional[str] = None
    distance: float
    congestion: float = 0.0
    hazard: float = 0.0
    cost: float

class RouteAlternative(BaseModel):
    rank: int
    is_best: bool
    path: List[str]
    edge_ids: List[str] = []
    total_cost: float
    distance_meters: float
    congestion_penalty: float = 0.0
    hazard_penalty: float = 0.0
    segments: List[Dict[str, Any]] = []

class RouteComparisonResponse(BaseModel):
    from_node: str
    to_node: str
    routes_found: int
    routes: List[RouteAlternative] = []
    blocked_edges: List[str] = []
    message: Optional[str] = None
    advisory_notice: str = (
        "Calculated route alternative for operator review. "
        "Advisory decision-support only; not certified emergency evacuation advice."
    )

class RouteCalculationRequest(BaseModel):
    from_node: str = Field(..., min_length=1, max_length=50, description="Origin node identifier")
    to_node: str = Field(..., min_length=1, max_length=50, description="Destination node identifier")
    max_routes: int = Field(3, ge=1, le=10, description="Maximum number of alternative routes to compute")
    venue_id: Optional[str] = Field(None, description="Target venue identifier (defaults to active venue)")
