import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.database import SessionLocal, Base, engine
from app.models.audit import AuditLog
from app.models.venue import Venue

def test_database_connection_and_models():
    session = SessionLocal()
    try:
        # Verify AuditLog query
        logs = session.query(AuditLog).all()
        assert isinstance(logs, list)
        assert len(logs) >= 1  # From init_db

        # Test inserting a venue
        test_venue = Venue(
            id="TEST-VENUE-01",
            name="Test Verification Grounds",
            description="Automated persistence test venue",
            center_lat=25.4358,
            center_lng=81.8463,
            default_zoom=16,
        )
        session.merge(test_venue)
        session.commit()

        # Query back
        v = session.query(Venue).filter_by(id="TEST-VENUE-01").first()
        assert v is not None
        assert v.name == "Test Verification Grounds"

        # Cleanup
        session.delete(v)
        session.commit()
    finally:
        session.close()

@pytest.mark.asyncio
async def test_audit_log_endpoint():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/audit?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(entry["actor_role"] in ("system", "operator") for entry in data)
