"""
VAC V-BOT: Advanced Vehicle-Actuated Autonomous Traffic Control Bot.
Implements the Multi-Sensor Fusion & Dilemma Zone Protection (DZP) model:
    f(R, G, R, G) = g( sum( x_i * S_i ) )
where S_i is the multi-stage sensor vector (S1, S2, S3) and x_i is the spatial urgency weight.
"""
from typing import Dict, Any, Optional
from sumo.controllers.base import BaseTrafficController
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN
from sumo.sensors.sensor_array import (
    ApproachSensorReadings,
    IntersectionSensorState,
    SensorWeightingEngine
)


class VacVBotController(BaseTrafficController):
    """
    VAC V-BOT (Vehicle Actuated Control Virtual Bot):
    1. Ingests multi-stage physical sensor arrays (S1 Loop, S2 Dilemma, S3 Radar).
    2. Computes weighted urgency across competing axes: U_NS vs U_EW.
    3. Enforces Dilemma Zone Protection (DZP) to eliminate red-light collision risks.
    4. Applies dynamic gap-out phase switching and platoon extension.
    """

    def __init__(
        self,
        min_green: int = 10,
        max_green: int = 60,
        yellow_time: int = 4,
        urgency_switch_threshold: float = 4.0,
        gap_out_threshold_sec: int = 3,
        name: str = "VAC-V-BOT"
    ):
        super().__init__(name=name)
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.urgency_switch_threshold = urgency_switch_threshold
        self.gap_out_threshold_sec = gap_out_threshold_sec

        self.weight_engine = SensorWeightingEngine()
        self.current_target_phase: int = PHASE_NS_GREEN
        self.active_green_gap_timer: int = 0
        self.dilemma_holds_triggered: int = 0
        self.dilemma_protection_active: bool = False

    def reset(self) -> None:
        self.current_target_phase = PHASE_NS_GREEN
        self.active_green_gap_timer = 0
        self.dilemma_holds_triggered = 0
        self.dilemma_protection_active = False

    def decide_action(self, metrics: SimulationMetrics) -> int:
        """
        Evaluate multi-sensor telemetry and make signal phase decision.
        """
        north_sensors = self._extract_approach_sensors("North", metrics)
        south_sensors = self._extract_approach_sensors("South", metrics)
        east_sensors = self._extract_approach_sensors("East", metrics)
        west_sensors = self._extract_approach_sensors("West", metrics)

        # Compute urgency scores: g(sum(x_i * S_i))
        urgency_ns = (
            self.weight_engine.evaluate_approach_urgency(north_sensors) +
            self.weight_engine.evaluate_approach_urgency(south_sensors)
        )
        urgency_ew = (
            self.weight_engine.evaluate_approach_urgency(east_sensors) +
            self.weight_engine.evaluate_approach_urgency(west_sensors)
        )

        current_phase = metrics.current_phase
        duration = metrics.current_phase_duration

        # 1. Dilemma Zone Protection (DZP) Check
        self.dilemma_protection_active = False
        if current_phase == PHASE_NS_GREEN:
            # Check if vehicles on North (SC) or South (S) are in the dilemma zone
            if north_sensors.s2_dilemma_risk_flag or south_sensors.s2_dilemma_risk_flag:
                if duration < self.max_green:
                    self.dilemma_protection_active = True
                    self.dilemma_holds_triggered += 1
                    self.current_target_phase = PHASE_NS_GREEN
                    return self.current_target_phase

        elif current_phase == PHASE_EW_GREEN:
            # Check if vehicles on East (SA) or West (SB) are in the dilemma zone
            if east_sensors.s2_dilemma_risk_flag or west_sensors.s2_dilemma_risk_flag:
                if duration < self.max_green:
                    self.dilemma_protection_active = True
                    self.dilemma_holds_triggered += 1
                    self.current_target_phase = PHASE_EW_GREEN
                    return self.current_target_phase

        # 2. Mandatory Safety Envelopes
        if duration < self.min_green:
            return current_phase

        if duration >= self.max_green:
            self.current_target_phase = PHASE_EW_GREEN if current_phase == PHASE_NS_GREEN else PHASE_NS_GREEN
            return self.current_target_phase

        # 3. Gap-Out Logic & Urgency Switching
        if current_phase == PHASE_NS_GREEN:
            ns_active = north_sensors.s1_queue_count + south_sensors.s1_queue_count + north_sensors.s3_radar_count + south_sensors.s3_radar_count
            ew_demand = east_sensors.s1_queue_count + west_sensors.s1_queue_count + east_sensors.s3_radar_count + west_sensors.s3_radar_count

            if ns_active == 0:
                self.active_green_gap_timer += 1
            else:
                self.active_green_gap_timer = 0

            # Gap out triggered OR high opposing urgency
            if (self.active_green_gap_timer >= self.gap_out_threshold_sec and ew_demand > 0) or \
               ((urgency_ew - urgency_ns) >= self.urgency_switch_threshold):
                self.current_target_phase = PHASE_EW_GREEN
                self.active_green_gap_timer = 0
            else:
                self.current_target_phase = PHASE_NS_GREEN

        elif current_phase == PHASE_EW_GREEN:
            ew_active = east_sensors.s1_queue_count + west_sensors.s1_queue_count + east_sensors.s3_radar_count + west_sensors.s3_radar_count
            ns_demand = north_sensors.s1_queue_count + south_sensors.s1_queue_count + north_sensors.s3_radar_count + south_sensors.s3_radar_count

            if ew_active == 0:
                self.active_green_gap_timer += 1
            else:
                self.active_green_gap_timer = 0

            # Gap out triggered OR high opposing urgency
            if (self.active_green_gap_timer >= self.gap_out_threshold_sec and ns_demand > 0) or \
               ((urgency_ns - urgency_ew) >= self.urgency_switch_threshold):
                self.current_target_phase = PHASE_NS_GREEN
                self.active_green_gap_timer = 0
            else:
                self.current_target_phase = PHASE_EW_GREEN

        return self.current_target_phase

    def _extract_approach_sensors(self, app_name: str, metrics: SimulationMetrics) -> ApproachSensorReadings:
        """Map simulation telemetry to S1, S2, S3 sensor signals."""
        q = metrics.approach_queues.get(app_name, 0)
        cnt = metrics.approach_counts.get(app_name, 0)
        spd = metrics.approach_speeds.get(app_name, 0.0)

        # S1: Stopline Queue (15m)
        s1_present = (q > 0)
        s1_count = q
        s1_occ = min(1.0, q / 6.0)

        # S3: Upstream Radar (100m)
        s3_count = max(0, cnt - q)
        s3_speed = spd if s3_count > 0 else 0.0
        s3_eta = (100.0 / max(1.0, s3_speed)) if (s3_count > 0 and s3_speed > 1.0) else 999.0

        # S2: Dilemma Zone (50m from stopline)
        # At 50m, arrival time to stopline is 50.0 / speed.
        # Dilemma risk is active if vehicle is traveling fast (>= 7.0 m/s) and within 2.0s to 6.5s of arrival
        s2_eta = (50.0 / max(1.0, s3_speed)) if (s3_count > 0 and s3_speed > 1.0) else 999.0
        s2_count = 1 if (s3_count > 0 and 1.5 <= s2_eta <= 6.5) else 0
        s2_risk = bool(s2_count > 0 and s3_speed >= 7.0)

        return ApproachSensorReadings(
            approach_name=app_name,
            s1_loop_present=s1_present,
            s1_queue_count=s1_count,
            s1_occupancy_pct=s1_occ,
            s2_dilemma_active=bool(s2_count > 0),
            s2_vehicle_count=s2_count,
            s2_mean_speed_mps=s3_speed,
            s2_dilemma_risk_flag=s2_risk,
            s3_radar_count=s3_count,
            s3_approach_speed_mps=s3_speed,
            s3_min_eta_seconds=s3_eta
        )
