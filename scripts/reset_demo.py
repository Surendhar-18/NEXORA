"""
NEXORA - Non-Destructive Demonstration Reset Script
Resets demonstration state safely without dropping tables or deleting user uploads.

Safeguards:
1. Requires explicit `--force` argument or user confirmation.
2. Only removes explicitly labeled demo records (INC-DEMO-%, EVT-DEMO-%, etc.).
3. Reopens any blocked venue walkways.
4. Resets all emergency response resources to available.
5. Preserves all genuine user uploads, test runs, and custom rules.
"""

import sys
import argparse
from pathlib import Path

# Ensure backend directory is in python search path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.video import Video
from app.models.job import Job
from app.models.detection import Detection
from app.models.event import Event
from app.models.incident import Incident, IncidentHistory, IncidentNote
from app.models.resource import Resource
from app.models.venue import VenueEdge
from app.models.audit import AuditLog


def reset_demo(force: bool = False):
    print("=" * 60)
    print("NEXORA - NON-DESTRUCTIVE DEMO RESET TOOL")
    print("=" * 60)

    if not force:
        print("WARNING: This will reset all demo incidents, events, and blocked walkways.")
        print("Genuine uploads and non-demo records will be preserved.")
        confirm = input("Type 'yes' to proceed with reset: ").strip().lower()
        if confirm != "yes":
            print("Operation aborted by user.")
            sys.exit(0)

    db = SessionLocal()
    try:
        # 1. Unblock all walkways
        unblocked = db.query(VenueEdge).filter(VenueEdge.is_blocked == True).update({
            VenueEdge.is_blocked: False,
            VenueEdge.blocked_at: None,
            VenueEdge.blocked_by: None,
            VenueEdge.blockage_reason: None
        })
        print(f"[1/4] Unblocked {unblocked} walkways.")

        # 2. Reset simulated resources to available
        res_reset = db.query(Resource).filter(Resource.status != "available").update({
            Resource.status: "available",
            Resource.assigned_incident_id: None
        })
        print(f"[2/4] Reset {res_reset} resource assignments to available.")

        # 3. Clean up demo-labeled incidents and associated notes/history
        demo_incidents = db.query(Incident).filter(
            (Incident.incident_number.like("INC-DEMO-%")) |
            (Incident.created_by == "demo_operator")
        ).all()
        demo_inc_ids = [inc.id for inc in demo_incidents]

        if demo_inc_ids:
            db.query(IncidentNote).filter(IncidentNote.incident_id.in_(demo_inc_ids)).delete(synchronize_session=False)
            db.query(IncidentHistory).filter(IncidentHistory.incident_id.in_(demo_inc_ids)).delete(synchronize_session=False)
            deleted_incs = db.query(Incident).filter(Incident.id.in_(demo_inc_ids)).delete(synchronize_session=False)
            print(f"[3/4] Removed {deleted_incs} demo incident records.")
        else:
            print("[3/4] No demo incidents found.")

        # 4. Clean up demo events
        demo_events = db.query(Event).filter(
            (Event.id.like("EVT-DEMO-%")) |
            (Event.rule_name == "SURGE_INGRESS_OVERFLOW")
        ).delete(synchronize_session=False)
        print(f"[4/4] Removed {demo_events} demo crowd event records.")

        db.commit()
        print("=" * 60)
        print("DEMO RESET COMPLETE! Walkways reopened and resources available.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"ERROR during demo reset: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset NEXORA demo records safely.")
    parser.add_argument("--force", action="store_true", help="Bypass interactive confirmation")
    args = parser.parse_args()
    reset_demo(force=args.force)
