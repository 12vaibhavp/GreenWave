"""
Builds standard 4-Way Intersection SUMO Network and Multi-Stage Sensor Array Definitions (S1, S2, S3).
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sumo.sumo_utils import get_netconvert_binary

NETWORK_DIR = Path(__file__).resolve().parent

NODES_XML = """<nodes>
    <node id="C" x="0.0" y="0.0" type="traffic_light"/>
    <node id="N" x="0.0" y="250.0" type="priority"/>
    <node id="S" x="0.0" y="-250.0" type="priority"/>
    <node id="E" x="250.0" y="0.0" type="priority"/>
    <node id="W" x="-250.0" y="0.0" type="priority"/>
</nodes>
"""

EDGES_XML = """<edges>
    <!-- Inbound Edges (2 lanes each approach, 250m long) -->
    <edge id="N2C" from="N" to="C" priority="2" numLanes="2" speed="13.89"/>
    <edge id="S2C" from="S" to="C" priority="2" numLanes="2" speed="13.89"/>
    <edge id="E2C" from="E" to="C" priority="2" numLanes="2" speed="13.89"/>
    <edge id="W2C" from="W" to="C" priority="2" numLanes="2" speed="13.89"/>

    <!-- Outbound Edges (2 lanes each approach) -->
    <edge id="C2N" from="C" to="N" priority="2" numLanes="2" speed="13.89"/>
    <edge id="C2S" from="C" to="S" priority="2" numLanes="2" speed="13.89"/>
    <edge id="C2E" from="C" to="E" priority="2" numLanes="2" speed="13.89"/>
    <edge id="C2W" from="C" to="W" priority="2" numLanes="2" speed="13.89"/>
</edges>
"""

CONNECTIONS_XML = """<connections>
    <!-- North to South (through), West (right), East (left) -->
    <connection from="N2C" to="C2S" fromLane="0" toLane="0"/>
    <connection from="N2C" to="C2S" fromLane="1" toLane="1"/>
    <connection from="N2C" to="C2W" fromLane="0" toLane="0"/>
    <connection from="N2C" to="C2E" fromLane="1" toLane="1"/>

    <!-- South to North (through), East (right), West (left) -->
    <connection from="S2C" to="C2N" fromLane="0" toLane="0"/>
    <connection from="S2C" to="C2N" fromLane="1" toLane="1"/>
    <connection from="S2C" to="C2E" fromLane="0" toLane="0"/>
    <connection from="S2C" to="C2W" fromLane="1" toLane="1"/>

    <!-- East to West (through), North (right), South (left) -->
    <connection from="E2C" to="C2W" fromLane="0" toLane="0"/>
    <connection from="E2C" to="C2W" fromLane="1" toLane="1"/>
    <connection from="E2C" to="C2N" fromLane="0" toLane="0"/>
    <connection from="E2C" to="C2S" fromLane="1" toLane="1"/>

    <!-- West to East (through), South (right), North (left) -->
    <connection from="W2C" to="C2E" fromLane="0" toLane="0"/>
    <connection from="W2C" to="C2E" fromLane="1" toLane="1"/>
    <connection from="W2C" to="C2S" fromLane="0" toLane="0"/>
    <connection from="W2C" to="C2N" fromLane="1" toLane="1"/>
</connections>
"""


def generate_additional_detectors(output_det_path: Optional[Path] = None) -> Path:
    """
    Generate SUMO E1 Induction Loop & Radar sensor definition file (.det.xml)
    Positions (edge length = ~250m, junction stopline is at ~240m from entry):
    - S1 (Stopline Loop): 15m from stopline (pos = 225m)
    - S2 (Dilemma Zone Sensor): 50m from stopline (pos = 190m)
    - S3 (Upstream Radar): 100m from stopline (pos = 140m)
    """
    det_file = output_det_path or (NETWORK_DIR / "intersection.det.xml")
    
    approaches = [
        ("N", "N2C", "SC"),
        ("S", "S2C", "S"),
        ("E", "E2C", "SA"),
        ("W", "W2C", "SB")
    ]

    xml_lines = [
        '<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">',
        '    <!-- ==================================================== -->',
        '    <!-- MULTI-STAGE TRAFFIC SENSOR ARRAYS (S1, S2, S3)       -->',
        '    <!-- ==================================================== -->'
    ]

    for prefix, edge_id, code in approaches:
        for lane in [0, 1]:
            # S1: Stopline Inductive Loop (15m from stopline, pos=225m)
            xml_lines.append(
                f'    <inductionLoop id="det_{prefix}_s1_l{lane}" lane="{edge_id}_{lane}" pos="225.0" freq="1.0" file="NUL"/>'
            )
            # S2: Dilemma Zone Sensor (50m from stopline, pos=190m)
            xml_lines.append(
                f'    <inductionLoop id="det_{prefix}_s2_l{lane}" lane="{edge_id}_{lane}" pos="190.0" freq="1.0" file="NUL"/>'
            )
            # S3: Upstream mmWave Radar (100m from stopline, pos=140m)
            xml_lines.append(
                f'    <inductionLoop id="det_{prefix}_s3_l{lane}" lane="{edge_id}_{lane}" pos="140.0" freq="1.0" file="NUL"/>'
            )

    xml_lines.append('</additional>')
    det_file.write_text('\n'.join(xml_lines))
    return det_file


def generate_network(output_net_path: Optional[Path] = None) -> Path:
    """Write node, edge, and connection XMLs and compile to .net.xml via netconvert."""
    output_net = output_net_path or (NETWORK_DIR / "intersection.net.xml")
    
    nod_file = NETWORK_DIR / "intersection.nod.xml"
    edg_file = NETWORK_DIR / "intersection.edg.xml"
    con_file = NETWORK_DIR / "intersection.con.xml"

    nod_file.write_text(NODES_XML)
    edg_file.write_text(EDGES_XML)
    con_file.write_text(CONNECTIONS_XML)

    # Also build sensor array detectors
    generate_additional_detectors()

    netconvert_bin = get_netconvert_binary()
    cmd = [
        netconvert_bin,
        "--node-files", str(nod_file),
        "--edge-files", str(edg_file),
        "--connection-files", str(con_file),
        "--output-file", str(output_net),
        "--no-turnarounds", "true"
    ]
    
    env = dict(os.environ)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"netconvert failed: {result.stderr}")

    return output_net


if __name__ == "__main__":
    net = generate_network()
    det = generate_additional_detectors()
    print(f"SUMO network generated at: {net}")
    print(f"Sensor array detectors generated at: {det}")
