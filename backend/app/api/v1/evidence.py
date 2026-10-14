import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from app.core.config import settings
from app.models.user import User
from app.api.deps import require_observer

router = APIRouter(prefix="/evidence", tags=["VisionX Evidence Frames"])

SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")
SAFE_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+\.(jpg|jpeg|png)$", re.IGNORECASE)

@router.get("/{job_id}/{filename}")
def get_evidence_frame(
    job_id: str,
    filename: str,
    current_user: User = Depends(require_observer)
):
    """
    Safely retrieve an authenticated/annotated evidence frame by job ID and filename.
    Enforces strict path traversal prevention and ensures target files remain strictly
    within the configured EVIDENCE_DIR.
    """
    if not SAFE_ID_REGEX.match(job_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job identifier format",
        )

    if not SAFE_FILENAME_REGEX.match(filename) or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or potentially malicious evidence filename",
        )

    evidence_root = settings.EVIDENCE_DIR.resolve()
    target_path = (settings.EVIDENCE_DIR / job_id / filename).resolve()

    # Verify containment within evidence root
    try:
        target_path.relative_to(evidence_root)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: path traversal attempt detected",
        )

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence frame '{filename}' for job '{job_id}' not found",
        )

    return FileResponse(
        path=str(target_path),
        media_type="image/jpeg",
        filename=filename,
    )
