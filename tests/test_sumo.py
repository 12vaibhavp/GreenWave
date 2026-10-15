"""
Phase 4 Automated Tests: SUMO Network, Route Generation & TraCI Simulation
"""
import os
import pytest
from pathlib import Path
from sumo.sumo_utils import get_sumo_binary, get_netconvert_binary
from sumo.network.build_network import generate_network
from sumo.routes.route_generator import generate_routes, SCENARIO_HOURLY_RATES
from sumo.simulation import (
    SumoSimulation,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW
)


def test_sumo_binaries_discoverable():
    """Ensure sumo and netconvert executables are resolved."""
    sumo_bin = get_sumo_binary(gui=False)
    netconv_bin = get_netconvert_binary()
    assert os.path.exists(sumo_bin)
    assert os.path.exists(netconv_bin)


def test_network_generation(tmp_path):
    """Ensure network generator creates a valid .net.xml file."""
    out_net = tmp_path / "test_intersection.net.xml"
    net_path = generate_network(out_net)
    assert net_path.exists()
    assert net_path.stat().st_size > 1000


def test_route_generation_scenarios(tmp_path):
    """Ensure route generator produces valid XML for all scenarios."""
    for sc in SCENARIO_HOURLY_RATES:
        out_rou = tmp_path / f"test_{sc}.rou.xml"
        rou_path = generate_routes(scenario=sc, seed=123, duration=300, output_path=out_rou)
        assert rou_path.exists()
        content = rou_path.read_text()
        assert "<routes" in content
        assert "vType id=\"car\"" in content
        assert "vehicle id=" in content


def test_traci_simulation_lifecycle(tmp_path):
    """
    Test starting SUMO with TraCI, running steps, testing signal transitions,
    collecting metrics, and safely closing.
    """
    out_net = tmp_path / "sim_test.net.xml"
    generate_network(out_net)
    out_rou = tmp_path / "sim_test.rou.xml"
    generate_routes(scenario="medium", seed=42, duration=200, output_path=out_rou)

    sim = SumoSimulation(
        net_path=out_net,
        route_path=out_rou,
        duration=200,
        min_green=5,
        yellow_time=2
    )

    try:
        sim.start()
        assert sim.is_running is True

        # Run 10 steps
        for _ in range(10):
            metrics = sim.step()

        assert metrics.step == 10
        assert metrics.current_phase == PHASE_NS_GREEN
        assert "North" in metrics.approach_queues
        assert metrics.total_queue_length >= 0

        # Request phase switch to EW_GREEN (satisfies min_green=5 since step=10)
        switched = sim.request_phase_switch(PHASE_EW_GREEN)
        assert switched is True
        # Current phase should now be NS_YELLOW for 2 steps
        assert sim.current_phase == PHASE_NS_YELLOW

        # Step 1 of yellow
        m1 = sim.step()
        assert m1.current_phase == PHASE_NS_YELLOW

        # Step 2 of yellow (transition completes)
        m2 = sim.step()
        assert m2.current_phase == PHASE_EW_GREEN

    finally:
        sim.close()
        assert sim.is_running is False
