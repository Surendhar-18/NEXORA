"""
Database initialisation and persistence verification script.
Creates all relational tables in SQLite and verifies write/read transactions.
"""
import sys
from app.database import Base, engine, SessionLocal
import app.models
from app.models.audit import AuditLog

def init_db():
    print("[NEXORA DB INIT] Initializing SQLite tables...")
    Base.metadata.create_all(bind=engine)
    print("  [SUCCESS] All tables created successfully.")

    # Verification: Write and read test record in audit_logs
    session = SessionLocal()
    try:
        test_entry = AuditLog(
            actor_id="system_init",
            actor_role="system",
            action_type="SYSTEM_BOOTSTRAP",
            entity_type="DATABASE",
            entity_id="init_001",
            details={"message": "Phase 1 database persistence verified"},
        )
        session.add(test_entry)
        session.commit()

        # Query back
        fetched = session.query(AuditLog).filter_by(entity_id="init_001").first()
        if fetched and fetched.actor_id == "system_init":
            print("  [SUCCESS] Database write and read persistence verified.")
            return True
        else:
            print("  [ERROR] Verification entry could not be retrieved.")
            return False
    except Exception as e:
        session.rollback()
        print(f"  [ERROR] Database initialization failed: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
