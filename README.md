# 🚦 GREENWAVE: Real-Time Intelligent Traffic Signal Control Using YOLO and Reinforcement Learning

> **A Complete University Major Project & Research Prototype**  
> Unifying Deep Learning (YOLOv8 Computer Vision), Trajectory-Based Vehicle Tracking, Mathematical Density & Queue Estimation, Microscopic Traffic Simulation (SUMO & TraCI), Tabular Q-Learning Reinforcement Learning, and a Real-Time Web Dashboard (FastAPI + WebSockets + Chart.js).

---

## 📌 1. Project Overview

Traffic congestion in urban intersections leads to massive fuel wastage, air pollution, and economic losses. Traditional **Fixed-Time Controllers** rely on static, historical timing plans that fail to respond to dynamic, unbalanced traffic surges.

**GREENWAVE** is an end-to-end intelligent traffic management system that:
1. Receives video camera feeds and performs real-time vehicle detection using **YOLOv8**.
2. Tracks vehicles with persistent IDs across frames to eliminate double-counting.
3. Computes continuous, normalized mathematical traffic density and estimates queue lengths.
4. Formulates signal control as a Markov Decision Process (MDP) and optimizes signal actions via **Tabular Q-Learning**.
5. Simulates ground-truth traffic environments in **SUMO** via **TraCI**.
6. Fairly compares **Fixed-Time**, **Adaptive-Actuated**, and **Q-Learning** controllers across 5 traffic demand regimes over multiple random seeds.
7. Displays real-time signal states, queue meters, and time-series telemetry on an interactive **Web Dashboard**.

---

## 🏛️ 2. System Architecture

```
+------------------+       +-------------------------+       +----------------------------+
|  CAMERA / VIDEO  | ----> |  YOLOv8 VEHICLE DETECT  | ----> | MULTI-OBJECT TRACKING (ID) |
+------------------+       +-------------------------+       +----------------------------+
                                                                            |
                                                                            v
+------------------+       +-------------------------+       +----------------------------+
| DISCRETE STATE S | <---- |   QUEUE ESTIMATION      | <---- | ROI / LANE DENSITY MATH    |
+------------------+       +-------------------------+       +----------------------------+
         |
         v
+------------------+       +-------------------------+       +----------------------------+
| Q-LEARNING AGENT | ----> | SAFE ACTION SELECTION   | ----> | SUMO + TraCI SIMULATION    |
+------------------+       +-------------------------+       +----------------------------+
                                                                            |
                                                                            v
+------------------+       +-------------------------+       +----------------------------+
|  WEB DASHBOARD   | <---- | FASTAPI + WEBSOCKETS    | <---- | SQLITE DB / METRICS LOG    |
+------------------+       +-------------------------+       +----------------------------+
```

---

## 💻 3. Technology Stack

* **Deep Learning & Computer Vision**: YOLOv8 (Ultralytics), PyTorch (with Apple Silicon MPS & CUDA acceleration), OpenCV, NumPy.
* **Traffic Simulation**: Eclipse SUMO 1.27.1, TraCI, Sumolib, Netconvert.
* **Reinforcement Learning**: Custom Tabular Q-Learning engine from scratch with Bellman optimality updates, $\epsilon$-greedy exploration, and decay.
* **Backend & API**: Python 3.10+, FastAPI, Uvicorn, Pydantic, WebSockets, SQLite.
* **Frontend & Data Visualization**: HTML5, CSS3, JavaScript (ES6+), Chart.js, Pandas, Matplotlib.
* **Testing & Reproducibility**: Pytest (38 passing automated tests).

---

## 📂 4. Project Structure

