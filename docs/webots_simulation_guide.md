# 🤖 Cyberbotics Webots: 3D Robotics Simulation Guide for GREENWAVE

This guide walks you step-by-step through running the **3D Robotics Simulation of GREENWAVE VAC V-BOT in Cyberbotics Webots**.

---

## 🏛️ 1. Architecture in Webots

```
                                  [ 3D WEBOTS WORLD ]
                                           │
          ┌────────────────────────────────┼────────────────────────────────┐
          ▼                                ▼                                ▼
  [S1: Stopline Loop]            [S2: Dilemma Zone Sensor]          [S3: Doppler Radar]
   DistanceSensor (15m)            DistanceSensor (50m)                Radar Device (100m)
          │                                │                                │
          └────────────────────────────────┼────────────────────────────────┘
                                           │ Real-time Telemetry
                                           ▼
                       [ VAC V-BOT SUPERVISOR CONTROLLER ]
                             (traffic_light_supervisor.py)
                                           │
                                           ▼
                       [ 3D TRAFFIC LIGHT ACTUATION (LEDs) ]
                            (Red, Yellow, Green Bulbs)
```

---

## 💻 2. Step 1: Install Cyberbotics Webots on Your Computer

Webots is 100% free and open-source.

### On macOS:
1. Download Webots from the official release page:
   👉 **[https://cyberbotics.com/#download](https://cyberbotics.com/#download)**
   *(Or via Homebrew: `brew install --cask webots`)*
2. Drag `Webots.app` into your **Applications** folder.

### On Windows / Linux:
* Download and run the installer from [https://cyberbotics.com](https://cyberbotics.com).

---

## 🚀 3. Step 2: Open the 3D Simulation in Webots

1. Launch **Cyberbotics Webots**.
2. Click **File ➔ Open World...** (or press `Ctrl + O` / `Cmd + O`).
3. Navigate to your project directory and select:
   📁 **`/Users/vaibhavprakash/.gemini/antigravity/scratch/GreenWave/webots/worlds/intersection_vbot.wbt`**
4. The 3D 4-way intersection will load with the traffic lights, roads, cars, and sensor arrays!

---

## 🎮 4. Step 3: Running and Interacting with the 3D Simulation

1. Click the **Play (▶)** button on the top Webots toolbar (or press `Spacebar`).
2. **Watch the 3D Lights Switch**:
   * The **Traffic Light LEDs** will illuminate in physical 3D (Green for active traffic, Yellow clearance, and Red for stopped traffic).
3. **Observe Dilemma Zone Protection**:
   * When a 3D vehicle approaches the intersection at high speed in the 50m zone, check the Webots bottom console:
     ```
     [Webots t=14.2s] Phase: NS-GREEN | DZP Holds: 1 (Dilemma Extension Triggered)
     ```
4. **Interactive Testing with Mouse**:
   * You can use your mouse in Webots to **drag and drop 3D cars** onto the South or East lanes and watch the **VAC V-BOT** immediately detect them with $S_1 / S_2 / S_3$ and switch the green light to clear them!

---

## 🎓 5. How to Demonstrate This to Your Teachers and Mentors

During your presentation, show **both** the microscopic simulation and the 3D robotics simulation:

1. **Step 1 (SUMO Microscopic Simulation)**:
   * Run: `python main.py vbot --scenario medium --gui`
   * Explain the large-scale network metrics (Throughput, Waiting times, Fuel savings, $CO_2$ drops).
2. **Step 2 (Webots 3D Physics Simulation)**:
   * Open `intersection_vbot.wbt` in Webots.
   * Point out the **physical sensors** placed along the road (Inductive Loop at 15m, Dilemma sensor at 50m, Radar at 100m).
   * Show the physical 3D traffic light LEDs switching in real time based on vehicle arrivals.
   * Explain how this proves the system works on **both traffic network scales (SUMO)** and **embedded 3D robotic hardware (Webots)**!
