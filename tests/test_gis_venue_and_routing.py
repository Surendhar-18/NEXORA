import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.database import get_db, SessionLocal
from app.models.venue import Venue, VenueZone, VenueNode, VenueEdge, VenueCamera
from app.models.event import Event
from app.models.audit import AuditLog
from app.services.venue_service import VenueService
from app.services.routing_engine import RoutingEngine

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        # Ensure default venue is seeded
        VenueService.seed_default_venue(db)
        yield db
    finally:
        # Reset any blocked walkways to unblocked for test isolation
        db.query(VenueEdge).filter(VenueEdge.venue_id == "venue_triveni").update({
            VenueEdge.is_blocked: False,
            VenueEdge.blocked_at: None,
            VenueEdge.blocked_by: None,
            VenueEdge.blockage_reason: None
        })
        db.commit()
        db.close()

# ---------------------------------------------------------
# 1. Venue & Graph Data Persistence Tests
# ---------------------------------------------------------

def test_venue_retrieval_and_seeded_structure(client, db_session):
    """Verifies default venue retrieval via API matching specification."""
    res = client.get("/api/v1/venue")
    assert res.status_code == 200
    data = res.json()

    assert data["venue_name"] == "Triveni Festival Grounds"
    assert data["center"]["latitude"] == pytest.approx(25.4358, rel=1e-3)
    assert data["center"]["longitude"] == pytest.approx(81.8463, rel=1e-3)
    assert len(data["zones"]) == 6
    assert len(data["nodes"]) == 12
    assert len(data["edges"]) == 16
    assert len(data["cameras"]) == 8

def test_venue_zones_integrity(client, db_session):
    """Verifies all configured venue zones exist with valid polygon coordinates."""
    res = client.get("/api/v1/venues/venue_triveni/zones")
    assert res.status_code == 200
    zones = res.json()
    assert len(zones) == 6

    zone_ids = [z["id"] for z in zones]
    expected_zones = [
        "zone_main_gate",
        "zone_north_plaza",
        "zone_east_wing",
        "zone_south_market",
        "zone_west_garden",
        "zone_central_stage"
    ]
    for ez in expected_zones:
        assert ez in zone_ids

    for z in zones:
        assert len(z["polygon"]) >= 3
        assert z["color"].startswith("#")

def test_venue_nodes_integrity(client, db_session):
    """Verifies routing graph nodes have valid types, coordinates, and zones."""
    res = client.get("/api/v1/venues/venue_triveni/nodes")
    assert res.status_code == 200
    nodes = res.json()
    assert len(nodes) == 12

    node_types = {n["node_type"] for n in nodes}
    assert "gate" in node_types
    assert "junction" in node_types
    assert "exit" in node_types

    # Coordinates must be valid latitudes and longitudes
    for n in nodes:
        assert 25.0 < n["latitude"] < 26.0
        assert 81.0 < n["longitude"] < 82.0
        assert n["is_active"] is True

def test_venue_edges_integrity(client, db_session):
    """Verifies walkway edges connect valid nodes with positive lengths."""
    res = client.get("/api/v1/venues/venue_triveni/edges")
    assert res.status_code == 200
    edges = res.json()
    assert len(edges) == 16

    nodes_res = client.get("/api/v1/venues/venue_triveni/nodes")
    node_ids = {n["id"] for n in nodes_res.json()}

    for e in edges:
        assert e["from_node"] in node_ids
        assert e["to_node"] in node_ids
        assert e["distance_meters"] > 0
        assert e["is_bidirectional"] is True
        assert e["is_blocked"] is False

# ---------------------------------------------------------
# 2. Route Calculation Tests
# ---------------------------------------------------------

def test_route_calculation_valid_path(client, db_session):
    """Verifies route calculation between valid nodes returns ordered path and distance."""
    res = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north&max_routes=3")
    assert res.status_code == 200
    data = res.json()

    assert data["routes_found"] >= 1
    assert data["from_node"] == "gate_main"
    assert data["to_node"] == "exit_north"

    best_route = data["routes"][0]
    assert best_route["rank"] == 1
    assert best_route["is_best"] is True
    assert best_route["path"][0] == "gate_main"
    assert best_route["path"][-1] == "exit_north"
    assert best_route["distance_meters"] > 0
    assert best_route["total_cost"] >= best_route["distance_meters"]
    assert len(best_route["segments"]) == len(best_route["path"]) - 1
    assert "advisory_notice" in data

