import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.incident import Incident, IncidentHistory, IncidentNote
from app.models.event import Event
from app.models.resource import Resource
from app.models.venue import VenueZone
from app.models.audit import AuditLog

logger = logging.getLogger("nexora.incident_service")

VALID_STATUSES = {"open", "acknowledged", "in_progress", "resolved", "closed"}

class IncidentService:
    @staticmethod
    def create_incident(
        db: Session,
        title: str,
        description: str,
        zone_id: Optional[str] = None,
        venue_id: Optional[str] = "venue_triveni",
        severity: str = "medium",
        event_id: Optional[str] = None,
        created_by: str = "operator"
    ) -> Incident:
        """
        Creates an operational incident from a human-reviewed crowd event or operator report.
        Enforces idempotency, event review eligibility, and foreign key integrity.
        """
        title = title.strip()
        description = description.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Incident title cannot be empty."
            )
        if not description:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Incident description cannot be empty."
            )

        linked_event = None
        if event_id:
            linked_event = db.query(Event).filter(Event.id == event_id).first()
            if not linked_event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source crowd event '{event_id}' not found."
                )

            # Enforce Event Review Eligibility: Event must be human-reviewed!
            if linked_event.status == "pending_review":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Crowd event '{event_id}' is pending review. "
                        "It must be reviewed and acknowledged by an operator prior to escalating to an incident."
                    )
                )
            if linked_event.status == "dismissed":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Crowd event '{event_id}' has been dismissed as non-actionable/false positive."
                )

            # Enforce Idempotency / Duplicate Creation Prevention
            existing_for_event = db.query(Incident).filter(Incident.event_id == event_id).first()
            if existing_for_event:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"An incident already exists for event '{event_id}' "
                        f"(Incident ID: {existing_for_event.id}, Reference: {existing_for_event.incident_number})."
                    )
                )

            # Inherit zone_id and severity if not explicitly provided
            if not zone_id and linked_event.zone_id:
                zone_id = linked_event.zone_id
            if severity == "medium" and linked_event.severity:
                severity = linked_event.severity

        # Determine location status based on known venue zones
        location_status = "unknown"
        if zone_id and zone_id != "zone_unknown":
            known_zone = db.query(VenueZone).filter(VenueZone.id == zone_id).first()
            location_status = "confirmed" if known_zone else "unconfirmed"
        else:
            zone_id = "zone_unknown"
            location_status = "unknown"

        # Generate unique human-readable incident reference
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        incident_count = db.query(Incident).count() + 1
        incident_number = f"INC-{today_str}-{incident_count:03d}"
        while db.query(Incident).filter(Incident.incident_number == incident_number).first():
            incident_count += 1
            incident_number = f"INC-{today_str}-{incident_count:03d}"

        incident = Incident(
            id=str(uuid.uuid4()),
            incident_number=incident_number,
            title=title,
            description=description,
            venue_id=venue_id,
            zone_id=zone_id,
            location_status=location_status,
            severity=severity.lower(),
            status="open",
            event_id=event_id,
            created_by=created_by
        )
        db.add(incident)
        db.flush()

        # Record Initial History
        history = IncidentHistory(
            incident_id=incident.id,
            action="created",
            old_value=None,
            new_value="open",
            details={
                "title": title,
                "severity": severity,
                "event_id": event_id,
                "zone_id": zone_id,
                "location_status": location_status
            },
            performed_by=created_by
        )
        db.add(history)

        # Audit Log Entry
        audit = AuditLog(
            action_type="incident_created",
            entity_type="incident",
            entity_id=incident.id,
            actor_id=created_by,
            actor_role="operator",
            details={
                "incident_number": incident_number,
                "title": title,
                "event_id": event_id,
                "severity": severity
            }
        )
        db.add(audit)

        db.commit()
        db.refresh(incident)
        logger.info("Created incident %s (%s) for event %s", incident.incident_number, incident.id, event_id)
        return incident

    @staticmethod
    def create_incident_from_event(
        db: Session,
        event_id: str,
        operator: str = "operator"
    ) -> Incident:
        """
        Escalates a human-reviewed crowd alert event into an operational incident.
        Validates event existence and review eligibility.
        """
        linked_event = db.query(Event).filter(Event.id == event_id).first()
        if not linked_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source crowd event '{event_id}' not found."
            )

        title = f"Alert: {linked_event.rule_name or 'Crowd Surge'} in {linked_event.zone_id}"
        description = linked_event.description or (
            f"Escalated from VisionX crowd rule '{linked_event.rule_name}' "
            f"with peak observed person count {linked_event.person_count}."
        )

        return IncidentService.create_incident(
            db=db,
            title=title,
            description=description,
            zone_id=linked_event.zone_id,
            venue_id="venue_triveni",
            event_id=event_id,
            severity=linked_event.severity or "medium",
            created_by=operator
        )

    @staticmethod
    def list_incidents(
        db: Session,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        venue_filter: Optional[str] = None,
        zone_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        query = db.query(Incident)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(Incident.status == status_filter.lower())
        if severity_filter and severity_filter.upper() != "ALL":
            query = query.filter(Incident.severity == severity_filter.lower())
        if venue_filter:
            query = query.filter(Incident.venue_id == venue_filter)
        if zone_filter:
            query = query.filter(Incident.zone_id == zone_filter)

        total = query.count()
        incidents = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "incidents": incidents,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def get_incident_detail(db: Session, incident_id: str) -> Incident:
        incident = db.query(Incident).filter(
            (Incident.id == incident_id) | (Incident.incident_number == incident_id)
        ).first()

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found."
            )
        return incident

    @staticmethod
    def update_incident_status(
        db: Session,
        incident_id: str,
        new_status: str,
        notes: Optional[str] = None,
        operator: str = "operator"
    ) -> Incident:
        incident = IncidentService.get_incident_detail(db, incident_id)
        old_status = incident.status
        new_status = new_status.lower()

        if new_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid incident status '{new_status}'. Allowed values: {sorted(list(VALID_STATUSES))}."
            )

        if old_status == new_status:
            return incident

        # Enforce State Machine Transitions
        # Allowed transitions:
        # open -> acknowledged
        # open -> in_progress
        # acknowledged -> in_progress
        # acknowledged -> resolved (requires resolution notes)
        # in_progress -> resolved (requires resolution notes)
        # resolved -> closed
        valid_transitions = {
            "open": {"acknowledged", "in_progress"},
            "acknowledged": {"in_progress", "resolved"},
            "in_progress": {"resolved"},
            "resolved": {"closed"},
            "closed": set()
        }

        if new_status not in valid_transitions.get(old_status, set()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Illegal transition from '{old_status}' to '{new_status}'. "
                    f"Valid transitions from '{old_status}' are: {sorted(list(valid_transitions.get(old_status, set())))}."
                )
            )

        # Resolution requires mandatory resolution summary
        now = datetime.now(timezone.utc)
        if new_status == "resolved":
            if not notes or not notes.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="A resolution summary note is mandatory when marking an incident as resolved."
                )
            incident.resolved_at = now
            incident.resolved_by = operator
            incident.resolution_notes = notes.strip()

            # Automatically release any assigned resource on resolution
            if incident.assigned_resource_id:
                res = db.query(Resource).filter(Resource.id == incident.assigned_resource_id).first()
                if res:
                    res.status = "available"
                    res.assigned_incident_id = None
                incident.assigned_resource_id = None

        elif new_status == "acknowledged":
            incident.acknowledged_at = now
            incident.acknowledged_by = operator

        elif new_status == "closed":
            incident.closed_at = now
            incident.closed_by = operator

        incident.status = new_status

        # Record History
        history = IncidentHistory(
            incident_id=incident.id,
            action="status_changed",
            old_value=old_status,
            new_value=new_status,
            details={"notes": notes},
            performed_by=operator
        )
        db.add(history)

        # Audit Log Entry
        audit = AuditLog(
            action_type="incident_status_changed",
            entity_type="incident",
            entity_id=incident.id,
            actor_id=operator,
            actor_role="operator",
            details={
                "previous_status": old_status,
                "new_status": new_status,
                "notes": notes
            }
        )
        db.add(audit)

        db.commit()
        db.refresh(incident)
        logger.info("Incident %s transitioned from %s to %s by %s", incident.id, old_status, new_status, operator)
        return incident

    @staticmethod
    def assign_resource(
        db: Session,
        incident_id: str,
        resource_id: str,
        operator: str = "operator"
    ) -> Dict[str, Any]:
        incident = IncidentService.get_incident_detail(db, incident_id)

        # Incidents must be active to accept resource assignments
        if incident.status in {"resolved", "closed"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot assign resources to an incident in '{incident.status}' status."
            )

        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{resource_id}' not found."
            )

        if resource.status != "available":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource '{resource.name}' ({resource.call_sign}) is currently '{resource.status}' and cannot be assigned."
            )

        # Release prior assigned resource if one was attached
        if incident.assigned_resource_id and incident.assigned_resource_id != resource.id:
            prior_res = db.query(Resource).filter(Resource.id == incident.assigned_resource_id).first()
            if prior_res:
                prior_res.status = "available"
                prior_res.assigned_incident_id = None

        # Assign resource
        resource.status = "assigned"
        resource.assigned_incident_id = incident.id
        incident.assigned_resource_id = resource.id

        # Advance incident to in_progress if still in open or acknowledged
        if incident.status in {"open", "acknowledged"}:
            incident.status = "in_progress"

        # Record History
        history = IncidentHistory(
            incident_id=incident.id,
            action="resource_assigned",
            old_value=None,
            new_value=resource.name,
            details={"resource_id": resource.id, "call_sign": resource.call_sign},
            performed_by=operator
        )
        db.add(history)

        # Audit Log Entry
        audit = AuditLog(
            action_type="resource_assigned",
            entity_type="incident",
            entity_id=incident.id,
            actor_id=operator,
            actor_role="operator",
            details={
                "resource_id": resource.id,
                "resource_name": resource.name,
                "incident_number": incident.incident_number
            }
        )
        db.add(audit)

        db.commit()
        db.refresh(incident)
        logger.info("Assigned resource %s to incident %s", resource.name, incident.incident_number)
        return incident

    @staticmethod
    def release_resource(
        db: Session,
        incident_id: str,
        operator: str = "operator"
    ) -> Incident:
        incident = IncidentService.get_incident_detail(db, incident_id)
        if not incident.assigned_resource_id:
            return incident

        resource = db.query(Resource).filter(Resource.id == incident.assigned_resource_id).first()
        res_name = resource.name if resource else "Resource"
        if resource:
            resource.status = "available"
            resource.assigned_incident_id = None

        incident.assigned_resource_id = None

        history = IncidentHistory(
            incident_id=incident.id,
            action="resource_released",
            old_value=res_name,
            new_value=None,
            performed_by=operator
        )
        db.add(history)

        audit = AuditLog(
            action_type="resource_released",
            entity_type="incident",
            entity_id=incident.id,
            actor_id=operator,
            actor_role="operator",
            details={"resource_name": res_name}
        )
        db.add(audit)

        db.commit()
        db.refresh(incident)
        logger.info("Released resource %s from incident %s", res_name, incident.incident_number)
        return incident

    @staticmethod
    def add_incident_note(
        db: Session,
        incident_id: str,
        note_text: str,
        author: str = "operator"
    ) -> IncidentNote:
        incident = IncidentService.get_incident_detail(db, incident_id)
        note_text = note_text.strip()
        if not note_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Note text cannot be empty."
            )

        note = IncidentNote(
            incident_id=incident.id,
            note_text=note_text,
            author=author
        )
        db.add(note)

        history = IncidentHistory(
            incident_id=incident.id,
            action="note_added",
            details={"note_snippet": note_text[:50]},
            performed_by=author
        )
        db.add(history)

        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def update_location(
        db: Session,
        incident_id: str,
        venue_id: Optional[str],
        zone_id: str,
        operator: str = "operator"
    ) -> Incident:
        incident = IncidentService.get_incident_detail(db, incident_id)

        # Validate that zone belongs to venue
        known_zone = db.query(VenueZone).filter(VenueZone.id == zone_id).first()
        location_status = "confirmed" if known_zone else "unconfirmed"

        old_loc = f"{incident.venue_id}/{incident.zone_id}"
        incident.venue_id = venue_id or incident.venue_id or "venue_triveni"
        incident.zone_id = zone_id
        incident.location_status = location_status

        history = IncidentHistory(
            incident_id=incident.id,
            action="location_updated",
            old_value=old_loc,
            new_value=f"{incident.venue_id}/{zone_id}",
            details={"location_status": location_status},
            performed_by=operator
        )
        db.add(history)

        audit = AuditLog(
            action_type="incident_location_updated",
            entity_type="incident",
            entity_id=incident.id,
            actor_id=operator,
            actor_role="operator",
            details={"zone_id": zone_id, "location_status": location_status}
        )
        db.add(audit)

        db.commit()
        db.refresh(incident)
        return incident
