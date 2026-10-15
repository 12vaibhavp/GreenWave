"""
Vision-to-RL Integration Bridge.
Converts Computer Vision IntersectionTrafficState into discrete RL State representation
and queries the RL / Adaptive policy for signal actuation.
"""
from typing import Tuple, Dict, Any, Optional
from vision.traffic_density import IntersectionTrafficState, DensityLevel
from reinforcement_learning.state import discretize_queue, discretize_duration, state_to_string
from reinforcement_learning.actions import ACTION_KEEP, ACTION_SWITCH
from sumo.controllers.q_learning_controller import QLearningController
from sumo.controllers.adaptive import AdaptiveController
from sumo.simulation import PHASE_NS_GREEN, PHASE_EW_GREEN


class VisionRLBridge:
    """
    Adapter bridging real-time Computer Vision detections with RL Policy decisions.
    """

    def __init__(
        self,
        controller_type: str = "q_learning",
        q_table_path: Optional[str] = None,
        min_green: int = 10,
        max_green: int = 60
    ):
        self.controller_type = controller_type
        self.min_green = min_green
        self.max_green = max_green

        if controller_type == "q_learning":
            self.controller = QLearningController(
                q_table_path=q_table_path,
                min_green=min_green,
                max_green=max_green
            )
        elif controller_type == "adaptive":
            self.controller = AdaptiveController(
                min_green=min_green,
                max_green=max_green
            )
        else:
            raise ValueError(f"Unsupported controller type '{controller_type}'")

        self.current_signal_phase: int = PHASE_NS_GREEN
        self.current_phase_duration: int = 0

    def step_timer(self, delta_seconds: int = 1) -> None:
        """Advance internal signal phase timer."""
        self.current_phase_duration += delta_seconds

    def convert_vision_to_rl_state(
        self,
        vision_state: IntersectionTrafficState
    ) -> Tuple[int, int, int, int]:
        """
        Map camera-derived approach queues into discrete state tuple:
        (ns_queue_level, ew_queue_level, current_phase_idx, duration_bucket)
        """
        # Sum stopped vehicles per axis
        ns_stopped = (
            vision_state.approaches.get("North", {}).queue_metrics.stopped_vehicles
            if "North" in vision_state.approaches else 0
        ) + (
            vision_state.approaches.get("South", {}).queue_metrics.stopped_vehicles
            if "South" in vision_state.approaches else 0
        )

        ew_stopped = (
            vision_state.approaches.get("East", {}).queue_metrics.stopped_vehicles
            if "East" in vision_state.approaches else 0
        ) + (
            vision_state.approaches.get("West", {}).queue_metrics.stopped_vehicles
            if "West" in vision_state.approaches else 0
        )

        ns_level = discretize_queue(ns_stopped)
        ew_level = discretize_queue(ew_stopped)
        phase_idx = 0 if self.current_signal_phase == PHASE_NS_GREEN else 1
        dur_bucket = discretize_duration(self.current_phase_duration, self.min_green, self.max_green)

        return (ns_level, ew_level, phase_idx, dur_bucket)

    def evaluate_signal_action(
        self,
        vision_state: IntersectionTrafficState
    ) -> Dict[str, Any]:
        """
        Evaluate camera state and produce recommended signal decision.
        """
        rl_state = self.convert_vision_to_rl_state(vision_state)
        state_key = state_to_string(rl_state)

        # Determine legal actions
        if self.current_phase_duration < self.min_green:
            legal_actions = [ACTION_KEEP]
        elif self.current_phase_duration >= self.max_green:
            legal_actions = [ACTION_SWITCH]
        else:
            legal_actions = [ACTION_KEEP, ACTION_SWITCH]

        if self.controller_type == "q_learning":
            action = self.controller.agent.choose_action(rl_state, legal_actions=legal_actions, deterministic=True)
        else:
            # Rule-based fallback
            action = ACTION_KEEP if self.current_phase_duration < self.min_green else ACTION_SWITCH

        action_name = "KEEP_PHASE" if action == ACTION_KEEP else "SWITCH_PHASE"

        # Apply target phase update if switch was decided
        if action == ACTION_SWITCH:
            target_phase = PHASE_EW_GREEN if self.current_signal_phase == PHASE_NS_GREEN else PHASE_NS_GREEN
            self.current_signal_phase = target_phase
            self.current_phase_duration = 0
        else:
            self.step_timer(1)

        return {
            "state_tuple": rl_state,
            "state_key": state_key,
            "action_id": action,
            "action_name": action_name,
            "active_phase": "North-South GREEN" if self.current_signal_phase == PHASE_NS_GREEN else "East-West GREEN",
            "phase_duration": self.current_phase_duration,
            "critical_approach": vision_state.critical_approach
        }
