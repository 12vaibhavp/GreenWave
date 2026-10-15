"""
Discrete State Space Representation for Tabular Q-Learning.
Discretizes continuous queue lengths, approach waiting times, and phase timers into a compact state tuple.
"""
from typing import Tuple, Dict
from dataclasses import dataclass
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN


def discretize_queue(queue_count: int) -> int:
    """
    Discretize approach queue into 4 levels:
    0: None (0 vehicles)
    1: Low (1 - 3 vehicles)
    2: Medium (4 - 8 vehicles)
    3: High (9+ vehicles)
    """
    if queue_count <= 0:
        return 0
    elif queue_count <= 3:
        return 1
    elif queue_count <= 8:
        return 2
    else:
        return 3


def discretize_duration(duration_sec: int, min_green: int = 10, max_green: int = 60) -> int:
    """
    Discretize phase duration into 4 buckets:
    0: Under minimum green (< min_green)
    1: Standard green range (min_green to 30s)
    2: Extended green range (30s to max_green)
    3: Maximum green exceeded (>= max_green)
    """
    if duration_sec < min_green:
        return 0
    elif duration_sec < 30:
        return 1
    elif duration_sec < max_green:
        return 2
    else:
        return 3


def extract_state_tuple(
    metrics: SimulationMetrics,
    min_green: int = 10,
    max_green: int = 60
) -> Tuple[int, int, int, int]:
    """
    Convert raw SimulationMetrics into a discrete state tuple:
    (ns_queue_level, ew_queue_level, phase_indicator, duration_bucket)
    
    Total discrete state space = 4 * 4 * 2 * 4 = 128 states.
    """
    ns_queue = metrics.approach_queues.get("North", 0) + metrics.approach_queues.get("South", 0)
    ew_queue = metrics.approach_queues.get("East", 0) + metrics.approach_queues.get("West", 0)

    ns_level = discretize_queue(ns_queue)
    ew_level = discretize_queue(ew_queue)

    # 0 for NS Green, 1 for EW Green (or yellow if transitioning)
    phase_idx = 0 if metrics.current_phase == PHASE_NS_GREEN else 1
    dur_bucket = discretize_duration(metrics.current_phase_duration, min_green, max_green)

    return (ns_level, ew_level, phase_idx, dur_bucket)


def state_to_string(state: Tuple[int, int, int, int]) -> str:
    """Convert state tuple to hashable/serializable string representation."""
    return f"{state[0]}_{state[1]}_{state[2]}_{state[3]}"


def string_to_state(state_str: str) -> Tuple[int, int, int, int]:
    """Parse serialized string back to state tuple."""
    parts = [int(p) for p in state_str.split("_")]
    return (parts[0], parts[1], parts[2], parts[3])
