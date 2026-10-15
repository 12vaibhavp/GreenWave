"""
Vision Module Configuration
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from pathlib import Path

@dataclass
class VisionConfig:
    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = 0.35
    iou_threshold: float = 0.45
    image_size: int = 640
    frame_skip: int = 1  # Process every frame by default; >1 for skipping
    target_classes: List[int] = field(default_factory=lambda: [2, 3, 5, 7]) # 2: car, 3: motorcycle, 5: bus, 7: truck
    class_names: Dict[int, str] = field(default_factory=lambda: {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    })
    
    # Density Classification Thresholds (Normalized vehicle occupancy / queue score: 0.0 - 1.0)
    density_low_max: float = 0.30
    density_med_max: float = 0.70
    
    # Minimum movement displacement (pixels) over history window to consider a vehicle moving vs stopped
    stopped_speed_threshold_px: float = 2.0
    queue_history_window: int = 15  # frames
