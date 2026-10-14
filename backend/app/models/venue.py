import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, synonym
from app.database import Base
from app.models.base import TimestampMixin

class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    default_zoom = Column(Integer, nullable=False, default=17)
    boundary_geojson = Column(JSON, nullable=True)

    # Relationships
    zones = relationship("VenueZone", back_populates="venue", cascade="all, delete-orphan")
    nodes = relationship("VenueNode", back_populates="venue", cascade="all, delete-orphan")
    edges = relationship("VenueEdge", back_populates="venue", cascade="all, delete-orphan")
    cameras = relationship("VenueCamera", back_populates="venue", cascade="all, delete-orphan")


class VenueZone(Base, TimestampMixin):
    __tablename__ = "venue_zones"

    id = Column(String(50), primary_key=True)
    venue_id = Column(String(50), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    polygon_json = Column(JSON, nullable=True)
    color = Column(String(20), nullable=False, default="#3B82F6")
    description = Column(String(255), nullable=True)
    camera_ids = Column(JSON, nullable=True)

    venue = relationship("Venue", back_populates="zones")


class VenueNode(Base, TimestampMixin):
    __tablename__ = "venue_nodes"

    id = Column(String(50), primary_key=True)
    venue_id = Column(String(50), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    node_type = Column(String(20), nullable=False, default="junction")  # junction, exit, gate, poi
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_id = Column(String(50), nullable=True, index=True)
    capacity = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    venue = relationship("Venue", back_populates="nodes")


class VenueEdge(Base, TimestampMixin):
    __tablename__ = "venue_edges"

    id = Column(String(50), primary_key=True)
    venue_id = Column(String(50), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    from_node_id = Column(String(50), ForeignKey("venue_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    to_node_id = Column(String(50), ForeignKey("venue_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    distance_meters = Column(Float, nullable=False)
    width_meters = Column(Float, nullable=False, default=4.0)
    congestion_penalty = Column(Float, nullable=False, default=0.0)
    hazard_penalty = Column(Float, nullable=False, default=0.0)
    is_bidirectional = Column(Boolean, nullable=False, default=True)
    is_blocked = Column(Boolean, nullable=False, default=False, index=True)
    blocked_at = Column(DateTime, nullable=True)
    blocked_by = Column(String(100), nullable=True)
    blockage_reason = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

    # Synonyms / aliases for backward compatibility and clean API mappings
    from_node = synonym("from_node_id")
    to_node = synonym("to_node_id")

    venue = relationship("Venue", back_populates="edges")


class VenueCamera(Base, TimestampMixin):
    __tablename__ = "venue_cameras"

    id = Column(String(50), primary_key=True)
    venue_id = Column(String(50), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_id = Column(String(50), nullable=True, index=True)
    direction = Column(String(50), nullable=True)

    venue = relationship("Venue", back_populates="cameras")


# Alias Walkway to VenueEdge for compatibility
Walkway = VenueEdge
