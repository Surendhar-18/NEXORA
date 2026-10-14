import os
from app.services.visionx_engine import process_video_job

def execute_video_processing_job(job_id: str):
    """
    Background worker task executing real video processing job lifecycle.
    Dispatches to VisionX engine for OpenCV frame extraction, YOLOv8 inference,
    evidence generation, and database persistence.
    """
    try:
        process_video_job(job_id)
    except Exception as e:
        # Exceptions are captured, recorded to Job.error_message and AuditLog in process_video_job
        pass
