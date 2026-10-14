import os
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.core.config import settings
from app.schemas.health import HealthResponse, StorageHealth, ModuleHealth

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_system_health(db: Session = Depends(get_db)):
    """
    Versioned system health check endpoint.
    Verifies SQLite connectivity, storage path permissions, and engine module statuses.
    """
    # 1. Database check
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Storage write test
    data_writable = False
    try:
        test_file = settings.DATA_DIR / ".health_test"
        test_file.write_text("health_check", encoding="utf-8")
        test_file.unlink()
        data_writable = True
    except Exception:
        data_writable = False

    storage_info = StorageHealth(
        data_dir_writable=data_writable,
        uploads_dir_exists=settings.UPLOAD_DIR.exists(),
        evidence_dir_exists=settings.EVIDENCE_DIR.exists(),
    )

    # 3. GIS Routing module check
    try:
        import networkx
        gis_status = "ready"
    except Exception as e:
        gis_status = f"unavailable: {str(e)}"

    # 4. Computer vision module status
    try:
        import cv2
        cv_status = "ready"
    except Exception as e:
        cv_status = f"isolated: {str(e)}"

    modules_info = ModuleHealth(
        database=db_status,
        gis_routing=gis_status,
        visionx_cv=cv_status,
    )

    overall_status = "healthy" if db_status == "connected" and data_writable else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        storage=storage_info,
        modules=modules_info,
    )


@router.get("/health/liveness", status_code=status.HTTP_200_OK)
def liveness_probe():
    """Lightweight Kubernetes / container liveness probe verifying process responsiveness."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/readiness")
def readiness_probe(db: Session = Depends(get_db)):
    """
    Readiness probe verifying database connectivity, storage integrity,
    and detector model weights readiness. Returns 503 if critical dependencies fail.
    """
    # 1. Database readiness
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. Storage write test
    storage_ok = False
    try:
        test_file = settings.DATA_DIR / ".ready_test"
        test_file.write_text("ready", encoding="utf-8")
        test_file.unlink()
        storage_ok = True
    except Exception:
        storage_ok = False

    # 3. Model weight check (local file existence, not network dependent)
    model_weight_file = settings.MODEL_DIR / "yolov8n.pt"
    model_ready = model_weight_file.exists()

    is_ready = db_ok and storage_ok

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "ready" if db_ok else "unreachable",
        "storage": "writable" if storage_ok else "read_only",
        "vision_model": "loaded" if model_ready else "weights_missing"
    }

    if not is_ready:
        return Response(content=json.dumps(payload), status_code=status.HTTP_503_SERVICE_UNAVAILABLE, media_type="application/json")

    return payload

