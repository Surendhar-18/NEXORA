import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    detection_id = Column(String(36), ForeignKey("detections.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_id = Column(String(50), ForeignKey("crowd_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    zone_id = Column(String(50), nullable=False, default="ZONE-01")
    camera_id = Column(String(50), nullable=True)
    event_type = Column(String(50), nullable=False)  # "threshold", "sustained"
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    person_count = Column(Integer, nullable=False)  # Peak observed count in the triggered window
    rule_name = Column(String(100), nullable=False)
    rule_threshold = Column(Integer, nullable=False)
    sustained_frames = Column(Integer, nullable=True)
    sustained_duration_sec = Column(Float, nullable=True)
    window_start_sec = Column(Float, nullable=True)
    window_end_sec = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    evidence_image_path = Column(String(500), nullable=True)
    supporting_frames_data = Column(JSON, nullable=True)  # List of {frame_index, timestamp_sec, person_count}
    status = Column(String(30), nullable=False, default="pending_review")  # pending_review, acknowledged, dismissed, resolved
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    video = relationship("Video", back_populates="events")
    job = relationship("Job", back_populates="events")
    detection = relationship("Detection", back_populates="events")
    rule = relationship("CrowdRule", back_populates="events")
    incidents = relationship("Incident", back_populates="event")
