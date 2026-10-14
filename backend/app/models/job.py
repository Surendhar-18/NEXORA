import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(String(50), nullable=True, default="ZONE-01")
    status = Column(String(50), nullable=False, default="queued")  # queued, processing, completed, failed
    progress_percent = Column(Float, nullable=False, default=0.0)
    current_frame = Column(Integer, nullable=False, default=0)
    total_frames_to_process = Column(Integer, nullable=False, default=0)
    sampling_interval_sec = Column(Float, nullable=False, default=2.0)
    confidence_threshold = Column(Float, nullable=False, default=0.5)
    model_name = Column(String(50), nullable=False, default="yolov8n")
    total_persons_detected = Column(Integer, nullable=False, default=0)
    max_person_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    video = relationship("Video", back_populates="jobs")
    detections = relationship("Detection", back_populates="job", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="job", cascade="all, delete-orphan")
