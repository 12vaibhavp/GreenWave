"""
Phase 6 Automated Tests: Q-Learning, State Discretization, Reward & Training
"""
import pytest
from pathlib import Path
from reinforcement_learning.state import (
    discretize_queue,
    discretize_duration,
    extract_state_tuple,
    state_to_string,
    string_to_state
)
from reinforcement_learning.actions import ACTION_KEEP, ACTION_SWITCH, NUM_ACTIONS
from reinforcement_learning.reward import RewardCalculator, RewardConfig
from reinforcement_learning.q_learning import QLearningAgent
from reinforcement_learning.train import train_agent
from sumo.simulation import SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN
from sumo.controllers.q_learning_controller import QLearningController


def make_dummy_metrics(phase: int, duration: int, ns_q: int, ew_q: int, wait: float = 0.0, arrived: int = 0) -> SimulationMetrics:
    return SimulationMetrics(
        step=duration,
        current_phase=phase,
        current_phase_duration=duration,
        approach_queues={"North": ns_q, "South": 0, "East": ew_q, "West": 0},
        approach_waiting_times={"North": wait, "South": 0.0, "East": 0.0, "West": 0.0},
        approach_speeds={"North": 10.0, "South": 10.0, "East": 10.0, "West": 10.0},
        approach_counts={"North": ns_q, "South": 0, "East": ew_q, "West": 0},
        total_queue_length=ns_q + ew_q,
        total_waiting_time=wait,
        average_speed_mps=10.0,
        total_arrived=arrived,
        total_departed=arrived,
        throughput=arrived,
        step_arrived=arrived,
        average_travel_time=15.0
    )


def test_state_discretization_logic():
    """Verify queue and duration binning."""
    assert discretize_queue(0) == 0
    assert discretize_queue(2) == 1
    assert discretize_queue(6) == 2
    assert discretize_queue(15) == 3

    assert discretize_duration(5, min_green=10, max_green=60) == 0
    assert discretize_duration(20, min_green=10, max_green=60) == 1
    assert discretize_duration(45, min_green=10, max_green=60) == 2
    assert discretize_duration(65, min_green=10, max_green=60) == 3

    m = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=25, ns_q=5, ew_q=10)
    s = extract_state_tuple(m)
    assert s == (2, 3, 0, 1)  # NS med (5), EW high (10), NS Green (0), duration 25s (1)

    s_str = state_to_string(s)
    assert s_str == "2_3_0_1"
    assert string_to_state(s_str) == s


def test_reward_formulation():
    """Verify reward calculator penalizes queues/switches and rewards throughput."""
    calc = RewardCalculator()
    
    # Case 1: Empty intersection, no switch -> 0 penalty
    m_clean = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=10, ns_q=0, ew_q=0)
    r1 = calc.calculate_reward(m_clean, action_taken=0, phase_switched=False)
    assert r1 == 0.0

    # Case 2: High queue penalty
    m_busy = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=10, ns_q=10, ew_q=10, wait=100.0)
    r2 = calc.calculate_reward(m_busy, action_taken=0, phase_switched=False)
    assert r2 < 0.0

    # Case 3: Throughput bonus
    m_arrived = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=10, ns_q=0, ew_q=0, arrived=3)
    r3 = calc.calculate_reward(m_arrived, action_taken=0, phase_switched=False)
    assert r3 == 30.0  # 3 * 10.0


def test_q_learning_bellman_update(tmp_path):
    """Verify Q-learning agent updates Q-table correctly via Bellman equation."""
    agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.0)

    s0 = (1, 1, 0, 1)
    s1 = (0, 0, 0, 1)
    action = ACTION_KEEP
    reward = 10.0

    # Before update
    assert agent._get_q_values(state_to_string(s0))[action] == 0.0

    # Update: Q(s0, 0) <- 0 + 0.5 * (10.0 + 0.9 * 0 - 0) = 5.0
    td = agent.update(s0, action, reward, s1, legal_next_actions=[0, 1], done=False)
    assert td == 10.0
    assert agent._get_q_values(state_to_string(s0))[action] == 5.0

    # Test serialization
    q_file = tmp_path / "test_qtable.json"
    agent.save(q_file)
    assert q_file.exists()

    agent_loaded = QLearningAgent()
    agent_loaded.load(q_file)
    assert agent_loaded._get_q_values(state_to_string(s0))[action] == 5.0


def test_short_training_run(tmp_path):
    """Run a fast 2-episode training loop to verify end-to-end RL execution."""
    out_q = tmp_path / "trained_q.json"
    out_res = tmp_path / "results"
    
    agent, df = train_agent(
        episodes=2,
        duration=60,  # 60 steps
        scenario="low",
        output_qtable_path=out_q,
        results_dir=out_res
    )

    assert out_q.exists()
    assert len(df) == 2
    assert "total_reward" in df.columns
    assert len(agent.q_table) > 0

    # Verify QLearningController can load and query the trained policy
    ctrl = QLearningController(q_table_path=out_q)
    m = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=20, ns_q=1, ew_q=8)
    chosen_phase = ctrl.decide_action(m)
    assert chosen_phase in [PHASE_NS_GREEN, PHASE_EW_GREEN]
