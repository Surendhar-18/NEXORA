from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.resource import ResourceResponse

class IncidentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Incident title")
    description: str = Field(..., min_length=3, description="Incident operational details")
    zone_id: Optional[str] = Field(None, description="Venue zone ID")
    venue_id: Optional[str] = Field("venue_triveni", description="Venue ID")
    event_id: Optional[str] = Field(None, description="Originating crowd event ID")
    priority: str = Field("medium", description="Priority/Severity: low, medium, high, critical")

class IncidentStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: open, acknowledged, in_progress, resolved, closed")
    notes: Optional[str] = Field(None, description="Status transition notes / mandatory resolution summary")
    operator: Optional[str] = Field("operator", description="Operator identifier")

class IncidentAssignResourceRequest(BaseModel):
    resource_id: str = Field(..., description="Resource identifier to assign")

class IncidentNoteCreateRequest(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=1000, description="Operator note text")

class IncidentLocationUpdateRequest(BaseModel):
    venue_id: Optional[str] = Field("venue_triveni", description="Venue ID")
    zone_id: str = Field(..., description="Target zone ID")

class IncidentHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    details: Optional[Any] = None
    performed_by: str
    created_at: datetime

class IncidentNoteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    note_text: str
    author: str
    created_at: datetime

class IncidentSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_number: str
    title: str
    zone_id: Optional[str] = None
    venue_id: Optional[str] = None
    location_status: str = "confirmed"
    severity: str
    status: str
    event_id: Optional[str] = None
    assigned_resource_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

class IncidentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_number: str
    title: str
    description: str
    venue_id: Optional[str] = None
    zone_id: Optional[str] = None
    location_status: str
    severity: str
    status: str
    event_id: Optional[str] = None
    assigned_resource: Optional[ResourceResponse] = None
    created_by: str
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    evidence_image_url: Optional[str] = None
    history: List[IncidentHistoryItem] = []
    notes: List[IncidentNoteItem] = []

class IncidentListResponse(BaseModel):
    incidents: List[IncidentSummaryItem]
    total: int
    limit: int
    offset: int
