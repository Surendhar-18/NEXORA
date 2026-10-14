import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base

class CrowdRule(Base):
    __tablename__ = "crowd_rules"

    id = Column(String(50), primary_key=True)  # e.g., "RULE-SURGE-DEFAULT", "RULE-SUSTAINED-DEFAULT"
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(30), nullable=False, default="threshold")  # "threshold", "sustained"
    operator = Column(String(10), nullable=False, default=">=")  # ">=", ">"
    threshold_count = Column(Integer, nullable=False, default=15)
    sustained_seconds = Column(Float, nullable=False, default=0.0)  # Min duration in seconds across qualifying samples
    min_consecutive_frames = Column(Integer, nullable=False, default=1)  # Min consecutive qualifying samples
    zone_id = Column(String(50), nullable=True)  # Specific monitored zone or None for all zones
    severity = Column(String(20), nullable=False, default="medium")  # "low", "medium", "high", "critical"
    cooldown_seconds = Column(Float, nullable=False, default=10.0)  # Cooldown deduplication window
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    events = relationship("Event", back_populates="rule")
