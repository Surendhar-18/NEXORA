from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_name: str = "person"

class DetectionItem(BaseModel):
    id: str
    video_id: str
    job_id: Optional[str] = None
    frame_index: int
    timestamp_seconds: float
    person_count: int
    avg_confidence: float
    max_confidence: float
    min_confidence: float
    evidence_image_path: Optional[str] = None
    evidence_image_url: Optional[str] = None
    bounding_boxes: List[BoundingBox] = []
    created_at: str

    model_config = {"from_attributes": True}

class JobDetectionsResponse(BaseModel):
    job_id: str
    video_id: str
    total_frames_processed: int
    total_persons_detected: int
    max_person_count: int
    detections: List[DetectionItem]
