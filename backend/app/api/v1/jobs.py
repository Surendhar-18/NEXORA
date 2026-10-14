import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.job import Job
from app.models.video import Video
from app.models.audit import AuditLog
from app.models.detection import Detection
from app.models.user import User
from app.api.deps import require_operator, require_observer
from app.schemas.job import (
    JobCreateRequest,
    JobDetailResponse,
    JobStatusResponse,
    JobListResponse,
)
from app.schemas.detection import (
    BoundingBox,
    DetectionItem,
    JobDetectionsResponse,
)
from app.services.job_worker import execute_video_processing_job

router = APIRouter(prefix="/jobs", tags=["VisionX Processing Jobs"])

@router.post("", response_model=JobDetailResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Create and queue a new processing job for an existing video.
    Executes asynchronously in a non-blocking background task.
    """
    actor_id = current_user.username
    video = db.query(Video).filter_by(id=request.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target video '{request.video_id}' not found",
        )

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        video_id=video.id,
        zone_id=request.zone_id or video.zone_id or "ZONE-01",
        status="queued",
        progress_percent=0.0,
        current_frame=0,
        total_frames_to_process=0,
        sampling_interval_sec=request.sampling_interval_sec,
        confidence_threshold=request.confidence_threshold,
        model_name="yolov8n",
        created_at=datetime.now(timezone.utc),
    )
    db.add(job)

    db.add(AuditLog(
        actor_id=actor_id,
        actor_role="operator",
        action_type="JOB_CREATED",
        entity_type="JOB",
        entity_id=job.id,
        details={
            "video_id": video.id,
            "sampling_interval_sec": job.sampling_interval_sec,
            "confidence_threshold": job.confidence_threshold,
        },
    ))
    db.commit()
    db.refresh(job)

    # Launch background task
    background_tasks.add_task(execute_video_processing_job, job.id)

    return build_job_response(job, video)

@router.get("", response_model=JobListResponse)
def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """List processing jobs with optional status filter and pagination."""
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)

    total = query.count()
    jobs = query.order_by(desc(Job.created_at)).offset(offset).limit(limit).all()

    # Pre-fetch videos
    video_ids = [j.video_id for j in jobs]
    videos = {v.id: v for v in db.query(Video).filter(Video.id.in_(video_ids)).all()}

    return JobListResponse(
        jobs=[build_job_response(j, videos.get(j.video_id)) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_detail(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """Retrieve full details of a processing job."""
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    video = db.query(Video).filter_by(id=job.video_id).first()
    return build_job_response(job, video)

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """Lightweight endpoint for frequent frontend progress polling."""
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress_percent=job.progress_percent,
        current_frame=job.current_frame,
        total_frames_to_process=job.total_frames_to_process,
        error_message=job.error_message,
    )

@router.get("/{job_id}/detections", response_model=JobDetectionsResponse)
def get_job_detections(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """
    Retrieve real VisionX frame detection records and evidence references for a processing job.
    Detections represent genuine person bounding boxes and confidence scores per sampled frame.
    Note: Repeated detections across frames are not unique-person counts.
    """
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    detections = db.query(Detection).filter_by(job_id=job.id).order_by(Detection.frame_index.asc()).all()

    items = []
    for d in detections:
        evidence_url = None
        if d.evidence_image_path:
            norm_path = d.evidence_image_path.replace("\\", "/")
            parts = norm_path.split("/")
            if len(parts) >= 2:
                filename = parts[-1]
                evidence_url = f"/api/v1/evidence/{job.id}/{filename}"

        boxes = [BoundingBox(**b) for b in (d.bounding_boxes or [])]
        items.append(DetectionItem(
            id=d.id,
            video_id=d.video_id,
            job_id=d.job_id,
            frame_index=d.frame_index,
            timestamp_seconds=d.timestamp_seconds,
            person_count=d.person_count,
            avg_confidence=d.avg_confidence,
            max_confidence=d.max_confidence,
            min_confidence=d.min_confidence,
            evidence_image_path=d.evidence_image_path,
            evidence_image_url=evidence_url,
            bounding_boxes=boxes,
            created_at=d.created_at.isoformat() if d.created_at else "",
        ))

    return JobDetectionsResponse(
        job_id=job.id,
        video_id=job.video_id,
        total_frames_processed=job.current_frame,
        total_persons_detected=job.total_persons_detected,
        max_person_count=job.max_person_count,
        detections=items,
    )

def build_job_response(job: Job, video: Optional[Video]) -> JobDetailResponse:
    """Helper to convert Job ORM entity into JobDetailResponse."""
    orig_name = video.original_filename if video else "unknown"
    file_size = video.file_size_bytes if video else 0
    file_type = orig_name.split(".")[-1].lower() if "." in orig_name else "mp4"

    return JobDetailResponse(
        id=job.id,
        video_id=job.video_id,
        original_filename=orig_name,
        file_size_bytes=file_size,
        file_type=file_type,
        zone_id=job.zone_id,
        status=job.status,
        progress_percent=job.progress_percent,
        current_frame=job.current_frame,
        total_frames_to_process=job.total_frames_to_process,
        sampling_interval_sec=job.sampling_interval_sec,
        confidence_threshold=job.confidence_threshold,
        model_name=job.model_name or "yolov8n",
        total_persons_detected=job.total_persons_detected,
        max_person_count=job.max_person_count,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else "",
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
