"""
GREENWAVE: Intelligent Traffic Signal Control Using Multi-Sensor Arrays and Reinforcement Learning.
Root Unified Application CLI.
"""
import sys
import argparse
from pathlib import Path
import uvicorn

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config.settings import settings
from reinforcement_learning.train import train_agent
from experiments.run_experiment import run_single_experiment, run_benchmark_matrix
from sumo.simulation import SumoSimulation
from sumo.controllers.adaptive import AdaptiveController
from sumo.controllers.fixed_time import FixedTimeController
from sumo.controllers.q_learning_controller import QLearningController
from sumo.controllers.vac_vbot import VacVBotController


def cmd_server(args):
    """Start FastAPI Server and Web Dashboard."""
    print(f"============================================================")
    print(f"  Starting GREENWAVE Server on http://{args.host}:{args.port}")
    print(f"  Dashboard: http://localhost:{args.port}")
    print(f"  API Specs: http://localhost:{args.port}/docs")
    print(f"============================================================")
    uvicorn.run("backend.app.main:app", host=args.host, port=args.port, reload=args.reload)


def cmd_train(args):
    """Train Q-Learning Agent."""
    train_agent(
        episodes=args.episodes,
        duration=args.duration,
        scenario=args.scenario
    )


def cmd_experiment(args):
    """Run evaluation benchmarks."""
    if args.matrix:
        run_benchmark_matrix(duration=args.duration)
    else:
        run_single_experiment(
            controller_name=args.controller,
            scenario_name=args.scenario,
            seed=args.seed,
            duration=args.duration
        )


def cmd_vbot(args):
    """Run VAC V-BOT Multi-Sensor Simulation with Dilemma Zone Protection."""
    print("==========================================================================")
    print("  🚦 GREENWAVE VAC V-BOT: Vehicle Actuated Autonomous Control Simulation")
    print(f"  Scenario: {args.scenario.upper()} | Duration: {args.duration}s | GUI: {args.gui}")
    print("  Sensors: S1 (Stopline Loop 15m), S2 (Dilemma 50m), S3 (Doppler Radar 100m)")
    print("==========================================================================")

    vbot = VacVBotController(min_green=10, max_green=60, yellow_time=4)
    sim = SumoSimulation(scenario=args.scenario, seed=args.seed, duration=args.duration, gui=args.gui)

    try:
        sim.start()
        print("\nStep | Phase | Queue | Waiting (s) | Fuel (ml) | CO2 (g) | Dilemma Zone Holds")
        print("-" * 75)
        for step in range(args.duration):
            m = sim.step()
            target_phase = vbot.decide_action(m)
            sim.request_phase_switch(target_phase)

            if step % 25 == 0 or vbot.dilemma_protection_active:
                dilemma_tag = "⚠️ [DZP HOLD ACTIVATED]" if vbot.dilemma_protection_active else f"Holds: {vbot.dilemma_holds_triggered}"
                phase_name = "NS-GREEN" if m.current_phase == 0 else "EW-GREEN" if m.current_phase == 2 else "YELLOW"
                print(
                    f"{step:04d} | {phase_name:8s} | {m.total_queue_length:2d} veh | "
                    f"{m.total_waiting_time:6.1f}s | {m.cumulative_fuel_ml:7.1f}ml | "
                    f"{m.cumulative_co2_g:6.1f}g | {dilemma_tag}"
                )
    finally:
        sim.close()
    print("\n--> VAC V-BOT Simulation Finished Successfully.")


