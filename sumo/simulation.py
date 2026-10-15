"""
SUMO Microscopic Traffic Simulation Environment Interface via TraCI.
Provides clean step-by-step simulation, telemetry metric collection, emissions tracking, and signal actuation.
"""
import os
import sys
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import traci
import traci.constants as tc
from sumo.sumo_utils import get_sumo_binary
from sumo.network.build_network import generate_network, generate_additional_detectors
from sumo.routes.route_generator import generate_routes

# Traffic light Phase Indices for intersection 'C'
# Phase 0: NS Green (42s default in XML)
# Phase 1: NS Yellow (4s)
# Phase 2: EW Green (42s default in XML)
# Phase 3: EW Yellow (4s)
PHASE_NS_GREEN = 0
PHASE_NS_YELLOW = 1
PHASE_EW_GREEN = 2
PHASE_EW_YELLOW = 3

APPROACH_LANES = {
    "North": ["N2C_0", "N2C_1"],
    "South": ["S2C_0", "S2C_1"],
    "East": ["E2C_0", "E2C_1"],
    "West": ["W2C_0", "W2C_1"]
}


@dataclass
class SimulationMetrics:
    """Instantaneous and aggregated telemetry collected from SUMO."""
    step: int
    current_phase: int
    current_phase_duration: int
    
    # Approach-level queue & waiting
    approach_queues: Dict[str, int]          # Halting vehicles per approach
    approach_waiting_times: Dict[str, float] # Accumulated waiting time per approach (s)
    approach_speeds: Dict[str, float]        # Mean vehicle speed (m/s)
    approach_counts: Dict[str, int]          # Active vehicles on inbound lanes
    
    # Intersection aggregate metrics
    total_queue_length: int
    total_waiting_time: float
    average_speed_mps: float
    
    # Cumulative flow metrics
    total_arrived: int
    total_departed: int
    throughput: int                          # Vehicles arrived / finished trip
    step_arrived: int
    average_travel_time: float

    # Environmental & Fuel Telemetry (HBEFA3 Emission Estimation)
    cumulative_fuel_ml: float = 0.0          # Total fuel consumed (milliliters)
    cumulative_co2_g: float = 0.0            # Total CO2 emissions (grams)
    instantaneous_fuel_rate_ml_s: float = 0.0


