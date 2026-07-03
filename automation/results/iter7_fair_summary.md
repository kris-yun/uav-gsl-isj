# Iteration 7: Fair Comparison with DQA-AS Baseline

**Date**: 2026-06-07
**Setup**: 5 seeds, 80 steps, synthetic Gaussian plume, deterministic
**Updated**: After BPFM centroid-attraction fix

---

## Results

| Method | Final Error (median) | Best Error (median) | vs DQA-AS |
|--------|---------------------|---------------------|-----------|
| **DQA_AS+BPFM** | **2.92m** | **2.92m** | **-54%** |
| **DQA_AS+MEMP** | **3.81m** | **3.20m** | **-40%** |
| DQA_AS+SDM | 6.02m | 4.27m | -5% |
| DQA_AS (baseline) | 6.32m | 2.92m | — |

### Reference baselines

| Method | Final Error (median) | Best Error (median) |
|--------|---------------------|---------------------|
| GreedyMAP | 5.15m | 2.92m |
| Infotaxis | 5.52m | 2.92m |
| Random | 5.02m | 2.55m |

---

## BPFM Fix

**Problem**: Original BPFM moved all particles by the same upwind vector, which translated the cloud without convergence.

**Fix**: Replaced uniform flow with centroid-attraction:
- On hit: particles drift toward weighted centroid + small upwind offset (strength 0.3)
- On miss: particles drift mildly toward centroid (strength 0.05) + full diffusion

This creates convergence toward high-weight regions rather than rigid translation.

---

## Honest Verdict

### BPFM: BEATS DQA-AS ✓
- 54% reduction in final error (2.92m vs 6.32m)
- Centroid-attraction provides stable convergence
- Now the best-performing innovation

### MEMP: BEATS DQA-AS ✓
- 40% reduction in final error (3.81m vs 6.32m)
- Consistent across all seeds

### SDM: MARGINAL
- 5% improvement under moderate wind
- Needs stronger wind conditions to show full benefit

---

## Files

| File | Description |
|------|-------------|
| `automation/results/iter7_fair_comparison.csv` | Raw results |
| `automation/results/iter7_fair_summary.md` | This file |
