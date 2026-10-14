import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.database import SessionLocal
from app.models.event import Event
from app.models.incident import Incident, IncidentHistory, IncidentNote
from app.models.resource import Resource
from app.models.audit import AuditLog
from app.models.venue import VenueEdge
from app.services.resource_service import ResourceService
from app.services.venue_service import VenueService
from app.services.routing_engine import RoutingEngine

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        VenueService.seed_default_venue(db)
        ResourceService.seed_default_resources(db)
        # Reset all resources to available for test isolation
        db.query(Resource).update({
            Resource.status: "available",
            Resource.assigned_incident_id: None
        })
        db.commit()
        yield db
    finally:
        # Reset any blocked walkways and clean test resources
        db.query(VenueEdge).filter(VenueEdge.venue_id == "venue_triveni").update({
            VenueEdge.is_blocked: False,
            VenueEdge.blocked_at: None,
            VenueEdge.blocked_by: None,
            VenueEdge.blockage_reason: None
        })
        db.query(Resource).update({
            Resource.status: "available",
            Resource.assigned_incident_id: None
        })
        db.commit()
        db.close()

def _create_test_event(db: Session, status: str = "acknowledged", zone_id: str = "zone_central_stage") -> Event:
    ev = Event(
        event_type="threshold",
        severity="high",
        person_count=45,
        rule_name="Stage Surge Rule",
        rule_threshold=30,
        zone_id=zone_id,
        camera_id="cam_stage_01",
        description="Observed high density crowd surge near stage",
        evidence_image_path="evidence/job_test_p6/frame_0001.jpg",
        status=status,
        reviewed_by="operator" if status != "pending_review" else None,
        reviewed_at=datetime.now(timezone.utc) if status != "pending_review" else None,
        review_notes="Verified crowd surge on camera" if status != "pending_review" else None
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


# =========================================================
# 1. Incident Creation & Event Eligibility Tests
# =========================================================

def test_create_incident_from_reviewed_event(client, db_session):
    """Eligible reviewed/acknowledged event successfully escalates into an incident."""
    ev = _create_test_event(db_session, status="acknowledged", zone_id="zone_central_stage")

    res = client.post(f"/api/v1/incidents/from-event/{ev.id}")
    assert res.status_code == 201
    data = res.json()

    assert data["event_id"] == ev.id
    assert "INC-" in data["incident_number"]
    assert data["severity"] == "high"
    assert data["status"] == "open"
    assert data["zone_id"] == "zone_central_stage"
    assert data["location_status"] == "confirmed"
    assert data["venue_id"] == "venue_triveni"


def test_ineligible_unreviewed_event_rejected(client, db_session):
    """Pending review events cannot be escalated to incidents (HTTP 422)."""
    ev = _create_test_event(db_session, status="pending_review")

    res = client.post(f"/api/v1/incidents/from-event/{ev.id}")
    assert res.status_code == 422
    assert "pending review" in res.json()["detail"]


def test_dismissed_event_rejected(client, db_session):
    """Dismissed events cannot be escalated to incidents (HTTP 422)."""
    ev = _create_test_event(db_session, status="dismissed")

    res = client.post(f"/api/v1/incidents/from-event/{ev.id}")
    assert res.status_code == 422
    assert "dismissed" in res.json()["detail"]


def test_nonexistent_source_event_rejected(client):
    """Escalating a non-existent event ID returns HTTP 404."""
    res = client.post("/api/v1/incidents/from-event/nonexistent_event_id_12345")
    assert res.status_code == 404


def test_duplicate_incident_creation_prevented(client, db_session):
    """Idempotency / conflict check prevents multiple incidents for the same source event (HTTP 409)."""
    ev = _create_test_event(db_session, status="acknowledged")

    res1 = client.post(f"/api/v1/incidents/from-event/{ev.id}")
    assert res1.status_code == 201

    res2 = client.post(f"/api/v1/incidents/from-event/{ev.id}")
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_source_event_remains_intact(client, db_session):
    """Source event fields and evidence references remain intact after escalation."""
    ev = _create_test_event(db_session, status="acknowledged")
    initial_desc = ev.description
    initial_path = ev.evidence_image_path

    res = client.post(f"/api/v1/incidents/from-event/{ev.id}")
    assert res.status_code == 201

    # Verify directly from DB
    reloaded_ev = db_session.query(Event).filter(Event.id == ev.id).first()
    assert reloaded_ev.description == initial_desc
    assert reloaded_ev.evidence_image_path == initial_path
    assert reloaded_ev.status == "acknowledged"


def test_unknown_location_remains_unknown(client, db_session):
    """Incident created without zone reference or with unmapped zone is marked unconfirmed/unknown."""
    res = client.post("/api/v1/incidents", json={
        "title": "Unlocated Distress Call",
        "description": "Reported distress from unmapped exterior area",
        "zone_id": "nonexistent_zone_999",
        "priority": "medium"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["location_status"] == "unconfirmed"


# =========================================================
# 2. Lifecycle & State Machine Transition Tests
# =========================================================

def test_valid_lifecycle_transitions(client, db_session):
    """Enforces valid progression: open -> acknowledged -> in_progress -> resolved -> closed."""
    res = client.post("/api/v1/incidents", json={
        "title": "Lifecycle Validation Test",
        "description": "Step-by-step state machine validation",
        "priority": "low"
    })
    assert res.status_code == 201
    inc_id = res.json()["id"]

    # 1. open -> acknowledged
    res_ack = client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "acknowledged"})
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "acknowledged"

    # 2. acknowledged -> in_progress
    res_prog = client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "in_progress"})
    assert res_prog.status_code == 200
    assert res_prog.json()["status"] == "in_progress"

    # 3. in_progress -> resolved (with mandatory notes)
    res_res = client.put(f"/api/v1/incidents/{inc_id}/status", json={
        "status": "resolved",
        "notes": "Situation stabilized and crowd dispersed safely."
    })
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "resolved"
    assert res_res.json()["resolved_at"] is not None

    # 4. resolved -> closed
    res_close = client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "closed", "notes": "Case archived."})
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "closed"


