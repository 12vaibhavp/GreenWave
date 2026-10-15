"""
Fixed-Time (Pre-Timed) Traffic Signal Controller.
Cycles through phases with fixed, predefined green durations.
"""
from sumo.controllers.base import BaseTrafficController
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN


class FixedTimeController(BaseTrafficController):
    """
    Fixed-Time Controller that switches between North-South and East-West green
    phases at fixed intervals.
    """

    def __init__(
        self,
        ns_green_duration: int = 30,
        ew_green_duration: int = 30,
        name: str = "Fixed-Time"
    ):
        super().__init__(name=name)
        self.ns_green_duration = max(5, ns_green_duration)
        self.ew_green_duration = max(5, ew_green_duration)
        self.current_target_phase: int = PHASE_NS_GREEN

    def reset(self) -> None:
        self.current_target_phase = PHASE_NS_GREEN

    def decide_action(self, metrics: SimulationMetrics) -> int:
        """
        Check if the active green phase has reached its fixed duration.
        If reached, switch to the opposite phase.
        """
        if metrics.current_phase == PHASE_NS_GREEN:
            if metrics.current_phase_duration >= self.ns_green_duration:
                self.current_target_phase = PHASE_EW_GREEN
            else:
                self.current_target_phase = PHASE_NS_GREEN
        elif metrics.current_phase == PHASE_EW_GREEN:
            if metrics.current_phase_duration >= self.ew_green_duration:
                self.current_target_phase = PHASE_NS_GREEN
            else:
                self.current_target_phase = PHASE_EW_GREEN

        return self.current_target_phase
