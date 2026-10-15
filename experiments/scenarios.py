"""
Traffic Demand Scenario Definitions and Configurations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TrafficScenario:
    name: str
    description: str
    total_vph: int
    ns_ratio: float
    ew_ratio: float
    is_surge: bool = False

SCENARIOS: Dict[str, TrafficScenario] = {
    "low": TrafficScenario(
        name="low",
        description="Light traffic conditions (~400 veh/hr)",
        total_vph=400,
        ns_ratio=0.50,
        ew_ratio=0.50
    ),
    "medium": TrafficScenario(
        name="medium",
        description="Balanced medium urban traffic (~900 veh/hr)",
        total_vph=900,
        ns_ratio=0.50,
        ew_ratio=0.50
    ),
    "high": TrafficScenario(
        name="high",
        description="High volume congested traffic (~1600 veh/hr)",
        total_vph=1600,
        ns_ratio=0.50,
        ew_ratio=0.50
    ),
    "unbalanced": TrafficScenario(
        name="unbalanced",
        description="Directionally unbalanced flow (80% North-South vs 20% East-West)",
        total_vph=1200,
        ns_ratio=0.80,
        ew_ratio=0.20
    ),
    "peak": TrafficScenario(
        name="peak",
        description="Peak hour sinusoidal surge peaking at 1800 veh/hr",
        total_vph=1800,
        ns_ratio=0.60,
        ew_ratio=0.40,
        is_surge=True
    )
}

DEFAULT_SEEDS: List[int] = [42, 101, 2024]
ALL_CONTROLLERS: List[str] = ["fixed_time", "adaptive", "vac_vbot", "q_learning"]
