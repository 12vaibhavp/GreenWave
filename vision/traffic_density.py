"""
Traffic Density and Queue Estimation Module
Computes reproducible normalized density scores, categorical density (LOW/MEDIUM/HIGH),
and queue length estimates across intersection approach zones.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2
from vision.tracker import TrackedVehicle
from vision.counter import RegionOfInterest
from vision.config import VisionConfig


class DensityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class ApproachQueueEstimate:
    """Queue and velocity condition metrics for a specific road approach."""
    approach_name: str
    active_vehicles: int
    stopped_vehicles: int  # Measured: speed <= threshold
    moving_vehicles: int
    estimated_queue_length_px: float  # Estimated: span from stopline to furthest stopped vehicle
    estimated_queue_length_m: float   # Estimated: converted via calibration scale factor
    average_speed_px: float


@dataclass
class ApproachDensityMetrics:
    """Complete density metrics for an approach."""
    approach_name: str
    active_vehicle_count: int
    roi_area_px: float
    occupied_area_px: float
    occupancy_ratio: float           # Measured: occupied_area / roi_area
    queue_metrics: ApproachQueueEstimate
    normalized_density_score: float  # Computed: 0.0 to 1.0
    density_level: DensityLevel      # Categorical: LOW, MEDIUM, HIGH


@dataclass
class IntersectionTrafficState:
    """Aggregated multi-approach intersection state for downstream RL and UI."""
    timestamp: float
    approaches: Dict[str, ApproachDensityMetrics]
    total_active_vehicles: int
    total_stopped_vehicles: int
    critical_approach: str  # Approach with highest density/queue


class TrafficDensityEstimator:
    """
    Computes mathematical traffic density and queue estimation.
    
    Density Formula:
        Score = w_count * (N / N_max) + w_occ * OccupancyRatio + w_queue * (Q / Q_max)
        where:
            N = active vehicles in ROI
            N_max = approach capacity (e.g. 10 vehicles)
            OccupancyRatio = sum(bbox_area) / roi_area
            Q = stopped/queued vehicles
            Q_max = maximum expected queue
            w_count + w_occ + w_queue = 1.0 (default 0.40, 0.30, 0.30)
    """

    def __init__(
        self,
        config: Optional[VisionConfig] = None,
        approach_regions: Optional[Dict[str, RegionOfInterest]] = None,
        stop_lines: Optional[Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]] = None,
        max_vehicles_per_approach: int = 12,
        pixels_per_meter: float = 15.0,  # Camera calibration scale
        w_count: float = 0.40,
        w_occ: float = 0.30,
        w_queue: float = 0.30,
    ):
        self.config = config or VisionConfig()
        self.approaches = approach_regions or {}
        self.stop_lines = stop_lines or {}
        self.max_vehicles = max(1, max_vehicles_per_approach)
        self.px_per_meter = max(0.1, pixels_per_meter)
        
        # Weights (must sum to 1.0)
        total_w = w_count + w_occ + w_queue
        self.w_count = w_count / total_w
        self.w_occ = w_occ / total_w
        self.w_queue = w_queue / total_w

    def add_approach(
        self,
        name: str,
        region: RegionOfInterest,
        stop_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    ) -> None:
        """Register an approach polygon and optional stopline."""
        self.approaches[name] = region
        if stop_line:
            self.stop_lines[name] = stop_line

    def _estimate_approach_queue(
        self,
        approach_name: str,
        tracks_in_roi: List[TrackedVehicle]
    ) -> ApproachQueueEstimate:
        """Calculate stopped vehicle counts and queue extent."""
        if not tracks_in_roi:
            return ApproachQueueEstimate(
                approach_name=approach_name,
                active_vehicles=0,
                stopped_vehicles=0,
                moving_vehicles=0,
                estimated_queue_length_px=0.0,
                estimated_queue_length_m=0.0,
                average_speed_px=0.0
            )

        stopped_tracks: List[TrackedVehicle] = []
        moving_tracks: List[TrackedVehicle] = []
        speeds: List[float] = []

        for tr in tracks_in_roi:
            spd = tr.speed_px
            speeds.append(spd)
            if spd <= self.config.stopped_speed_threshold_px:
                stopped_tracks.append(tr)
            else:
                moving_tracks.append(tr)

        # Estimate queue length
        queue_len_px = 0.0
        if stopped_tracks:
            # If stopline is defined, distance from stopline to furthest stopped vehicle
            stop_line = self.stop_lines.get(approach_name)
            if stop_line:
                p1, p2 = np.array(stop_line[0]), np.array(stop_line[1])
                line_mid = (p1 + p2) / 2.0
                distances = [
                    np.linalg.norm(np.array(tr.centroid) - line_mid)
                    for tr in stopped_tracks
                ]
                queue_len_px = float(max(distances))
            else:
                # Approximate from bounding boxes span
                ys = [tr.centroid[1] for tr in stopped_tracks]
                xs = [tr.centroid[0] for tr in stopped_tracks]
                queue_len_px = float(max(max(ys) - min(ys), max(xs) - min(xs)))

        queue_len_m = queue_len_px / self.px_per_meter

        return ApproachQueueEstimate(
            approach_name=approach_name,
            active_vehicles=len(tracks_in_roi),
            stopped_vehicles=len(stopped_tracks),
            moving_vehicles=len(moving_tracks),
            estimated_queue_length_px=queue_len_px,
            estimated_queue_length_m=queue_len_m,
            average_speed_px=float(np.mean(speeds)) if speeds else 0.0
        )

    def evaluate_approach(
        self,
        approach_name: str,
        active_tracks: List[TrackedVehicle]
    ) -> ApproachDensityMetrics:
        """Compute full density breakdown for a given approach ROI."""
        region = self.approaches.get(approach_name)
        if not region:
            raise ValueError(f"Approach '{approach_name}' not configured.")

        # 1. Filter tracks inside this approach ROI
        tracks_in_roi = [tr for tr in active_tracks if region.contains_point(tr.centroid)]

        # 2. Queue estimation
        queue_estimate = self._estimate_approach_queue(approach_name, tracks_in_roi)

        # 3. Polygon ROI area
        pts = np.array(region.polygon, dtype=np.int32)
        roi_area = max(1.0, float(cv2.contourArea(pts)))

        # 4. Occupied bounding box area
        occupied_area = sum(
            (tr.bbox[2] - tr.bbox[0]) * (tr.bbox[3] - tr.bbox[1])
            for tr in tracks_in_roi
        )
        occupancy_ratio = min(1.0, occupied_area / roi_area)

        # 5. Normalized Density Score
        count_term = min(1.0, len(tracks_in_roi) / self.max_vehicles)
        queue_term = min(1.0, queue_estimate.stopped_vehicles / self.max_vehicles)
        
        normalized_score = float(
            self.w_count * count_term +
            self.w_occ * occupancy_ratio +
            self.w_queue * queue_term
        )
        normalized_score = max(0.0, min(1.0, normalized_score))

        # 6. Categorical Level Classification
        if normalized_score < self.config.density_low_max:
            level = DensityLevel.LOW
        elif normalized_score < self.config.density_med_max:
            level = DensityLevel.MEDIUM
        else:
            level = DensityLevel.HIGH

        return ApproachDensityMetrics(
            approach_name=approach_name,
            active_vehicle_count=len(tracks_in_roi),
            roi_area_px=roi_area,
            occupied_area_px=float(occupied_area),
            occupancy_ratio=occupancy_ratio,
            queue_metrics=queue_estimate,
            normalized_density_score=normalized_score,
            density_level=level
        )

    def evaluate_intersection(
        self,
        active_tracks: List[TrackedVehicle],
        timestamp: float = 0.0
    ) -> IntersectionTrafficState:
        """Evaluate all intersection approaches and determine critical approach."""
        approach_metrics: Dict[str, ApproachDensityMetrics] = {}
        total_active = 0
        total_stopped = 0
        max_density = -1.0
        critical_app = "None"

        for app_name in self.approaches:
            m = self.evaluate_approach(app_name, active_tracks)
            approach_metrics[app_name] = m
            total_active += m.active_vehicle_count
            total_stopped += m.queue_metrics.stopped_vehicles

            if m.normalized_density_score > max_density:
                max_density = m.normalized_density_score
                critical_app = app_name

        return IntersectionTrafficState(
            timestamp=timestamp,
            approaches=approach_metrics,
            total_active_vehicles=total_active,
            total_stopped_vehicles=total_stopped,
            critical_approach=critical_app
        )

    def draw_density_dashboard(
        self,
        frame: np.ndarray,
        state: IntersectionTrafficState
    ) -> np.ndarray:
        """Render density gauges and queue estimates onto the video frame."""
        vis = frame.copy()
        h, w = vis.shape[:2]

        # Draw Approach overlay cards on right side of frame
        panel_w = 260
        panel_x = w - panel_w - 10
        panel_y = 10

        for i, (app_name, m) in enumerate(state.approaches.items()):
            cy = panel_y + i * 85
            # Card background
            cv2.rectangle(vis, (panel_x, cy), (panel_x + panel_w, cy + 78), (20, 20, 20), -1)
            
            # Level border color
            color = (0, 255, 0) if m.density_level == DensityLevel.LOW else \
                    (0, 200, 255) if m.density_level == DensityLevel.MEDIUM else (0, 0, 255)
            cv2.rectangle(vis, (panel_x, cy), (panel_x + panel_w, cy + 78), color, 2)

            # Title
            cv2.putText(vis, f"Approach: {app_name}", (panel_x + 10, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Density bar
            bar_w = int(240 * m.normalized_density_score)
            cv2.rectangle(vis, (panel_x + 10, cy + 28), (panel_x + 10 + bar_w, cy + 38), color, -1)
            cv2.rectangle(vis, (panel_x + 10, cy + 28), (panel_x + 250, cy + 38), (100, 100, 100), 1)

            # Metrics text
            score_text = f"Density: {m.density_level.value} ({m.normalized_density_score:.2f})"
            queue_text = f"Queue: {m.queue_metrics.stopped_vehicles} veh (~{m.queue_metrics.estimated_queue_length_m:.1f}m)"
            cv2.putText(vis, score_text, (panel_x + 10, cy + 54),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            cv2.putText(vis, queue_text, (panel_x + 10, cy + 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        return vis
