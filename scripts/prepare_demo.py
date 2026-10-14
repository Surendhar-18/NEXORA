"""
NEXORA - Demonstration Dataset Preparation Script
Initializes or refreshes the demonstration environment in an idempotent, non-destructive manner.

Features:
1. Verifies database schema integrity.
2. Seeds default venue (Triveni Festival Grounds: 6 zones, 12 nodes, 16 walkways, cameras).
3. Seeds default crowd-count rules and detection thresholds.
4. Seeds 8 simulated emergency response resources.
5. Seeds a predictable, operator-facing demo scenario:
   - 1 Demonstration Video record & completed analysis job
   - Sampled frame detection records with crowd surge evidence
   - 1 Crowd event awaiting review (North Plaza Surge)
   - 1 Active operational incident (Entrance Bottleneck)
   - 1 Resolved historical incident with resolution notes
6. Leaves all existing user uploads and custom data untouched.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Ensure backend directory is in python search path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import engine, Base, SessionLocal
from app.models.video import Video
from app.models.job import Job
from app.models.detection import Detection
from app.models.rule import CrowdRule
from app.models.event import Event
from app.models.incident import Incident, IncidentHistory, IncidentNote
from app.models.resource import Resource
from app.models.venue import VenueEdge
from app.models.audit import AuditLog
from app.services.venue_service import VenueService
from app.services.resource_service import ResourceService
from app.services.crowd_rules_engine import seed_default_rules


def prepare_demo():
    print("=" * 60)
    print("NEXORA - PREPARING DEMOSTRATION ENVIRONMENT")
    print("=" * 60)

    # 1. Initialize Tables
    print("[1/5] Verifying database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 2. Seed Core Infrastructure
        print("[2/5] Seeding venue GIS and crowd rules...")
        venue = VenueService.seed_default_venue(db)
        if venue:
            print(f"  -> Venue confirmed: {venue.name} ({venue.id})")
        else:
            print("  -> Venue already present.")

        seed_default_rules(db)
        rule_count = db.query(CrowdRule).count()
        print(f"  -> Crowd rules verified ({rule_count} active rules in database).")

        # 3. Seed Simulated Response Units
        print("[3/5] Seeding simulated emergency response units...")
        ResourceService.seed_default_resources(db)
        resource_count = db.query(Resource).count()
        print(f"  -> Simulated response units confirmed ({resource_count} total units).")

        # 4. Ensure Walkways are Open for Fresh Demo
        print("[4/5] Restoring walkway corridors to open state...")
        unblocked_count = db.query(VenueEdge).filter(VenueEdge.is_blocked == True).update({
            VenueEdge.is_blocked: False,
            VenueEdge.blocked_at: None,
            VenueEdge.blocked_by: None,
            VenueEdge.blockage_reason: None
        })
        if unblocked_count > 0:
            print(f"  -> Reopened {unblocked_count} previously blocked walkways.")
        else:
            print("  -> All walkways currently open.")

        # 5. Seed Predictable Demo Scenarios
        print("[5/5] Seeding demo scenario events and incidents...")
        now = datetime.now(timezone.utc)

        # A. Demo Video record
        demo_vid_id = "video-demo-north-plaza"
        demo_job_id = "job-demo-north-plaza"

        existing_vid = db.query(Video).filter(Video.id == demo_vid_id).first()
        if not existing_vid:
            demo_vid = Video(
                id=demo_vid_id,
                filename="demo_north_plaza_surge.mp4",
                original_filename="cctv_gate1_ingress_rush.mp4",
                file_path="data/uploads/v_pipeline_test_01.mp4",
                file_size_bytes=21719,
                zone_id="zone_north_plaza",
                uploaded_by="demo_operator",
                status="processed",
                created_at=now - timedelta(minutes=45)
            )
            db.add(demo_vid)
            print(f"  -> Added demo video: {demo_vid_id}")

        # B. Demo Job record
        existing_job = db.query(Job).filter(Job.id == demo_job_id).first()
        if not existing_job:
            demo_job = Job(
                id=demo_job_id,
                video_id=demo_vid_id,
                zone_id="zone_north_plaza",
                status="completed",
                progress_percent=100.0,
                current_frame=10,
                total_frames_to_process=10,
                sampling_interval_sec=2.0,
                confidence_threshold=0.5,
                model_name="yolov8n",
                total_persons_detected=52,
                max_person_count=26,
                started_at=now - timedelta(minutes=44),
                completed_at=now - timedelta(minutes=43),
                created_at=now - timedelta(minutes=45)
            )
            db.add(demo_job)
            print(f"  -> Added demo job: {demo_job_id}")

        # C. Demo Detection Record
        det_id = "det-demo-01"
        existing_det = db.query(Detection).filter(Detection.id == det_id).first()
        if not existing_det:
            demo_det = Detection(
                id=det_id,
                video_id=demo_vid_id,
                job_id=demo_job_id,
                frame_index=6,
                timestamp_seconds=12.0,
                person_count=26,
                avg_confidence=0.88,
                max_confidence=0.96,
                min_confidence=0.75,
                evidence_image_path="evidence_test_frame.jpg"
            )
            db.add(demo_det)
            print(f"  -> Added demo detection frame: {det_id}")

        # D. Demo Crowd Event (Pending Review)
        evt_id = "EVT-DEMO-001"
        existing_evt = db.query(Event).filter(Event.id == evt_id).first()
        if not existing_evt:
            demo_evt = Event(
                id=evt_id,
                event_type="threshold",
                severity="critical",
                person_count=26,
                rule_name="SURGE_INGRESS_OVERFLOW",
                rule_threshold=20,
                zone_id="zone_north_plaza",
                video_id=demo_vid_id,
                job_id=demo_job_id,
                detection_id=det_id,
                window_start_sec=10.0,
                window_end_sec=14.0,
                description="Detected 26 persons exceeding safety threshold 20 at North Plaza.",
                evidence_image_path="evidence_test_frame.jpg",
                status="pending_review",
                created_at=now - timedelta(minutes=30)
            )
            db.add(demo_evt)
            print(f"  -> Added demo crowd event awaiting review: {evt_id}")

        # D. Demo Operational Incidents
        # Active incident: North Plaza Ingress Congestion
        inc1_num = "INC-DEMO-001"
        existing_inc1 = db.query(Incident).filter(Incident.incident_number == inc1_num).first()
        if not existing_inc1:
            inc1 = Incident(
                id="inc-demo-001-id",
                incident_number=inc1_num,
                title="[DEMO] North Plaza Ingress Congestion",
                description="High crowd concentration near Entry Gate 1. Ingress funnel requires marshaling.",
                venue_id="venue_triveni",
                zone_id="zone_north_plaza",
                location_status="confirmed",
                severity="high",
                status="open",
                created_by="demo_operator",
                created_at=now - timedelta(minutes=25),
                updated_at=now - timedelta(minutes=25)
            )
            db.add(inc1)
            db.flush()
            # Initial history
            db.add(IncidentHistory(
                incident_id=inc1.id,
                action="created",
                new_value="open",
                performed_by="demo_operator",
                created_at=now - timedelta(minutes=25)
            ))
            print(f"  -> Added active demo incident: {inc1_num}")

        # Resolved incident: South Gate Diversion
        inc2_num = "INC-DEMO-002"
        existing_inc2 = db.query(Incident).filter(Incident.incident_number == inc2_num).first()
        if not existing_inc2:
            inc2 = Incident(
                id="inc-demo-002-id",
                incident_number=inc2_num,
                title="[DEMO] South Concourse Footfall Surge",
                description="Temporary bottleneck formed at South Food Court corridor.",
                venue_id="venue_triveni",
                zone_id="zone_food_court",
                location_status="confirmed",
                severity="medium",
                status="resolved",
                created_by="demo_operator",
                resolution_notes="Crowd safely diverted via Walkway East. Normal pedestrian flow verified.",
                resolved_by="demo_operator",
                resolved_at=now - timedelta(minutes=10),
                created_at=now - timedelta(hours=1),
                updated_at=now - timedelta(minutes=10)
            )
            db.add(inc2)
            db.flush()
            db.add(IncidentHistory(
                incident_id=inc2.id,
                action="status_change",
                old_value="in_progress",
                new_value="resolved",
                details={"resolution_notes": "Crowd safely diverted via Walkway East."},
                performed_by="demo_operator",
                created_at=now - timedelta(minutes=10)
            ))
            print(f"  -> Added resolved historical demo incident: {inc2_num}")

        db.commit()
        print("=" * 60)
        print("DEMO ENVIRONMENT PREPARATION COMPLETE!")
        print("Venue: Triveni Festival Grounds (16 Walkways, 6 Zones)")
        print("Active Demo Records: 1 Video, 1 Job, 1 Event, 2 Incidents, 8 Resources")
        print("Ready for live walkthrough.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"ERROR preparing demo data: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    prepare_demo()
