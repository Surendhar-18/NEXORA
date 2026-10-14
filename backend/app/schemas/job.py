from typing import Optional, List
from pydantic import BaseModel, Field

class JobCreateRequest(BaseModel):
    video_id: str = Field(..., description="Target video UUID to process")
    zone_id: Optional[str] = Field("ZONE-01", description="Monitored venue zone identifier")
    sampling_interval_sec: float = Field(2.0, ge=0.5, le=30.0, description="Sampling rate in seconds")
    confidence_threshold: float = Field(0.5, ge=0.1, le=1.0, description="Detection threshold")

class JobDetailResponse(BaseModel):
    id: str
    video_id: str
    original_filename: str
    file_size_bytes: int
    file_type: str
    zone_id: Optional[str] = "ZONE-01"
    status: str
    progress_percent: float = 0.0
    current_frame: int = 0
    total_frames_to_process: int = 0
    sampling_interval_sec: float = 2.0
    confidence_threshold: float = 0.5
    model_name: str = "yolov8n"
    total_persons_detected: int = 0
    max_person_count: int = 0
    error_message: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    model_config = {"from_attributes": True}

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    current_frame: int
    total_frames_to_process: int
    error_message: Optional[str] = None

class JobListResponse(BaseModel):
    jobs: List[JobDetailResponse]
    total: int
    limit: int
    offset: int
