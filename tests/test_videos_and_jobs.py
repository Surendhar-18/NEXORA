import pytest
import io
import os
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.core.config import settings
from app.database import SessionLocal
from app.models.video import Video
from app.models.job import Job
from app.models.audit import AuditLog
from app.services.job_worker import execute_video_processing_job

# Valid MP4 header with 'ftyp' box
VALID_MP4_HEADER = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + (b"\x00" * 4096)

def generate_valid_video_bytes(num_frames: int = 15) -> bytes:
    """Generate real in-memory MP4 video bytes decodable by OpenCV."""
    import tempfile
    import cv2
    import numpy as np
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        temp_name = tf.name
    fourcc = getattr(cv2, "VideoWriter_fourcc")(*"mp4v")
    writer = cv2.VideoWriter(temp_name, fourcc, 10.0, (160, 120))
    for i in range(num_frames):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()
    with open(temp_name, "rb") as f:
        data = f.read()
    try:
        os.unlink(temp_name)
    except Exception:
        pass
    return data

@pytest.mark.asyncio
async def test_upload_valid_video():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "file": ("test_surveillance.mp4", io.BytesIO(VALID_MP4_HEADER), "video/mp4")
        }
        data = {
            "zone_id": "ZONE-02",
            "sampling_interval_sec": "2.5",
            "confidence_threshold": "0.45",
        }
        response = await client.post("/api/v1/videos/upload", files=files, data=data)
        assert response.status_code == 201
        res_json = response.json()
        assert res_json["original_filename"] == "test_surveillance.mp4"
        assert res_json["file_type"] == "mp4"
        assert res_json["zone_id"] == "ZONE-02"
        assert res_json["status"] == "queued"
        assert res_json["sampling_interval_sec"] == 2.5
        assert "id" in res_json

        video_id = res_json["id"]

        # Verify database record
        db = SessionLocal()
        try:
            v = db.query(Video).filter_by(id=video_id).first()
            assert v is not None
            assert v.file_size_bytes == len(VALID_MP4_HEADER)
            assert os.path.exists(v.file_path)

            # Check audit entry
            audit = db.query(AuditLog).filter_by(entity_id=video_id).first()
            assert audit is not None
            assert audit.action_type == "VIDEO_UPLOADED"
        finally:
            db.close()

@pytest.mark.asyncio
async def test_upload_invalid_file_extension():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "file": ("malicious_script.sh", io.BytesIO(b"#!/bin/bash\necho hack"), "text/plain")
        }
        response = await client.post("/api/v1/videos/upload", files=files)
        assert response.status_code == 415
        assert "Unsupported media type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_fake_extension_invalid_magic_bytes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # File named .mp4 but containing HTML text
        files = {
            "file": ("fake_video.mp4", io.BytesIO(b"<!DOCTYPE html><html><body>Not a video</body></html>"), "video/mp4")
        }
        response = await client.post("/api/v1/videos/upload", files=files)
        assert response.status_code == 400
        assert "binary signature validation" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_size_limit_exceeded():
    transport = ASGITransport(app=app)
    original_max = settings.MAX_UPLOAD_SIZE_MB
    try:
        # Temporarily restrict max upload size to 0.001 MB (~1 KB)
        settings.MAX_UPLOAD_SIZE_MB = 0.001
        large_payload = b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * 4096)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            files = {
                "file": ("oversized.mp4", io.BytesIO(large_payload), "video/mp4")
            }
            response = await client.post("/api/v1/videos/upload", files=files)
            assert response.status_code == 413
            assert "exceeds maximum allowed size" in response.json()["detail"]
    finally:
        settings.MAX_UPLOAD_SIZE_MB = original_max

@pytest.mark.asyncio
async def test_list_videos_and_get_details():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First list
        res = await client.get("/api/v1/videos")
        assert res.status_code == 200
        data = res.json()
        assert "videos" in data
        assert isinstance(data["videos"], list)
        assert data["total"] >= 1

        video_id = data["videos"][0]["id"]

        # Get specific video detail
        detail_res = await client.get(f"/api/v1/videos/{video_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == video_id

@pytest.mark.asyncio
async def test_create_and_poll_job():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload video
        video_payload = generate_valid_video_bytes(20)
        files = {
            "file": ("flow_test.mp4", io.BytesIO(video_payload), "video/mp4")
        }
        upload_res = await client.post("/api/v1/videos/upload", files=files)
        assert upload_res.status_code == 201
        video_id = upload_res.json()["id"]

        # 2. Create secondary job for this video
        job_req = {
            "video_id": video_id,
            "zone_id": "ZONE-03",
            "sampling_interval_sec": 3.0,
            "confidence_threshold": 0.6,
        }
        job_res = await client.post("/api/v1/jobs", json=job_req)
        assert job_res.status_code == 201
        job_data = job_res.json()
        job_id = job_data["id"]
        assert job_data["video_id"] == video_id
        assert job_data["zone_id"] == "ZONE-03"

        # 3. Check status endpoint
        status_res = await client.get(f"/api/v1/jobs/{job_id}/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["job_id"] == job_id
        assert status_data["status"] in ("queued", "processing", "completed")

        # 4. Check list jobs
        list_jobs_res = await client.get("/api/v1/jobs")
        assert list_jobs_res.status_code == 200
        assert list_jobs_res.json()["total"] >= 1

@pytest.mark.asyncio
async def test_missing_resources_return_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        non_existent = "00000000-0000-0000-0000-000000000000"
        res_v = await client.get(f"/api/v1/videos/{non_existent}")
        assert res_v.status_code == 404

        res_j = await client.get(f"/api/v1/jobs/{non_existent}")
        assert res_j.status_code == 404

        res_js = await client.get(f"/api/v1/jobs/{non_existent}/status")
        assert res_js.status_code == 404

def test_job_worker_execution_lifecycle():
    # Directly test worker state machine transitions with a valid OpenCV video
    import cv2
    import numpy as np
    db = SessionLocal()
    try:
        # Create valid synthetic video file
        test_video_path = settings.UPLOAD_DIR / "worker_test.mp4"
        fourcc = getattr(cv2, "VideoWriter_fourcc")(*"mp4v")
        writer = cv2.VideoWriter(str(test_video_path), fourcc, 10.0, (320, 240))
        for i in range(25):
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            cv2.circle(frame, (160, 100), 20, (200, 200, 200), -1)
            writer.write(frame)
        writer.release()

        test_video = Video(
            id="v_worker_test",
            filename="worker_test.mp4",
            original_filename="worker_test.mp4",
            file_path=str(test_video_path),
            file_size_bytes=test_video_path.stat().st_size,
            status="uploaded",
        )
        db.merge(test_video)

        test_job = Job(
            id="j_worker_test",
            video_id="v_worker_test",
            sampling_interval_sec=1.0,
            confidence_threshold=0.5,
            status="queued",
            progress_percent=0.0,
        )
        db.merge(test_job)
        db.commit()

        # Run worker synchronously
        execute_video_processing_job("j_worker_test")

        # Check job status became completed
        updated_job = db.query(Job).filter_by(id="j_worker_test").first()
        assert updated_job is not None
        assert updated_job.status == "completed"
        assert updated_job.progress_percent == 100.0
        assert updated_job.completed_at is not None
        assert updated_job.current_frame > 0

        # Check audit log entries
        completed_audit = db.query(AuditLog).filter_by(entity_id="j_worker_test", action_type="JOB_COMPLETED").first()
        assert completed_audit is not None
    finally:
        db.close()
