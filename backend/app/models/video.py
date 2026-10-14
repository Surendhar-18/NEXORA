import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    total_frames = Column(Integer, nullable=True)
    resolution = Column(String(50), nullable=True)
    zone_id = Column(String(50), nullable=True, default="ZONE-01")
    uploaded_by = Column(String(100), nullable=False, default="operator")
    status = Column(String(50), nullable=False, default="uploaded")  # uploaded, processing, processed, failed

    jobs = relationship("Job", back_populates="video", cascade="all, delete-orphan")
    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="video", cascade="all, delete-orphan")
