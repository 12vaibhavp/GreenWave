"""
Q-Learning Training Pipeline for GREENWAVE Traffic Signal Optimization.
Runs multi-episode tabular Q-learning, logs performance metrics, plots training curves,
and exports the trained Q-table.
"""
import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from reinforcement_learning.q_learning import QLearningAgent
from reinforcement_learning.environment import TrafficRLEnvironment


def train_agent(
    episodes: int = 15,
    duration: int = 600,  # 10 minutes per episode for fast convergence
    scenario: str = "medium",
    alpha: float = 0.1,
    gamma: float = 0.95,
    epsilon: float = 1.0,
    epsilon_decay: float = 0.90,
    epsilon_min: float = 0.01,
    output_qtable_path: Optional[Path] = None,
    results_dir: Optional[Path] = None
) -> Tuple[QLearningAgent, pd.DataFrame]:
    """
    Train Q-Learning Agent across multiple episodes in SUMO.
    """
    out_qtable = output_qtable_path or (root_dir / "models" / "q_table.json")
    out_results = results_dir or (root_dir / "data" / "results")
    out_results.mkdir(parents=True, exist_ok=True)

    agent = QLearningAgent(
        alpha=alpha,
        gamma=gamma,
        epsilon=epsilon,
        epsilon_decay=epsilon_decay,
        epsilon_min=epsilon_min
    )

    env = TrafficRLEnvironment(
        scenario=scenario,
        duration=duration,
        min_green=10,
        max_green=60,
        yellow_time=4
    )

    logs = []
    print(f"=== Starting GREENWAVE Q-Learning Training ({episodes} episodes, {duration}s/ep) ===")

    try:
        for ep in range(1, episodes + 1):
            ep_seed = 1000 + ep
            state = env.reset(new_seed=ep_seed)
            total_reward = 0.0
            total_queue = 0
            total_wait = 0.0
            steps = 0

            start_t = time.time()
            done = False
            while not done:
                legal = env.get_legal_actions()
                action = agent.choose_action(state, legal_actions=legal)
                next_state, reward, done, info = env.step(action)

                # Q-learning update
                legal_next = env.get_legal_actions()
                agent.update(
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                    legal_next_actions=legal_next,
                    done=done
                )

                state = next_state
                total_reward += reward
                total_queue += info["queue_length"]
                total_wait += info["waiting_time"]
                steps += 1

            # Episode summary
            avg_queue = total_queue / max(1, steps)
            avg_wait = total_wait / max(1, steps)
            elapsed = time.time() - start_t
            agent.decay_epsilon()

            log_entry = {
                "episode": ep,
                "total_reward": round(total_reward, 2),
                "avg_queue": round(avg_queue, 2),
                "avg_wait": round(avg_wait, 2),
                "throughput": info["throughput"],
                "epsilon": round(agent.epsilon, 4),
                "states_discovered": len(agent.q_table),
                "duration_sec": round(elapsed, 2)
            }
            logs.append(log_entry)

            print(
                f"Episode {ep:02d}/{episodes:02d} | "
                f"Reward: {total_reward:9.2f} | "
                f"Avg Queue: {avg_queue:5.2f} | "
                f"Avg Wait: {avg_wait:6.2f}s | "
                f"Throughput: {info['throughput']:4d} | "
                f"Epsilon: {agent.epsilon:.3f} | "
                f"States: {len(agent.q_table):3d} | "
                f"Time: {elapsed:4.1f}s"
            )

    finally:
        env.close()

    # Save Q-table
    agent.save(out_qtable)
    print(f"\n[+] Trained Q-Table saved to: {out_qtable} (Total states: {len(agent.q_table)})")

    # Save training log to CSV
    df_logs = pd.DataFrame(logs)
    csv_path = out_results / "training_log.csv"
    df_logs.to_csv(csv_path, index=False)
    print(f"[+] Training log exported to: {csv_path}")

    # Plot training curves
    plot_path = out_results / "training_curves.png"
    _plot_training_results(df_logs, plot_path)
    print(f"[+] Training curves saved to: {plot_path}")

    return agent, df_logs


def _plot_training_results(df: pd.DataFrame, plot_path: Path) -> None:
    """Generate professional 4-panel training evaluation graphs."""
    plt.figure(figsize=(12, 8))
    
    # 1. Total Reward Curve
    plt.subplot(2, 2, 1)
    plt.plot(df["episode"], df["total_reward"], marker="o", color="#2563eb", linewidth=2)
    plt.title("Episode Total Reward", fontsize=12, fontweight="bold")
    plt.xlabel("Episode")
    plt.ylabel("Cumulative Reward")
    plt.grid(True, linestyle="--", alpha=0.6)

    # 2. Average Queue Length
    plt.subplot(2, 2, 2)
    plt.plot(df["episode"], df["avg_queue"], marker="s", color="#dc2626", linewidth=2)
    plt.title("Average Queue Length (Vehicles)", fontsize=12, fontweight="bold")
    plt.xlabel("Episode")
    plt.ylabel("Vehicles")
    plt.grid(True, linestyle="--", alpha=0.6)

    # 3. Average Waiting Time
    plt.subplot(2, 2, 3)
    plt.plot(df["episode"], df["avg_wait"], marker="^", color="#d97706", linewidth=2)
    plt.title("Average Waiting Time (Seconds)", fontsize=12, fontweight="bold")
    plt.xlabel("Episode")
    plt.ylabel("Seconds")
    plt.grid(True, linestyle="--", alpha=0.6)

    # 4. Epsilon Decay & States Discovered
    plt.subplot(2, 2, 4)
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    l1 = ax1.plot(df["episode"], df["epsilon"], color="#16a34a", label="Epsilon (Exploration)", linewidth=2)
    l2 = ax2.plot(df["episode"], df["states_discovered"], color="#9333ea", linestyle="--", label="States Discovered")
    ax1.set_xlabel("Episode")
    ax1.set_ylabel("Epsilon Rate", color="#16a34a")
    ax2.set_ylabel("States Count", color="#9333ea")
    plt.title("Exploration Rate & State Exploration", fontsize=12, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=200)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train GREENWAVE Q-Learning Agent")
    parser.add_argument("--episodes", type=int, default=10, help="Number of training episodes")
    parser.add_argument("--duration", type=int, default=600, help="Duration in seconds per episode")
    parser.add_argument("--scenario", type=str, default="medium", help="Traffic demand scenario")
    args = parser.parse_args()

    train_agent(episodes=args.episodes, duration=args.duration, scenario=args.scenario)
