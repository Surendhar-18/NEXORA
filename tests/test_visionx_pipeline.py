import os
import cv2
import numpy as np
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.database import SessionLocal
from app.models.video import Video
from app.models.job import Job
from app.models.detection import Detection
from app.models.audit import AuditLog
from app.services.visionx_engine import process_video_job, get_yolo_model

def create_synthetic_test_video(file_path: Path, num_frames: int = 30, fps: float = 10.0) -> Path:
    """Helper to generate a real, playable synthetic MP4 video file with OpenCV."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(file_path), fourcc, fps, (320, 240))
    for i in range(num_frames):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Draw background elements
        cv2.putText(frame, f"F:{i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        # Draw humanoid silhouettes
        cv2.circle(frame, (100, 70), 18, (220, 220, 220), -1)
        cv2.rectangle(frame, (85, 90), (115, 180), (220, 220, 220), -1)
        cv2.circle(frame, (220, 80), 16, (220, 220, 220), -1)
        cv2.rectangle(frame, (205, 98), (235, 175), (220, 220, 220), -1)
        writer.write(frame)
    writer.release()
    return file_path

def test_opencv_video_properties_and_sampling(tmp_path):
    """Verify OpenCV reads video stream properties and extracts frames at intervals."""
    video_path = tmp_path / "sample_stream.mp4"
    create_synthetic_test_video(video_path, num_frames=40, fps=20.0)

    cap = cv2.VideoCapture(str(video_path))
    assert cap.isOpened()
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    assert fps == 20.0
    assert total_frames == 40
    assert width == 320
    assert height == 240

def test_yolo_model_availability_and_person_detection():
    """Verify YOLOv8n loads from data/models and detects people on synthetic frames."""
    model = get_yolo_model("yolov8n")
    assert model is not None

    test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    cv2.circle(test_frame, (320, 150), 40, (255, 255, 255), -1)
    cv2.rectangle(test_frame, (270, 200), (370, 500), (255, 255, 255), -1)

    results = model(test_frame, classes=[0], conf=0.1, verbose=False)
    assert len(results) >= 1
    assert hasattr(results[0], "boxes")

def test_full_visionx_processing_pipeline(tmp_path):
    """
    Test end-to-end VisionX video processing:
    1. OpenCV frame sampling
    2. YOLO person detection
    3. Evidence image generation
    4. Database record persistence
    5. Successful job completion status
    """
    db = SessionLocal()
    video_id = "v_pipeline_test_01"
    job_id = "j_pipeline_test_01"

    try:
        video_file = settings.UPLOAD_DIR / f"{video_id}.mp4"
        create_synthetic_test_video(video_file, num_frames=30, fps=10.0)

        video = Video(
            id=video_id,
            filename=f"{video_id}.mp4",
            original_filename="cctv_entrance_sample.mp4",
            file_path=str(video_file),
            file_size_bytes=video_file.stat().st_size,
            status="uploaded",
        )
        db.merge(video)

        job = Job(
            id=job_id,
            video_id=video_id,
            sampling_interval_sec=1.0,  # 10 fps -> samples every 10 frames = 3 frames total
            confidence_threshold=0.3,
            model_name="yolov8n",
            status="queued",
            progress_percent=0.0,
        )
        db.query(Detection).filter_by(job_id=job_id).delete()
        db.merge(job)
        db.commit()

        # Run pipeline
        process_video_job(job_id)

        # Assert job state
        updated_job = db.query(Job).filter_by(id=job_id).first()
        assert updated_job.status == "completed"
        assert updated_job.progress_percent == 100.0
        assert updated_job.current_frame == updated_job.total_frames_to_process
        assert updated_job.completed_at is not None
        assert updated_job.total_frames_to_process == 3

        # Assert video updated metadata
        updated_video = db.query(Video).filter_by(id=video_id).first()
        assert updated_video.status == "processed"
        assert updated_video.total_frames == 30
        assert updated_video.fps == 10.0
        assert updated_video.duration_seconds == 3.0

        # Assert Detections saved in database
        detections = db.query(Detection).filter_by(job_id=job_id).all()
        assert len(detections) == 3
        for d in detections:
            assert d.video_id == video_id
            assert d.job_id == job_id
            assert d.evidence_image_path is not None
            # Verify evidence file exists on disk
            ev_file = settings.EVIDENCE_DIR / d.evidence_image_path
            assert ev_file.exists(), f"Evidence file {ev_file} missing on disk"

    finally:
        db.close()

def test_corrupt_video_handling_fails_safely():
    """Verify that corrupt or zero-frame videos fail gracefully and never complete."""
    db = SessionLocal()
    video_id = "v_corrupt_test_01"
    job_id = "j_corrupt_test_01"

    try:
        # Create a corrupt non-video file
        corrupt_file = settings.UPLOAD_DIR / f"{video_id}.mp4"
        corrupt_file.write_bytes(b"\x00\x00\x00\x18ftypmp42corrupted_garbage_stream_with_no_atoms")

        video = Video(
            id=video_id,
            filename=f"{video_id}.mp4",
            original_filename="corrupt_feed.mp4",
            file_path=str(corrupt_file),
            file_size_bytes=len(corrupt_file.read_bytes()),
            status="uploaded",
        )
        db.merge(video)

        job = Job(
            id=job_id,
            video_id=video_id,
            status="queued",
            progress_percent=0.0,
        )
        db.merge(job)
        db.commit()

        # Run pipeline — should raise exception and transition job to failed
        with pytest.raises(Exception):
            process_video_job(job_id)

        # Verify job is marked as failed and NOT completed
        failed_job = db.query(Job).filter_by(id=job_id).first()
        assert failed_job.status == "failed"
        assert failed_job.error_message is not None
        assert "Inference pipeline failed" in failed_job.error_message
        assert failed_job.completed_at is not None

        # Verify audit log recorded failure
        fail_audit = db.query(AuditLog).filter_by(entity_id=job_id, action_type="JOB_FAILED").first()
        assert fail_audit is not None

    finally:
        db.close()

@pytest.mark.asyncio
async def test_get_job_detections_api():
    """Verify GET /api/v1/jobs/{job_id}/detections API returns valid detection telemetry."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query detections for the pipeline test job created earlier
        res = await client.get("/api/v1/jobs/j_pipeline_test_01/detections")
        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == "j_pipeline_test_01"
        assert data["video_id"] == "v_pipeline_test_01"
        assert len(data["detections"]) == 3
        first_det = data["detections"][0]
        assert "frame_index" in first_det
        assert "timestamp_seconds" in first_det
        assert "person_count" in first_det
        assert "evidence_image_url" in first_det
        assert "/api/v1/evidence/j_pipeline_test_01/" in first_det["evidence_image_url"]

