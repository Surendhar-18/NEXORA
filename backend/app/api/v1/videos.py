from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.video import Video
from app.models.job import Job
from app.models.user import User
from app.api.deps import require_operator, require_observer
from app.schemas.video import VideoUploadResponse, VideoDetailResponse, VideoListResponse
from app.schemas.job import JobDetailResponse, JobListResponse
from app.services.video_service import handle_video_upload
from app.services.job_worker import execute_video_processing_job

router = APIRouter(prefix="/videos", tags=["VisionX Video Ingestion"])

@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    zone_id: Optional[str] = Form("ZONE-01"),
    sampling_interval_sec: float = Form(2.0),
    confidence_threshold: float = Form(0.5),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Upload a prerecorded video file for analysis.
    Validates magic bytes, size limits, saves securely, and initiates a non-blocking background job.
    """
    video, job = await handle_video_upload(
        file=file,
        zone_id=zone_id or "ZONE-01",
        sampling_interval_sec=sampling_interval_sec,
        confidence_threshold=confidence_threshold,
        db=db,
        actor_id=current_user.username,
    )

    # Launch background job asynchronously
    background_tasks.add_task(execute_video_processing_job, job.id)

    return VideoUploadResponse(
        id=video.id,
        original_filename=video.original_filename,
        file_size_bytes=video.file_size_bytes,
        file_type=file.filename.split(".")[-1].lower() if file.filename else "mp4",
        zone_id=video.zone_id,
        status=job.status,
        sampling_interval_sec=job.sampling_interval_sec,
        confidence_threshold=job.confidence_threshold,
        created_at=video.created_at.isoformat() if video.created_at else "",
        message="Video uploaded successfully. Processing will begin shortly.",
    )

@router.get("", response_model=VideoListResponse)
def list_videos(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """List all uploaded videos."""
    total = db.query(Video).count()
    videos = db.query(Video).order_by(desc(Video.created_at)).offset(offset).limit(limit).all()

    return VideoListResponse(
        videos=[
            VideoDetailResponse(
                id=v.id,
                filename=v.filename,
                original_filename=v.original_filename,
                file_size_bytes=v.file_size_bytes,
                duration_seconds=v.duration_seconds,
                fps=v.fps,
                total_frames=v.total_frames,
                resolution=v.resolution,
                zone_id=v.zone_id,
                uploaded_by=v.uploaded_by,
                status=v.status,
                created_at=v.created_at.isoformat() if v.created_at else "",
            )
            for v in videos
        ],
        total=total,
    )

@router.get("/{video_id}", response_model=VideoDetailResponse)
def get_video_detail(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """Retrieve details for a specific uploaded video."""
    video = db.query(Video).filter_by(id=video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID '{video_id}' not found",
        )

    return VideoDetailResponse(
        id=video.id,
        filename=video.filename,
        original_filename=video.original_filename,
        file_size_bytes=video.file_size_bytes,
        duration_seconds=video.duration_seconds,
        fps=video.fps,
        total_frames=video.total_frames,
        resolution=video.resolution,
        zone_id=video.zone_id,
        uploaded_by=video.uploaded_by,
        status=video.status,
        created_at=video.created_at.isoformat() if video.created_at else "",
    )

# Alias routes matching docs/09-api-specification.md: GET /videos/jobs and GET /videos/jobs/{job_id}
@router.get("/jobs", response_model=JobListResponse)
def list_jobs_via_videos_prefix(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all processing jobs (API Specification Section 4.3 alias)."""
    from app.api.v1.jobs import list_jobs
    return list_jobs(status_filter=status_filter, limit=limit, offset=offset, db=db)

@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job_via_videos_prefix(job_id: str, db: Session = Depends(get_db)):
    """Get job details (API Specification Section 4.4 alias)."""
    from app.api.v1.jobs import get_job_detail
    return get_job_detail(job_id=job_id, db=db)