def cmd_simulate(args):
    """Run standalone SUMO simulation from CLI."""
    print(f"--> Running SUMO Simulation [Controller: {args.controller}, Scenario: {args.scenario}, Duration: {args.duration}s]...")
    if args.controller == "fixed_time":
        ctrl = FixedTimeController(ns_green_duration=30, ew_green_duration=30)
    elif args.controller == "adaptive":
        ctrl = AdaptiveController(min_green=10, max_green=60)
    elif args.controller == "q_learning":
        ctrl = QLearningController()
    elif args.controller == "vac_vbot":
        ctrl = VacVBotController()
    else:
        raise ValueError(f"Unknown controller: {args.controller}")

    sim = SumoSimulation(scenario=args.scenario, seed=args.seed, duration=args.duration, gui=args.gui)
    try:
        sim.start()
        for step in range(args.duration):
            m = sim.step()
            target_phase = ctrl.decide_action(m)
            sim.request_phase_switch(target_phase)
            if step % 50 == 0:
                print(f"Step {step:04d}/{args.duration} | Phase: {m.current_phase} | Total Queue: {m.total_queue_length:2d} | Waiting: {m.total_waiting_time:5.1f}s | Throughput: {m.throughput:3d}")
    finally:
        sim.close()
    print("--> Simulation complete.")


def main():
    parser = argparse.ArgumentParser(
        description="GREENWAVE: Intelligent Traffic Signal Control Using Multi-Sensor Arrays & Reinforcement Learning"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 1. Server / Dashboard command
    server_p = subparsers.add_parser("server", aliases=["dashboard"], help="Start FastAPI Backend and Web Dashboard")
    server_p.add_argument("--host", type=str, default=settings.HOST, help="Host address")
    server_p.add_argument("--port", type=int, default=settings.PORT, help="Port number")
    server_p.add_argument("--reload", action="store_true", help="Enable hot reload")

    # 2. V-BOT command (Mid-Semester Presentation Simulation)
    vbot_p = subparsers.add_parser("vbot", help="Run VAC V-BOT Simulation with Dilemma Zone Protection & Sensors")
    vbot_p.add_argument("--scenario", type=str, default="medium", choices=["low", "medium", "high", "unbalanced", "peak"])
    vbot_p.add_argument("--seed", type=int, default=42, help="Random seed")
    vbot_p.add_argument("--duration", type=int, default=300, help="Seconds to simulate")
    vbot_p.add_argument("--gui", action="store_true", help="Open SUMO Graphical Desktop Window")

    # 3. Train command
    train_p = subparsers.add_parser("train", help="Train Q-Learning Agent")
    train_p.add_argument("--episodes", type=int, default=12, help="Number of training episodes")
    train_p.add_argument("--duration", type=int, default=600, help="Seconds per episode")
    train_p.add_argument("--scenario", type=str, default="medium", help="Traffic demand scenario")

    # 4. Experiment command
    exp_p = subparsers.add_parser("experiment", help="Run simulation experiments")
    exp_p.add_argument("--controller", type=str, default="vac_vbot", choices=["fixed_time", "adaptive", "q_learning", "vac_vbot", "all"])
    exp_p.add_argument("--scenario", type=str, default="medium", choices=["low", "medium", "high", "unbalanced", "peak", "all"])
    exp_p.add_argument("--seed", type=int, default=42, help="Random seed")
    exp_p.add_argument("--duration", type=int, default=300, help="Duration in seconds")
    exp_p.add_argument("--matrix", action="store_true", help="Run full cross-product comparison matrix")

    # 5. Simulate command
    sim_p = subparsers.add_parser("simulate", help="Run standalone SUMO simulation")
    sim_p.add_argument("--controller", type=str, default="vac_vbot", choices=["fixed_time", "adaptive", "q_learning", "vac_vbot"])
    sim_p.add_argument("--scenario", type=str, default="medium")
    sim_p.add_argument("--seed", type=int, default=42)
    sim_p.add_argument("--duration", type=int, default=300)
    sim_p.add_argument("--gui", action="store_true", help="Enable SUMO GUI")

    args = parser.parse_args()

    if args.command in ("server", "dashboard"):
        cmd_server(args)
    elif args.command == "vbot":
        cmd_vbot(args)
    elif args.command == "train":
        cmd_train(args)
    elif args.command == "experiment":
        cmd_experiment(args)
    elif args.command == "simulate":
        cmd_simulate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
