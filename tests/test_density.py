"""
Phase 3 Automated Tests: Traffic Density & Queue Estimation
"""
import pytest
from vision.config import VisionConfig
from vision.counter import RegionOfInterest
from vision.tracker import TrackedVehicle
from vision.traffic_density import (
    TrafficDensityEstimator,
    DensityLevel,
    ApproachDensityMetrics,
    IntersectionTrafficState
)


@pytest.fixture
def setup_intersection():
    """Create a 4-way intersection setup for testing."""
    north_roi = RegionOfInterest(
        name="North",
        polygon=[(100, 0), (200, 0), (200, 200), (100, 200)]
    )
    south_roi = RegionOfInterest(
        name="South",
        polygon=[(100, 300), (200, 300), (200, 500), (100, 500)]
    )
    east_roi = RegionOfInterest(
        name="East",
        polygon=[(300, 100), (500, 100), (500, 200), (300, 200)]
    )
    west_roi = RegionOfInterest(
        name="West",
        polygon=[(0, 100), (100, 100), (100, 200), (0, 200)]
    )

    estimator = TrafficDensityEstimator(
        max_vehicles_per_approach=10,
        pixels_per_meter=10.0,
        stop_lines={
            "North": ((100, 200), (200, 200)),
            "South": ((100, 300), (200, 300))
        }
    )
    estimator.add_approach("North", north_roi)
    estimator.add_approach("South", south_roi)
    estimator.add_approach("East", east_roi)
    estimator.add_approach("West", west_roi)

    return estimator


def test_empty_approach_density(setup_intersection):
    """Empty intersection should yield LOW density and 0.0 score."""
    estimator = setup_intersection
    state = estimator.evaluate_intersection(active_tracks=[])

    assert state.total_active_vehicles == 0
    assert state.total_stopped_vehicles == 0
    for app_name, m in state.approaches.items():
        assert m.normalized_density_score == 0.0
        assert m.density_level == DensityLevel.LOW
        assert m.queue_metrics.stopped_vehicles == 0
        assert m.queue_metrics.estimated_queue_length_m == 0.0


def test_queue_detection_stopped_vs_moving(setup_intersection):
    """Verify vehicles with small displacement are marked stopped and counted as queue."""
    estimator = setup_intersection

    # Vehicle 1 in North: Stopped (history with almost 0 displacement)
    v1 = TrackedVehicle(
        track_id=1,
        bbox=(120, 100, 160, 150),
        class_id=2,
        class_name="car",
        confidence=0.9,
        history=[(140, 125), (140, 125), (140, 125)]
    )
    assert v1.speed_px == 0.0

    # Vehicle 2 in North: Moving fast (displacement > threshold)
    v2 = TrackedVehicle(
        track_id=2,
        bbox=(120, 20, 160, 70),
        class_id=2,
        class_name="car",
        confidence=0.9,
        history=[(140, 10), (140, 25), (140, 45)]
    )
    assert v2.speed_px > 5.0

    metrics = estimator.evaluate_approach("North", [v1, v2])
    assert metrics.active_vehicle_count == 2
    assert metrics.queue_metrics.stopped_vehicles == 1
    assert metrics.queue_metrics.moving_vehicles == 1
    assert metrics.queue_metrics.estimated_queue_length_px > 0.0


def test_density_levels_thresholds(setup_intersection):
    """Verify density level transitions between LOW, MEDIUM, and HIGH."""
    estimator = setup_intersection

    # 1 vehicle: LOW
    v_low = [
        TrackedVehicle(
            track_id=1,
            bbox=(120, 50, 150, 80),
            class_id=2,
            class_name="car",
            confidence=0.9,
            history=[(135, 65)]
        )
    ]
    m_low = estimator.evaluate_approach("North", v_low)
    assert m_low.density_level == DensityLevel.LOW

    # 4 vehicles: MEDIUM
    v_med = [
        TrackedVehicle(
            track_id=i,
            bbox=(120, 20 + i * 40, 160, 50 + i * 40),
            class_id=2,
            class_name="car",
            confidence=0.9,
            history=[(140, 35 + i * 40)]
        )
        for i in range(4)
    ]
    m_med = estimator.evaluate_approach("North", v_med)
    assert m_med.density_level == DensityLevel.MEDIUM

    # 10 stopped vehicles packed into North ROI: HIGH
    v_high = [
        TrackedVehicle(
            track_id=i,
            bbox=(110, 5 + i * 18, 180, 22 + i * 18),
            class_id=2,
            class_name="car",
            confidence=0.9,
            history=[(145, 13 + i * 18), (145, 13 + i * 18)]
        )
        for i in range(10)
    ]
    m_high = estimator.evaluate_approach("North", v_high)
    assert m_high.normalized_density_score >= 0.70
    assert m_high.density_level == DensityLevel.HIGH


def test_critical_approach_identification(setup_intersection):
    """Verify the intersection correctly tags the approach with highest queue/density."""
    estimator = setup_intersection

    # South has 5 stopped vehicles, East has 1 moving
    south_tracks = [
        TrackedVehicle(
            track_id=10 + i,
            bbox=(120, 320 + i * 25, 160, 345 + i * 25),
            class_id=2,
            class_name="car",
            confidence=0.9,
            history=[(140, 330 + i * 25), (140, 330 + i * 25)]
        )
        for i in range(5)
    ]
    east_tracks = [
        TrackedVehicle(
            track_id=50,
            bbox=(350, 120, 390, 160),
            class_id=2,
            class_name="car",
            confidence=0.9,
            history=[(320, 140), (370, 140)]
        )
    ]

    state = estimator.evaluate_intersection(active_tracks=south_tracks + east_tracks)
    assert state.critical_approach == "South"
    assert state.approaches["South"].queue_metrics.stopped_vehicles == 5
    assert state.total_stopped_vehicles == 5
