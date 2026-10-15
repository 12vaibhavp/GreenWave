"""
Phase 1 Environment & Foundation Verification Tests
"""
import os
import sys
from pathlib import Path
import pytest

def test_python_version():
    """Ensure Python version is 3.10+"""
    assert sys.version_info >= (3, 10), f"Python version too old: {sys.version}"

def test_core_dependencies():
    """Ensure all required ML, simulation, and backend libraries import properly"""
    import torch
    import torchvision
    import ultralytics
    import cv2
    import traci
    import sumolib
    import fastapi
    import pydantic
    import pandas
    import numpy
    import matplotlib
    import websockets
    
    assert ultralytics.__version__ is not None
    assert cv2.__version__ is not None
    assert traci is not None
    assert sumolib is not None

def test_yolo_weights_exist():
    """Verify that yolov8n.pt model weight exists in models/ directory"""
    weight_path = Path(__file__).resolve().parent.parent / "models" / "yolov8n.pt"
    assert weight_path.exists(), f"YOLO model weights not found at {weight_path}"
    assert weight_path.stat().st_size > 1_000_000, "YOLO weights file is suspiciously small"

def test_sumo_binary_available():
    """Verify that SUMO simulation binary is discoverable and executable"""
    import sumolib
    sumo_bin = sumolib.checkBinary("sumo")
    assert sumo_bin is not None and os.path.exists(sumo_bin), f"SUMO binary not found: {sumo_bin}"

def test_config_loading():
    """Verify that vision config and backend settings instantiate correctly"""
    from vision.config import VisionConfig
    from backend.app.config.settings import settings
    
    vcfg = VisionConfig()
    assert vcfg.confidence_threshold == 0.35
    assert len(vcfg.target_classes) == 4
    assert 2 in vcfg.target_classes  # Car
    
    assert settings.PROJECT_NAME.startswith("GREENWAVE")
    assert settings.RL_MIN_GREEN >= 5
