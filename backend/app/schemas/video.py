from typing import Optional, List
from pydantic import BaseModel, Field

class VideoUploadResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    file_type: str
    zone_id: Optional[str] = "ZONE-01"
    status: str
    sampling_interval_sec: float = 2.0
    confidence_threshold: float = 0.5
    created_at: str
    message: str

class VideoDetailResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    resolution: Optional[str] = None
    zone_id: Optional[str] = "ZONE-01"
    uploaded_by: str = "operator"
    status: str
    created_at: str

    model_config = {"from_attributes": True}

class VideoListResponse(BaseModel):
    videos: List[VideoDetailResponse]
    total: int
