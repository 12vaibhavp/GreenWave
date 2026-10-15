"""
YOLO Vehicle Detector Module
Handles loading YOLO models and performing batched or single-frame vehicle detection.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import cv2
import torch
from ultralytics import YOLO
from vision.config import VisionConfig


@dataclass
class Detection:
    """Represents a single detected object in a frame."""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: str

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    @property
    def area(self) -> int:
        x1, y1, x2, y2 = self.bbox
        return max(0, x2 - x1) * max(0, y2 - y1)


class VehicleDetector:
    """
    Real-time Vehicle Detector wrapping Ultralytics YOLO models.
    Supports GPU (MPS / CUDA) and CPU inference.
    """

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig()
        self.device = self._resolve_device(self.config)
        self.model = self._load_model(self.config.model_path)

    @staticmethod
    def _resolve_device(config: VisionConfig) -> str:
        """Resolve optimal device for execution."""
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _load_model(self, model_path: str) -> YOLO:
        """Load pretrained or custom YOLO model."""
        try:
            model = YOLO(model_path)
            # Pre-warm / move to resolved device
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model from '{model_path}': {str(e)}")

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Perform detection on a single image frame (BGR format from OpenCV).
        Returns a list of Detection objects filtered by vehicle classes and confidence.
        """
        if frame is None or frame.size == 0:
            return []

        # Run inference
        results = self.model(
            source=frame,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            imgsz=self.config.image_size,
            device=self.device,
            verbose=False
        )

        detections: List[Detection] = []
        if not results:
            return detections

        res = results[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())

            # Filter for configured target classes (e.g. car, motorcycle, bus, truck)
            if self.config.target_classes and cls_id not in self.config.target_classes:
                continue

            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy[0], xyxy[1], xyxy[2], xyxy[3]
            cls_name = self.config.class_names.get(cls_id, res.names.get(cls_id, f"class_{cls_id}"))

            detections.append(
                Detection(
                    bbox=(x1, y1, x2, y2),
                    confidence=conf,
                    class_id=cls_id,
                    class_name=cls_name
                )
            )

        return detections

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        color: Tuple[int, int, int] = (0, 255, 0)
    ) -> np.ndarray:
        """Draw bounding boxes and class labels onto the frame."""
        vis = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name}: {det.confidence:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(vis, (x1, y1 - 20), (x1 + w, y1), color, -1)
            cv2.putText(
                vis,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )
        return vis
