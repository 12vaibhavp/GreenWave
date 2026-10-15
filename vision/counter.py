"""
Vehicle Counter Module
Computes unique vehicle counts, class-wise counts, and lane/region-wise counts.
Prevents duplicate counts using verified Track IDs.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
import numpy as np
import cv2
from vision.tracker import TrackedVehicle


@dataclass
class RegionOfInterest:
    """Represents a polygonal region of interest (e.g. lane or approach direction)."""
    name: str
    polygon: List[Tuple[int, int]]  # List of (x, y) vertices
    color: Tuple[int, int, int] = (0, 200, 200)

    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if a 2D point (x, y) lies inside the polygon using cv2.pointPolygonTest."""
        pts = np.array(self.polygon, dtype=np.int32)
        # Returns +1 (inside), 0 (on edge), -1 (outside)
        return cv2.pointPolygonTest(pts, (float(point[0]), float(point[1])), False) >= 0


@dataclass
class CountingMetrics:
    """Consolidated vehicle counting statistics."""
    total_unique_vehicles: int
    active_vehicles: int
    class_counts: Dict[str, int]
    region_active_counts: Dict[str, int]
    region_cumulative_counts: Dict[str, int]


class VehicleCounter:
    """
    Tracks and aggregates vehicle counts over time across the whole frame and within configurable ROIs.
    """

    def __init__(self, regions: Optional[List[RegionOfInterest]] = None):
        self.regions: Dict[str, RegionOfInterest] = {r.name: r for r in (regions or [])}
        
        # Cumulative unique vehicle tracking
        self.seen_track_ids: Set[int] = set()
        self.class_counts: Dict[str, int] = {}
        
        # Region-wise unique vehicle tracking
        self.region_seen_ids: Dict[str, Set[int]] = {r_name: set() for r_name in self.regions}

    def add_region(self, region: RegionOfInterest) -> None:
        """Add or update an ROI polygon."""
        self.regions[region.name] = region
        if region.name not in self.region_seen_ids:
            self.region_seen_ids[region.name] = set()

    def update(self, active_tracks: List[TrackedVehicle]) -> CountingMetrics:
        """
        Process current frame tracks and update cumulative and active counts.
        """
        region_active_counts: Dict[str, int] = {r_name: 0 for r_name in self.regions}

        for tr in active_tracks:
            # 1. Global unique count
            if tr.track_id not in self.seen_track_ids:
                self.seen_track_ids.add(tr.track_id)
                self.class_counts[tr.class_name] = self.class_counts.get(tr.class_name, 0) + 1

            # 2. Region-wise count
            centroid = tr.centroid
            for r_name, region in self.regions.items():
                if region.contains_point(centroid):
                    region_active_counts[r_name] += 1
                    self.region_seen_ids[r_name].add(tr.track_id)

        region_cumulative_counts = {
            r_name: len(seen) for r_name, seen in self.region_seen_ids.items()
        }

        return CountingMetrics(
            total_unique_vehicles=len(self.seen_track_ids),
            active_vehicles=len(active_tracks),
            class_counts=dict(self.class_counts),
            region_active_counts=region_active_counts,
            region_cumulative_counts=region_cumulative_counts
        )

    def draw_overlays(
        self,
        frame: np.ndarray,
        metrics: CountingMetrics,
        show_regions: bool = True
    ) -> np.ndarray:
        """Draw HUD statistics and ROI polygons onto the frame."""
        vis = frame.copy()

        # 1. Draw Regions
        if show_regions:
            for r_name, region in self.regions.items():
                pts = np.array(region.polygon, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(vis, [pts], isClosed=True, color=region.color, thickness=2)
                # Label region
                if len(region.polygon) > 0:
                    rx, ry = region.polygon[0]
                    active_cnt = metrics.region_active_counts.get(r_name, 0)
                    cum_cnt = metrics.region_cumulative_counts.get(r_name, 0)
                    label = f"{r_name} (Act:{active_cnt} | Cum:{cum_cnt})"
                    cv2.putText(vis, label, (rx, ry - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, region.color, 1)

        # 2. Draw HUD Info Panel (Top-Left)
        cv2.rectangle(vis, (10, 10), (280, 110), (0, 0, 0), -1)
        cv2.rectangle(vis, (10, 10), (280, 110), (255, 255, 255), 1)

        cv2.putText(vis, f"Active Vehicles: {metrics.active_vehicles}", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(vis, f"Total Unique: {metrics.total_unique_vehicles}", (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Show top class counts
        cls_str = " | ".join([f"{k}:{v}" for k, v in list(metrics.class_counts.items())[:3]])
        cv2.putText(vis, f"Classes: {cls_str or 'None'}", (20, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        return vis
