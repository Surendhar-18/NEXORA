import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.resource import Resource

logger = logging.getLogger("nexora.resource_service")

DEMO_RESOURCES = [
    {
        "id": "res_med_01",
        "name": "Medical Team Alpha",
        "resource_type": "medical",
        "call_sign": "MEDIC-1",
        "current_zone_id": "zone_main_gate",
        "contact_info": "+91-98765-43201",
        "description": "First-aid team with mobile defibrillator and triage kit"
    },
    {
        "id": "res_med_02",
        "name": "Medical Team Bravo",
        "resource_type": "medical",
        "call_sign": "MEDIC-2",
        "current_zone_id": "zone_central_stage",
        "contact_info": "+91-98765-43202",
        "description": "Paramedic squad for high-density congregation areas"
    },
    {
        "id": "res_sec_01",
        "name": "Security Patrol 1",
        "resource_type": "security",
        "call_sign": "SEC-1",
        "current_zone_id": "zone_main_gate",
        "contact_info": "+91-98765-43203",
        "description": "Perimeter crowd monitoring squad"
    },
    {
        "id": "res_sec_02",
        "name": "Security Quick Response",
        "resource_type": "security",
        "call_sign": "SEC-2",
        "current_zone_id": "zone_central_stage",
        "contact_info": "+91-98765-43204",
        "description": "Tactical crowd management and de-escalation squad"
    },
    {
        "id": "res_crw_01",
        "name": "Crowd Warden Team Alpha",
        "resource_type": "crowd_controller",
        "call_sign": "WARDEN-1",
        "current_zone_id": "zone_north_plaza",
        "contact_info": "+91-98765-43205",
        "description": "Egress diversion and barrier operators"
    },
    {
        "id": "res_crw_02",
        "name": "Crowd Warden Team Bravo",
        "resource_type": "crowd_controller",
        "call_sign": "WARDEN-2",
        "current_zone_id": "zone_south_market",
        "contact_info": "+91-98765-43206",
        "description": "Gate ingress coordinators and queue marshals"
    },
    {
        "id": "res_log_01",
        "name": "Logistics Support Squad",
        "resource_type": "logistics",
        "call_sign": "LOG-1",
        "current_zone_id": "zone_west_garden",
        "contact_info": "+91-98765-43207",
        "description": "Emergency signage and perimeter barricade deployment"
    },
    {
        "id": "res_fire_01",
        "name": "Fire & Safety Unit",
        "resource_type": "fire",
        "call_sign": "FIRE-1",
        "current_zone_id": "zone_east_wing",
        "contact_info": "+91-98765-43208",
        "description": "Venue fire safety and hazard inspection unit"
    }
]

class ResourceService:
    @staticmethod
    def seed_default_resources(db: Session) -> None:
        """Seeds standard simulated response resources if table is empty."""
        existing = db.query(Resource).first()
        if existing:
            return

        for item in DEMO_RESOURCES:
            res = Resource(
                id=item["id"],
                name=item["name"],
                resource_type=item["resource_type"],
                call_sign=item["call_sign"],
                status="available",
                current_zone_id=item["current_zone_id"],
                contact_info=item["contact_info"],
                description=item["description"],
                assigned_incident_id=None
            )
            db.add(res)

        db.commit()
        logger.info("Seeded %d simulated response resources.", len(DEMO_RESOURCES))

    @staticmethod
    def list_resources(
        db: Session,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        ResourceService.seed_default_resources(db)
        query = db.query(Resource)

        if status_filter:
            query = query.filter(Resource.status == status_filter)
        if type_filter:
            query = query.filter(Resource.resource_type == type_filter)

        resources = query.all()
        all_resources = db.query(Resource).all()

        available_count = sum(1 for r in all_resources if r.status == "available")
        assigned_count = sum(1 for r in all_resources if r.status == "assigned")
        unavailable_count = sum(1 for r in all_resources if r.status == "unavailable")

        return {
            "resources": resources,
            "total": len(all_resources),
            "available": available_count,
            "assigned": assigned_count,
            "unavailable": unavailable_count
        }

    @staticmethod
    def get_resource_by_id(db: Session, resource_id: str) -> Resource:
        res = db.query(Resource).filter(Resource.id == resource_id).first()
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{resource_id}' not found."
            )
        return res