def test_route_alternatives_ranking(client, db_session):
    """Verifies Yen's algorithm computes ranked alternative paths."""
    res = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north&max_routes=3")
    assert res.status_code == 200
    data = res.json()

    assert data["routes_found"] == 3
    routes = data["routes"]
    # Ranks must be 1, 2, 3 in ascending cost order
    assert routes[0]["rank"] == 1 and routes[0]["is_best"] is True
    assert routes[1]["rank"] == 2 and routes[1]["is_best"] is False
    assert routes[2]["rank"] == 3 and routes[2]["is_best"] is False

    assert routes[0]["total_cost"] <= routes[1]["total_cost"]
    assert routes[1]["total_cost"] <= routes[2]["total_cost"]

def test_route_calculation_invalid_endpoints(client, db_session):
    """Verifies 404 for nonexistent node and 422 for identical origin/destination."""
    # Nonexistent origin
    res1 = client.get("/api/v1/routes/compare?from_node=gate_ghost&to_node=exit_north")
    assert res1.status_code == 404

    # Nonexistent destination
    res2 = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_ghost")
    assert res2.status_code == 404

    # Same origin and destination
    res3 = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=gate_main")
    assert res3.status_code == 422

# ---------------------------------------------------------
# 3. Walkway Block & Reopen Lifecycle Tests
# ---------------------------------------------------------

def test_block_and_reopen_walkway_lifecycle(client, db_session):
    """Tests blocking an available walkway and reopening it with audit trail."""
    edge_id = "walk_1_2"

    # 1. Block walkway
    block_res = client.put(
        f"/api/v1/venue/edges/{edge_id}/block",
        json={"reason": "Hazardous spill diversion"}
    )
    assert block_res.status_code == 200
    block_data = block_res.json()
    assert block_data["id"] == edge_id
    assert block_data["is_blocked"] is True
    assert block_data["blockage_reason"] == "Hazardous spill diversion"

    # 2. Verify 409 Conflict when blocking already blocked walkway
    conflict_res = client.put(
        f"/api/v1/venue/edges/{edge_id}/block",
        json={"reason": "Duplicate block"}
    )
    assert conflict_res.status_code == 409

    # 3. Verify audit log created
    audit = db_session.query(AuditLog).filter(
        AuditLog.action_type == "walkway_blocked",
        AuditLog.entity_id == edge_id
    ).order_by(AuditLog.timestamp.desc()).first()
    assert audit is not None
    assert audit.details["action"] == "block"
    assert audit.details["reason"] == "Hazardous spill diversion"

    # 4. Reopen walkway
    reopen_res = client.put(f"/api/v1/venue/edges/{edge_id}/reopen")
    assert reopen_res.status_code == 200
    reopen_data = reopen_res.json()
    assert reopen_data["is_blocked"] is False
    assert reopen_data["blockage_reason"] is None

    # 5. Verify 409 Conflict when reopening already open walkway
    reopen_conflict = client.put(f"/api/v1/venue/edges/{edge_id}/reopen")
    assert reopen_conflict.status_code == 409

    # 6. Verify audit log for reopen
    reopen_audit = db_session.query(AuditLog).filter(
        AuditLog.action_type == "walkway_reopened",
        AuditLog.entity_id == edge_id
    ).first()
    assert reopen_audit is not None
    assert reopen_audit.details["action"] == "reopen"

def test_block_walkway_not_found(client, db_session):
    """Verifies 404 for invalid walkway ID."""
    res = client.put("/api/v1/venue/edges/walkway_ghost/block", json={"reason": "test"})
    assert res.status_code == 404

# ---------------------------------------------------------
# 4. Detour & No-Route Verification Tests
# ---------------------------------------------------------

def test_blocked_walkway_forces_reroute(client, db_session):
    """
    Verifies that blocking a primary walkway forces the routing engine
    to detour through an alternative valid path.
    """
    # Baseline route from gate_main to exit_north
    base_res = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north")
    assert base_res.status_code == 200
    base_route = base_res.json()["routes"][0]
    assert "walk_1_2" in base_route["edge_ids"]

    # Block walk_1_2
    client.put("/api/v1/venue/edges/walk_1_2/block", json={"reason": "Simulated blockage"})

    # Recalculate route
    detour_res = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north")
    assert detour_res.status_code == 200
    detour_data = detour_res.json()
    assert detour_data["routes_found"] >= 1

    # Verify new best route strictly excludes the blocked edge walk_1_2
    new_best = detour_data["routes"][0]
    assert "walk_1_2" not in new_best["edge_ids"]
    assert "walk_1_2" in detour_data["blocked_edges"]
    assert new_best["total_cost"] > base_route["total_cost"]

