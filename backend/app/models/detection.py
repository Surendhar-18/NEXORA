import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    frame_index = Column(Integer, nullable=False)
    timestamp_seconds = Column(Float, nullable=False, index=True)
    person_count = Column(Integer, nullable=False)
    avg_confidence = Column(Float, nullable=False)
    max_confidence = Column(Float, nullable=False)
    min_confidence = Column(Float, nullable=False)
    evidence_image_path = Column(String(500), nullable=True)
    bounding_boxes = Column(JSON, nullable=True)  # list of {x1, y1, x2, y2, conf}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    video = relationship("Video", back_populates="detections")
    job = relationship("Job", back_populates="detections")
    events = relationship("Event", back_populates="detection")
