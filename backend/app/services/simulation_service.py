"""
Background Simulation Service.
Orchestrates live SUMO simulation runs and streams telemetry to connected WebSocket clients.
"""
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from sumo.simulation import (
    SumoSimulation,
    SimulationMetrics,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW
)
from sumo.controllers.fixed_time import FixedTimeController
from sumo.controllers.adaptive import AdaptiveController
from sumo.controllers.q_learning_controller import QLearningController
from sumo.controllers.vac_vbot import VacVBotController
from backend.app.config.settings import settings
from backend.app.models.database import save_experiment_result

PHASE_NAMES = {
    PHASE_NS_GREEN: "North-South GREEN",
    PHASE_NS_YELLOW: "North-South YELLOW",
    PHASE_EW_GREEN: "East-West GREEN",
    PHASE_EW_YELLOW: "East-West YELLOW"
}


class SimulationService:
    """
    Singleton service managing the lifecycle of live SUMO simulations in background threads.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.sim: Optional[SumoSimulation] = None
        self.controller = None
        self.controller_name: str = "adaptive"
        self.scenario_name: str = "medium"
        self.seed: int = 42
        self.duration: int = 1800
        self.step_delay: float = 0.05
        
        self.is_running: bool = False
        self.stop_requested: bool = False
        self.thread: Optional[threading.Thread] = None
        
        # Latest telemetry snapshot
        self.latest_metrics: Optional[SimulationMetrics] = None
        self.history_samples: List[Dict[str, Any]] = []
        self.ws_subscribers: List[asyncio.Queue] = []

    def start_simulation(
        self,
        controller: str = "adaptive",
        scenario: str = "medium",
        seed: int = 42,
        duration: int = 1800,
        step_delay: float = 0.05
    ) -> Dict[str, Any]:
        """Start a new background simulation run."""
        if self.is_running:
            self.stop_simulation()

        self.controller_name = controller
        self.scenario_name = scenario
        self.seed = seed
        self.duration = duration
        self.step_delay = step_delay
        self.stop_requested = False
        self.history_samples = []

        # Instantiate controller
        q_table_path = Path(settings.MODELS_DIR) / "q_table.json"
        if controller == "fixed_time":
            self.controller = FixedTimeController(ns_green_duration=30, ew_green_duration=30)
        elif controller == "adaptive":
            self.controller = AdaptiveController(min_green=10, max_green=60)
        elif controller == "q_learning":
            self.controller = QLearningController(q_table_path=q_table_path)
        elif controller == "vac_vbot":
            self.controller = VacVBotController()
        else:
            raise ValueError(f"Unknown controller '{controller}'")

        self.controller.reset()

        # Start thread
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        return {"status": "started", "controller": controller, "scenario": scenario, "seed": seed}

    def _run_loop(self):
        """Worker thread executing SUMO steps."""
        self.is_running = True
        self.sim = SumoSimulation(
            scenario=self.scenario_name,
            seed=self.seed,
            duration=self.duration,
            min_green=10,
            max_green=60,
            yellow_time=4
        )

        try:
            self.sim.start()
            while not self.stop_requested and self.sim.current_step < self.duration:
                metrics = self.sim.step()
                self.latest_metrics = metrics

                # Apply controller decision
                target_phase = self.controller.decide_action(metrics)
                self.sim.request_phase_switch(target_phase)

                # Record snapshot
                snapshot = {
                    "step": metrics.step,
                    "phase": metrics.current_phase,
                    "phase_name": PHASE_NAMES.get(metrics.current_phase, f"Phase {metrics.current_phase}"),
                    "phase_duration": metrics.current_phase_duration,
                    "total_queue": metrics.total_queue_length,
                    "total_wait": round(metrics.total_waiting_time, 2),
                    "throughput": metrics.throughput,
                    "average_speed": round(metrics.average_speed_mps, 2),
                    "approaches": metrics.approach_queues
                }
                self.history_samples.append(snapshot)
                if len(self.history_samples) > 500:
                    self.history_samples.pop(0)

                # Visual pacing delay
                if self.step_delay > 0:
                    time.sleep(self.step_delay)

        finally:
            if self.sim:
                self.sim.close()
            self.is_running = False

    def stop_simulation(self) -> Dict[str, Any]:
        """Request the active simulation to halt."""
        self.stop_requested = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.is_running = False
        return {"status": "stopped"}

    def get_current_state(self) -> Dict[str, Any]:
        """Format current telemetry for REST API or WebSockets."""
        if self.latest_metrics is None or not self.is_running:
            return {
                "step": 0,
                "current_phase": 0,
                "phase_name": "Standby",
                "phase_duration": 0,
                "total_queue": 0,
                "total_waiting_time": 0.0,
                "average_speed_mps": 0.0,
                "throughput": 0,
                "approaches": {
                    "North": {"approach_name": "North", "active_vehicles": 0, "queue_length": 0, "waiting_time_s": 0.0, "mean_speed_mps": 0.0, "density_level": "LOW", "normalized_density": 0.0},
                    "South": {"approach_name": "South", "active_vehicles": 0, "queue_length": 0, "waiting_time_s": 0.0, "mean_speed_mps": 0.0, "density_level": "LOW", "normalized_density": 0.0},
                    "East": {"approach_name": "East", "active_vehicles": 0, "queue_length": 0, "waiting_time_s": 0.0, "mean_speed_mps": 0.0, "density_level": "LOW", "normalized_density": 0.0},
                    "West": {"approach_name": "West", "active_vehicles": 0, "queue_length": 0, "waiting_time_s": 0.0, "mean_speed_mps": 0.0, "density_level": "LOW", "normalized_density": 0.0},
                },
                "active_controller": self.controller_name,
                "simulation_running": False
            }

        m = self.latest_metrics
        app_dict = {}
        for name in ["North", "South", "East", "West"]:
            q = m.approach_queues.get(name, 0)
            w = m.approach_waiting_times.get(name, 0.0)
            spd = m.approach_speeds.get(name, 0.0)
            cnt = m.approach_counts.get(name, 0)
            
            density_score = min(1.0, (q * 0.5 + cnt * 0.5) / 10.0)
            level = "LOW" if density_score < 0.3 else "MEDIUM" if density_score < 0.7 else "HIGH"
            
            app_dict[name] = {
                "approach_name": name,
                "active_vehicles": cnt,
                "queue_length": q,
                "waiting_time_s": round(w, 2),
                "mean_speed_mps": round(spd, 2),
                "density_level": level,
                "normalized_density": round(density_score, 2)
            }

        return {
            "step": m.step,
            "current_phase": m.current_phase,
            "phase_name": PHASE_NAMES.get(m.current_phase, f"Phase {m.current_phase}"),
            "phase_duration": m.current_phase_duration,
            "total_queue": m.total_queue_length,
            "total_waiting_time": round(m.total_waiting_time, 2),
            "average_speed_mps": round(m.average_speed_mps, 2),
            "throughput": m.throughput,
            "approaches": app_dict,
            "active_controller": self.controller_name,
            "simulation_running": self.is_running
        }

simulation_service = SimulationService()