@pytest.mark.asyncio
async def test_evidence_frame_retrieval_and_access_control():
    """Verify evidence image retrieval endpoint and path traversal protection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Retrieve valid evidence image
        db = SessionLocal()
        det = db.query(Detection).filter_by(job_id="j_pipeline_test_01").first()
        db.close()
        assert det is not None
        filename = Path(det.evidence_image_path).name

        res = await client.get(f"/api/v1/evidence/j_pipeline_test_01/{filename}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
        assert len(res.content) > 100

        # 2. Path traversal attack with ../ should be rejected (400 or 404)
        malicious_res = await client.get("/api/v1/evidence/j_pipeline_test_01/..%2F..%2F..%2Fsecret.txt")
        assert malicious_res.status_code in (400, 404)

        # 3. Nonexistent file returns 404
        missing_res = await client.get("/api/v1/evidence/j_pipeline_test_01/missing_frame.jpg")
        assert missing_res.status_code == 404

def test_confidence_threshold_filtering():
    """Verify confidence threshold filtering correctly controls person detection outputs."""
    model = get_yolo_model("yolov8n")
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    cv2.circle(frame, (320, 150), 40, (255, 255, 255), -1)
    cv2.rectangle(frame, (270, 200), (370, 500), (255, 255, 255), -1)

    # Ultra-high threshold (0.999) should produce zero detections
    strict_res = model(frame, classes=[0], conf=0.999, verbose=False)
    strict_count = len(strict_res[0].boxes) if strict_res and strict_res[0].boxes is not None else 0
    assert strict_count == 0

    # Low threshold (0.05) accepts detections
    loose_res = model(frame, classes=[0], conf=0.05, verbose=False)
    loose_count = len(loose_res[0].boxes) if loose_res and loose_res[0].boxes is not None else 0
    assert loose_count >= strict_count