def test_no_valid_route_when_graph_is_disconnected(client, db_session):
    """
    Verifies that blocking the only path to an exit returns routes_found=0
    and an explicit explanation rather than fabricating a route.
    """
    # Block walk_5_exit_s, which isolates exit_south
    client.put("/api/v1/venue/edges/walk_5_exit_s/block", json={"reason": "Perimeter gate maintenance"})

    res = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_south")
    assert res.status_code == 200
    data = res.json()

    assert data["routes_found"] == 0
    assert data["routes"] == []
    assert "walk_5_exit_s" in data["blocked_edges"]
    assert "No valid route exists" in data["message"]
    assert "advisory_notice" in data

# ---------------------------------------------------------
# 5. Zone & Phase 4 Crowd Event Linkage Tests
# ---------------------------------------------------------

def test_event_zone_linkage(client, db_session):
    """Verifies that crowd events associate with configured venue zones."""
    import uuid
    test_evt_id = f"evt-gis-{uuid.uuid4().hex[:8]}"

    # Seed an event linked to zone_main_gate
    ev = Event(
        id=test_evt_id,
        zone_id="zone_main_gate",
        event_type="threshold_surge",
        severity="high",
        person_count=35,
        rule_name="Surge Threshold Rule",
        rule_threshold=15,
        status="pending_review",
        description="High crowd count near Main Gate ingress"
    )
    db_session.add(ev)
    db_session.commit()

    # Query event detail
    res = client.get(f"/api/v1/events/{test_evt_id}")
    assert res.status_code == 200
    event_data = res.json()
    assert event_data["zone_id"] == "zone_main_gate"

    # Query venue zone to ensure zone exists in topology
    zone_res = client.get("/api/v1/venues/venue_triveni/zones")
    assert zone_res.status_code == 200
    matched_zone = next((z for z in zone_res.json() if z["id"] == event_data["zone_id"]), None)
    assert matched_zone is not None
    assert matched_zone["name"] == "Main Gate Area"

    # Clean up test event
    db_session.query(Event).filter(Event.id == test_evt_id).delete()
    db_session.commit()

# ---------------------------------------------------------
# 6. End-to-End GIS & Routing Demonstration Test
# ---------------------------------------------------------

def test_end_to_end_gis_routing_and_recovery_flow(client, db_session):
    """
    Complete end-to-end integration test:
    1. Operator loads venue GIS topology
    2. Verifies open walkways
    3. Calculates primary route from gate_main to exit_north
    4. Operator blocks walk_1_2 due to congestion
    5. Operator recalculates route -> obtains verified alternative detour
    6. Operator reopens walk_1_2 -> verifies primary shortest path is restored
    """
    # 1. Load venue
    venue_res = client.get("/api/v1/venue")
    assert venue_res.status_code == 200
    assert venue_res.json()["venue_name"] == "Triveni Festival Grounds"

    # 2. Initial route
    r1 = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north&max_routes=3")
    assert r1.status_code == 200
    initial_best = r1.json()["routes"][0]
    assert initial_best["path"] == ["gate_main", "junction_1", "junction_2", "junction_7", "exit_north"]
    initial_cost = initial_best["total_cost"]

    # 3. Block walk_1_2
    b_res = client.put("/api/v1/venue/edges/walk_1_2/block", json={"reason": "Live operator simulation"})
    assert b_res.status_code == 200
    assert b_res.json()["is_blocked"] is True

    # 4. Reroute
    r2 = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north&max_routes=3")
    assert r2.status_code == 200
    detour_best = r2.json()["routes"][0]
    assert "walk_1_2" not in detour_best["edge_ids"]
    assert detour_best["total_cost"] > initial_cost

    # 5. Reopen walk_1_2
    ro_res = client.put("/api/v1/venue/edges/walk_1_2/reopen")
    assert ro_res.status_code == 200
    assert ro_res.json()["is_blocked"] is False

    # 6. Restored route
    r3 = client.get("/api/v1/routes/compare?from_node=gate_main&to_node=exit_north&max_routes=3")
    assert r3.status_code == 200
    restored_best = r3.json()["routes"][0]
    assert restored_best["path"] == ["gate_main", "junction_1", "junction_2", "junction_7", "exit_north"]
    assert restored_best["total_cost"] == initial_cost
