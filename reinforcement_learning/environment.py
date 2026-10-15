"""
Gym-like Reinforcement Learning Environment for SUMO Traffic Signal Control.
"""
from typing import Tuple, List, Optional, Dict, Any
from pathlib import Path
from sumo.simulation import (
    SumoSimulation,
    SimulationMetrics,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW
)
from reinforcement_learning.state import extract_state_tuple
from reinforcement_learning.actions import ACTION_KEEP, ACTION_SWITCH
from reinforcement_learning.reward import RewardCalculator, RewardConfig


class TrafficRLEnvironment:
    """
    RL Environment wrapping SumoSimulation with standard step() and reset() API.
    """

    def __init__(
        self,
        scenario: str = "medium",
        seed: int = 42,
        duration: int = 3600,
        min_green: int = 10,
        max_green: int = 60,
        yellow_time: int = 4,
        reward_config: Optional[RewardConfig] = None,
        gui: bool = False
    ):
        self.scenario = scenario
        self.seed = seed
        self.duration = duration
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.reward_calculator = RewardCalculator(reward_config)
        self.gui = gui

        self.sim: Optional[SumoSimulation] = None
        self.last_metrics: Optional[SimulationMetrics] = None

    def reset(self, new_seed: Optional[int] = None) -> Tuple[int, int, int, int]:
        """Reset environment, restart simulation, and return initial state."""
        if new_seed is not None:
            self.seed = new_seed

        if self.sim is not None:
            self.sim.close()

        self.sim = SumoSimulation(
            scenario=self.scenario,
            seed=self.seed,
            duration=self.duration,
            min_green=self.min_green,
            max_green=self.max_green,
            yellow_time=self.yellow_time,
            gui=self.gui
        )
        self.sim.start()

        # Step 1 to initialize metrics
        self.last_metrics = self.sim.step()
        state = extract_state_tuple(self.last_metrics, self.min_green, self.max_green)
        return state

    def get_legal_actions(self) -> List[int]:
        """
        Return legal actions in the current state:
        - If yellow transition is active -> [ACTION_KEEP]
        - If current_phase_duration < min_green -> [ACTION_KEEP]
        - If current_phase_duration >= max_green -> [ACTION_SWITCH]
        - Otherwise -> [ACTION_KEEP, ACTION_SWITCH]
        """
        if self.sim is None:
            return [ACTION_KEEP]

        if self.sim.yellow_timer > 0:
            return [ACTION_KEEP]

        if self.sim.phase_timer < self.min_green:
            return [ACTION_KEEP]

        if self.sim.phase_timer >= self.max_green:
            return [ACTION_SWITCH]

        return [ACTION_KEEP, ACTION_SWITCH]

    def step(
        self,
        action: int
    ) -> Tuple[Tuple[int, int, int, int], float, bool, Dict[str, Any]]:
        """
        Execute an action, step simulation, compute reward, and return (next_state, reward, done, info).
        """
        if self.sim is None or not self.sim.is_running:
            raise RuntimeError("Environment is not running. Call reset() first.")

        switched = False
        if action == ACTION_SWITCH:
            target_phase = PHASE_EW_GREEN if self.sim.current_phase == PHASE_NS_GREEN else PHASE_NS_GREEN
            switched = self.sim.request_phase_switch(target_phase)

        # Advance simulation step
        metrics = self.sim.step()
        self.last_metrics = metrics

        # Next state
        next_state = extract_state_tuple(metrics, self.min_green, self.max_green)

        # Reward
        max_green_exceeded = (self.sim.phase_timer >= self.max_green)
        reward = self.reward_calculator.calculate_reward(
            metrics=metrics,
            action_taken=action,
            phase_switched=switched,
            max_green_exceeded=max_green_exceeded
        )

        done = (self.sim.current_step >= self.duration)
        info = {
            "step": metrics.step,
            "queue_length": metrics.total_queue_length,
            "waiting_time": metrics.total_waiting_time,
            "throughput": metrics.throughput,
            "average_speed": metrics.average_speed_mps
        }

        return next_state, reward, done, info

    def close(self) -> None:
        """Close simulation safely."""
        if self.sim is not None:
            self.sim.close()
            self.sim = None
