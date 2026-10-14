import pytest
import numpy as np
import cv2
import os
from pathlib import Path
from ultralytics import YOLO

def test_opencv_and_numpy_integration():
    """Verify OpenCV functions and NumPy 2 array allocations without ABI mismatch."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, "NEXORA VISIONX TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    assert img.shape == (480, 640, 3)
    assert img.dtype == np.uint8

    # Test encode to JPEG memory buffer
    success, encoded = cv2.imencode(".jpg", img)
    assert success is True
    assert len(encoded) > 0

def test_opencv_video_encoding_and_decoding(tmp_path):
    """Verify OpenCV can encode and decode video frames (cv2.VideoCapture / cv2.VideoWriter)."""
    test_video_path = tmp_path / "test_cv_clip.mp4"
    fourcc = getattr(cv2, "VideoWriter_fourcc")(*"mp4v")
    writer = cv2.VideoWriter(str(test_video_path), fourcc, 10.0, (320, 240))
    
    assert writer.isOpened(), "VideoWriter failed to open"
    for i in range(15):
        frame = np.full((240, 320, 3), i * 15, dtype=np.uint8)
        writer.write(frame)
    writer.release()

    # Re-open with VideoCapture
    cap = cv2.VideoCapture(str(test_video_path))
    assert cap.isOpened(), "VideoCapture failed to open created video"
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
    cap.release()

    assert frame_count == 15, f"Expected 15 frames, decoded {frame_count}"

def test_yolo_model_loading_and_inference():
    """Verify Ultralytics YOLOv8n loads model weights and executes inference on input frames."""
    model_path = Path("data/models/yolov8n.pt")
    assert model_path.exists(), "yolov8n.pt should be present in data/models"

    model = YOLO(str(model_path))
    assert model is not None

    # Create dummy 640x640 frame
    test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    # Draw simple person-like outline
    cv2.circle(test_frame, (320, 150), 40, (200, 200, 200), -1)
    cv2.rectangle(test_frame, (270, 200), (370, 500), (200, 200, 200), -1)

    results = model(test_frame, verbose=False, classes=[0])  # class 0 = person
    assert len(results) == 1
    boxes = results[0].boxes
    assert hasattr(boxes, "conf")
    assert hasattr(boxes, "cls")
