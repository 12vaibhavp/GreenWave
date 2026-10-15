"""
Multi-Sensor Array Model for Vehicle-Actuated Control (VAC).
Replaces optical cameras with dedicated physical traffic sensors:
1. S1: Inductive Loop Detectors (ILD) at Stopline (15m) - Queue & Presence
2. S2: Ultrasonic / Infrared Sensors at Dilemma Zone (50m) - Stopping Safety & Collision Prevention
3. S3: mmWave Doppler Radar at Advance Upstream (100m) - Speed Tracking & Arrival ETA
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class ApproachSensorReadings:
    """Sensor readings across S1, S2, S3 for a single intersection approach."""
    approach_name: str  # North (SC), South (S), East (SA), West (SB)
    
    # S1: Inductive Loop Detector (Stopline Queue - 15m)
    s1_loop_present: bool = False
    s1_queue_count: int = 0
    s1_occupancy_pct: float = 0.0
    
    # S2: Dilemma Zone Sensor (Safety - 50m)
    s2_dilemma_active: bool = False
    s2_vehicle_count: int = 0
    s2_mean_speed_mps: float = 0.0
    s2_dilemma_risk_flag: bool = False  # True if vehicle trapped in dilemma zone
    
    # S3: mmWave Doppler Radar (Upstream Advance - 100m)
    s3_radar_count: int = 0
    s3_approach_speed_mps: float = 0.0
    s3_min_eta_seconds: float = 999.0   # t_arrival = d / v


@dataclass
class IntersectionSensorState:
    """Consolidated readings across all 4 approach arms (North, South, East, West)."""
    timestamp: float
    north: ApproachSensorReadings  # SC
    south: ApproachSensorReadings  # S
    east: ApproachSensorReadings   # SA
    west: ApproachSensorReadings   # SB
    total_active_queue: int = 0
    total_radar_arrivals: int = 0
    dilemma_protection_active: bool = False
    critical_approach: str = "None"


class SensorWeightingEngine:
    """
    Computes the mathematical weighting factor x_i for each sensor station:
    x_i(d_i, v_i) = [ 1 / (1 + lambda * d_i) ] * [ 1 + beta * (v_i / v_limit) ]
    
    And evaluates the combined urgency score:
    Urgency = sum( x_i * S_i )
    """

    def __init__(
        self,
        d_s1: float = 15.0,
        d_s2: float = 50.0,
        d_s3: float = 100.0,
        speed_limit_mps: float = 13.89,  # 50 km/h
        dist_decay_lambda: float = 0.015,
        speed_urgency_beta: float = 0.75,
        w_s1_queue: float = 4.0,
        w_s2_dilemma: float = 8.0,
        w_s3_arrival: float = 2.5
    ):
        self.d_s1 = d_s1
        self.d_s2 = d_s2
        self.d_s3 = d_s3
        self.v_limit = max(1.0, speed_limit_mps)
        self.dist_decay = dist_decay_lambda
        self.speed_beta = speed_urgency_beta
        
        self.w_s1 = w_s1_queue
        self.w_s2 = w_s2_dilemma
        self.w_s3 = w_s3_arrival

    def compute_sensor_weight(self, distance: float, speed: float) -> float:
        """Calculate spatial-temporal weighting factor x_i."""
        decay = 1.0 / (1.0 + self.dist_decay * distance)
        urgency = 1.0 + self.speed_beta * (max(0.0, speed) / self.v_limit)
        return float(decay * urgency)

    def evaluate_approach_urgency(self, readings: ApproachSensorReadings) -> float:
        """
        Evaluate urgency score:
        f_approach = x1 * S1 + x2 * S2 + x3 * S3
        """
        # S1: Stopline Queue (distance = 15m, speed ≈ 0 for queued)
        x1 = self.compute_sensor_weight(self.d_s1, 0.0)
        s1_score = self.w_s1 * readings.s1_queue_count

        # S2: Dilemma Zone (distance = 50m, speed = s2_mean_speed)
        x2 = self.compute_sensor_weight(self.d_s2, readings.s2_mean_speed_mps)
        s2_score = self.w_s2 * (2.0 if readings.s2_dilemma_risk_flag else readings.s2_vehicle_count)

        # S3: Upstream Radar (distance = 100m, speed = s3_speed)
        x3 = self.compute_sensor_weight(self.d_s3, readings.s3_approach_speed_mps)
        # Higher score if ETA is short (< 6 seconds)
        eta_factor = max(0.0, 1.0 - (readings.s3_min_eta_seconds / 15.0)) if readings.s3_min_eta_seconds < 999 else 0.0
        s3_score = self.w_s3 * (readings.s3_radar_count + 2.0 * eta_factor)

        total_urgency = (x1 * s1_score) + (x2 * s2_score) + (x3 * s3_score)
        return float(total_urgency)
