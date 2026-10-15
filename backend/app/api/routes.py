"""
FastAPI REST Routes for GREENWAVE.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse, FileResponse

from backend.app.config.settings import settings
from backend.app.models.schemas import (
    HealthResponse,
    TrafficCurrentResponse,
    SimulationStartRequest,
    SimulationStatusResponse,
    VisionStartRequest,
    VisionStatusResponse,
    ExperimentRecordResponse,
    RLStatusResponse
)
from backend.app.services.simulation_service import simulation_service
from backend.app.services.vision_service import vision_service
from backend.app.services.experiment_service import experiment_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """System health and dependencies check."""
    yolo_exists = Path(settings.YOLO_MODEL_PATH).exists()
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        yolo_loaded=yolo_exists,
        sumo_available=True,
        timestamp=datetime.now().isoformat()
    )


@router.get("/traffic/current", response_model=TrafficCurrentResponse)
def get_current_traffic():
    """Retrieve instantaneous intersection traffic and signal state."""
    return simulation_service.get_current_state()


@router.get("/traffic/history")
def get_traffic_history():
    """Retrieve recent time-series telemetry samples."""
    return {"history": simulation_service.history_samples}


@router.get("/signals")
def get_signals_state():
    """Retrieve traffic signal phase status and timing."""
    state = simulation_service.get_current_state()
    return {
        "current_phase": state["current_phase"],
        "phase_name": state["phase_name"],
        "phase_duration": state["phase_duration"],
        "active_controller": state["active_controller"]
    }


@router.get("/metrics")
def get_traffic_metrics():
    """Retrieve aggregate performance metrics for the active simulation."""
    state = simulation_service.get_current_state()
    return {
        "total_queue": state["total_queue"],
        "total_waiting_time": state["total_waiting_time"],
        "average_speed_mps": state["average_speed_mps"],
        "throughput": state["throughput"]
    }


@router.post("/simulation/start")
def start_simulation(req: SimulationStartRequest):
    """Start background SUMO simulation."""
    try:
        res = simulation_service.start_simulation(
            controller=req.controller,
            scenario=req.scenario,
            seed=req.seed,
            duration=req.duration,
            step_delay=req.step_delay_sec
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/stop")
def stop_simulation():
    """Stop active simulation."""
    return simulation_service.stop_simulation()


@router.post("/simulation/reset")
def reset_simulation():
    """Reset simulation to initial state."""
    simulation_service.stop_simulation()
    return {"status": "reset"}


@router.get("/simulation/status", response_model=SimulationStatusResponse)
def get_simulation_status():
    """Get active simulation status."""
    return SimulationStatusResponse(
        is_running=simulation_service.is_running,
        controller=simulation_service.controller_name,
        scenario=simulation_service.scenario_name,
        current_step=simulation_service.sim.current_step if simulation_service.sim else 0,
        duration=simulation_service.duration,
        throughput=simulation_service.sim.cumulative_arrived_vehicles if simulation_service.sim else 0
    )


@router.post("/vision/start")
def start_vision_pipeline(req: VisionStartRequest):
    """Start YOLO computer vision stream processing."""
    try:
        return vision_service.start_vision(source=req.source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vision/stop")
def stop_vision_pipeline():
    """Stop YOLO vision processing."""
    return vision_service.stop_vision()


@router.get("/vision/stream")
def get_vision_mjpeg_stream():
    """Live MJPEG video stream with YOLO bounding boxes, tracks, and density gauges."""
    if not vision_service.is_running:
        vision_service.start_vision(source="sample")

    return StreamingResponse(
        vision_service.get_stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/experiments", response_model=List[ExperimentRecordResponse])
def get_experiments_list():
    """Retrieve logged experimental runs."""
    return experiment_service.get_experiments()


@router.get("/experiments/benchmark/summary")
def get_benchmark_summary():
    """Retrieve summarized benchmark comparison across controllers and scenarios."""
    return experiment_service.get_benchmark_summary()


@router.get("/experiments/export/csv")
def export_experiments_csv():
    """Export all experiment runs as a downloadable CSV."""
    csv_data = experiment_service.export_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=greenwave_experiments.csv"}
    )


@router.get("/rl/status", response_model=RLStatusResponse)
def get_rl_status():
    """Retrieve Q-table statistics and exploration state."""
    q_table_path = Path(settings.MODELS_DIR) / "q_table.json"
    if not q_table_path.exists():
        return RLStatusResponse(
            q_table_loaded=False,
            total_states_discovered=0,
            alpha=0.1,
            gamma=0.95,
            epsilon=0.0,
            sample_state_actions={}
        )

    with open(q_table_path, "r") as f:
        data = json.load(f)

    q_table = data.get("q_table", {})
    # Return first 10 states as sample
    samples = {k: v for k, v in list(q_table.items())[:10]}

    return RLStatusResponse(
        q_table_loaded=True,
        total_states_discovered=len(q_table),
        alpha=data.get("alpha", 0.1),
        gamma=data.get("gamma", 0.95),
        epsilon=data.get("epsilon", 0.0),
        sample_state_actions=samples
    )