class SumoSimulation:
    """
    Manages TraCI connection lifecycle, detector ingestion, and microscopic traffic simulation execution.
    """

    def __init__(
        self,
        net_path: Optional[Path] = None,
        route_path: Optional[Path] = None,
        det_path: Optional[Path] = None,
        scenario: str = "medium",
        seed: int = 42,
        duration: int = 3600,
        step_length: float = 1.0,
        gui: bool = False,
        min_green: int = 10,
        max_green: int = 60,
        yellow_time: int = 4,
        tls_id: str = "C"
    ):
        self.net_path = net_path or (Path(__file__).resolve().parent / "network" / "intersection.net.xml")
        self.det_path = det_path or (Path(__file__).resolve().parent / "network" / "intersection.det.xml")
        self.route_path = route_path
        self.scenario = scenario
        self.seed = seed
        self.duration = duration
        self.step_length = step_length
        self.gui = gui
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.tls_id = tls_id

        self.is_running: bool = False
        self.current_step: int = 0
        self.current_phase: int = PHASE_NS_GREEN
        self.phase_timer: int = 0
        self.pending_phase: Optional[int] = None
        self.yellow_timer: int = 0

        # Accumulated metrics tracking
        self.cumulative_arrived_vehicles: int = 0
        self.cumulative_departed_vehicles: int = 0
        self.completed_travel_times: List[float] = []
        self.vehicle_depart_times: Dict[str, float] = {}

        # Fuel and CO2 tracking
        self.cumulative_fuel_mg: float = 0.0
        self.cumulative_co2_mg: float = 0.0

    def _ensure_assets(self) -> Tuple[Path, Path, Path]:
        """Ensure network, detectors, and route files exist before launching."""
        if not self.net_path.exists():
            generate_network(self.net_path)

        if not self.det_path.exists():
            generate_additional_detectors(self.det_path)

        if self.route_path is None or not self.route_path.exists():
            self.route_path = generate_routes(
                scenario=self.scenario,
                seed=self.seed,
                duration=self.duration
            )
        return self.net_path, self.det_path, self.route_path

    def start(self) -> None:
        """Start SUMO process and connect via TraCI."""
        if self.is_running:
            self.close()

        net_file, det_file, route_file = self._ensure_assets()
        sumo_bin = get_sumo_binary(self.gui)

        sumo_cmd = [
            sumo_bin,
            "--net-file", str(net_file),
            "--route-files", str(route_file),
            "--additional-files", str(det_file),
            "--step-length", str(self.step_length),
            "--seed", str(self.seed),
            "--no-warnings", "true",
            "--waiting-time-memory", "1000",
            "--time-to-teleport", "-1"
        ]

        traci.start(sumo_cmd)
        self.is_running = True
        self.current_step = 0
        self.current_phase = PHASE_NS_GREEN
        self.phase_timer = 0
        self.pending_phase = None
        self.yellow_timer = 0
        self.cumulative_arrived_vehicles = 0
        self.cumulative_departed_vehicles = 0
        self.completed_travel_times = []
        self.vehicle_depart_times = {}
        self.cumulative_fuel_mg = 0.0
        self.cumulative_co2_mg = 0.0

        # Set initial signal phase
        traci.trafficlight.setPhase(self.tls_id, self.current_phase)

    def step(self) -> SimulationMetrics:
        """Advance simulation by 1 step and collect telemetry."""
        if not self.is_running:
            raise RuntimeError("Simulation is not running. Call start() first.")

        # Track departed vehicles for travel time calculation
        departed_ids = traci.simulation.getDepartedIDList()
        for vid in departed_ids:
            self.vehicle_depart_times[vid] = self.current_step * self.step_length
            self.cumulative_departed_vehicles += 1

        # Track arrived vehicles for travel time calculation
        arrived_ids = traci.simulation.getArrivedIDList()
        for vid in arrived_ids:
            if vid in self.vehicle_depart_times:
                travel_time = (self.current_step * self.step_length) - self.vehicle_depart_times.pop(vid)
                self.completed_travel_times.append(travel_time)
            self.cumulative_arrived_vehicles += 1

        # Advance SUMO simulation step
        traci.simulationStep()
        self.current_step += 1
        self.phase_timer += 1

        # Handle yellow transition timers
        if self.yellow_timer > 0:
            self.yellow_timer -= 1
            if self.yellow_timer == 0 and self.pending_phase is not None:
                # Yellow finished, switch to pending target green phase
                self.current_phase = self.pending_phase
                self.pending_phase = None
                self.phase_timer = 0
                traci.trafficlight.setPhase(self.tls_id, self.current_phase)

        # Collect approach-level telemetry and emissions
        app_queues: Dict[str, int] = {}
        app_wait_times: Dict[str, float] = {}
        app_speeds: Dict[str, float] = {}
        app_counts: Dict[str, int] = {}

        step_fuel_mg = 0.0
        step_co2_mg = 0.0

        for app_name, lanes in APPROACH_LANES.items():
            q_sum = sum(traci.lane.getLastStepHaltingNumber(lid) for lid in lanes)
            w_sum = sum(traci.lane.getWaitingTime(lid) for lid in lanes)
            speeds = [traci.lane.getLastStepMeanSpeed(lid) for lid in lanes]
            c_sum = sum(traci.lane.getLastStepVehicleNumber(lid) for lid in lanes)
            
            # Emissions from inbound lanes
            fuel_sum = sum(traci.lane.getFuelConsumption(lid) for lid in lanes)
            co2_sum = sum(traci.lane.getCO2Emission(lid) for lid in lanes)
            step_fuel_mg += fuel_sum
            step_co2_mg += co2_sum

            app_queues[app_name] = q_sum
            app_wait_times[app_name] = w_sum
            app_speeds[app_name] = float(sum(speeds) / max(1, len(speeds)))
            app_counts[app_name] = c_sum

        self.cumulative_fuel_mg += step_fuel_mg
        self.cumulative_co2_mg += step_co2_mg

        # Conversion: 1 mg of fuel ≈ 0.00134 ml (density 0.745 g/ml)
        cum_fuel_ml = (self.cumulative_fuel_mg / 1000.0) * 1.34
        cum_co2_g = self.cumulative_co2_mg / 1000.0
        instant_fuel_rate_ml_s = (step_fuel_mg / 1000.0) * 1.34

        total_q = sum(app_queues.values())
        total_w = sum(app_wait_times.values())
        avg_spd = float(sum(app_speeds.values()) / max(1, len(app_speeds)))
        avg_travel = float(sum(self.completed_travel_times) / max(1, len(self.completed_travel_times))) if self.completed_travel_times else 0.0

        return SimulationMetrics(
            step=self.current_step,
            current_phase=self.current_phase,
            current_phase_duration=self.phase_timer,
            approach_queues=app_queues,
            approach_waiting_times=app_wait_times,
            approach_speeds=app_speeds,
            approach_counts=app_counts,
            total_queue_length=total_q,
            total_waiting_time=total_w,
            average_speed_mps=avg_spd,
            total_arrived=self.cumulative_arrived_vehicles,
            total_departed=self.cumulative_departed_vehicles,
            throughput=self.cumulative_arrived_vehicles,
            step_arrived=len(arrived_ids),
            average_travel_time=avg_travel,
            cumulative_fuel_ml=cum_fuel_ml,
            cumulative_co2_g=cum_co2_g,
            instantaneous_fuel_rate_ml_s=instant_fuel_rate_ml_s
        )

    def request_phase_switch(self, target_green_phase: int) -> bool:
        """
        Request signal phase switch to a target green phase (PHASE_NS_GREEN or PHASE_EW_GREEN).
        Enforces safety constraints:
          1. Cannot switch if yellow transition is currently active.
          2. Must satisfy min_green duration before leaving current phase.
          3. Automatically transitions through yellow phase.
        """
        if self.yellow_timer > 0:
            return False

        if self.current_phase == target_green_phase:
            return True

        if self.phase_timer < self.min_green:
            return False

        # Intermediate yellow phase
        if self.current_phase == PHASE_NS_GREEN:
            yellow_phase = PHASE_NS_YELLOW
        else:
            yellow_phase = PHASE_EW_YELLOW

        self.current_phase = yellow_phase
        self.pending_phase = target_green_phase
        self.yellow_timer = self.yellow_time
        traci.trafficlight.setPhase(self.tls_id, yellow_phase)
        return True

    def close(self) -> None:
        """Safely disconnect and close TraCI."""
        if self.is_running:
            try:
                traci.close()
            except Exception:
                pass
            self.is_running = False
