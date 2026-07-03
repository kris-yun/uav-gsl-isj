# Iteration 3 Rerun Summary

**Date**: 2026-06-07
**Trigger**: MEMP performed same as DQA_AS in iter3 — root cause was missing gas signal

---

## What Changed

**File**: `workspace/uav_diagsense/src/memp/memp_planner.py` (line 47)

**Bug**: `hit = last.get("hit", False)` — the `"hit"` key never exists in `obs_history`. Observations use `"gas"` (float concentration).

**Fix**: `hit = float(last.get("gas", 0.0)) > 0.01`

**Impact**: MEMPPosteriorEstimator was receiving `hit=False` on every step, including when gas was detected. The Laplacian smoothing was applied to a posterior that was only ever updated with miss observations — explaining why MEMP behaved identically to DQA_AS (they shared the same action selection but MEMP's unique component — the smoothed posterior — was starved of signal).

---

## Why It Should Help

MEMP's core innovation is the Laplacian-smoothed posterior that prevents isolated peaks and enforces spatial continuity. Without hit updates:
- The posterior was uniformly "miss-updated" → Laplacian smoothing had nothing to smooth
- MAP estimate was essentially the starting centroid → same as any non-informed planner

With proper gas signal integration:
- Hit observations create peaks in the posterior
- Laplacian smoothing spreads these peaks to neighboring free cells (preventing isolated spikes)
- MAP estimate follows the smoothed belief → more robust source declaration

---

## Result Comparison

### Synthetic Plume (5 seeds, 80 steps, deterministic)

| Method | Final Error (median) | Best Error (median) |
|--------|---------------------|---------------------|
| Infotaxis | 2.92m | 2.69m |
| GreedyMAP | 3.35m | 3.04m |
| Random | 4.27m | 3.04m |
| **MEMP_fixed** | **4.53m** | **2.83m** |

### Per-seed breakdown (final error)

| Seed | Start | MEMP_fixed | GreedyMAP | Random | Infotaxis |
|------|-------|-----------|-----------|--------|-----------|
| 0 | (-5,-5) | 4.27 | 4.30 | 4.61 | 4.27 |
| 1 | (-3,-1) | 4.92 | 3.35 | 4.03 | 2.69 |
| 2 | (0,-5) | 3.20 | 2.50 | 4.27 | 2.92 |
| 3 | (-1,0) | 5.00 | 3.50 | 1.41 | 4.27 |
| 4 | (-4,-3) | 4.53 | 3.20 | 4.30 | 2.50 |

---

## Interpretation

The fix is **necessary but not sufficient**. MEMP_fixed's action selection wrapper (used in this eval because DQAASPlanner can't be imported without GADEN) is too simplistic — it uses a crude explore/surge/map heuristic. On the full system with DQAAS action selection, the MEMP posterior should provide better waypoint scoring.

Key observations:
1. **MEMP_best (2.83m)** is competitive with Infotaxis (2.69m) — the posterior IS finding the source in some seeds
2. **MEMP_final (4.53m)** is worst — the planner fails to *stay* near the source once found
3. This suggests the action selection (not the posterior) is the bottleneck

---

## Next Steps

1. **Priority**: Run MEMP with the full DQAAS action library on GADEN (when stable) to isolate posterior quality from action selection quality
2. **If GADEN stays unstable**: Enhance the lightweight runner with proper A* pathfinding and action library
3. **Consider**: Adding a "hover-and-confirm" action when posterior entropy is low (MEMP finds source but doesn't declare)

---

## Files Created/Modified

| File | Action |
|------|--------|
| `workspace/uav_diagsense/src/memp/memp_planner.py` | Fixed gas signal extraction |
| `workspace/uav_diagsense/tests/test_memp_signal.py` | New integration test |
| `workspace/uav_diagsense/scripts/run_small_eval.py` | New lightweight eval runner |
| `automation/results/iter3_rerun_comparison.csv` | Raw results |
| `automation/results/iter3_rerun_summary.md` | This file |
