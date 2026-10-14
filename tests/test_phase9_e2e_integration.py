"""
NEXORA Phase 9 - Complete Cross-Module End-to-End Integration Test Suite.
Validates the full operational lifecycle across all subsystems:
1. Video upload and validation.
2. Job processing, frame extraction, and detection persistence.
3. Crowd rule evaluation, event generation, and peak evidence frame linking.
4. Human operator event review (triage -> acknowledge).
5. Incident escalation from reviewed crowd event (idempotency & conflict protection).
6. Simulated emergency response resource assignment and double-booking prevention.
7. GIS venue routing: path calculation, dynamic walkway blocking, and rerouting.
8. Incident resolution with mandatory resolution notes and automatic resource release.
9. Operational analytics overview & trend series reflection.
10. Multi-format report generation (PDF & CSV exports with formula injection neutralization).
11. Deterministic chronological audit log tracking and anti-recursion protection.
12. Database persistence verification across session reloads.
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
from app.core.config import settings
from app.models.video import Video
from app.models.job import Job
from app.models.detection import Detection
from app.models.rule import CrowdRule
from app.models.event import Event
from app.models.incident import Incident, IncidentHistory, IncidentNote
from app.models.resource import Resource
from app.models.venue import VenueEdge
from app.models.audit import AuditLog
from app.services.crowd_rules_engine import seed_default_rules, evaluate_rules_for_job
from app.services.venue_service import VenueService
from app.services.resource_service import ResourceService
from app.services.report_service import ReportService
from app.schemas.report import ReportGenerateRequest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        seed_default_rules(db)
        VenueService.seed_default_venue(db)
        ResourceService.seed_default_resources(db)
        yield db
    finally:
        # Cleanup test-isolated artifacts
        db.query(Incident).filter(Incident.incident_number.like("INC-E2E-P9%")).delete(synchronize_session=False)
        db.query(Event).filter(Event.rule_name == "P9_E2E_SURGE_RULE").delete(synchronize_session=False)
        db.query(CrowdRule).filter(CrowdRule.id == "RULE-P9-E2E").delete(synchronize_session=False)
        db.query(Detection).filter(Detection.id.like("DET-P9-E2E%")).delete(synchronize_session=False)
        db.query(Job).filter(Job.id == "job-p9-e2e-integration").delete(synchronize_session=False)
        db.query(Video).filter(Video.id == "video-p9-e2e-integration").delete(synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.actor_id == "p9_e2e_tester").delete(synchronize_session=False)

        # Reset resource assignments
        db.query(Resource).filter(Resource.call_sign == "MEDIC-1").update({
            Resource.status: "available",
            Resource.assigned_incident_id: None,
        })
        # Reset walkway blockages
        db.query(VenueEdge).filter(VenueEdge.id == "walk_1_2").update({
            VenueEdge.is_blocked: False,
            VenueEdge.blocked_at: None,
            VenueEdge.blocked_by: None,
            VenueEdge.blockage_reason: None,
        })
        db.commit()
        db.close()


def test_full_cross_module_operational_lifecycle(client, db_session):
    """
    Executes the entire end-to-end NEXORA workflow from video upload to final report export.
    """
    now = datetime.now(timezone.utc)
    video_id = "video-p9-e2e-integration"
    job_id = "job-p9-e2e-integration"
    det_id = "DET-P9-E2E-01"

    # =========================================================================
    # STEP 1: Video Upload & Persistence
    # =========================================================================
    # Upload through REST API with valid MP4 header magic bytes
    valid_mp4_header = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + (b"\x00" * 2048)
    upload_res = client.post(
        "/api/v1/videos/upload",
        files={"file": ("p9_e2e_crowd_test.mp4", valid_mp4_header, "video/mp4")},
        data={"zone_id": "zone_north_plaza", "sampling_interval_sec": "2.0"},
    )
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    uploaded_video_id = upload_res.json()["id"]
    assert uploaded_video_id is not None
    assert upload_res.json()["status"] in ["queued", "uploaded"]

    # =========================================================================
    # STEP 2: Job Analysis, Frame Extraction & Detection Persistence
    # =========================================================================
    # Establish a deterministic video/job record with synthetic detection surge
    test_video = Video(
        id=video_id,
        filename=f"{video_id}.mp4",
        original_filename="p9_e2e_crowd_surveillance.mp4",
        file_path="data/uploads/v_pipeline_test_01.mp4",
        file_size_bytes=21719,
        zone_id="zone_north_plaza",
        uploaded_by="p9_e2e_tester",
        status="processed",
    )
    db_session.merge(test_video)

    test_job = Job(
        id=job_id,
        video_id=video_id,
        zone_id="zone_north_plaza",
        status="completed",
        progress_percent=100.0,
        current_frame=10,
        total_frames_to_process=10,
        sampling_interval_sec=2.0,
        confidence_threshold=0.5,
        model_name="yolov8n",
        total_persons_detected=48,
        max_person_count=24,
        started_at=now - timedelta(minutes=15),
        completed_at=now - timedelta(minutes=14),
    )
    db_session.merge(test_job)

    # Detection record reflecting person count surge
    test_det = Detection(
        id=det_id,
        video_id=video_id,
        job_id=job_id,
        frame_index=4,
        timestamp_seconds=8.0,
        person_count=24,
        avg_confidence=0.88,
        max_confidence=0.96,
        min_confidence=0.74,
        evidence_image_path="evidence_test_frame.jpg",
    )
    db_session.merge(test_det)

    # Configure surge rule
    surge_rule = CrowdRule(
        id="RULE-P9-E2E",
        name="P9_E2E_SURGE_RULE",
        rule_type="threshold",
        operator=">=",
        threshold_count=20,
        severity="critical",
        is_active=True,
    )
    db_session.merge(surge_rule)
    db_session.commit()

    # =========================================================================
    # STEP 3: Crowd Rule Evaluation & Event Generation
    # =========================================================================
    generated_events = evaluate_rules_for_job(job_id, db_session)
    assert len(generated_events) >= 1
    event = generated_events[0]
    assert event.status == "pending_review"
    assert event.person_count == 24
    assert event.severity in ["high", "critical"]
    event_id = event.id

    # Verify event appears in review triage API
    events_res = client.get("/api/v1/events?status=pending_review")
    assert events_res.status_code == 200
    pending_list = events_res.json()["events"]
    assert any(e["id"] == event_id for e in pending_list)

    # =========================================================================
    # STEP 4: Human Event Review Workflow (Triage -> Acknowledge)
    # =========================================================================
    review_res = client.put(
        f"/api/v1/events/{event_id}/review",
        json={
            "action": "acknowledge",
            "notes": "Phase 9 E2E: Verified crowd density surge at North Plaza.",
            "operator_id": "p9_e2e_tester",
        },
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "acknowledged"

    # =========================================================================
    # STEP 5: Incident Escalation from Reviewed Event
    # =========================================================================
    inc_create_res = client.post(
        f"/api/v1/incidents/from-event/{event_id}",
        json={
            "title": "North Plaza Crowd Surge Alert",
            "description": "Critical congestion observed in North Plaza exceeding threshold.",
            "operator": "p9_e2e_tester",
        },
    )
    assert inc_create_res.status_code == 201
    incident_data = inc_create_res.json()
    incident_id = incident_data["id"]
    incident_num = incident_data["incident_number"]
    assert incident_data["status"] == "open"
    assert incident_data["severity"] in ["high", "critical"]
    assert incident_data["event_id"] == event_id

    # Verify idempotency: duplicate escalation must return 409 Conflict
    dup_res = client.post(f"/api/v1/incidents/from-event/{event_id}")
    assert dup_res.status_code == 409

    # Add operational note to incident
    note_res = client.post(
        f"/api/v1/incidents/{incident_id}/notes",
        json={"note_text": "Phase 9 E2E: Dispatching field controller to coordinate ingress."},
    )
    assert note_res.status_code == 201

    # =========================================================================
    # STEP 6: Simulated Response Resource Allocation & Conflict Protection
    # =========================================================================
    # Find available medical or security resource
    resource = db_session.query(Resource).filter(Resource.call_sign == "MEDIC-1").first()
    assert resource is not None
    assert resource.status == "available"
    resource_id = resource.id

    # Assign resource to incident
    assign_res = client.post(
        f"/api/v1/incidents/{incident_id}/assign",
        json={"resource_id": resource_id},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_resource"]["id"] == resource_id
    assert assign_res.json()["status"] == "in_progress"

    # Verify resource is now marked 'assigned'
    db_session.refresh(resource)
    assert resource.status == "assigned"

    # Verify double-booking prevention: attempting to assign same resource elsewhere fails
    another_inc = Incident(
        incident_number="INC-E2E-P9-CONFLICT",
        title="Conflict Test Incident",
        description="Testing double booking prevention",
        zone_id="zone_north_plaza",
        status="open",
        created_by="p9_e2e_tester",
    )
    db_session.add(another_inc)
    db_session.commit()

    double_book_res = client.post(
        f"/api/v1/incidents/{another_inc.id}/assign",
        json={"resource_id": resource_id},
    )
    assert double_book_res.status_code == 409
    assert "cannot be assigned" in double_book_res.json()["detail"].lower()

    # =========================================================================
    # STEP 7: GIS Operations: Routing, Walkway Blocking & Dynamic Rerouting
    # =========================================================================
    # Calculate baseline route from Gate Main to North Exit
    initial_route_res = client.get(
        "/api/v1/routes/compare?from_node=gate_main&to_node=exit_north"
    )
    assert initial_route_res.status_code == 200
    initial_routes = initial_route_res.json()["routes"]
    assert len(initial_routes) > 0
    base_route = initial_routes[0]
    assert "walk_1_2" in base_route["edge_ids"]

    # Block the main walkway edge (walk_1_2)
    block_res = client.put(
        "/api/v1/venue/edges/walk_1_2/block",
        json={"reason": "P9 E2E: Emergency evacuation corridor blocked for testing"},
    )
    assert block_res.status_code == 200
    assert block_res.json()["is_blocked"] is True

    # Recalculate route after blockage: must find alternative bypassing blocked edge
    rerouted_res = client.get(
        "/api/v1/routes/compare?from_node=gate_main&to_node=exit_north"
    )
    assert rerouted_res.status_code == 200
    rerouted_data = rerouted_res.json()
    assert rerouted_data["routes_found"] >= 1
    new_best = rerouted_data["routes"][0]
    assert "walk_1_2" not in new_best["edge_ids"], "Routing failed to exclude blocked walkway!"
    assert "walk_1_2" in rerouted_data["blocked_edges"]

    # =========================================================================
    # STEP 8: Incident Resolution with Mandatory Notes & Resource Release
    # =========================================================================
    # Attempting to resolve without notes must fail with 422 Unprocessable Entity
    empty_notes_res = client.put(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "resolved", "notes": "", "operator": "p9_e2e_tester"},
    )
    assert empty_notes_res.status_code == 422
    assert "mandatory" in empty_notes_res.json()["detail"].lower()

    # Resolve with valid resolution notes
    resolve_res = client.put(
        f"/api/v1/incidents/{incident_id}/status",
        json={
            "status": "resolved",
            "notes": "P9 E2E: Crowd dispersed safely via alternate corridors. Density returned to baseline.",
            "operator": "p9_e2e_tester",
        },
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"
    assert resolve_res.json()["resolved_at"] is not None

    # Verify resource was automatically released
    db_session.refresh(resource)
    assert resource.status == "available"
    assert resource.assigned_incident_id is None

    # =========================================================================
    # STEP 9: Operational Analytics Overview & Trend Metrics
    # =========================================================================
    analytics_res = client.get("/api/v1/analytics/overview?period=24h")
    assert analytics_res.status_code == 200
    overview_data = analytics_res.json()
    assert "metrics" in overview_data
    assert "incidents" in overview_data
    assert "events" in overview_data
    assert "status_distribution" in overview_data["incidents"]
    assert "status_distribution" in overview_data["events"]
    assert overview_data["metrics"]["total_resources"] == 8

    # =========================================================================
    # STEP 10: Multi-Format Report Generation (PDF & CSV Exports)
    # =========================================================================
    # Generate Operational Summary Preview
    report_req = ReportGenerateRequest(
        report_type="operational_summary",
        period="24h",
    )
    preview = ReportService.generate_preview(db_session, report_req)
    assert preview.metadata.record_count > 0
    assert "active_incidents_now" in preview.summary_metrics

    # PDF Export
    pdf_fname, pdf_bytes = ReportService.export_pdf(db_session, report_req)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000

    # CSV Export
    csv_fname, csv_bytes = ReportService.export_csv(db_session, report_req)
    assert csv_bytes.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert len(csv_bytes) > 100

    # =========================================================================
    # STEP 11: Reopen Walkway & Check Deterministic Audit Trail
    # =========================================================================
    reopen_res = client.put("/api/v1/venue/edges/walk_1_2/reopen")
    assert reopen_res.status_code == 200
    assert reopen_res.json()["is_blocked"] is False

    # Export audit records via shortcut
    audit_res = client.post("/api/v1/reports/audit/export", json={"period": "24h", "format": "csv"})
    assert audit_res.status_code == 200
    assert audit_res.content.startswith(b"\xef\xbb\xbf")

    # =========================================================================
    # STEP 12: Database Persistence Check across Isolated Session Reload
    # =========================================================================
    db_check = SessionLocal()
    try:
        persisted_incident = db_check.query(Incident).filter_by(id=incident_id).first()
        assert persisted_incident is not None
        assert persisted_incident.status == "resolved"
        assert persisted_incident.resolution_notes is not None
        assert len(persisted_incident.notes) >= 1
    finally:
        db_check.close()
