import uuid
from sqlalchemy import Column, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)  # medical, security, crowd_controller, fire, logistics
    call_sign = Column(String(50), unique=True, nullable=False)
    status = Column(String(30), nullable=False, default="available")  # available, assigned, unavailable
    assigned_incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    current_zone_id = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    contact_info = Column(String(100), nullable=True)

    # Relationship to assigned incident
    incidents = relationship("Incident", back_populates="assigned_resource", foreign_keys="Incident.assigned_resource_id")
