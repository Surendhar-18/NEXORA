import sqlite3
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.database import Base, engine
import app.models

db_file = Path(settings.DATA_DIR) / "nexora.db"
con = sqlite3.connect(str(db_file))
cur = con.cursor()

# Incidents columns migration
cols = [r[1] for r in cur.execute("PRAGMA table_info(incidents)").fetchall()]
incident_columns = [
    ("venue_id", "VARCHAR(50) DEFAULT 'venue_triveni'"),
    ("location_status", "VARCHAR(30) DEFAULT 'confirmed'"),
    ("acknowledged_at", "DATETIME"),
    ("acknowledged_by", "VARCHAR(100)"),
    ("resolved_by", "VARCHAR(100)"),
    ("closed_at", "DATETIME"),
    ("closed_by", "VARCHAR(100)")
]
for col, ctype in incident_columns:
    if col not in cols:
        cur.execute(f"ALTER TABLE incidents ADD COLUMN {col} {ctype}")
        print(f"Added {col} to incidents table")

# Resources columns migration
r_cols = [r[1] for r in cur.execute("PRAGMA table_info(resources)").fetchall()]
resource_columns = [
    ("assigned_incident_id", "VARCHAR(36)"),
    ("description", "TEXT")
]
for col, ctype in resource_columns:
    if col not in r_cols:
        cur.execute(f"ALTER TABLE resources ADD COLUMN {col} {ctype}")
        print(f"Added {col} to resources table")

con.commit()
con.close()

# Create all new tables (incident_history, incident_notes)
Base.metadata.create_all(bind=engine)
print("Phase 6 database schema migration completed successfully.")
