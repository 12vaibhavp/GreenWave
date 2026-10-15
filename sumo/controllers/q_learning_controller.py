"""
Reinforcement Learning (Q-Learning) Traffic Signal Controller.
Uses a learned Q-table policy to actuate traffic signal phases online.
"""
from pathlib import Path
from typing import Optional
from sumo.controllers.base import BaseTrafficController
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN
from reinforcement_learning.q_learning import QLearningAgent
from reinforcement_learning.state import extract_state_tuple
from reinforcement_learning.actions import ACTION_KEEP, ACTION_SWITCH


class QLearningController(BaseTrafficController):
    """
    Q-Learning Traffic Controller:
    Maps incoming traffic telemetry to discrete state, queries the trained Q-table,
    and applies optimal phase extension or switching actions.
    """

    def __init__(
        self,
        q_table_path: Optional[Path] = None,
        agent: Optional[QLearningAgent] = None,
        min_green: int = 10,
        max_green: int = 60,
        name: str = "Q-Learning"
    ):
        super().__init__(name=name)
        self.min_green = min_green
        self.max_green = max_green

        if agent is not None:
            self.agent = agent
        elif q_table_path is not None and Path(q_table_path).exists():
            self.agent = QLearningAgent(epsilon=0.0)  # Pure greedy evaluation
            self.agent.load(Path(q_table_path))
        else:
            # Untrained default agent with zero Q-table
            self.agent = QLearningAgent(epsilon=0.0)

        self.current_target_phase: int = PHASE_NS_GREEN

    def reset(self) -> None:
        self.current_target_phase = PHASE_NS_GREEN

    def decide_action(self, metrics: SimulationMetrics) -> int:
        """
        Query Q-policy for the best action given current traffic state.
        Returns target phase: PHASE_NS_GREEN or PHASE_EW_GREEN.
        """
        state = extract_state_tuple(metrics, self.min_green, self.max_green)

        # Determine legal actions based on safety bounds
        if metrics.current_phase_duration < self.min_green:
            legal_actions = [ACTION_KEEP]
        elif metrics.current_phase_duration >= self.max_green:
            legal_actions = [ACTION_SWITCH]
        else:
            legal_actions = [ACTION_KEEP, ACTION_SWITCH]

        action = self.agent.choose_action(state, legal_actions=legal_actions, deterministic=True)

        if action == ACTION_KEEP:
            # Maintain current phase
            if metrics.current_phase in [PHASE_NS_GREEN, PHASE_EW_GREEN]:
                self.current_target_phase = metrics.current_phase
        elif action == ACTION_SWITCH:
            # Switch to opposite phase
            if metrics.current_phase == PHASE_NS_GREEN:
                self.current_target_phase = PHASE_EW_GREEN
            elif metrics.current_phase == PHASE_EW_GREEN:
                self.current_target_phase = PHASE_NS_GREEN

        return self.current_target_phase
