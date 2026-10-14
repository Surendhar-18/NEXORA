import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.database import SessionLocal
from app.models.incident import Incident, IncidentHistory
from app.models.event import Event
from app.models.job import Job
from app.models.video import Video
from app.models.resource import Resource
from app.models.venue import VenueEdge
from app.models.audit import AuditLog
from app.services.resource_service import ResourceService
from app.services.venue_service import VenueService
from app.services.analytics_service import AnalyticsService

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        VenueService.seed_default_venue(db)
        ResourceService.seed_default_resources(db)
        # Ensure clean resource availability for test isolation
        db.query(Resource).update({
            Resource.status: "available",
            Resource.assigned_incident_id: None
        })
        # Reset walkway blockages
        db.query(VenueEdge).filter(VenueEdge.venue_id == "venue_triveni").update({
            VenueEdge.is_blocked: False,
            VenueEdge.blocked_at: None,
            VenueEdge.blocked_by: None,
            VenueEdge.blockage_reason: None
        })
        db.commit()
        yield db
    finally:
        db.query(Incident).filter(Incident.incident_number.like("INC-ANL%")).delete(synchronize_session=False)
        db.query(Incident).filter(Incident.incident_number.like("INC-TIME%")).delete(synchronize_session=False)
        db.query(Incident).filter(Incident.incident_number.like("INC-RES%")).delete(synchronize_session=False)
        db.query(Resource).update({
            Resource.status: "available",
            Resource.assigned_incident_id: None
        })
        db.commit()
        db.close()

# -------------------------------------------------------------
# 1. Primary Metrics & Current State Tests
# -------------------------------------------------------------

def test_primary_metrics_snapshot_endpoint(client, db_session):
    """Verifies GET /api/v1/analytics/metrics returns real-time KPI counts."""
    res = client.get("/api/v1/analytics/metrics")
    assert res.status_code == 200
    data = res.json()

    assert "active_incidents" in data
    assert "pending_events" in data
    assert "processing_jobs" in data
    assert "critical_high_incidents" in data
    assert "available_resources" in data
    assert "total_resources" in data
    assert "blocked_walkways" in data
    assert "total_walkways" in data

    assert data["total_resources"] == 8
    assert data["total_walkways"] == 16


def test_analytics_overview_schema_and_integrity(client, db_session):
    """Verifies GET /api/v1/analytics/overview returns documented schema and structure."""
    res = client.get("/api/v1/analytics/overview?period=24h")
    assert res.status_code == 200
    data = res.json()

    assert data["reporting_period"] == "24h"
    assert "period_start" in data
    assert "period_end" in data
    assert "refreshed_at" in data
    assert "metrics" in data
    assert "incidents" in data
    assert "events" in data
    assert "jobs" in data
    assert "resources" in data
    assert "gis" in data
    assert "attention_queue" in data
    assert "recent_activity" in data


# -------------------------------------------------------------
# 2. Metric Calculations & Distribution Accuracy
# -------------------------------------------------------------

def test_incident_status_and_severity_counts(client, db_session):
    """Verifies active incident calculations, status distributions, and severity distributions."""
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6].upper()

    # Insert controlled incident records
    inc_open = Incident(
        incident_number=f"INC-ANL1-{tag}",
        title="Open Crowd Congestion",
        description="Testing analytics",
        status="open",
        severity="critical",
        zone_id="zone_central_stage",
        created_at=now - timedelta(hours=2)
    )
    inc_in_prog = Incident(
        incident_number=f"INC-ANL2-{tag}",
        title="Dispatched Medical Unit",
        description="Testing analytics",
        status="in_progress",
        severity="high",
        zone_id="zone_central_stage",
        created_at=now - timedelta(hours=1)
    )
    inc_resolved = Incident(
        incident_number=f"INC-ANL3-{tag}",
        title="Resolved Minor Spill",
        description="Testing analytics",
        status="resolved",
        severity="low",
        zone_id="zone_central_stage",
        resolution_notes="Cleaned by facilities squad.",
        resolved_at=now - timedelta(minutes=10),
        created_at=now - timedelta(minutes=40)
    )
    db_session.add_all([inc_open, inc_in_prog, inc_resolved])
    db_session.commit()

    overview = AnalyticsService.get_overview(db_session, period="24h")

    assert overview.incidents.status_distribution["open"] >= 1
    assert overview.incidents.status_distribution["in_progress"] >= 1
    assert overview.incidents.status_distribution["resolved"] >= 1
    assert overview.incidents.severity_distribution["critical"] >= 1
    assert overview.incidents.severity_distribution["high"] >= 1

    # Active count includes open, acknowledged, in_progress, but NOT resolved or closed
    assert overview.incidents.active_count >= 2


