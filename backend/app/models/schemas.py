"""
Pydantic API Request/Response Schemas for GREENWAVE.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    project: str
    version: str
    yolo_loaded: bool
    sumo_available: bool
    timestamp: str


class ApproachStatus(BaseModel):
    approach_name: str
    active_vehicles: int
    queue_length: int
    waiting_time_s: float
    mean_speed_mps: float
    density_level: str
    normalized_density: float


class TrafficCurrentResponse(BaseModel):
    step: int
    current_phase: int
    phase_name: str
    phase_duration: int
    total_queue: int
    total_waiting_time: float
    average_speed_mps: float
    throughput: int
    approaches: Dict[str, ApproachStatus]
    active_controller: str
    simulation_running: bool


class SimulationStartRequest(BaseModel):
    controller: str = Field(default="adaptive", description="fixed_time, adaptive, or q_learning")
    scenario: str = Field(default="medium", description="low, medium, high, unbalanced, or peak")
    seed: int = Field(default=42, description="Random seed")
    duration: int = Field(default=1800, description="Duration in simulation steps (seconds)")
    step_delay_sec: float = Field(default=0.05, description="Wall-clock delay between simulation steps for visual pacing")


class SimulationStatusResponse(BaseModel):
    is_running: bool
    controller: Optional[str] = None
    scenario: Optional[str] = None
    current_step: int = 0
    duration: int = 0
    throughput: int = 0
    avg_queue: float = 0.0
    avg_wait: float = 0.0


class VisionStartRequest(BaseModel):
    source: str = Field(default="sample", description="Video file path or 'sample' or webcam index '0'")
    confidence_threshold: float = Field(default=0.35, ge=0.05, le=0.95)
    iou_threshold: float = Field(default=0.45, ge=0.05, le=0.95)


class VisionStatusResponse(BaseModel):
    is_running: bool
    source: str
    active_vehicles: int
    total_unique_vehicles: int
    critical_approach: str
    fps: float


class ExperimentRecordResponse(BaseModel):
    id: int
    experiment_id: str
    timestamp: str
    controller: str
    scenario: str
    seed: int
    duration_sec: int
    avg_waiting_time: float
    total_waiting_time: float
    avg_queue_length: float
    max_queue_length: int
    throughput: int
    avg_travel_time: float
    avg_speed_mps: float


class RLStatusResponse(BaseModel):
    q_table_loaded: bool
    total_states_discovered: int
    alpha: float
    gamma: float
    epsilon: float
    sample_state_actions: Dict[str, List[float]]
