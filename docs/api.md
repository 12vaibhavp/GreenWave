# GREENWAVE REST & WebSocket API Reference

The backend provides OpenAPI / Swagger documentation at `http://localhost:8000/docs`.

---

## REST Endpoints

### 1. Health & Status
* `GET /health`: Returns system health, YOLO model loading status, and SUMO environment readiness.
* `GET /api/v1/traffic/current`: Instantaneous intersection state, current signal phase, and approach queue breakdown.
* `GET /api/v1/traffic/history`: Recent time-series telemetry samples.
* `GET /api/v1/signals`: Active signal phase, name, duration, and active controller.
* `GET /api/v1/metrics`: Summary intersection performance metrics (total queue, total waiting time, throughput).

### 2. Simulation Lifecycle Controls
* `POST /api/v1/simulation/start`: Launch background SUMO simulation.
  ```json
  {
    "controller": "adaptive",
    "scenario": "medium",
    "seed": 42,
    "duration": 1800,
    "step_delay_sec": 0.05
  }
  ```
* `POST /api/v1/simulation/stop`: Halts the active simulation.
* `POST /api/v1/simulation/reset`: Resets simulation state and clears historical chart points.
* `GET /api/v1/simulation/status`: Returns current step, running state, and throughput.

### 3. Computer Vision & Video Stream
* `POST /api/v1/vision/start`: Start background YOLO detection on video source (`"sample"` or video filepath).
* `POST /api/v1/vision/stop`: Stops video processing thread.
* `GET /api/v1/vision/stream`: Returns live multipart/x-mixed-replace MJPEG video stream with bounding boxes and HUD.

### 4. Reinforcement Learning & Benchmarks
* `GET /api/v1/rl/status`: Returns Q-table discovery statistics, hyperparameters ($\alpha, \gamma, \epsilon$), and state action samples.
* `GET /api/v1/experiments`: List of all logged simulation experiment runs from SQLite database.
* `GET /api/v1/experiments/benchmark/summary`: Consolidated scenario benchmark metrics.
* `GET /api/v1/experiments/export/csv`: Direct download of experiment database as CSV.

---

## WebSocket API
* `ws://localhost:8000/ws/traffic`: Streams live telemetry at 5 Hz.
