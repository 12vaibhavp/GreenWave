"""
Phase 10 Automated Integration Tests: Full Vision-to-RL-to-Signal Pipeline
"""
import numpy as np
import pytest
from pathlib import Path
from vision.detector import VehicleDetector, Detection
from vision.tracker import VehicleTracker, TrackedVehicle
from vision.counter import VehicleCounter, RegionOfInterest
from vision.traffic_density import TrafficDensityEstimator, IntersectionTrafficState
from vision.vision_rl_bridge import VisionRLBridge


def test_vision_to_rl_bridge_pipeline():
    """
    Test end-to-end flow:
    Simulated Frame -> Detector -> Tracker -> Counter -> Density -> Bridge -> Action Decision
    """
    # 1. Setup Vision components
    north_roi = RegionOfInterest("North", [(200, 0), (400, 0), (400, 200), (200, 200)])
    south_roi = RegionOfInterest("South", [(200, 300), (400, 300), (400, 500), (200, 500)])
    east_roi = RegionOfInterest("East", [(400, 200), (600, 200), (600, 400), (400, 400)])
    west_roi = RegionOfInterest("West", [(0, 200), (200, 200), (200, 400), (0, 400)])

    estimator = TrafficDensityEstimator(
        approach_regions={"North": north_roi, "South": south_roi, "East": east_roi, "West": west_roi}
    )

    # 2. Simulate 4 stopped vehicles in East approach (congested side)
    east_vehicles = [
        TrackedVehicle(
            track_id=10 + i,
            bbox=(450, 220 + i * 30, 490, 245 + i * 30),
            class_id=2,
            class_name="car",
            confidence=0.9,
            history=[(470, 230 + i * 30), (470, 230 + i * 30)]  # 0 speed -> stopped
        )
        for i in range(4)
    ]

    vision_state = estimator.evaluate_intersection(active_tracks=east_vehicles)
    assert vision_state.critical_approach == "East"
    assert vision_state.approaches["East"].queue_metrics.stopped_vehicles == 4

    # 3. Feed into VisionRLBridge
    bridge = VisionRLBridge(controller_type="q_learning", min_green=5, max_green=30)
    
    # State mapping verification
    rl_state = bridge.convert_vision_to_rl_state(vision_state)
    assert rl_state[1] == 2  # EW queue level is Medium (4 vehicles)

    # Decision evaluation
    decision = bridge.evaluate_signal_action(vision_state)
    assert "action_name" in decision
    assert decision["action_name"] in ["KEEP_PHASE", "SWITCH_PHASE"]
    assert decision["critical_approach"] == "East"
