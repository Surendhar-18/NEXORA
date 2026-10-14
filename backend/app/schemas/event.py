from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SupportingFrameItem(BaseModel):
    frame_index: int
    timestamp_seconds: float
    person_count: int
    evidence_image_path: Optional[str] = None
    evidence_image_url: Optional[str] = None

class EventDetailResponse(BaseModel):
    id: str
    video_id: Optional[str] = None
    job_id: Optional[str] = None
    detection_id: Optional[str] = None
    rule_id: Optional[str] = None
    zone_id: str
    camera_id: Optional[str] = None
    event_type: str
    severity: str
    person_count: int
    rule_name: str
    rule_threshold: int
    sustained_frames: Optional[int] = None
    sustained_duration_sec: Optional[float] = None
    window_start_sec: Optional[float] = None
    window_end_sec: Optional[float] = None
    description: Optional[str] = None
    evidence_image_path: Optional[str] = None
    evidence_image_url: Optional[str] = None
    supporting_frames: List[SupportingFrameItem] = []
    status: str
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}

class EventListResponse(BaseModel):
    events: List[EventDetailResponse]
    total: int
    limit: int
    offset: int

class EventReviewRequest(BaseModel):
    action: str = Field(..., description="Action to take: 'acknowledge', 'dismiss', 'resolve'")
    notes: Optional[str] = Field(None, max_length=1000, description="Operator assessment notes or rationale")
    operator_id: Optional[str] = Field("operator", description="Operator identity performing review")

class EventReviewResponse(BaseModel):
    id: str
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    review_notes: Optional[str]
    message: str

class RuleEvaluationResponse(BaseModel):
    job_id: str
    events_generated_count: int
    events: List[EventDetailResponse]
