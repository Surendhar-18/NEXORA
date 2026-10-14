from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class VenueZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    polygon: Optional[List[List[float]]] = None
    color: str = "#3B82F6"
    description: Optional[str] = None
    camera_ids: Optional[List[str]] = None

class VenueNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    node_type: str
    latitude: float
    longitude: float
    zone_id: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True

class VenueEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_node: str
    to_node: str
    name: Optional[str] = None
    distance_meters: float
    width_meters: float = 4.0
    congestion_penalty: float = 0.0
    hazard_penalty: float = 0.0
    is_bidirectional: bool = True
    is_blocked: bool = False
    blocked_at: Optional[datetime] = None
    blocked_by: Optional[str] = None
    blockage_reason: Optional[str] = None
    description: Optional[str] = None

class VenueCameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    latitude: float
    longitude: float
    zone_id: Optional[str] = None
    direction: Optional[str] = None

class VenueDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    venue_name: str
    description: Optional[str] = None
    center: Dict[str, float]
    zoom_level: int = 17
    zones: List[VenueZoneResponse] = []
    nodes: List[VenueNodeResponse] = []
    edges: List[VenueEdgeResponse] = []
    cameras: List[VenueCameraResponse] = []

class VenueSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    center_lat: float
    center_lng: float
    default_zoom: int = 17

class WalkwayBlockRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=255, description="Reason for blocking walkway")

class WalkwayBlockResponse(BaseModel):
    id: str
    name: Optional[str] = None
    is_blocked: bool
    blocked_at: Optional[datetime] = None
    blocked_by: Optional[str] = None
    blockage_reason: Optional[str] = None
    message: str
