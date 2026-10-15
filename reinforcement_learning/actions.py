"""
Action Space Definition and Signal Mapping for Traffic RL.
"""
from typing import List

# Discrete Actions
ACTION_KEEP = 0    # Maintain current green phase
ACTION_SWITCH = 1  # Switch to opposite green phase

NUM_ACTIONS = 2
ALL_ACTIONS = [ACTION_KEEP, ACTION_SWITCH]

ACTION_NAMES = {
    ACTION_KEEP: "KEEP_PHASE",
    ACTION_SWITCH: "SWITCH_PHASE"
}
