import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.venue import Venue, VenueZone, VenueNode, VenueEdge, VenueCamera
from app.models.audit import AuditLog

logger = logging.getLogger("nexora.venue_service")

class VenueService:
    @staticmethod
    def seed_default_venue(db: Session) -> Optional[Venue]:
        """Seeds demo venue from data/venue/demo_venue.json if not already present."""
        existing = db.query(Venue).first()
        if existing:
            return existing

        venue_file = Path(settings.DATA_DIR) / "venue" / "demo_venue.json"
        if not venue_file.exists():
            # Try alternate path relative to project root
            venue_file = Path("data/venue/demo_venue.json")

        if not venue_file.exists():
            logger.warning("Venue configuration file not found at %s. Skipping automatic seeding.", venue_file)
            return None

        try:
            with open(venue_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error("Failed to read venue configuration file: %s", e)
            return None

        venue_id = data.get("venue_id", "venue_triveni")
        venue_name = data.get("venue_name", "Triveni Festival Grounds")
        center = data.get("center", {"latitude": 25.4358, "longitude": 81.8463})
        default_zoom = data.get("default_zoom", 17)
        description = data.get("description", "Demonstration Festival Grounds")

        venue = Venue(
            id=venue_id,
            name=venue_name,
            description=description,
            center_lat=float(center.get("latitude", 25.4358)),
            center_lng=float(center.get("longitude", 81.8463)),
            default_zoom=int(default_zoom),
            boundary_geojson=data.get("boundary_geojson")
        )
        db.add(venue)
        db.flush()

        # Seed zones
        for z in data.get("zones", []):
            zone = VenueZone(
                id=z["id"],
                venue_id=venue_id,
                name=z["name"],
                polygon_json=z.get("polygon"),
                color=z.get("color", "#3B82F6"),
                description=z.get("description"),
                camera_ids=z.get("camera_ids", [])
            )
            db.add(zone)

        # Seed nodes
        node_ids = set()
        for n in data.get("nodes", []):
            node_ids.add(n["id"])
            node = VenueNode(
                id=n["id"],
                venue_id=venue_id,
                name=n["name"],
                node_type=n.get("type", "junction"),
                latitude=float(n["latitude"]),
                longitude=float(n["longitude"]),
                zone_id=n.get("zone_id"),
                capacity=n.get("capacity"),
                description=n.get("description"),
                is_active=True
            )
            db.add(node)
        db.flush()

        # Seed edges / walkways
        for e in data.get("edges", []):
            # Validate endpoints exist in node set
            if e["from_node"] not in node_ids or e["to_node"] not in node_ids:
                logger.error("Edge %s has invalid endpoints: %s -> %s", e["id"], e["from_node"], e["to_node"])
                continue
            
            dist = float(e.get("distance_meters", 100.0))
            if dist <= 0:
                dist = 50.0

            edge = VenueEdge(
                id=e["id"],
                venue_id=venue_id,
                name=e.get("name"),
                from_node_id=e["from_node"],
                to_node_id=e["to_node"],
                distance_meters=dist,
                width_meters=float(e.get("width_meters", 4.0)),
                congestion_penalty=float(e.get("congestion_penalty", 0.0)),
                hazard_penalty=float(e.get("hazard_penalty", 0.0)),
                is_bidirectional=bool(e.get("is_bidirectional", True)),
                is_blocked=False,
                description=e.get("description")
            )
            db.add(edge)

        # Seed cameras
        for c in data.get("cameras", []):
            cam = VenueCamera(
                id=c["id"],
                venue_id=venue_id,
                name=c["name"],
                latitude=float(c["latitude"]),
                longitude=float(c["longitude"]),
                zone_id=c.get("zone_id"),
                direction=c.get("direction")
            )
            db.add(cam)

        db.commit()
        db.refresh(venue)
        logger.info("Successfully seeded demo venue '%s' with %d nodes and %d edges.",
                    venue_id, len(node_ids), len(data.get("edges", [])))
        return venue

    @staticmethod
    def get_default_venue(db: Session) -> Dict[str, Any]:
        """Returns the full structure of the active/default venue."""
        venue = db.query(Venue).first()
        if not venue:
            venue = VenueService.seed_default_venue(db)
            if not venue:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No venue configured.")

        return VenueService.format_venue_response(venue, db)

    @staticmethod
    def get_venue_by_id(db: Session, venue_id: str) -> Dict[str, Any]:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not venue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venue '{venue_id}' not found.")
        return VenueService.format_venue_response(venue, db)

    @staticmethod
    def list_venues(db: Session) -> List[Dict[str, Any]]:
        venues = db.query(Venue).all()
        if not venues:
            seeded = VenueService.seed_default_venue(db)
            venues = [seeded] if seeded else []
        return [
            {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "center_lat": v.center_lat,
                "center_lng": v.center_lng,
                "default_zoom": v.default_zoom
            }
            for v in venues
        ]

    @staticmethod
    def format_venue_response(venue: Venue, db: Session) -> Dict[str, Any]:
        zones = db.query(VenueZone).filter(VenueZone.venue_id == venue.id).all()
        nodes = db.query(VenueNode).filter(VenueNode.venue_id == venue.id).all()
        edges = db.query(VenueEdge).filter(VenueEdge.venue_id == venue.id).all()
        cameras = db.query(VenueCamera).filter(VenueCamera.venue_id == venue.id).all()

        return {
            "id": venue.id,
            "venue_name": venue.name,
            "description": venue.description,
            "center": {
                "latitude": venue.center_lat,
                "longitude": venue.center_lng
            },
            "zoom_level": venue.default_zoom,
            "zones": [
                {
                    "id": z.id,
                    "name": z.name,
                    "polygon": z.polygon_json if isinstance(z.polygon_json, list) else [],
                    "color": z.color,
                    "description": z.description,
                    "camera_ids": z.camera_ids if isinstance(z.camera_ids, list) else []
                }
                for z in zones
            ],
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "latitude": n.latitude,
                    "longitude": n.longitude,
                    "zone_id": n.zone_id,
                    "capacity": n.capacity,
                    "description": n.description,
                    "is_active": n.is_active
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "from_node": e.from_node_id,
                    "to_node": e.to_node_id,
                    "name": e.name,
                    "distance_meters": e.distance_meters,
                    "width_meters": e.width_meters,
                    "congestion_penalty": e.congestion_penalty,
                    "hazard_penalty": e.hazard_penalty,
                    "is_bidirectional": e.is_bidirectional,
                    "is_blocked": e.is_blocked,
                    "blocked_at": e.blocked_at,
                    "blocked_by": e.blocked_by,
                    "blockage_reason": e.blockage_reason,
                    "description": e.description
                }
                for e in edges
            ],
            "cameras": [
                {
                    "id": c.id,
                    "name": c.name,
                    "latitude": c.latitude,
                    "longitude": c.longitude,
                    "zone_id": c.zone_id,
                    "direction": c.direction
                }
                for c in cameras
            ]
        }

    @staticmethod
    def get_venue_zones(db: Session, venue_id: str) -> List[Dict[str, Any]]:
        zones = db.query(VenueZone).filter(VenueZone.venue_id == venue_id).all()
        return [
            {
                "id": z.id,
                "name": z.name,
                "polygon": z.polygon_json,
                "color": z.color,
                "description": z.description,
                "camera_ids": z.camera_ids
            }
            for z in zones
        ]

    @staticmethod
    def get_venue_nodes(db: Session, venue_id: str) -> List[Dict[str, Any]]:
        nodes = db.query(VenueNode).filter(VenueNode.venue_id == venue_id).all()
        return [
            {
                "id": n.id,
                "name": n.name,
                "node_type": n.node_type,
                "latitude": n.latitude,
                "longitude": n.longitude,
                "zone_id": n.zone_id,
                "capacity": n.capacity,
                "description": n.description,
                "is_active": n.is_active
            }
            for n in nodes
        ]

    @staticmethod
    def get_venue_edges(db: Session, venue_id: str) -> List[Dict[str, Any]]:
        edges = db.query(VenueEdge).filter(VenueEdge.venue_id == venue_id).all()
        return [
            {
                "id": e.id,
                "from_node": e.from_node_id,
                "to_node": e.to_node_id,
                "name": e.name,
                "distance_meters": e.distance_meters,
                "width_meters": e.width_meters,
                "congestion_penalty": e.congestion_penalty,
                "hazard_penalty": e.hazard_penalty,
                "is_bidirectional": e.is_bidirectional,
                "is_blocked": e.is_blocked,
                "blocked_at": e.blocked_at,
                "blocked_by": e.blocked_by,
                "blockage_reason": e.blockage_reason,
                "description": e.description
            }
            for e in edges
        ]

    @staticmethod
    def block_walkway(db: Session, edge_id: str, reason: Optional[str] = None, operator: str = "operator") -> VenueEdge:
        edge = db.query(VenueEdge).filter(VenueEdge.id == edge_id).first()
        if not edge:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Walkway '{edge_id}' not found.")

        if edge.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Walkway '{edge_id}' is already blocked."
            )

        edge.is_blocked = True
        edge.blocked_at = datetime.now(timezone.utc)
        edge.blocked_by = operator
        edge.blockage_reason = reason

        # Log audit record
        audit = AuditLog(
            action_type="walkway_blocked",
            entity_type="edge",
            entity_id=edge_id,
            actor_id=operator,
            actor_role="operator",
            details={
                "action": "block",
                "reason": reason,
                "from_node": edge.from_node_id,
                "to_node": edge.to_node_id,
                "name": edge.name
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(edge)
        logger.info("Walkway %s blocked by %s: %s", edge_id, operator, reason)
        return edge

    @staticmethod
    def reopen_walkway(db: Session, edge_id: str, operator: str = "operator") -> VenueEdge:
        edge = db.query(VenueEdge).filter(VenueEdge.id == edge_id).first()
        if not edge:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Walkway '{edge_id}' not found.")

        if not edge.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Walkway '{edge_id}' is not currently blocked."
            )

        edge.is_blocked = False
        edge.blocked_at = None
        edge.blocked_by = None
        edge.blockage_reason = None

        # Log audit record
        audit = AuditLog(
            action_type="walkway_reopened",
            entity_type="edge",
            entity_id=edge_id,
            actor_id=operator,
            actor_role="operator",
            details={
                "action": "reopen",
                "from_node": edge.from_node_id,
                "to_node": edge.to_node_id,
                "name": edge.name
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(edge)
        logger.info("Walkway %s reopened by %s", edge_id, operator)
        return edge

