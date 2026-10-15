"""
Vision Service for Video Input Processing, Object Tracking, and MJPEG Streaming.
"""
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator
import cv2
import numpy as np

from vision.config import VisionConfig
from vision.detector import VehicleDetector
from vision.tracker import VehicleTracker
from vision.counter import VehicleCounter, RegionOfInterest
from vision.traffic_density import TrafficDensityEstimator, IntersectionTrafficState


class VisionService:
    """
    Singleton service managing live video ingestion, YOLO vehicle detection,
    multi-object tracking, and MJPEG frame encoding.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VisionService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.config = VisionConfig()
        self.detector: Optional[VehicleDetector] = None
        self.tracker: Optional[VehicleTracker] = None
        self.counter: Optional[VehicleCounter] = None
        self.density_estimator: Optional[TrafficDensityEstimator] = None

        self.source_path: str = "sample"
        self.is_running: bool = False
        self.stop_requested: bool = False
        self.thread: Optional[threading.Thread] = None

        self.latest_jpeg: Optional[bytes] = None
        self.latest_state: Optional[IntersectionTrafficState] = None
        self.total_unique: int = 0
        self.fps: float = 0.0

        self._setup_default_rois()

    def _setup_default_rois(self):
        """Configure standard 4-quadrant intersection approach ROIs."""
        # Standard 640x480 resolution approach zones
        north_roi = RegionOfInterest("North", [(220, 20), (420, 20), (420, 200), (220, 200)])
        south_roi = RegionOfInterest("South", [(220, 280), (420, 280), (420, 460), (220, 460)])
        east_roi = RegionOfInterest("East", [(440, 140), (620, 140), (620, 340), (440, 340)])
        west_roi = RegionOfInterest("West", [(20, 140), (200, 140), (200, 340), (20, 340)])

        self.counter = VehicleCounter(regions=[north_roi, south_roi, east_roi, west_roi])
        self.density_estimator = TrafficDensityEstimator(
            approach_regions={"North": north_roi, "South": south_roi, "East": east_roi, "West": west_roi}
        )

    def _lazy_load_models(self):
        """Lazy load YOLO detector on first start to preserve fast backend booting."""
        if self.detector is None:
            self.detector = VehicleDetector(self.config)
        if self.tracker is None:
            self.tracker = VehicleTracker(max_age=15, min_hits=2)

    def start_vision(self, source: str = "sample") -> Dict[str, Any]:
        """Start the vision processing pipeline in background."""
        if self.is_running:
            self.stop_vision()

        self._lazy_load_models()
        self.source_path = source
        self.stop_requested = False
        self.is_running = True

        self.thread = threading.Thread(target=self._process_video_loop, daemon=True)
        self.thread.start()
        return {"status": "started", "source": source}

    def stop_vision(self) -> Dict[str, Any]:
        """Stop vision pipeline."""
        self.stop_requested = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.is_running = False
        return {"status": "stopped"}

    def _process_video_loop(self):
        """Main frame processing loop."""
        # If source is "sample" or file does not exist, synthesize realistic dynamic traffic scene
        use_synthetic = (self.source_path == "sample" or not Path(self.source_path).exists())
        cap = None if use_synthetic else cv2.VideoCapture(self.source_path)

        synthetic_step = 0
        while not self.stop_requested:
            start_t = time.time()
            if use_synthetic:
                frame = self._generate_synthetic_frame(synthetic_step)
                synthetic_step += 1
            else:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

            # 1. YOLO Detection
            detections = self.detector.detect(frame)

            # 2. Vehicle Tracking
            active_tracks = self.tracker.update(detections)

            # 3. Counting & HUD
            count_metrics = self.counter.update(active_tracks)
            self.total_unique = count_metrics.total_unique_vehicles

            # 4. Density & Queue Estimation
            intersection_state = self.density_estimator.evaluate_intersection(
                active_tracks=active_tracks,
                timestamp=time.time()
            )
            self.latest_state = intersection_state

            # 5. Render overlays
            vis_frame = self.detector.draw_detections(frame, detections)
            vis_frame = self.tracker.draw_tracks(vis_frame, active_tracks)
            vis_frame = self.counter.draw_overlays(vis_frame, count_metrics)
            vis_frame = self.density_estimator.draw_density_dashboard(vis_frame, intersection_state)

            # 6. Encode to JPEG for MJPEG stream
            _, buffer = cv2.imencode(".jpg", vis_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            self.latest_jpeg = buffer.tobytes()

            elapsed = time.time() - start_t
            self.fps = 1.0 / max(0.001, elapsed)
            time.sleep(max(0.0, 0.05 - elapsed))  # ~20 FPS

        if cap:
            cap.release()
        self.is_running = False

    def _generate_synthetic_frame(self, step: int) -> np.ndarray:
        """Create a synthetic 640x480 4-way intersection frame with moving vehicles for testing."""
        frame = np.full((480, 640, 3), 40, dtype=np.uint8)

        # Draw roads (gray asphalt)
        # Vertical road (NS)
        cv2.rectangle(frame, (240, 0), (400, 480), (60, 60, 60), -1)
        # Horizontal road (EW)
        cv2.rectangle(frame, (0, 160), (640, 320), (60, 60, 60), -1)

        # Draw lane dividers (yellow dashes)
        for y in range(0, 480, 40):
            if y < 160 or y > 320:
                cv2.line(frame, (320, y), (320, y + 20), (0, 255, 255), 2)
        for x in range(0, 640, 40):
            if x < 240 or x > 400:
                cv2.line(frame, (x, 240), (x + 20, 240), (0, 255, 255), 2)

        # Draw synthetic vehicles moving along lanes
        # Vehicle 1: North approach moving down
        y_pos = int((step * 4) % 180) + 10
        cv2.rectangle(frame, (260, y_pos), (300, y_pos + 45), (180, 50, 50), -1)
        cv2.rectangle(frame, (265, y_pos + 10), (295, y_pos + 35), (240, 240, 240), -1)

        # Vehicle 2: West approach moving right
        x_pos = int((step * 3) % 180) + 10
        cv2.rectangle(frame, (x_pos, 260), (x_pos + 45, 295), (50, 120, 220), -1)

        return frame

    def get_stream_generator(self) -> Generator[bytes, None, None]:
        """Yield multipart MJPEG frame bytes."""
        while self.is_running:
            if self.latest_jpeg is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.latest_jpeg + b'\r\n')
            time.sleep(0.04)

vision_service = VisionService()
