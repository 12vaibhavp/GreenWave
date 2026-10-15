"""
Phase 2 Automated Tests: YOLO Detection, Tracking & Vehicle Counting
"""
import numpy as np
import cv2
import pytest
from vision.config import VisionConfig
from vision.detector import VehicleDetector, Detection
from vision.tracker import VehicleTracker, TrackedVehicle, calculate_iou
from vision.counter import VehicleCounter, RegionOfInterest, CountingMetrics


def test_detector_initialization():
    """Verify detector loads configuration and YOLO model properly."""
    cfg = VisionConfig()
    detector = VehicleDetector(cfg)
    assert detector.model is not None
    assert detector.device in ["mps", "cuda", "cpu"]


def test_detector_inference_blank_frame():
    """Verify detector handles empty / blank frames without error."""
    detector = VehicleDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)
    assert isinstance(detections, list)
    assert len(detections) == 0


def test_iou_calculation():
    """Verify Intersection over Union logic."""
    b1 = (0, 0, 100, 100)
    b2 = (0, 0, 100, 100)
    assert pytest.approx(calculate_iou(b1, b2), 0.01) == 1.0

    b3 = (50, 50, 150, 150)
    # intersection: (50,50,100,100) -> 50*50 = 2500
    # union: 10000 + 10000 - 2500 = 17500 -> iou = 2500/17500 = 1/7 = 0.1428
    assert pytest.approx(calculate_iou(b1, b3), 0.01) == (2500 / 17500)

    b_disjoint = (200, 200, 300, 300)
    assert calculate_iou(b1, b_disjoint) == 0.0


def test_tracker_persistent_id():
    """
    Simulate a vehicle moving across 10 frames.
    Verify the tracker assigns exactly 1 unique ID and maintains it.
    """
    tracker = VehicleTracker(max_age=5, min_hits=2, iou_threshold=0.3)
    
    assigned_ids = []
    for frame_idx in range(10):
        # Vehicle moves 5 pixels right each frame: x1 = 100 + frame*5
        x1 = 100 + frame_idx * 5
        y1 = 100
        x2 = x1 + 50
        y2 = y1 + 50
        
        det = Detection(bbox=(x1, y1, x2, y2), confidence=0.9, class_id=2, class_name="car")
        tracks = tracker.update([det])
        
        assert len(tracks) == 1
        assigned_ids.append(tracks[0].track_id)

    # All frames should have tracked the SAME vehicle ID
    assert len(set(assigned_ids)) == 1
    assert assigned_ids[0] == 1


def test_counter_no_double_counting():
    """
    Simulate a vehicle tracked across 10 frames.
    Verify total unique count is 1, not 10.
    """
    tracker = VehicleTracker()
    counter = VehicleCounter()

    for frame_idx in range(10):
        x1 = 50 + frame_idx * 4
        y1 = 50
        det = Detection(bbox=(x1, y1, x1 + 40, y1 + 40), confidence=0.85, class_id=2, class_name="car")
        tracks = tracker.update([det])
        metrics = counter.update(tracks)

    assert metrics.total_unique_vehicles == 1
    assert metrics.active_vehicles == 1
    assert metrics.class_counts.get("car") == 1


def test_region_of_interest_counting():
    """Verify polygonal ROI filtering correctly identifies vehicle presence."""
    north_roi = RegionOfInterest(
        name="North_Approach",
        polygon=[(0, 0), (200, 0), (200, 200), (0, 200)]
    )
    south_roi = RegionOfInterest(
        name="South_Approach",
        polygon=[(300, 300), (500, 300), (500, 500), (300, 500)]
    )

    counter = VehicleCounter(regions=[north_roi, south_roi])
    tracker = VehicleTracker()

    # Frame 1: Car inside North ROI (centroid at (100, 100))
    det_north = Detection(bbox=(80, 80, 120, 120), confidence=0.9, class_id=2, class_name="car")
    tracks = tracker.update([det_north])
    metrics = counter.update(tracks)

    assert metrics.region_active_counts["North_Approach"] == 1
    assert metrics.region_active_counts["South_Approach"] == 0
    assert metrics.region_cumulative_counts["North_Approach"] == 1
