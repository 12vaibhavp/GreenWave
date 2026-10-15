# GREENWAVE Methodology

## 1. Vehicle Detection & Classification
Vehicle detection uses **YOLOv8** (You Only Look Once, Version 8) trained on the COCO dataset.

### Configured Vehicle Classes
* Class 2: `car`
* Class 3: `motorcycle`
* Class 5: `bus`
* Class 7: `truck`

Inference operates with configurable confidence ($\ge 0.35$) and IoU thresholds ($\ge 0.45$).

---

## 2. Multi-Object Tracking & Non-Duplicating Counting
Counting detections per frame leads to catastrophic double-counting. GREENWAVE assigns persistent `TrackID`s using a two-stage association algorithm:

1. **Stage 1 — IoU Association**: Pairs detections with active tracks using greedy maximum IoU matching ($\ge 0.25$).
2. **Stage 2 — Proximity Association**: For unassigned detections, associates using Euclidean centroid distance within a spatial search radius ($\le 80\text{px}$).
3. **Track Lifecycle**:
   * New track initialized with `hits = 1`.
   * Promoted to confirmed track after `hits >= min_hits`.
   * Trajectory history recorded up to 50 past centroids.
   * Dead tracks pruned after `time_since_update > max_age` (15 frames).

---

## 3. Mathematical Density & Queue Estimation

### Continuous Density Score Formula
$$\text{DensityScore} = w_c \cdot \min\left(1.0, \frac{N}{N_{\max}}\right) + w_o \cdot \text{OccupancyRatio} + w_q \cdot \min\left(1.0, \frac{Q}{Q_{\max}}\right)$$

Where:
* $N$: Active vehicles inside the approach polygon.
* $N_{\max}$: Approach vehicle capacity (e.g. 12 vehicles).
* $\text{OccupancyRatio} = \frac{\sum \text{BBox Area}}{\text{ROI Area}}$.
* $Q$: Stationary vehicles ($\text{speed} \le 2.0\text{ px/frame}$).
* $Q_{\max}$: Maximum expected queue.
* Weights $w_c = 0.40, w_o = 0.30, w_q = 0.30$.

### Categorical Classification
* $\text{LOW}$: $\text{Score} < 0.30$
* $\text{MEDIUM}$: $0.30 \le \text{Score} < 0.70$
* $\text{HIGH}$: $\text{Score} \ge 0.70$

### Queue Distance Estimation
$$\text{QueueLength}_{\text{meters}} = \frac{\max_{v \in \text{Stopped}} \|\text{Centroid}_v - \text{StopLine}_{\text{mid}}\|}{\text{PixelsPerMeter}}$$
