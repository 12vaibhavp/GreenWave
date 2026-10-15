"""
Automated Experiment Execution Engine for GREENWAVE.
Fairly evaluates Fixed-Time, Adaptive, VAC V-BOT, and Q-Learning controllers under identical traffic scenarios and seeds.
"""
import os
import sys
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sumo.simulation import SumoSimulation, PHASE_NS_GREEN, PHASE_EW_GREEN
from sumo.controllers.fixed_time import FixedTimeController
from sumo.controllers.adaptive import AdaptiveController
from sumo.controllers.q_learning_controller import QLearningController
from sumo.controllers.vac_vbot import VacVBotController
from experiments.scenarios import SCENARIOS, DEFAULT_SEEDS, ALL_CONTROLLERS
from backend.app.models.database import init_db, save_experiment_result
from experiments.analysis import generate_benchmark_analysis


def instantiate_controller(controller_name: str, q_table_path: Optional[Path] = None):
    """Factory to instantiate the appropriate controller."""
    q_path = q_table_path or (root_dir / "models" / "q_table.json")

    if controller_name == "fixed_time":
        return FixedTimeController(ns_green_duration=30, ew_green_duration=30)
    elif controller_name == "adaptive":
        return AdaptiveController(min_green=10, max_green=60, queue_disparity_threshold=3)
    elif controller_name == "q_learning":
        return QLearningController(q_table_path=q_path, min_green=10, max_green=60)
    elif controller_name == "vac_vbot":
        return VacVBotController(min_green=10, max_green=60, yellow_time=4)
    else:
        raise ValueError(f"Unknown controller '{controller_name}'. Choose from {ALL_CONTROLLERS}")


