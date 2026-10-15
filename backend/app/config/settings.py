"""
GreenWave Global Configuration and Settings Management
"""
import os
from pathlib import Path
from typing import List

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings:
    # Project Info
    PROJECT_NAME: str = "GREENWAVE: Real-Time Intelligent Traffic Signal Control"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    MODELS_DIR: Path = BASE_DIR / "models"
    DATA_DIR: Path = BASE_DIR / "data"
    RESULTS_DIR: Path = BASE_DIR / "data" / "results"
    SUMO_DIR: Path = BASE_DIR / "sumo"
    
    # YOLO & Vision Defaults
    YOLO_MODEL_PATH: str = str(MODELS_DIR / "yolov8n.pt")
    YOLO_CONFIDENCE_THRESHOLD: float = 0.35
    YOLO_IOU_THRESHOLD: float = 0.45
    YOLO_DEVICE: str = "auto"
    YOLO_VEHICLE_CLASSES: List[int] = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    
    # SUMO Settings
    SUMO_STEP_LENGTH: float = 1.0
    SIMULATION_DURATION: int = 3600
    SUMO_GUI: bool = False
    
    # RL Settings
    RL_ALPHA: float = 0.1
    RL_GAMMA: float = 0.95
    RL_EPSILON: float = 1.0
    RL_EPSILON_DECAY: float = 0.995
    RL_EPSILON_MIN: float = 0.01
    RL_MIN_GREEN: int = 10
    RL_MAX_GREEN: int = 60
    RL_YELLOW_TIME: int = 4
    
    # Database
    DATABASE_PATH: str = str(RESULTS_DIR / "greenwave.db")
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

settings = Settings()