def test_invalid_status_transitions_rejected(client, db_session):
    """Rejects illegal lifecycle jumps (e.g. open -> closed, resolved -> open)."""
    res = client.post("/api/v1/incidents", json={
        "title": "Illegal Transition Test",
        "description": "Testing rejection of illegal status skips",
        "priority": "medium"
    })
    inc_id = res.json()["id"]

    # open -> closed is illegal (HTTP 409)
    res_bad = client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "closed"})
    assert res_bad.status_code == 409
    assert "Illegal transition" in res_bad.json()["detail"]


def test_resolution_notes_mandatory(client, db_session):
    """Marking an incident as resolved without notes is rejected (HTTP 422)."""
    res = client.post("/api/v1/incidents", json={
        "title": "Mandatory Notes Test",
        "description": "Testing missing resolution notes rejection",
        "priority": "medium"
    })
    inc_id = res.json()["id"]
    client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "acknowledged"})

    # Attempt resolve without notes
    res_res = client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "resolved", "notes": ""})
    assert res_res.status_code == 422
    assert "resolution summary note is mandatory" in res_res.json()["detail"]


def test_resolved_incident_cannot_be_reopened(client, db_session):
    """A resolved incident cannot silently jump back to open."""
    res = client.post("/api/v1/incidents", json={
        "title": "No Reopen Test",
        "description": "Verifying terminal state protections",
        "priority": "medium"
    })
    inc_id = res.json()["id"]
    client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "acknowledged"})
    client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "resolved", "notes": "Resolved properly."})

    # Attempt to reopen
    res_reopen = client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "open"})
    assert res_reopen.status_code == 409


# =========================================================
# 3. Simulated Resource Registry & Assignment Tests
# =========================================================

def test_resource_registry_seeded(client, db_session):
    """Simulated response resources are seeded and returned via API."""
    res = client.get("/api/v1/resources")
    assert res.status_code == 200
    data = res.json()

    assert data["total"] == 8
    assert len(data["resources"]) == 8
    assert data["available"] >= 1


def test_valid_resource_assignment(client, db_session):
    """Assigning a resource links unit, updates resource to 'assigned', and incident to 'in_progress'."""
    res_inc = client.post("/api/v1/incidents", json={
        "title": "Medical Incident",
        "description": "Crowd member requires first aid",
        "priority": "high",
        "zone_id": "zone_central_stage"
    })
    inc_id = res_inc.json()["id"]

    res_assign = client.post(f"/api/v1/incidents/{inc_id}/assign", json={"resource_id": "res_med_01"})
    assert res_assign.status_code == 200
    data = res_assign.json()

    assert data["status"] == "in_progress"
    assert data["assigned_resource"]["id"] == "res_med_01"
    assert data["assigned_resource"]["status"] == "assigned"

    # Verify resource record directly
    unit = db_session.query(Resource).filter(Resource.id == "res_med_01").first()
    assert unit.status == "assigned"
    assert unit.assigned_incident_id == inc_id


def test_double_resource_assignment_prevented(client, db_session):
    """A busy resource cannot be assigned to another active incident (HTTP 409)."""
    # Create incident 1 and assign unit
    res1 = client.post("/api/v1/incidents", json={"title": "Inc 1", "description": "Desc 1"})
    inc1_id = res1.json()["id"]
    client.post(f"/api/v1/incidents/{inc1_id}/assign", json={"resource_id": "res_sec_01"})

    # Create incident 2 and attempt assigning same unit
    res2 = client.post("/api/v1/incidents", json={"title": "Inc 2", "description": "Desc 2"})
    inc2_id = res2.json()["id"]
    res_conflict = client.post(f"/api/v1/incidents/{inc2_id}/assign", json={"resource_id": "res_sec_01"})
    assert res_conflict.status_code == 409
    assert "cannot be assigned" in res_conflict.json()["detail"]


