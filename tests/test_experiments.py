"""
Phase 7 Automated Tests: Experiment Runner, Scenario Matrix & Benchmark Analysis
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from experiments.scenarios import SCENARIOS, DEFAULT_SEEDS, ALL_CONTROLLERS
from experiments.run_experiment import run_single_experiment, instantiate_controller
from experiments.analysis import generate_benchmark_analysis
from backend.app.models.database import fetch_all_experiments


def test_scenarios_and_controllers_registry():
    """Verify all 5 traffic scenarios and 3 controllers are defined."""
    assert len(SCENARIOS) == 5
    assert "low" in SCENARIOS
    assert "peak" in SCENARIOS
    assert len(ALL_CONTROLLERS) == 4
    assert "vac_vbot" in ALL_CONTROLLERS


def test_instantiate_controllers():
    """Verify all controllers instantiate properly."""
    for ctrl_name in ALL_CONTROLLERS:
        ctrl = instantiate_controller(ctrl_name)
        assert ctrl is not None
        assert ctrl.name is not None


def test_single_experiment_execution(tmp_path):
    """Run a fast 30-step single experiment and verify metrics structure."""
    result = run_single_experiment(
        controller_name="fixed_time",
        scenario_name="low",
        seed=42,
        duration=30,
        save_to_db=False
    )

    assert result["controller"] == "fixed_time"
    assert result["scenario"] == "low"
    assert result["avg_waiting_time"] >= 0.0
    assert result["avg_queue_length"] >= 0.0
    assert result["throughput"] >= 0


def test_benchmark_analysis_math(tmp_path):
    """Verify mean, std, and relative improvement percentages calculation."""
    # Synthetic raw results dataframe
    data = [
        # Low scenario
        {"scenario": "low", "controller": "fixed_time", "seed": 1, "avg_waiting_time": 10.0, "avg_queue_length": 4.0, "throughput": 100, "avg_travel_time": 30.0},
        {"scenario": "low", "controller": "fixed_time", "seed": 2, "avg_waiting_time": 12.0, "avg_queue_length": 4.5, "throughput": 98, "avg_travel_time": 32.0},
        {"scenario": "low", "controller": "q_learning", "seed": 1, "avg_waiting_time": 5.0, "avg_queue_length": 2.0, "throughput": 105, "avg_travel_time": 25.0},
        {"scenario": "low", "controller": "q_learning", "seed": 2, "avg_waiting_time": 6.0, "avg_queue_length": 2.2, "throughput": 104, "avg_travel_time": 24.0},
    ]
    df_raw = pd.DataFrame(data)
    df_summary = generate_benchmark_analysis(df_raw, output_dir=tmp_path)

    assert not df_summary.empty
    assert (tmp_path / "benchmark_summary.csv").exists()
    assert (tmp_path / "comparison_waiting_time.png").exists()

    # Fixed time base wait mean = 11.0. Q-learning wait mean = 5.5
    # Expected improvement = (11 - 5.5) / 11 = 50.0%
    ql_row = df_summary[(df_summary["scenario"] == "low") & (df_summary["controller"] == "q_learning")].iloc[0]
    assert ql_row["waiting_time_reduction_pct"] == pytest.approx(50.0, 0.1)
    assert ql_row["queue_reduction_pct"] == pytest.approx(50.59, 0.5)
