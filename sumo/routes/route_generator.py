"""
Deterministic Route and Vehicle Flow Generator for SUMO Simulation.
Generates reproducible vehicle flows for different traffic scenarios and random seeds.
"""
import os
import sys
import random
import math
from pathlib import Path
from typing import Dict, List, Optional

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

ROUTES_DIR = Path(__file__).resolve().parent

# Scenario rate specifications (average vehicles per hour across all approaches)
SCENARIO_HOURLY_RATES = {
    "low": {"total_vph": 400, "ns_ratio": 0.50, "ew_ratio": 0.50},
    "medium": {"total_vph": 900, "ns_ratio": 0.50, "ew_ratio": 0.50},
    "high": {"total_vph": 1600, "ns_ratio": 0.50, "ew_ratio": 0.50},
    "unbalanced": {"total_vph": 1200, "ns_ratio": 0.80, "ew_ratio": 0.20},
    "peak": {"total_vph": 1800, "ns_ratio": 0.60, "ew_ratio": 0.40, "is_surge": True}
}

VALID_ROUTES = [
    ("r_N_S", "N2C C2S"),
    ("r_N_E", "N2C C2E"),
    ("r_N_W", "N2C C2W"),
    ("r_S_N", "S2C C2N"),
    ("r_S_E", "S2C C2E"),
    ("r_S_W", "S2C C2W"),
    ("r_E_W", "E2C C2W"),
    ("r_E_N", "E2C C2N"),
    ("r_E_S", "E2C C2S"),
    ("r_W_E", "W2C C2E"),
    ("r_W_N", "W2C C2N"),
    ("r_W_S", "W2C C2S"),
]

ROUTE_CATEGORIES = {
    "NS": ["r_N_S", "r_N_E", "r_N_W", "r_S_N", "r_S_E", "r_S_W"],
    "EW": ["r_E_W", "r_E_N", "r_E_S", "r_W_E", "r_W_N", "r_W_S"]
}


def generate_routes(
    scenario: str = "medium",
    seed: int = 42,
    duration: int = 3600,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a deterministic .rou.xml file for the given scenario and seed.
    """
    if scenario not in SCENARIO_HOURLY_RATES:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from {list(SCENARIO_HOURLY_RATES.keys())}")

    rng = random.Random(seed)
    spec = SCENARIO_HOURLY_RATES[scenario]
    output_file = output_path or (ROUTES_DIR / f"routes_{scenario}_seed{seed}.rou.xml")

    # Vehicle types distribution
    # (type_id, length, maxSpeed, accel, decel, vClass, prob_weight)
    vtypes = [
        ("car", 4.5, 13.89, 2.6, 4.5, "passenger", 0.70),
        ("motorcycle", 2.2, 14.50, 3.0, 5.0, "motorcycle", 0.15),
        ("bus", 12.0, 10.50, 1.2, 3.5, "bus", 0.08),
        ("truck", 9.0, 10.00, 1.5, 3.5, "truck", 0.07)
    ]
    type_ids = [t[0] for t in vtypes]
    type_weights = [t[6] for t in vtypes]

    xml_lines = [
        '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
        '    <!-- Vehicle Type Definitions -->'
    ]

    for tid, length, maxSpd, acc, dec, vcls, _ in vtypes:
        xml_lines.append(
            f'    <vType id="{tid}" vClass="{vcls}" length="{length}" maxSpeed="{maxSpd}" '
            f'accel="{acc}" decel="{dec}" sigma="0.5" carFollowModel="IDM"/>'
        )

    xml_lines.append('\n    <!-- Route Definitions -->')
    for r_id, edges in VALID_ROUTES:
        xml_lines.append(f'    <route id="{r_id}" edges="{edges}"/>')

    xml_lines.append('\n    <!-- Vehicle Departures -->')

    total_vph = spec["total_vph"]
    ns_ratio = spec["ns_ratio"]
    ew_ratio = spec["ew_ratio"]
    is_surge = spec.get("is_surge", False)

    # Generate vehicles second by second using Poisson/Bernoulli arrival probability
    veh_count = 0
    for t in range(duration):
        # Peak surge modulation: multiplier up to 1.8x at middle of simulation
        multiplier = 1.0
        if is_surge:
            # Gaussian / sine wave bell curve centered at duration / 2
            mid = duration / 2.0
            sigma = duration / 6.0
            multiplier = 0.5 + 1.2 * math.exp(-0.5 * ((t - mid) / sigma) ** 2)

        # Arrival rate lambda (vehicles per second)
        lambda_ns = (total_vph * ns_ratio * multiplier) / 3600.0
        lambda_ew = (total_vph * ew_ratio * multiplier) / 3600.0

        # NS Approach Departure check
        if rng.random() < lambda_ns:
            veh_count += 1
            v_type = rng.choices(type_ids, weights=type_weights, k=1)[0]
            route = rng.choice(ROUTE_CATEGORIES["NS"])
            xml_lines.append(
                f'    <vehicle id="veh_{veh_count}" type="{v_type}" route="{route}" depart="{t:.1f}" departLane="best" departSpeed="max"/>'
            )

        # EW Approach Departure check
        if rng.random() < lambda_ew:
            veh_count += 1
            v_type = rng.choices(type_ids, weights=type_weights, k=1)[0]
            route = rng.choice(ROUTE_CATEGORIES["EW"])
            xml_lines.append(
                f'    <vehicle id="veh_{veh_count}" type="{v_type}" route="{route}" depart="{t:.1f}" departLane="best" departSpeed="max"/>'
            )

    xml_lines.append('</routes>')
    output_file.write_text('\n'.join(xml_lines))
    return output_file


if __name__ == "__main__":
    for sc in SCENARIO_HOURLY_RATES:
        f = generate_routes(scenario=sc, seed=42, duration=3600)
        print(f"Generated {sc} route file: {f}")
