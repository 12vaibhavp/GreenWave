"""
Phase 5 Automated Tests: Fixed-Time & Adaptive Baseline Controllers
"""
import pytest
from sumo.simulation import (
    SumoSimulation,
    SimulationMetrics,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW
)
from sumo.controllers.fixed_time import FixedTimeController
from sumo.controllers.adaptive import AdaptiveController
from sumo.network.build_network import generate_network
from sumo.routes.route_generator import generate_routes


def make_dummy_metrics(phase: int, duration: int, ns_q: int = 0, ew_q: int = 0) -> SimulationMetrics:
    """Helper to construct dummy SimulationMetrics for controller unit testing."""
    return SimulationMetrics(
        step=duration,
        current_phase=phase,
        current_phase_duration=duration,
        approach_queues={"North": ns_q // 2, "South": ns_q - ns_q // 2, "East": ew_q // 2, "West": ew_q - ew_q // 2},
        approach_waiting_times={"North": 0.0, "South": 0.0, "East": 0.0, "West": 0.0},
        approach_speeds={"North": 10.0, "South": 10.0, "East": 10.0, "West": 10.0},
        approach_counts={"North": ns_q, "South": ns_q, "East": ew_q, "West": ew_q},
        total_queue_length=ns_q + ew_q,
        total_waiting_time=0.0,
        average_speed_mps=10.0,
        total_arrived=0,
        total_departed=0,
        throughput=0,
        step_arrived=0,
        average_travel_time=0.0
    )


def test_fixed_time_controller_logic():
    """Verify FixedTimeController requests switch only after duration threshold."""
    controller = FixedTimeController(ns_green_duration=25, ew_green_duration=25)

    # Below duration: maintain
    m_below = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=15)
    assert controller.decide_action(m_below) == PHASE_NS_GREEN

    # At or above duration: switch to EW
    m_reached = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=25)
    assert controller.decide_action(m_reached) == PHASE_EW_GREEN

    # EW phase below duration: maintain EW
    m_ew_below = make_dummy_metrics(phase=PHASE_EW_GREEN, duration=10)
    assert controller.decide_action(m_ew_below) == PHASE_EW_GREEN

    # EW phase reached: switch to NS
    m_ew_reached = make_dummy_metrics(phase=PHASE_EW_GREEN, duration=25)
    assert controller.decide_action(m_ew_reached) == PHASE_NS_GREEN


def test_adaptive_controller_queue_pressure():
    """Verify AdaptiveController responds to queue disparity and respects min_green."""
    controller = AdaptiveController(min_green=10, max_green=45, queue_disparity_threshold=4)

    # Case 1: High EW queue (8 veh) vs NS queue (1 veh), but min_green not met (duration=5) -> Must stay NS
    m_early = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=5, ns_q=1, ew_q=8)
    assert controller.decide_action(m_early) == PHASE_NS_GREEN

    # Case 2: Same queues, but min_green is met (duration=12) -> Must switch to EW
    m_switch = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=12, ns_q=1, ew_q=8)
    assert controller.decide_action(m_switch) == PHASE_EW_GREEN

    # Case 3: Gap-out (NS=0, EW=2) after min_green -> Must switch to EW
    m_gapout = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=15, ns_q=0, ew_q=2)
    assert controller.decide_action(m_gapout) == PHASE_EW_GREEN

    # Case 4: Max green reached -> Must switch regardless
    m_max = make_dummy_metrics(phase=PHASE_NS_GREEN, duration=45, ns_q=10, ew_q=0)
    assert controller.decide_action(m_max) == PHASE_EW_GREEN


def test_controllers_in_sumo_simulation(tmp_path):
    """
    Run closed-loop SUMO simulation comparing FixedTime and Adaptive controllers.
    """
    net_path = tmp_path / "ctrl_test.net.xml"
    generate_network(net_path)
    rou_path = tmp_path / "ctrl_test.rou.xml"
    generate_routes(scenario="unbalanced", seed=99, duration=120, output_path=rou_path)

    # 1. Run with FixedTime
    sim_fixed = SumoSimulation(net_path=net_path, route_path=rou_path, duration=120, min_green=5, yellow_time=2)
    ctrl_fixed = FixedTimeController(ns_green_duration=15, ew_green_duration=15)
    try:
        sim_fixed.start()
        for _ in range(60):
            m = sim_fixed.step()
            target_phase = ctrl_fixed.decide_action(m)
            sim_fixed.request_phase_switch(target_phase)
        assert sim_fixed.current_step == 60
    finally:
        sim_fixed.close()

    # 2. Run with Adaptive
    sim_adapt = SumoSimulation(net_path=net_path, route_path=rou_path, duration=120, min_green=5, yellow_time=2)
    ctrl_adapt = AdaptiveController(min_green=5, max_green=30, queue_disparity_threshold=2)
    try:
        sim_adapt.start()
        for _ in range(60):
            m = sim_adapt.step()
            target_phase = ctrl_adapt.decide_action(m)
            sim_adapt.request_phase_switch(target_phase)
        assert sim_adapt.current_step == 60
    finally:
        sim_adapt.close()