def test_resource_release_succeeds(client, db_session):
    """Releasing a resource returns it to available status."""
    res_inc = client.post("/api/v1/incidents", json={"title": "Patrol Check", "description": "Desc"})
    inc_id = res_inc.json()["id"]
    client.post(f"/api/v1/incidents/{inc_id}/assign", json={"resource_id": "res_crw_01"})

    res_rel = client.post(f"/api/v1/incidents/{inc_id}/release")
    assert res_rel.status_code == 200
    assert res_rel.json()["assigned_resource"] is None

    # Check resource status
    db_session.expire_all()
    unit = db_session.query(Resource).filter(Resource.id == "res_crw_01").first()
    assert unit.status == "available"
    assert unit.assigned_incident_id is None


def test_resolved_incident_releases_resource(client, db_session):
    """Resolving an incident automatically releases any assigned resource."""
    res_inc = client.post("/api/v1/incidents", json={"title": "Crowd Bottleneck", "description": "Desc"})
    inc_id = res_inc.json()["id"]
    client.post(f"/api/v1/incidents/{inc_id}/assign", json={"resource_id": "res_crw_02"})

    # Resolve incident
    res_resolve = client.put(f"/api/v1/incidents/{inc_id}/status", json={
        "status": "resolved",
        "notes": "Bottleneck cleared; gates reopened."
    })
    assert res_resolve.status_code == 200

    # Resource must now be available
    db_session.expire_all()
    unit = db_session.query(Resource).filter(Resource.id == "res_crw_02").first()
    assert unit.status == "available"
    assert unit.assigned_incident_id is None


# =========================================================
# 4. Operator Notes & Audit Trail Tests
# =========================================================

def test_notes_persisted_and_validated(client, db_session):
    """Operator notes are persisted and linked to the incident."""
    res_inc = client.post("/api/v1/incidents", json={"title": "Notes Test", "description": "Desc"})
    inc_id = res_inc.json()["id"]

    res_note = client.post(f"/api/v1/incidents/{inc_id}/notes", json={
        "note_text": "Ambulance team en-route via West Perimeter."
    })
    assert res_note.status_code == 201
    assert res_note.json()["note_text"] == "Ambulance team en-route via West Perimeter."

    # Verify on incident detail
    detail = client.get(f"/api/v1/incidents/{inc_id}").json()
    assert len(detail["notes"]) == 1
    assert detail["notes"][0]["note_text"] == "Ambulance team en-route via West Perimeter."


def test_blank_note_rejected(client, db_session):
    """Empty or whitespace-only notes are rejected (HTTP 422)."""
    res_inc = client.post("/api/v1/incidents", json={"title": "Blank Note Test", "description": "Desc"})
    inc_id = res_inc.json()["id"]

    res_bad = client.post(f"/api/v1/incidents/{inc_id}/notes", json={"note_text": "   "})
    assert res_bad.status_code == 422


def test_history_order_and_actions(client, db_session):
    """Incident history records creation, status transitions, and assignments in order."""
    res_inc = client.post("/api/v1/incidents", json={"title": "History Test", "description": "Desc"})
    inc_id = res_inc.json()["id"]

    client.put(f"/api/v1/incidents/{inc_id}/status", json={"status": "acknowledged"})
    client.post(f"/api/v1/incidents/{inc_id}/assign", json={"resource_id": "res_sec_02"})

    history_res = client.get(f"/api/v1/incidents/{inc_id}/history")
    assert history_res.status_code == 200
    actions = [h["action"] for h in history_res.json()]

    assert "created" in actions
    assert "status_changed" in actions
    assert "resource_assigned" in actions


# =========================================================
# 5. GIS Routing Integration & Walkway Blockage
# =========================================================

def test_incident_gis_route_integration(client, db_session):
    """Verifies response route calculation from Main Gate to Central Stage respects blocked walkways."""
    # 1. Check clean route from Gate Main to Junction 4 (Stage area)
    res_route = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=junction_4")
    assert res_route.status_code == 200
    clean_data = res_route.json()
    assert clean_data["routes_found"] >= 1

    # 2. Block the primary walkway walk_1_4 (Central Stage Promenade)
    client.put("/api/v1/venue/edges/walk_1_4/block", json={"reason": "Hazard spill"})

    # 3. Route again - must exclude blocked edge and provide alternative or increased cost
    res_blocked = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=junction_4")
    assert res_blocked.status_code == 200
    blocked_data = res_blocked.json()
    assert "walk_1_4" in blocked_data["blocked_edges"]

    for r in blocked_data["routes"]:
        assert "walk_1_4" not in r["edge_ids"]


def test_incident_persistence_across_session(client, db_session):
    """Verifies created incident and status persist across database sessions."""
    res_inc = client.post("/api/v1/incidents", json={
        "title": "Persistent Incident",
        "description": "Must survive DB reload",
        "priority": "critical",
        "zone_id": "zone_central_stage"
    })
    inc_id = res_inc.json()["id"]

    # Commit and close session, open fresh session
    db_session.commit()
    db_session.close()

    new_db = SessionLocal()
    try:
        persisted = new_db.query(Incident).filter(Incident.id == inc_id).first()
        assert persisted is not None
        assert persisted.title == "Persistent Incident"
        assert persisted.severity == "critical"
    finally:
        new_db.close()
