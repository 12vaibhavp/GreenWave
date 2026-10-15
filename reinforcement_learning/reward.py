"""
Reward Function Formulation for Traffic Signal RL Agent.
Mathematically balances queue reduction, waiting time reduction, throughput reward, and switch penalty.
"""
from dataclasses import dataclass
from typing import Optional
from sumo.simulation import SimulationMetrics


@dataclass
class RewardConfig:
    w_queue: float = 0.25           # Penalty per queued vehicle
    w_wait: float = 0.05            # Penalty per second of accumulated waiting time
    w_switch: float = 5.0           # Penalty for initiating phase change (avoids signal flickering)
    w_throughput: float = 10.0      # Positive bonus per vehicle cleared/arrived
    w_max_green_penalty: float = 15.0 # Penalty for staying on green past max_green


class RewardCalculator:
    """
    Computes step-level scalar reward:
    R = - (w_queue * Q + w_wait * W + w_switch * is_switch) + w_throughput * Arrived
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        self.config = config or RewardConfig()

    def calculate_reward(
        self,
        metrics: SimulationMetrics,
        action_taken: int,
        phase_switched: bool,
        max_green_exceeded: bool = False
    ) -> float:
        """Calculate the scalar reward for the current simulation transition."""
        total_q = metrics.total_queue_length
        total_wait = metrics.total_waiting_time
        arrived = metrics.step_arrived

        # Base penalties
        penalty = (self.config.w_queue * total_q) + (self.config.w_wait * total_wait)

        # Signal switch penalty
        if phase_switched:
            penalty += self.config.w_switch

        # Excess green duration penalty
        if max_green_exceeded and action_taken == 0:
            penalty += self.config.w_max_green_penalty

        # Throughput bonus
        reward = (self.config.w_throughput * arrived) - penalty
        return float(reward)