```
GreenWave/
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI Application Entrypoint
│       ├── api/                     # REST & WebSocket Endpoints
│       ├── services/                # Background Simulation & Vision Services
│       ├── models/                  # Pydantic Schemas & SQLite Database
│       └── config/                  # Settings & Environment Parser
├── vision/
│   ├── detector.py                 # YOLOv8 Vehicle Detection Engine
│   ├── tracker.py                  # Multi-Object Tracker (Prevents Double Counting)
│   ├── counter.py                  # Lane & Polygonal ROI Vehicle Counter
│   ├── traffic_density.py          # Mathematical Density & Queue Estimator
│   ├── vision_rl_bridge.py         # Adapter bridging Vision State to RL State
│   └── config.py                   # Vision Hyperparameters
├── reinforcement_learning/
│   ├── q_learning.py               # Pure Python Tabular Q-Learning Agent
│   ├── state.py                    # 128-State Discretization
│   ├── actions.py                  # Discrete Action Space & Safety Bounds
│   ├── reward.py                   # Multi-Objective Reward Function
│   ├── environment.py              # Gym-like TraCI RL Environment Wrapper
│   └── train.py                    # Multi-Episode Training Pipeline
├── sumo/
│   ├── network/                    # 4-Way Intersection XML & Builder
│   ├── routes/                     # Deterministic Multi-Scenario Route Generator
│   ├── controllers/                # Fixed-Time, Adaptive, and Q-Learning Controllers
│   ├── simulation.py               # TraCI Lifecycle Manager & Telemetry Collector
│   └── sumo_utils.py               # SUMO Binary & SUMO_HOME Path Resolver
├── dashboard/                      # Interactive Web Dashboard (HTML/CSS/JS)
├── data/results/                   # Empirical CSV Datasets, Plots, and SQLite DB
├── models/                         # Pretrained YOLO Weights & Trained Q-Table
├── experiments/                    # Automated Benchmark & Scenario Runners
├── tests/                          # 38 Automated Unit & Integration Tests
├── docs/                           # Comprehensive Academic Documentation
├── requirements.txt                # Pinned Dependencies
├── .env.example                    # Configuration Template
├── main.py                         # Root Unified CLI
└── README.md
```

---

## ⚡ 5. Quickstart & Installation

### Step 1: Clone and Navigate
```bash
cd /Users/vaibhavprakash/.gemini/antigravity/scratch/GreenWave
```

### Step 2: Set Up Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Run Automated Test Suite
```bash
pytest -v tests/
```
*(All 38 tests should pass in under 15 seconds).*

---

## 🚀 6. Running the System

### 1. Start Web Dashboard & Backend Server
```bash
python main.py server --port 8000
```
Open **`http://localhost:8000`** in your browser to view the interactive dashboard.  
Visit **`http://localhost:8000/docs`** for interactive Swagger API specs.

### 2. Train the Q-Learning Agent
```bash
python main.py train --episodes 15 --duration 600 --scenario medium
```
*Trained policy is saved to `models/q_table.json` and training curves to `data/results/training_curves.png`.*

### 3. Run Benchmark Experiments (Fair Comparison)
```bash
python main.py experiment --matrix --duration 300
```
*Runs all 3 controllers across all 5 traffic scenarios over 3 random seeds (45 total runs) and updates summary tables and plots.*

### 4. Run Standalone SUMO Simulation
```bash
python main.py simulate --controller adaptive --scenario peak --duration 300
```

---

## 📊 7. Empirical Experimental Results

All numbers below were measured during 45 real SUMO TraCI simulation runs across 3 random seeds (`42`, `101`, `2024`):

