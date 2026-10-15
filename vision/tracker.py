"""
Multi-Object Vehicle Tracker
Maintains persistent IDs across video frames using IoU & spatial association.
Prevents duplicate vehicle counts.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import numpy as np
import cv2
from vision.detector import Detection


@dataclass
class TrackedVehicle:
    """Represents a persistently tracked vehicle."""
    track_id: int
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    class_id: int
    class_name: str
    confidence: float
    history: List[Tuple[int, int]] = field(default_factory=list)
    hits: int = 1
    age: int = 1
    time_since_update: int = 0
    is_confirmed: bool = False

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    @property
    def speed_px(self) -> float:
        """Estimate instantaneous speed in pixels per frame based on last 5 frames."""
        if len(self.history) < 2:
            return 0.0
        p1 = np.array(self.history[-1])
        p2 = np.array(self.history[-min(len(self.history), 5)])
        dist = np.linalg.norm(p1 - p2)
        frames = min(len(self.history), 5) - 1
        return float(dist / max(1, frames))

    def update(self, detection: Detection) -> None:
        """Update track with a new detection."""
        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.class_id = detection.class_id
        self.class_name = detection.class_name
        self.history.append(self.centroid)
        if len(self.history) > 50:  # Retain last 50 positions
            self.history.pop(0)
        self.hits += 1
        self.time_since_update = 0
        if self.hits >= 2:  # Confirmed after 2 successful detections
            self.is_confirmed = True

    def mark_missed(self) -> None:
        """Mark track as missed in the current frame."""
        self.time_since_update += 1


def calculate_iou(bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int]) -> float:
    """Compute Intersection-over-Union (IoU) between two bounding boxes."""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class VehicleTracker:
    """
    Real-Time Vehicle Tracker.
    Associates incoming detections with active tracks using combined IoU and centroid proximity.
    """

    def __init__(
        self,
        max_age: int = 15,
        min_hits: int = 2,
        iou_threshold: float = 0.25,
        max_distance_px: float = 80.0
    ):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.max_distance_px = max_distance_px
        self.next_id: int = 1
        self.tracks: Dict[int, TrackedVehicle] = {}

    def update(self, detections: List[Detection]) -> List[TrackedVehicle]:
        """
        Update tracker with new frame detections.
        Returns list of active, confirmed TrackedVehicle instances.
        """
        for track in self.tracks.values():
            track.age += 1

        active_track_ids = list(self.tracks.keys())
        unmatched_detections = list(range(len(detections)))
        matched_tracks = set()

        if active_track_ids and detections:
            # 1. IoU Association
            cost_matrix = np.zeros((len(active_track_ids), len(detections)))
            for i, tid in enumerate(active_track_ids):
                for j, det in enumerate(detections):
                    iou = calculate_iou(self.tracks[tid].bbox, det.bbox)
                    cost_matrix[i, j] = iou

            # Greedy matching for highest IoU
            while cost_matrix.size > 0 and np.max(cost_matrix) >= self.iou_threshold:
                i, j = np.unravel_index(np.argmax(cost_matrix), cost_matrix.shape)
                tid = active_track_ids[i]
                self.tracks[tid].update(detections[j])
                matched_tracks.add(tid)
                if j in unmatched_detections:
                    unmatched_detections.remove(j)
                cost_matrix[i, :] = -1.0
                cost_matrix[:, j] = -1.0

            # 2. Centroid distance matching for remaining unmatched detections
            remaining_tids = [tid for tid in active_track_ids if tid not in matched_tracks]
            for j in list(unmatched_detections):
                det = detections[j]
                det_c = np.array(det.centroid)
                best_tid = None
                best_dist = self.max_distance_px

                for tid in remaining_tids:
                    tr_c = np.array(self.tracks[tid].centroid)
                    dist = np.linalg.norm(det_c - tr_c)
                    if dist < best_dist and self.tracks[tid].class_id == det.class_id:
                        best_dist = dist
                        best_tid = tid

                if best_tid is not None:
                    self.tracks[best_tid].update(det)
                    matched_tracks.add(best_tid)
                    remaining_tids.remove(best_tid)
                    unmatched_detections.remove(j)

        # Mark unmatched tracks as missed
        for tid in active_track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missed()

        # Create new tracks for unmatched detections
        for j in unmatched_detections:
            det = detections[j]
            new_track = TrackedVehicle(
                track_id=self.next_id,
                bbox=det.bbox,
                class_id=det.class_id,
                class_name=det.class_name,
                confidence=det.confidence,
                history=[det.centroid],
                hits=1,
                age=1,
                time_since_update=0,
                is_confirmed=(self.min_hits <= 1)
            )
            self.tracks[self.next_id] = new_track
            self.next_id += 1

        # Prune expired tracks
        dead_ids = [
            tid for tid, tr in self.tracks.items()
            if tr.time_since_update > self.max_age
        ]
        for tid in dead_ids:
            del self.tracks[tid]

        # Return all active tracks (confirmed or young)
        return [tr for tr in self.tracks.values() if tr.time_since_update == 0]

    def draw_tracks(
        self,
        frame: np.ndarray,
        tracks: List[TrackedVehicle],
        color: Tuple[int, int, int] = (255, 128, 0)
    ) -> np.ndarray:
        """Draw tracked bounding boxes, IDs, and trajectory trails."""
        vis = frame.copy()
        for tr in tracks:
            x1, y1, x2, y2 = tr.bbox
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"ID:{tr.track_id} {tr.class_name}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(vis, (x1, y1 - 20), (x1 + w, y1), color, -1)
            cv2.putText(vis, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # Draw trajectory history
            if len(tr.history) > 1:
                pts = np.array(tr.history, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(vis, [pts], isClosed=False, color=(0, 255, 255), thickness=2)

        return vis