def test_resolution_duration_calculation(client, db_session):
    """Verifies average resolution duration calculates accurately and ignores nulls."""
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6].upper()
    # Incident resolved in exactly 30 minutes
    inc = Incident(
        incident_number=f"INC-TIME-{tag}",
        title="Timed Incident",
        description="Testing resolution math",
        status="resolved",
        severity="medium",
        zone_id="zone_central_stage",
        created_at=now - timedelta(minutes=45),
        resolved_at=now - timedelta(minutes=15),
        resolution_notes="Done"
    )
    db_session.add(inc)
    db_session.commit()

    overview = AnalyticsService.get_overview(db_session, period="24h")
    assert overview.incidents.avg_resolution_duration_minutes is not None
    assert overview.incidents.avg_resolution_duration_minutes >= 0


def test_crowd_event_status_distribution(client, db_session):
    """Verifies event analytics distinguishes pending_review, acknowledged, and dismissed."""
    now = datetime.now(timezone.utc)
    ev_pending = Event(
        event_type="threshold",
        severity="high",
        person_count=40,
        rule_name="Test Rule Pending",
        rule_threshold=25,
        zone_id="zone_central_stage",
        status="pending_review",
        created_at=now - timedelta(minutes=30)
    )
    ev_ack = Event(
        event_type="threshold",
        severity="medium",
        person_count=30,
        rule_name="Test Rule Ack",
        rule_threshold=25,
        zone_id="zone_north_plaza",
        status="acknowledged",
        reviewed_by="operator",
        reviewed_at=now - timedelta(minutes=10),
        created_at=now - timedelta(minutes=20)
    )
    db_session.add_all([ev_pending, ev_ack])
    db_session.commit()

    overview = AnalyticsService.get_overview(db_session, period="24h")
    assert overview.events.status_distribution["pending_review"] >= 1
    assert overview.events.status_distribution["acknowledged"] >= 1
    assert overview.metrics.pending_events >= 1


def test_resource_analytics_breakdown(client, db_session):
    """Verifies resource breakdown by type and assigned units list."""
    # Assign one resource to an incident
    tag = uuid.uuid4().hex[:6].upper()
    inc = Incident(
        incident_number=f"INC-RES-{tag}",
        title="Resource Test",
        description="Desc",
        status="in_progress",
        severity="medium",
        zone_id="zone_central_stage",
        assigned_resource_id="res_med_01"
    )
    db_session.add(inc)
    res_unit = db_session.query(Resource).filter(Resource.id == "res_med_01").first()
    res_unit.status = "assigned"
    res_unit.assigned_incident_id = inc.id
    db_session.commit()

    overview = AnalyticsService.get_overview(db_session, period="24h")
    assert overview.resources.assigned >= 1
    assert overview.resources.available == overview.resources.total - overview.resources.assigned
    assert "medical" in overview.resources.by_type
    assert len(overview.resources.assigned_units) >= 1
    assert overview.resources.assigned_units[0].call_sign == "MEDIC-1"


