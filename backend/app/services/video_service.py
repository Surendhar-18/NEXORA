import os
import uuid
from typing import Tuple
from pathlib import Path
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.video import Video
from app.models.job import Job
from app.models.audit import AuditLog
from app.services.video_validator import (
    ALLOWED_EXTENSIONS,
    check_video_magic_bytes,
    sanitize_filename,
)

async def handle_video_upload(
    file: UploadFile,
    zone_id: str,
    sampling_interval_sec: float,
    confidence_threshold: float,
    db: Session,
    actor_id: str = "operator",
) -> Tuple[Video, Job]:
    """
    Validates and persists uploaded video file and initiates a background job record.
    Enforces strict magic byte validation, file size ceilings, and path sanitization.
    """
    clean_name = sanitize_filename(file.filename or "uploaded.mp4")
    file_ext = Path(clean_name).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{file_ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Generate secure random storage filename outside public directories
    video_uuid = str(uuid.uuid4())
    safe_filename = f"{video_uuid}{file_ext}"
    dest_path = settings.UPLOAD_DIR / safe_filename

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    bytes_written = 0
    header_bytes = bytearray()

    try:
        with open(dest_path, "wb") as out_file:
            while chunk := await file.read(1024 * 64):  # 64 KB chunks
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    out_file.close()
                    if dest_path.exists():
                        dest_path.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB",
                    )
                if len(header_bytes) < 32:
                    header_bytes.extend(chunk[:32 - len(header_bytes)])
                out_file.write(chunk)

        # Validate magic bytes from initial chunk
        is_valid_magic, container_type = check_video_magic_bytes(bytes(header_bytes))
        if not is_valid_magic:
            if dest_path.exists():
                dest_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content failed binary signature validation (detected: {container_type}). Not a valid video stream.",
            )

        # Create Video Database Record
        video_record = Video(
            id=video_uuid,
            filename=safe_filename,
            original_filename=clean_name,
            file_path=str(dest_path),
            file_size_bytes=bytes_written,
            zone_id=zone_id or "ZONE-01",
            uploaded_by=actor_id,
            status="uploaded",
        )
        db.add(video_record)

        # Create Initial Processing Job
        job_record = Job(
            id=str(uuid.uuid4()),
            video_id=video_uuid,
            zone_id=zone_id or "ZONE-01",
            status="queued",
            progress_percent=0.0,
            current_frame=0,
            total_frames_to_process=0,
            sampling_interval_sec=sampling_interval_sec,
            confidence_threshold=confidence_threshold,
            model_name="yolov8n",
            created_at=datetime.now(timezone.utc),
        )
        db.add(job_record)

        # Create Audit Log Entry
        audit_entry = AuditLog(
            actor_id=actor_id,
            actor_role="operator",
            action_type="VIDEO_UPLOADED",
            entity_type="VIDEO",
            entity_id=video_uuid,
            details={
                "original_filename": clean_name,
                "file_size_bytes": bytes_written,
                "container_type": container_type,
                "initial_job_id": job_record.id,
            },
        )
        db.add(audit_entry)

        db.commit()
        db.refresh(video_record)
        db.refresh(job_record)

        return video_record, job_record

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process video upload: {str(e)}",
        )