| Traffic Scenario | Controller | Avg Wait Time (s) | Wait Reduction % | Avg Queue (veh) | Queue Reduction % | Throughput (veh) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Low (400 vph)** | Fixed-Time | 7.04 &plusmn; 2.22 | Baseline | 0.72 &plusmn; 0.11 | Baseline | 22.7 |
| | **Adaptive-Actuated** | **0.49 &plusmn; 0.08** | **-92.99%** | **0.16 &plusmn; 0.01** | **-77.88%** | 22.7 |
| | Q-Learning | 11.05 &plusmn; 3.44 | +57.01% | 0.87 &plusmn; 0.11 | +20.74% | 22.3 |
| **Medium (900 vph)** | Fixed-Time | 15.53 &plusmn; 3.57 | Baseline | 1.59 &plusmn; 0.40 | Baseline | 62.7 |
| | **Adaptive-Actuated** | **1.92 &plusmn; 0.06** | **-87.64%** | **0.48 &plusmn; 0.01** | **-69.81%** | **64.0** |
| | Q-Learning | 56.01 &plusmn; 22.16 | +260.68% | 3.14 &plusmn; 0.79 | +97.27% | 58.7 |
| **High (1600 vph)** | Fixed-Time | 31.98 &plusmn; 2.49 | Baseline | 3.10 &plusmn; 0.12 | Baseline | 101.0 |
| | **Adaptive-Actuated** | **4.89 &plusmn; 1.89** | **-84.70%** | **1.07 &plusmn; 0.28** | **-65.59%** | **104.3** |
| | Q-Learning | 115.09 &plusmn; 15.38 | +259.91% | 5.81 &plusmn; 0.64 | +87.42% | 99.0 |
| **Unbalanced (80/20)**| Fixed-Time | 16.76 &plusmn; 6.11 | Baseline | 1.81 &plusmn; 0.46 | Baseline | 79.0 |
| | **Adaptive-Actuated** | **8.23 &plusmn; 4.75** | **-50.89%** | **1.20 &plusmn; 0.46** | **-33.70%** | **80.7** |
| | Q-Learning | 67.38 &plusmn; 32.27 | +302.13% | 4.54 &plusmn; 1.76 | +150.83% | 73.3 |
| **Peak Surge (1800 vph)**| Fixed-Time | 62.94 &plusmn; 3.82 | Baseline | 5.65 &plusmn; 0.24 | Baseline | 127.0 |
| | **Adaptive-Actuated** | **15.87 &plusmn; 2.51** | **-74.78%** | **2.94 &plusmn; 0.45** | **-47.96%** | **133.0** |
| | Q-Learning | 170.85 &plusmn; 33.74 | +171.47% | 8.68 &plusmn; 1.50 | +53.63% | 125.7 |

---

## 🎓 8. Academic Viva / Defense Q&A

**Q1: Why use YOLO for vehicle detection instead of traditional background subtraction?**  
*Answer:* Background subtraction suffers from illumination changes, moving shadows, weather shifts, and camera jitter. YOLOv8 is a state-of-the-art CNN/Anchor-free detector capable of classifying vehicle types (`car`, `bus`, `truck`, `motorcycle`) in real time with high mAP.

**Q2: How does GREENWAVE prevent counting the same vehicle in consecutive frames?**  
*Answer:* We implemented multi-object tracking (`tracker.py`) using two-stage IoU and Euclidean centroid distance association. Vehicles are assigned persistent unique `TrackID`s; total counts are computed by tracking cardinality ($|\{ \text{TrackID} \}|$), ensuring a car visible across 30 frames is counted strictly once.

**Q3: Why use Tabular Q-Learning instead of Deep Q-Networks (DQN) for the baseline?**  
*Answer:* Tabular Q-learning is mathematically exact, fully explainable, converges deterministically without hyperparameter instability, and runs with sub-millisecond latency suitable for embedded traffic controllers.

**Q4: How are safety constraints enforced during reinforcement learning control?**  
*Answer:* An action masking and state transition wrapper prevents the RL agent from directly setting raw signal states. The agent can only issue high-level phase hold/switch decisions, which are constrained by minimum green duration ($10$s), maximum green duration ($60$s), and mandatory yellow change clearance intervals ($4$s).

**Q5: Why did the Adaptive controller outperform 12-episode Q-Learning in waiting times?**  
*Answer:* The Adaptive controller utilizes a deterministic greedy queue-disparity and gap-out rule that immediately clears backlogs. Tabular Q-learning trained for only 12 episodes explored a subset of the 128-state space ($\approx 26$ states); RL theory dictates that complete tabular convergence requires hundreds of episodes or deep function approximation (DQN).

---

## 🔮 9. Future Scope & Extensions

1. **Deep Q-Networks (DQN & PPO)**: Scaling state space to multi-intersection arterial corridors (Green Wave synchronization).
2. **Pedestrian & Emergency Preemption**: Integrating YOLO pedestrian detection and emergency vehicle priority lanes.
3. **Hardware Deployment**: Porting the vision-to-RL pipeline to NVIDIA Jetson edge devices via TensorRT.

---

## 📜 10. License & Academic Attribution
Developed as a production-grade University Major Project. All rights reserved.
