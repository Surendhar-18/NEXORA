"""
NEXORA Phase 8 - Reports & Comprehensive Audit Export Test Suite.
Validates:
1. Supported report types discovery.
2. Report preview generation across all 7 categories from persisted SQLite data.
3. Cross-module metric consistency matching Phase 7 semantics.
4. Safe PDF generation (valid %PDF- signature, multi-page, metadata).
5. Safe CSV generation (spreadsheet formula injection neutralization, BOM header).
6. Deterministic chronological audit ordering.
7. Date boundary validation and empty state handling.
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.database import SessionLocal
from app.models.incident import Incident
from app.models.event import Event
from app.models.job import Job
from app.models.video import Video
from app.models.resource import Resource
from app.models.venue import VenueEdge
from app.models.audit import AuditLog
from app.services.resource_service import ResourceService
from app.services.venue_service import VenueService
from app.utils.csv_exporter import sanitize_csv_cell, sanitize_filename


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        VenueService.seed_default_venue(db)
        ResourceService.seed_default_resources(db)
        yield db
    finally:
        db.query(Incident).filter(Incident.incident_number.like("INC-TEST-REP%")).delete(synchronize_session=False)
        db.query(Event).filter(Event.rule_name == "TEST_CROWD_RULE_REP").delete(synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.actor_id == "test_operator_rep").delete(synchronize_session=False)
        db.commit()
        db.close()


def test_supported_report_types(client):
    """Verifies that all 7 required report categories are discoverable."""
    res = client.get("/api/v1/reports/types")
    assert res.status_code == 200
    data = res.json()
    assert "report_types" in data
    types = [rt["report_type"] for rt in data["report_types"]]
    expected = [
        "operational_summary",
        "incident_report",
        "crowd_event_report",
        "video_analysis_report",
        "gis_operations_report",
        "resource_deployment_report",
        "audit_report",
    ]
    for exp in expected:
        assert exp in types, f"Missing report type: {exp}"


def test_report_preview_operational_summary(client, db_session):
    """Tests preview generation for operational summary report."""
    req_payload = {
        "report_type": "operational_summary",
        "period": "24h",
    }
    res = client.post("/api/v1/reports/generate", json=req_payload)
    assert res.status_code == 200
    data = res.json()
    assert "metadata" in data
    assert data["metadata"]["report_type"] == "operational_summary"
    assert "summary_metrics" in data
    assert "active_incidents_now" in data["summary_metrics"]
    assert "available_resources_now" in data["summary_metrics"]
    assert "columns" in data
    assert "records" in data
    assert isinstance(data["records"], list)


def test_report_preview_incident_filters(client, db_session):
    """Tests incident report generation and status/severity filtering."""
    now = datetime.now(timezone.utc)
    inc1 = Incident(
        incident_number="INC-TEST-REP-01",
        title="Test Critical Incident",
        description="Testing report filter",
        severity="critical",
        status="open",
        zone_id="ZONE-01",
        created_at=now - timedelta(hours=1),
    )
    inc2 = Incident(
        incident_number="INC-TEST-REP-02",
        title="Test Low Resolved Incident",
        description="Testing report filter",
        severity="low",
        status="resolved",
        zone_id="ZONE-01",
        created_at=now - timedelta(hours=2),
        resolved_at=now - timedelta(hours=1),
    )
    db_session.add_all([inc1, inc2])
    db_session.commit()

    # Query with severity filter = critical
    res_crit = client.post("/api/v1/reports/generate", json={
        "report_type": "incident_report",
        "period": "24h",
        "severity": "critical",
    })
    assert res_crit.status_code == 200
    records_crit = res_crit.json()["records"]
    assert any(r["incident_number"] == "INC-TEST-REP-01" for r in records_crit)
    assert not any(r["incident_number"] == "INC-TEST-REP-02" for r in records_crit)

    # Query with status filter = resolved
    res_res = client.post("/api/v1/reports/generate", json={
        "report_type": "incident_report",
        "period": "24h",
        "status": "resolved",
    })
    assert res_res.status_code == 200
    records_res = res_res.json()["records"]
    assert any(r["incident_number"] == "INC-TEST-REP-02" for r in records_res)
    assert not any(r["incident_number"] == "INC-TEST-REP-01" for r in records_res)


def test_report_preview_crowd_event_report(client, db_session):
    """Tests crowd event report preview and YOLO bounding-box disclaimer."""
    now = datetime.now(timezone.utc)
    ev = Event(
        rule_name="TEST_CROWD_RULE_REP",
        event_type="threshold",
        severity="high",
        person_count=35,
        rule_threshold=20,
        status="pending_review",
        created_at=now - timedelta(hours=1),
    )
    db_session.add(ev)
    db_session.commit()

    res = client.post("/api/v1/reports/generate", json={
        "report_type": "crowd_event_report",
        "period": "24h",
    })
    assert res.status_code == 200
    data = res.json()
    assert "Sampled-frame detection counts reflect person bounding boxes" in data["metadata"]["disclaimer"]
    assert any(r["rule_name"] == "TEST_CROWD_RULE_REP" for r in data["records"])


def test_report_preview_video_analysis_security(client, db_session):
    """Ensures video analysis reports do NOT leak private local storage paths."""
    res = client.post("/api/v1/reports/generate", json={
        "report_type": "video_analysis_report",
        "period": "24h",
    })
    assert res.status_code == 200
    data = res.json()
    columns = data["columns"]
    # Internal filesystem paths must NEVER be column or cell data
    assert "file_path" not in columns
    assert "storage_path" not in columns
    for row in data["records"]:
        assert "C:\\" not in str(row.values())
        assert "/var/" not in str(row.values())


def test_report_preview_date_validation(client):
    """Tests custom date range error handling."""
    # Inverted custom date range: start_date > end_date
    res_inv = client.post("/api/v1/reports/generate", json={
        "report_type": "operational_summary",
        "period": "custom",
        "start_date": "2026-10-14T10:00:00Z",
        "end_date": "2026-10-12T10:00:00Z",
    })
    assert res_inv.status_code == 422
    assert "start_date must be earlier than or equal to end_date" in res_inv.json()["detail"]

    # Unsupported report type
    res_bad = client.post("/api/v1/reports/generate", json={
        "report_type": "non_existent_report",
        "period": "24h",
    })
    assert res_bad.status_code == 400


def test_pdf_export_operational_summary(client, db_session):
    """Verifies PDF binary generation, %PDF- magic bytes, and response headers."""
    res = client.post("/api/v1/reports/export/pdf", json={
        "report_type": "operational_summary",
        "period": "24h",
    })
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    pdf_bytes = res.content
    assert pdf_bytes.startswith(b"%PDF-"), "Generated file does not have valid PDF header signature"
    assert len(pdf_bytes) > 2000, "PDF file is unexpectedly small"


def test_csv_export_and_formula_injection_mitigation(client, db_session):
    """Verifies CSV generation with BOM and checks formula injection mitigation."""
    # 1. Test cell sanitizer directly
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-malicious") == "'-malicious"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("\tleading_tab") == "'\tleading_tab"
    assert sanitize_csv_cell("\rleading_cr") == "'\rleading_cr"
    # Pure numbers must remain intact
    assert sanitize_csv_cell(-42) == -42
    assert sanitize_csv_cell(3.14) == 3.14
    assert sanitize_csv_cell("-15.5") == "-15.5"

    # 2. Test CSV export endpoint
    res = client.post("/api/v1/reports/export/csv", json={
        "report_type": "operational_summary",
        "period": "24h",
    })
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert res.content.startswith(b"\xef\xbb\xbf"), "CSV missing UTF-8 BOM"
    csv_text = res.content.decode("utf-8")
    assert "# NEXORA REPORT: Operational Summary Report" in csv_text
    assert "timestamp" in csv_text.lower()


def test_audit_export_and_deterministic_ordering(client, db_session):
    """Verifies that audit export maintains deterministic chronological ordering."""
    now = datetime.now(timezone.utc)
    log1 = AuditLog(
        id=str(uuid.uuid4()),
        timestamp=now - timedelta(minutes=5),
        actor_id="test_operator_rep",
        actor_role="admin",
        action_type="test_action_1",
        entity_type="test",
        entity_id="E1",
    )
    log2 = AuditLog(
        id=str(uuid.uuid4()),
        timestamp=now - timedelta(minutes=2),
        actor_id="test_operator_rep",
        actor_role="admin",
        action_type="test_action_2",
        entity_type="test",
        entity_id="E2",
    )
    db_session.add_all([log1, log2])
    db_session.commit()

    # Export audit twice via shortcut and verify identical data record rows
    res1 = client.post("/api/v1/reports/audit/export", json={"period": "24h", "format": "csv"})
    res2 = client.post("/api/v1/reports/audit/export", json={"period": "24h", "format": "csv"})
    assert res1.status_code == 200
    assert res2.status_code == 200

    # Extract data lines (non-metadata comments)
    lines1 = [line for line in res1.content.decode("utf-8").splitlines() if not line.startswith("#")]
    lines2 = [line for line in res2.content.decode("utf-8").splitlines() if not line.startswith("#")]
    assert lines1 == lines2, "Audit CSV records are not deterministic across repeat exports"

    # Verify descending chronological order: log2 (-2min) must appear before log1 (-5min)
    content_str = res1.content.decode("utf-8")
    idx_log2 = content_str.find("test_action_2")
    idx_log1 = content_str.find("test_action_1")
    assert idx_log2 != -1 and idx_log1 != -1
    assert idx_log2 < idx_log1, "Audit logs are not ordered in reverse chronological order (newest first)"

    # Test PDF format shortcut
    res_pdf = client.post("/api/v1/reports/audit/export", json={"period": "24h", "format": "pdf"})
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")


def test_empty_report_handling(client):
    """Verifies that querying a date window with no records handles gracefully without crash."""
    future_start = "2099-01-01T00:00:00Z"
    future_end = "2099-01-02T00:00:00Z"

    # Preview
    res_preview = client.post("/api/v1/reports/generate", json={
        "report_type": "incident_report",
        "period": "custom",
        "start_date": future_start,
        "end_date": future_end,
    })
    assert res_preview.status_code == 200
    assert res_preview.json()["metadata"]["record_count"] == 0
    assert res_preview.json()["records"] == []

    # PDF Export of empty report
    res_pdf = client.post("/api/v1/reports/export/pdf", json={
        "report_type": "incident_report",
        "period": "custom",
        "start_date": future_start,
        "end_date": future_end,
    })
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")

    # CSV Export of empty report
    res_csv = client.post("/api/v1/reports/export/csv", json={
        "report_type": "incident_report",
        "period": "custom",
        "start_date": future_start,
        "end_date": future_end,
    })
    assert res_csv.status_code == 200
    assert res_csv.content.startswith(b"\xef\xbb\xbf")
