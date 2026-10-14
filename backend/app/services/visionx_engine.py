import os
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from ultralytics import YOLO

from app.core.config import settings
from app.database import SessionLocal
from app.models.job import Job
from app.models.video import Video
from app.models.detection import Detection
from app.models.audit import AuditLog

# In-memory cached YOLO models
_MODEL_CACHE: Dict[str, YOLO] = {}

def get_yolo_model(model_name: str = "yolov8n") -> YOLO:
    """
    Load or retrieve cached YOLO model instance.
    Validates model weight file existence in data/models/.
    """
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    model_path = settings.MODEL_DIR / f"{model_name}.pt"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model weights file '{model_path.name}' not found at {model_path}. "
            f"Ensure weights are downloaded into {settings.MODEL_DIR}"
        )

    # Initialize Ultralytics model
    model = YOLO(str(model_path))
    _MODEL_CACHE[model_name] = model
    return model

def draw_detection_hud(
    frame: np.ndarray,
    boxes_data: List[Dict[str, Any]],
    timestamp_sec: float,
    frame_index: int,
    confidence_thresh: float,
) -> np.ndarray:
    """
    Draw clean, high-contrast bounding boxes and terminal-style telemetry HUD
    following the NEXORA Factory Dark design system.
    """
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    # Draw bounding boxes (Vibrant Signal Orange / Metric Green for clear contrast)
    # OpenCV uses BGR ordering: Orange ~ (24, 96, 238), Green ~ (80, 202, 160)
    box_color = (24, 96, 238)
    text_bg = (16, 16, 16)
    text_color = (240, 240, 240)

    for item in boxes_data:
        x1 = max(0, int(item["x1"]))
        y1 = max(0, int(item["y1"]))
        x2 = min(w - 1, int(item["x2"]))
        y2 = min(h - 1, int(item["y2"]))
        conf = item["confidence"]

        # Box outline
        cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)

        # Confidence tag
        label = f"PERSON {conf:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        thickness = 1
        (label_w, label_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        tag_y1 = max(0, y1 - label_h - 6)
        tag_y2 = y1
        cv2.rectangle(annotated, (x1, tag_y1), (x1 + label_w + 8, tag_y2), text_bg, -1)
        cv2.rectangle(annotated, (x1, tag_y1), (x1 + label_w + 8, tag_y2), box_color, 1)
        cv2.putText(
            annotated,
            label,
            (x1 + 4, tag_y2 - 3),
            font,
            font_scale,
            text_color,
            thickness,
            cv2.LINE_AA,
        )

    # Telemetry HUD banner along the top
    hud_height = 32
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, 0), (w, hud_height), (16, 16, 16), -1)
    cv2.addWeighted(overlay, 0.85, annotated, 0.15, 0, annotated)

    hud_text = (
        f"NEXORA VISIONX // TIME: {timestamp_sec:.2f}s | FRAME: {frame_index} | "
        f"PERSON COUNT: {len(boxes_data)} | CONF_THRESH: {confidence_thresh:.2f}"
    )
    cv2.putText(
        annotated,
        hud_text,
        (10, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (238, 96, 24), # Signal orange in BGR
        1,
        cv2.LINE_AA,
    )

    return annotated

def process_video_job(job_id: str) -> None:
    """
    Core video processing pipeline for VisionX Phase 3:
    1. Extracts video stream properties using OpenCV.
    2. Performs frame sampling based on configured interval.
    3. Runs YOLOv8 person detection (COCO class 0) on sampled frames.
    4. Filters detections by configured confidence threshold.
    5. Saves timestamped evidence frames with bounding boxes to safe storage.
    6. Persists genuine frame detection records and updates job progress.
    7. Safely releases all video resources in a guaranteed finally block.
    """
    db = SessionLocal()
    cap: Optional[cv2.VideoCapture] = None

    try:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            return

        if job.status not in ("queued", "pending"):
            return

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        job.status = "processing"
        job.started_at = now_utc
        job.progress_percent = 5.0
        db.add(AuditLog(
            actor_id="visionx_engine",
            actor_role="system",
            action_type="JOB_STARTED",
            entity_type="JOB",
            entity_id=job.id,
            details={"video_id": job.video_id, "status": "processing"}
        ))
        db.commit()

        video = db.query(Video).filter_by(id=job.video_id).first()
        if not video or not os.path.exists(video.file_path):
            raise FileNotFoundError(f"Video file for video ID '{job.video_id}' not found on disk")

        # Load YOLO model
        model = get_yolo_model(job.model_name or "yolov8n")

        # Open video with OpenCV
        cap = cv2.VideoCapture(video.file_path)
        if not cap.isOpened():
            raise ValueError(f"OpenCV failed to open video file: '{video.original_filename}'. File may be corrupt or an unsupported stream.")

        # Read video metadata
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0.0 or np.isnan(fps):
            fps = 25.0  # standard fallback if container lacks FPS metadata

        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_video_frames <= 0:
            raise ValueError(f"Video file has zero readable frames or invalid header: '{video.original_filename}'")

        duration_sec = round(total_video_frames / fps, 2)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        resolution_str = f"{frame_width}x{frame_height}"

        # Persist video stream metadata back to Video record
        video.fps = fps
        video.total_frames = total_video_frames
        video.duration_seconds = duration_sec
        video.resolution = resolution_str
        db.commit()

        # Compute sampling schedule
        sampling_interval = max(0.5, float(job.sampling_interval_sec))
        frame_step = max(1, int(round(fps * sampling_interval)))
        sample_frame_indices = list(range(0, total_video_frames, frame_step))
        total_samples = len(sample_frame_indices)

        if total_samples == 0:
            sample_frame_indices = [0]
            total_samples = 1

        job.total_frames_to_process = total_samples
        job.progress_percent = 10.0
        db.commit()

        # Evidence frames output directory: data/evidence/<job_id>/
        evidence_dir = settings.EVIDENCE_DIR / job.id
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # Clear any prior detections if job was retried/re-run
        db.query(Detection).filter_by(job_id=job.id).delete()
        db.commit()

        # Run inference loop
        total_detected_sum = 0
        max_detected_frame = 0

        for sample_idx, target_frame_idx in enumerate(sample_frame_indices):
            # Seek to target frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                # If seek failed (e.g. near EOF), break or continue
                continue

            frame_ts = round(target_frame_idx / fps, 2)

            # Ultralytics inference: class 0 is 'person' in COCO
            results = model(
                frame,
                classes=[0],
                conf=job.confidence_threshold,
                verbose=False
            )

            boxes_data: List[Dict[str, Any]] = []
            confidences: List[float] = []

            if len(results) > 0 and results[0].boxes is not None:
                for b in results[0].boxes:
                    xyxy = b.xyxy[0].tolist()
                    conf = float(b.conf[0].item())
                    boxes_data.append({
                        "x1": round(xyxy[0], 2),
                        "y1": round(xyxy[1], 2),
                        "x2": round(xyxy[2], 2),
                        "y2": round(xyxy[3], 2),
                        "confidence": round(conf, 4),
                        "class_name": "person",
                    })
                    confidences.append(conf)

            person_count = len(boxes_data)
            avg_conf = round(float(np.mean(confidences)), 4) if confidences else 0.0
            max_conf = round(float(np.max(confidences)), 4) if confidences else 0.0
            min_conf = round(float(np.min(confidences)), 4) if confidences else 0.0

            # Draw telemetry HUD & bounding boxes on evidence frame
            annotated_frame = draw_detection_hud(
                frame=frame,
                boxes_data=boxes_data,
                timestamp_sec=frame_ts,
                frame_index=target_frame_idx,
                confidence_thresh=job.confidence_threshold,
            )

            # Persist evidence image to safe filesystem location
            evidence_filename = f"frame_{sample_idx:04d}_{target_frame_idx:06d}.jpg"
            evidence_full_path = evidence_dir / evidence_filename
            cv2.imwrite(str(evidence_full_path), annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            relative_evidence_path = f"{job.id}/{evidence_filename}"

            # Create Detection database record
            detection_record = Detection(
                video_id=video.id,
                job_id=job.id,
                frame_index=target_frame_idx,
                timestamp_seconds=frame_ts,
                person_count=person_count,
                avg_confidence=avg_conf,
                max_confidence=max_conf,
                min_confidence=min_conf,
                evidence_image_path=relative_evidence_path,
                bounding_boxes=boxes_data,
            )
            db.add(detection_record)

            # Update running job statistics
            total_detected_sum += person_count
            if person_count > max_detected_frame:
                max_detected_frame = person_count

            # Progress calculation (from 10% to 95%)
            progress = round(10.0 + ((sample_idx + 1) / total_samples) * 85.0, 1)
            job.current_frame = sample_idx + 1
            job.progress_percent = min(98.0, progress)
            job.total_persons_detected = total_detected_sum
            job.max_person_count = max_detected_frame

            # Commit periodically
            if sample_idx % 5 == 0 or (sample_idx + 1) == total_samples:
                db.commit()

        # Finalize job as completed
        completed_ts = datetime.now(timezone.utc).replace(tzinfo=None)
        job.status = "completed"
        job.progress_percent = 100.0
        job.current_frame = total_samples
        job.total_persons_detected = total_detected_sum
        job.max_person_count = max_detected_frame
        job.completed_at = completed_ts
        if video:
            video.status = "processed"

        duration_sec_total = (completed_ts - now_utc).total_seconds()
        db.add(AuditLog(
            actor_id="visionx_engine",
            actor_role="system",
            action_type="JOB_COMPLETED",
            entity_type="JOB",
            entity_id=job.id,
            details={
                "video_id": job.video_id,
                "total_samples_processed": total_samples,
                "total_persons_detected": total_detected_sum,
                "max_person_count": max_detected_frame,
                "duration_seconds": duration_sec_total,
            }
        ))
        db.commit()

        # Phase 4: Automatically evaluate configured crowd rules for the completed job
        try:
            from app.services.crowd_rules_engine import evaluate_rules_for_job
            evaluate_rules_for_job(job.id, db)
        except Exception as rule_err:
            db.add(AuditLog(
                actor_id="visionx_engine",
                actor_role="system",
                action_type="RULE_EVALUATION_ERROR",
                entity_type="JOB",
                entity_id=job.id,
                details={"error": str(rule_err)}
            ))
            db.commit()

    except Exception as e:
        db.rollback()
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.error_message = f"Inference pipeline failed: {str(e)}"
                job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.add(AuditLog(
                    actor_id="visionx_engine",
                    actor_role="system",
                    action_type="JOB_FAILED",
                    entity_type="JOB",
                    entity_id=job.id,
                    details={"error": str(e)}
                ))
                db.commit()
        except Exception:
            pass
        raise e

    finally:
        # Guarantee OpenCV video resources are released
        if cap is not None:
            cap.release()
        db.close()
