import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    venue_id = Column(String(50), nullable=True, default="venue_triveni")
    zone_id = Column(String(50), nullable=True, index=True)
    location_status = Column(String(30), nullable=False, default="confirmed")  # confirmed, unconfirmed, unknown
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(30), nullable=False, default="open")  # open, acknowledged, in_progress, resolved, closed
    event_id = Column(String(36), ForeignKey("events.id", ondelete="SET NULL"), unique=True, nullable=True)
    assigned_resource_id = Column(String(36), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(100), nullable=False, default="operator")
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(String(100), nullable=True)

    # Relationships
    event = relationship("Event", back_populates="incidents")
    assigned_resource = relationship("Resource", back_populates="incidents", foreign_keys=[assigned_resource_id])
    history = relationship("IncidentHistory", back_populates="incident", cascade="all, delete-orphan", order_by="desc(IncidentHistory.created_at)")
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan", order_by="desc(IncidentNote.created_at)")


class IncidentHistory(Base):
    __tablename__ = "incident_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # created, status_changed, resource_assigned, resource_released, location_updated, note_added
    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    performed_by = Column(String(100), nullable=False, default="operator")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    incident = relationship("Incident", back_populates="history")


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    note_text = Column(Text, nullable=False)
    author = Column(String(100), nullable=False, default="operator")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    incident = relationship("Incident", back_populates="notes")
