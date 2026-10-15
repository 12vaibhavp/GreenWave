"""
Statistical Analysis and Visualization Engine for GREENWAVE Experiments.
Computes Mean, Standard Deviation, and Improvement % across controllers and scenarios.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CONTROLLER_DISPLAY = {
    "fixed_time": "Fixed-Time",
    "adaptive": "Adaptive-Actuated",
    "q_learning": "Q-Learning (Ours)"
}

CONTROLLER_COLORS = {
    "fixed_time": "#94a3b8",      # Slate gray
    "adaptive": "#f59e0b",        # Amber orange
    "q_learning": "#10b981"       # Emerald green
}


def generate_benchmark_analysis(
    df_raw: pd.DataFrame,
    output_dir: Path
) -> pd.DataFrame:
    """
    Compute grouped statistics (mean +/- std) and relative improvement % vs Fixed-Time baseline.
    Exports summary CSV and visualization charts.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if df_raw.empty:
        print("[!] No experiment data to analyze.")
        return pd.DataFrame()

    # Group by Scenario and Controller
    grouped = df_raw.groupby(["scenario", "controller"]).agg(
        avg_wait_mean=("avg_waiting_time", "mean"),
        avg_wait_std=("avg_waiting_time", "std"),
        avg_queue_mean=("avg_queue_length", "mean"),
        avg_queue_std=("avg_queue_length", "std"),
        throughput_mean=("throughput", "mean"),
        throughput_std=("throughput", "std"),
        travel_time_mean=("avg_travel_time", "mean"),
        travel_time_std=("avg_travel_time", "std"),
        sample_runs=("seed", "count")
    ).reset_index()

    # Fill NaN stds (if only 1 run per scenario/controller) with 0.0
    grouped = grouped.fillna(0.0)

    # Compute percentage improvements relative to Fixed-Time
    summary_rows = []
    scenarios = df_raw["scenario"].unique()

    for scen in scenarios:
        scen_group = grouped[grouped["scenario"] == scen]
        fixed_row = scen_group[scen_group["controller"] == "fixed_time"]

        base_wait = fixed_row["avg_wait_mean"].values[0] if not fixed_row.empty else 1.0
        base_queue = fixed_row["avg_queue_mean"].values[0] if not fixed_row.empty else 1.0

        for _, row in scen_group.iterrows():
            ctrl = row["controller"]
            wait_m = row["avg_wait_mean"]
            queue_m = row["avg_queue_mean"]

            # Improvement = (Fixed - Target) / Fixed * 100
            wait_imp = ((base_wait - wait_m) / max(0.01, base_wait)) * 100.0 if base_wait > 0 else 0.0
            queue_imp = ((base_queue - queue_m) / max(0.01, base_queue)) * 100.0 if base_queue > 0 else 0.0

            summary_rows.append({
                "scenario": scen,
                "controller": ctrl,
                "controller_label": CONTROLLER_DISPLAY.get(ctrl, ctrl),
                "avg_waiting_time_s": round(wait_m, 2),
                "waiting_time_std": round(row["avg_wait_std"], 2),
                "waiting_time_reduction_pct": round(wait_imp, 2),
                "avg_queue_length_veh": round(queue_m, 2),
                "queue_length_std": round(row["avg_queue_std"], 2),
                "queue_reduction_pct": round(queue_imp, 2),
                "throughput_veh": round(row["throughput_mean"], 1),
                "travel_time_s": round(row["travel_time_mean"], 2),
                "runs": int(row["sample_runs"])
            })

    df_summary = pd.DataFrame(summary_rows)
    summary_csv = output_dir / "benchmark_summary.csv"
    df_summary.to_csv(summary_csv, index=False)
    print(f"[+] Benchmark summary CSV saved to: {summary_csv}")

    # Generate Graphs
    _plot_metric_bars(
        df_summary=df_summary,
        metric_col="avg_waiting_time_s",
        std_col="waiting_time_std",
        title="Average Waiting Time Comparison Across Scenarios",
        ylabel="Average Waiting Time (seconds)",
        output_file=output_dir / "comparison_waiting_time.png"
    )

    _plot_metric_bars(
        df_summary=df_summary,
        metric_col="avg_queue_length_veh",
        std_col="queue_length_std",
        title="Average Queue Length Comparison Across Scenarios",
        ylabel="Average Queue Length (vehicles)",
        output_file=output_dir / "comparison_queue_length.png"
    )

    _plot_metric_bars(
        df_summary=df_summary,
        metric_col="throughput_veh",
        std_col=None,
        title="Vehicle Throughput Comparison Across Scenarios",
        ylabel="Throughput (vehicles arrived)",
        output_file=output_dir / "comparison_throughput.png"
    )

    return df_summary


def _plot_metric_bars(
    df_summary: pd.DataFrame,
    metric_col: str,
    std_col: Optional[str],
    title: str,
    ylabel: str,
    output_file: Path
) -> None:
    """Plot grouped bar chart with optional error bars."""
    scenarios = list(df_summary["scenario"].unique())
    controllers = ["fixed_time", "adaptive", "q_learning"]

    x = np.arange(len(scenarios))
    width = 0.25

    plt.figure(figsize=(10, 6))
    ax = plt.gca()

    for idx, ctrl in enumerate(controllers):
        ctrl_data = df_summary[df_summary["controller"] == ctrl]
        vals = []
        errs = []

        for scen in scenarios:
            row = ctrl_data[ctrl_data["scenario"] == scen]
            if not row.empty:
                vals.append(row[metric_col].values[0])
                errs.append(row[std_col].values[0] if std_col else 0.0)
            else:
                vals.append(0.0)
                errs.append(0.0)

        offset = (idx - 1) * width
        yerr = errs if std_col and any(e > 0 for e in errs) else None
        bars = ax.bar(
            x + offset,
            vals,
            width,
            yerr=yerr,
            capsize=4,
            label=CONTROLLER_DISPLAY.get(ctrl, ctrl),
            color=CONTROLLER_COLORS.get(ctrl, "#666666"),
            edgecolor="#1e293b",
            linewidth=1.2,
            alpha=0.9
        )

        # Value labels on top of bars
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.annotate(
                    f"{h:.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold"
                )

    ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xlabel("Traffic Scenario", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([s.capitalize() for s in scenarios], fontsize=10, fontweight="bold")
    ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="#cbd5e1", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()
