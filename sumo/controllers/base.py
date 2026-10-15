"""
Abstract Base Traffic Signal Controller Interface.
Provides uniform execution contract across Fixed-Time, Adaptive, and Q-Learning controllers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN


class BaseTrafficController(ABC):
    """Abstract Base Class for all traffic signal controllers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def reset(self) -> None:
        """Reset internal timers or state for a new simulation episode."""
        pass

    @abstractmethod
    def decide_action(self, metrics: SimulationMetrics) -> int:
        """
        Decide the target green phase for the current simulation step.
        Returns target phase: PHASE_NS_GREEN (0) or PHASE_EW_GREEN (2).
        """
        pass
