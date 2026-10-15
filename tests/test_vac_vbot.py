"""
Automated Tests for Multi-Sensor Array & VAC V-BOT Controller.
"""
import pytest
from sumo.sensors.sensor_array import (
    ApproachSensorReadings,
    SensorWeightingEngine
)
from sumo.controllers.vac_vbot import VacVBotController
from sumo.simulation import SumoSimulation, SimulationMetrics, PHASE_NS_GREEN, PHASE_EW_GREEN


def test_sensor_weighting_engine_math():
    """Verify x_i(d_i, v_i) distance decay and speed urgency calculations."""
    engine = SensorWeightingEngine(speed_limit_mps=13.89)

    # 1. Stationary vehicle at S1 (15m, v=0)
    w_s1 = engine.compute_sensor_weight(distance=15.0, speed=0.0)
    assert 0.70 < w_s1 < 1.0  # Decayed slightly by distance

    # 2. Fast vehicle at S2 (50m, v=13.89 m/s at limit)
    w_s2 = engine.compute_sensor_weight(distance=50.0, speed=13.89)
    assert w_s2 > 0.90  # Speed factor boosts weight despite 50m distance

    # 3. Urgency evaluation
    readings = ApproachSensorReadings(
        approach_name="South",
        s1_loop_present=True,
        s1_queue_count=4,
        s2_dilemma_active=True,
        s2_vehicle_count=1,
        s2_mean_speed_mps=10.0,
        s2_dilemma_risk_flag=True,
        s3_radar_count=2,
        s3_approach_speed_mps=11.0,
        s3_min_eta_seconds=4.5
    )
    urgency = engine.evaluate_approach_urgency(readings)
    assert urgency > 15.0  # High urgency due to dilemma risk and queue


def test_vac_vbot_dilemma_hold():
    """Verify VAC V-BOT triggers DZP Green extension when a vehicle is trapped in dilemma zone."""
    vbot = VacVBotController(min_green=10, max_green=60, yellow_time=4)
    vbot.reset()

    # Simulate metrics where North approach has high-speed vehicle in dilemma zone at duration = 15s (> min_green)
    dummy_metrics = SimulationMetrics(
        step=15,
        current_phase=PHASE_NS_GREEN,
        current_phase_duration=15,
        approach_queues={"North": 0, "South": 0, "East": 3, "West": 2},
        approach_waiting_times={"North": 0.0, "South": 0.0, "East": 25.0, "West": 18.0},
        approach_speeds={"North": 12.0, "South": 0.0, "East": 0.0, "West": 0.0},
        approach_counts={"North": 1, "South": 0, "East": 3, "West": 2},
        total_queue_length=5,
        total_waiting_time=43.0,
        average_speed_mps=2.4,
        total_arrived=5,
        total_departed=10,
        throughput=5,
        step_arrived=0,
        average_travel_time=18.5
    )

    action = vbot.decide_action(dummy_metrics)
    # Despite East-West having 5 queued vehicles, VAC V-BOT MUST hold NS Green to protect North dilemma vehicle
    assert action == PHASE_NS_GREEN
    assert vbot.dilemma_protection_active is True
    assert vbot.dilemma_holds_triggered >= 1


def test_vac_vbot_in_sumo_simulation():
    """Verify closed-loop execution of VAC V-BOT in SUMO with sensor arrays."""
    sim = SumoSimulation(scenario="low", seed=42, duration=30)
    vbot = VacVBotController(min_green=10, max_green=40)
    vbot.reset()

    try:
        sim.start()
        for _ in range(30):
            m = sim.step()
            target_phase = vbot.decide_action(m)
            sim.request_phase_switch(target_phase)
            assert m.total_queue_length >= 0
            assert m.cumulative_fuel_ml >= 0.0
            assert m.cumulative_co2_g >= 0.0
    finally:
        sim.close()
