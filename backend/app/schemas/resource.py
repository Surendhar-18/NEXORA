from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    resource_type: str
    call_sign: str
    status: str
    assigned_incident_id: Optional[str] = None
    current_zone_id: Optional[str] = None
    description: Optional[str] = None
    contact_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ResourceListResponse(BaseModel):
    resources: List[ResourceResponse]
    total: int
    available: int
    assigned: int
    unavailable: int