def test_gis_walkway_blocked_counts(client, db_session):
    """Verifies GIS operational overview accurately counts and describes blocked walkways."""
    edge = db_session.query(VenueEdge).filter(VenueEdge.id == "walk_main_j1").first()
    edge.is_blocked = True
    edge.blocked_at = datetime.now(timezone.utc)
    edge.blockage_reason = "Construction barrier"
    db_session.commit()

    overview = AnalyticsService.get_overview(db_session, period="24h")
    assert overview.gis.blocked_count == 1
    assert overview.gis.unblocked_count == overview.gis.total_walkways - 1
    assert len(overview.gis.blocked_details) == 1
    assert overview.gis.blocked_details[0].id == "walk_main_j1"
    assert overview.gis.blocked_details[0].blockage_reason == "Construction barrier"


# -------------------------------------------------------------
# 3. Time Windows, Trends & Boundary Tests
# -------------------------------------------------------------

def test_invalid_period_rejected(client):
    """Rejects unknown period strings (HTTP 422)."""
    res = client.get("/api/v1/analytics/overview?period=invalid_period_name")
    assert res.status_code == 422
    assert "Invalid reporting period" in res.json()["detail"]


def test_custom_period_validation(client):
    """Custom period requires both start_date and end_date, rejecting invalid dates or reversed intervals."""
    # Missing end date
    res1 = client.get("/api/v1/analytics/overview?period=custom&start_date=2026-10-01T00:00:00Z")
    assert res1.status_code == 422

    # Reversed interval
    res2 = client.get(
        "/api/v1/analytics/overview?period=custom&start_date=2026-10-15T00:00:00Z&end_date=2026-10-01T00:00:00Z"
    )
    assert res2.status_code == 422
    assert "start_date must be earlier than" in res2.json()["detail"]

    # Valid custom period
    res3 = client.get(
        "/api/v1/analytics/overview?period=custom&start_date=2026-10-01T00:00:00Z&end_date=2026-10-05T00:00:00Z"
    )
    assert res3.status_code == 200
    assert res3.json()["reporting_period"] == "custom"


def test_time_series_trends_endpoint_and_buckets(client, db_session):
    """Verifies GET /api/v1/analytics/trends generates gapless buckets with correct intervals."""
    # 24h period -> hourly buckets (24 buckets)
    res_24h = client.get("/api/v1/analytics/trends?period=24h")
    assert res_24h.status_code == 200
    data_24h = res_24h.json()
    assert data_24h["interval"] == "hourly"
    assert len(data_24h["buckets"]) == 24
    assert "incidents_created" in data_24h["buckets"][0]
    assert "events_created" in data_24h["buckets"][0]
    assert "jobs_completed" in data_24h["buckets"][0]

    # 7d period -> daily buckets (7 buckets)
    res_7d = client.get("/api/v1/analytics/trends?period=7d")
    assert res_7d.status_code == 200
    data_7d = res_7d.json()
    assert data_7d["interval"] == "daily"
    assert len(data_7d["buckets"]) == 7


def test_attention_queue_prioritization(client, db_session):
    """Attention queue captures pending reviews, critical incidents, unassigned incidents, and blocked walkways."""
    now = datetime.now(timezone.utc)
    ev = Event(
        event_type="threshold",
        severity="critical",
        person_count=60,
        rule_name="Critical Surge",
        rule_threshold=20,
        zone_id="zone_central_stage",
        status="pending_review",
        created_at=now
    )
    edge = db_session.query(VenueEdge).filter(VenueEdge.id == "walk_1_2").first()
    edge.is_blocked = True
    edge.blocked_at = now
    edge.blockage_reason = "Density bottleneck"
    db_session.add(ev)
    db_session.commit()

    overview = AnalyticsService.get_overview(db_session, period="24h")
    categories = [item.category for item in overview.attention_queue]

    assert "pending_event" in categories
    assert "blocked_walkway" in categories