def run_single_experiment(
    controller_name: str,
    scenario_name: str,
    seed: int = 42,
    duration: int = 3600,
    q_table_path: Optional[Path] = None,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    Execute one reproducible simulation experiment and record ground-truth performance metrics.
    """
    exp_id = f"{controller_name}_{scenario_name}_seed{seed}_{int(time.time())}"
    print(f"--> Running Experiment [{exp_id}] ({duration}s)...")

    controller = instantiate_controller(controller_name, q_table_path=q_table_path)
    controller.reset()

    sim = SumoSimulation(
        scenario=scenario_name,
        seed=seed,
        duration=duration,
        min_green=10,
        max_green=60,
        yellow_time=4
    )

    step_queues = []
    step_waits = []
    step_speeds = []

    start_wall_time = time.time()
    try:
        sim.start()
        for _ in range(duration):
            metrics = sim.step()

            # Controller makes action decision
            target_phase = controller.decide_action(metrics)
            sim.request_phase_switch(target_phase)

            # Record step metrics
            step_queues.append(metrics.total_queue_length)
            step_waits.append(metrics.total_waiting_time)
            step_speeds.append(metrics.average_speed_mps)

    finally:
        sim.close()

    elapsed_wall = time.time() - start_wall_time

    # Calculate actual aggregate statistics
    avg_q = float(np.mean(step_queues)) if step_queues else 0.0
    max_q = int(np.max(step_queues)) if step_queues else 0
    avg_wait = float(np.mean(step_waits)) if step_waits else 0.0
    total_wait = float(np.sum(step_waits)) if step_waits else 0.0
    avg_speed = float(np.mean(step_speeds)) if step_speeds else 0.0
    throughput = int(sim.cumulative_arrived_vehicles)
    departed = int(sim.cumulative_departed_vehicles)
    avg_travel = float(np.mean(sim.completed_travel_times)) if sim.completed_travel_times else 0.0

    result_record = {
        "experiment_id": exp_id,
        "timestamp": datetime.now().isoformat(),
        "controller": controller_name,
        "scenario": scenario_name,
        "seed": seed,
        "duration_sec": duration,
        "avg_waiting_time": round(avg_wait, 2),
        "total_waiting_time": round(total_wait, 2),
        "avg_queue_length": round(avg_q, 2),
        "max_queue_length": max_q,
        "throughput": throughput,
        "total_departed": departed,
        "avg_travel_time": round(avg_travel, 2),
        "avg_speed_mps": round(avg_speed, 2),
        "config_json": json.dumps({
            "controller": controller_name,
            "scenario": scenario_name,
            "seed": seed,
            "wall_time_sec": round(elapsed_wall, 2),
            "fuel_ml": round(sim.cumulative_fuel_mg * 0.00134, 1),
            "co2_g": round(sim.cumulative_co2_mg / 1000.0, 1)
        })
    }

    if save_to_db:
        save_experiment_result(result_record)

    print(
        f"    [Done] Avg Wait: {avg_wait:.2f}s | "
        f"Avg Queue: {avg_q:.2f} | "
        f"Throughput: {throughput} veh | "
        f"Avg Travel: {avg_travel:.1f}s | "
        f"Wall Time: {elapsed_wall:.2f}s"
    )
    return result_record


def run_benchmark_matrix(
    duration: int = 300,
    seeds: Optional[List[int]] = None,
    controllers: Optional[List[str]] = None,
    scenarios: Optional[List[str]] = None,
    output_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run full cross-product benchmark matrix across controllers, scenarios, and random seeds.
    """
    seeds = seeds or DEFAULT_SEEDS
    controllers = controllers or ALL_CONTROLLERS
    scenarios = scenarios or list(SCENARIOS.keys())
    out_dir = output_dir or (root_dir / "data" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    init_db()
    total_runs = len(controllers) * len(scenarios) * len(seeds)
    print("==========================================================================")
    print(f"  GREENWAVE BENCHMARK SUITE: Starting {total_runs} Reproducible Runs")
    print(f"  Controllers: {controllers}")
    print(f"  Scenarios  : {scenarios}")
    print(f"  Seeds      : {seeds} | Duration per run: {duration}s")
    print("==========================================================================")

    records = []
    run_idx = 1
    for scen in scenarios:
        for ctrl in controllers:
            for seed in seeds:
                print(f"\n[{run_idx}/{total_runs}] Running {ctrl} on '{scen}' (seed={seed})...")
                res = run_single_experiment(
                    controller_name=ctrl,
                    scenario_name=scen,
                    seed=seed,
                    duration=duration,
                    save_to_db=True
                )
                records.append(res)
                run_idx += 1

    df_raw = pd.DataFrame(records)
    raw_csv_path = out_dir / "experiments_raw.csv"
    df_raw.to_csv(raw_csv_path, index=False)
    print(f"\n--> All raw experiment runs saved to: {raw_csv_path}")

    # Generate Statistical Analysis & Plots
    print("\n--> Generating consolidated benchmark summary and comparison plots...")
    summary_df = generate_benchmark_analysis(raw_csv_path, out_dir)
    return summary_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GREENWAVE Simulation Experiments")
    parser.add_argument("--controller", type=str, default="vac_vbot", choices=["fixed_time", "adaptive", "q_learning", "vac_vbot", "all"])
    parser.add_argument("--scenario", type=str, default="medium", choices=["low", "medium", "high", "unbalanced", "peak", "all"])
    parser.add_argument("--seed", type=int, default=42, help="Random seed for traffic generation")
    parser.add_argument("--duration", type=int, default=300, help="Simulation duration in seconds")
    parser.add_argument("--matrix", action="store_true", help="Run full cross-product benchmark matrix")

    args = parser.parse_args()

    if args.matrix:
        run_benchmark_matrix(duration=args.duration)
    else:
        ctrls = ALL_CONTROLLERS if args.controller == "all" else [args.controller]
        scens = list(SCENARIOS.keys()) if args.scenario == "all" else [args.scenario]
        for s in scens:
            for c in ctrls:
                run_single_experiment(controller_name=c, scenario_name=s, seed=args.seed, duration=args.duration)
