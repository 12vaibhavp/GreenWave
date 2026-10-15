"""
Rule-Based Actuated / Adaptive Traffic Signal Controller.
Dynamically extends or switches signal phases based on real-time queue length disparity and gap-out.
"""
from sumo.controllers.base import BaseTrafficController
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN


class AdaptiveController(BaseTrafficController):
    """
    Rule-Based Adaptive Controller:
    - Extends green if current phase has queued or arriving vehicles.
    - Switches green to competing phase if:
        1. Competing queue exceeds active queue by threshold (queue pressure), OR
        2. Active phase has 0 queue / gap-out for consecutive steps, OR
        3. Active green duration reaches max_green limit.
    - Respects min_green time.
    """

    def __init__(
        self,
        min_green: int = 10,
        max_green: int = 60,
        queue_disparity_threshold: int = 3,
        name: str = "Adaptive-Actuated"
    ):
        super().__init__(name=name)
        self.min_green = min_green
        self.max_green = max_green
        self.queue_disparity_threshold = queue_disparity_threshold
        self.current_target_phase: int = PHASE_NS_GREEN

    def reset(self) -> None:
        self.current_target_phase = PHASE_NS_GREEN

    def decide_action(self, metrics: SimulationMetrics) -> int:
        """
        Evaluate real-time approach queues and decide target phase.
        """
        ns_queue = metrics.approach_queues.get("North", 0) + metrics.approach_queues.get("South", 0)
        ew_queue = metrics.approach_queues.get("East", 0) + metrics.approach_queues.get("West", 0)

        # If currently serving NS
        if metrics.current_phase == PHASE_NS_GREEN:
            # 1. Max green reached -> must switch
            if metrics.current_phase_duration >= self.max_green:
                self.current_target_phase = PHASE_EW_GREEN
            # 2. Before min green -> must stay
            elif metrics.current_phase_duration < self.min_green:
                self.current_target_phase = PHASE_NS_GREEN
            # 3. Gap-out: NS is empty and EW has vehicles -> switch
            elif ns_queue == 0 and ew_queue > 0:
                self.current_target_phase = PHASE_EW_GREEN
            # 4. Queue disparity: EW queue significantly higher -> switch
            elif (ew_queue - ns_queue) >= self.queue_disparity_threshold:
                self.current_target_phase = PHASE_EW_GREEN
            else:
                self.current_target_phase = PHASE_NS_GREEN

        # If currently serving EW
        elif metrics.current_phase == PHASE_EW_GREEN:
            # 1. Max green reached -> must switch
            if metrics.current_phase_duration >= self.max_green:
                self.current_target_phase = PHASE_NS_GREEN
            # 2. Before min green -> must stay
            elif metrics.current_phase_duration < self.min_green:
                self.current_target_phase = PHASE_EW_GREEN
            # 3. Gap-out: EW is empty and NS has vehicles -> switch
            elif ew_queue == 0 and ns_queue > 0:
                self.current_target_phase = PHASE_NS_GREEN
            # 4. Queue disparity: NS queue significantly higher -> switch
            elif (ns_queue - ew_queue) >= self.queue_disparity_threshold:
                self.current_target_phase = PHASE_NS_GREEN
            else:
                self.current_target_phase = PHASE_EW_GREEN

        return self.current_target_phase
