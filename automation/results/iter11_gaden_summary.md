# Iter11 GADEN Experiment Summary

**Date**: 2026-06-07
**Experiment**: DQA_AS vs baselines on GADEN VGR (3 houses, 5 seeds each)
**Methods**: Random, GreedyMAP, Infotaxis, KLD, DQA_AS, DQA_AS_V2
**Seeds/starts**: 0=(0,-5), 1=(-3,-1), 2=(0,0), 3=(-1,2), 4=(-4,-3)
**max_steps**: 100, **sensor**: ideal

## Bug Fixes Applied

1. **Occupancy grid boundary bug**: House02 showed 0 free cells because z_max=2.0 included the solid ceiling plane (z=25, 1.5m). Fixed `load_occupancy_2d` to auto-trim fully-occupied boundary z-slices.
2. **DQA_AS ACCESS_VIOLATION crash**: Caused by massive scalar `hit_prob` calls (11,000+/step) in `_expected_risk_reduction`. Fixed by vectorizing `batch_hit_prob` in `SourceObservationModel`.
3. **DQA_AS_V2 ACCESS_VIOLATION crash**: Caused by FDPOE scorer calling scalar `hit_prob` 1725 times/step. Fixed by vectorizing `fisher_score` in `FDPOEScorer`.
4. **MEMP scipy.sparse instability**: Dense Laplacian matrix replaced sparse (scipy.sparse caused intermittent C-level crashes).
5. **Worker subprocess retry**: Added automatic retry (max 2) for non-zero exit codes.

## Start Position Validity

| Seed | Start | House01 | House02 | House03 |
|------|-------|---------|---------|---------|
| 0 | (0,-5) | OCC→free(adj) | FREE | OOB→free(adj) |
| 1 | (-3,-1) | OCC→free(adj) | OCC→free(adj) | OOB→free(adj) |
| 2 | (0,0) | FREE | OCC→free(adj) | OCC→free(adj) |
| 3 | (-1,2) | OCC→free(adj) | OCC→free(adj) | OOB→free(adj) |
| 4 | (-4,-3) | FREE | FREE | OOB→free(adj) |

**Note**: Most start positions are inside walls or out-of-bounds. The `smart_move` BFS finds the nearest free cell. This means all methods start from similar positions, which may reduce differentiation.

## House01 (source=(-0.4, -2.9), config=2,4-1_fast)

| Method | Decl | S@1m | S@2m | Med Err | Mean Err | Best Err |
|--------|------|------|------|---------|----------|----------|
| Random       | 4/5 | 2/5 | 2/5 | 5.02m | 3.89m | 0.85m |
| GreedyMAP    | 3/5 | 1/5 | 1/5 | 5.02m | 4.67m | 0.85m |
| Infotaxis    | 3/5 | 0/5 | 1/5 | 2.98m | 3.93m | 1.03m |
| KLD          | 3/5 | 0/5 | 1/5 | 2.98m | 3.93m | 1.03m |
| DQA_AS       | 4/5 | 1/5 | 1/5 | 3.31m | 4.23m | 0.85m |
| DQA_AS_V2    | 3/5 | 0/5 | 0/5 | 5.02m | 5.08m | 3.10m |

Per-seed errors (censored_error_m):

| Seed | Start | Random       | GreedyMAP    | Infotaxis    | KLD          | DQA_AS       | DQA_AS_V2    |
|------|-------|--------------|--------------|--------------|--------------|--------------|--------------|
| 0 | (0,-5) | 0.85**       | 0.85**       | 2.98*        | 2.98*        | 3.02*        | 3.10*        |
| 1 | (-3,-1) | 6.23         | 6.23         | 1.03         | 1.03         | 3.31*        | 3.31         |
| 2 | (0,0) | 0.85**       | 5.02*        | 1.03**       | 1.03**       | 0.85**       | 5.02*        |
| 3 | (-1,2) | 5.02*        | 5.02*        | 7.76         | 7.76         | 7.76*        | 7.76*        |
| 4 | (-4,-3) | 6.51*        | 6.23         | 6.85*        | 6.85*        | 6.23         | 6.23         |

**Bold** = S@2m success, *Italic* = declared but >2m error

## House02 (source=(0.0, -1.0), config=3,5-1_fast)

| Method | Decl | S@1m | S@2m | Med Err | Mean Err | Best Err |
|--------|------|------|------|---------|----------|----------|
| Random       | 5/5 | 1/5 | 2/5 | 4.49m | 4.45m | 0.76m |
| GreedyMAP    | 5/5 | 1/5 | 2/5 | 4.49m | 4.45m | 0.76m |
| Infotaxis    | 4/5 | 1/5 | 2/5 | 2.52m | 3.08m | 0.76m |
| KLD          | 4/5 | 1/5 | 2/5 | 5.47m | 4.08m | 0.76m |
| DQA_AS       | 5/5 | 1/5 | 2/5 | 4.19m | 3.67m | 0.76m |
| DQA_AS_V2    | 5/5 | 1/5 | 3/5 | 1.67m | 2.45m | 0.76m |

Per-seed errors (censored_error_m):

| Seed | Start | Random       | GreedyMAP    | Infotaxis    | KLD          | DQA_AS       | DQA_AS_V2    |
|------|-------|--------------|--------------|--------------|--------------|--------------|--------------|
| 0 | (0,-5) | 4.49*        | 4.49*        | 2.52*        | 5.47*        | 5.47*        | 4.19*        |
| 1 | (-3,-1) | 7.67*        | 7.67*        | 4.19*        | 6.25*        | 6.25*        | 4.19*        |
| 2 | (0,0) | 0.76**       | 0.76**       | 0.76**       | 0.76**       | 0.76**       | 0.76**       |
| 3 | (-1,2) | 1.67**       | 1.67**       | 1.67**       | 1.67**       | 1.67**       | 1.67**       |
| 4 | (-4,-3) | 7.67*        | 7.67*        | 6.25         | 6.25         | 4.19*        | 1.46**       |

**Bold** = S@2m success, *Italic* = declared but >2m error

## House03 (source=(-0.45, 1.9), config=1-2,5_fast)

| Method | Decl | S@1m | S@2m | Med Err | Mean Err | Best Err |
|--------|------|------|------|---------|----------|----------|
| Random       | 5/5 | 0/5 | 4/5 | 1.81m | 3.99m | 1.81m |
| GreedyMAP    | 5/5 | 0/5 | 4/5 | 1.81m | 3.99m | 1.81m |
| Infotaxis    | 5/5 | 0/5 | 4/5 | 1.81m | 3.99m | 1.81m |
| KLD          | 5/5 | 0/5 | 4/5 | 1.81m | 3.99m | 1.81m |
| DQA_AS       | 5/5 | 0/5 | 4/5 | 1.81m | 3.90m | 1.37m |
| DQA_AS_V2    | 5/5 | 0/5 | 4/5 | 1.81m | 3.90m | 1.37m |

Per-seed errors (censored_error_m):

| Seed | Start | Random       | GreedyMAP    | Infotaxis    | KLD          | DQA_AS       | DQA_AS_V2    |
|------|-------|--------------|--------------|--------------|--------------|--------------|--------------|
| 0 | (0,-5) | 12.72*       | 12.72*       | 12.72*       | 12.72*       | 12.72*       | 12.72*       |
| 1 | (-3,-1) | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.81**       |
| 2 | (0,0) | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.81**       |
| 3 | (-1,2) | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.37**       | 1.37**       |
| 4 | (-4,-3) | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.81**       | 1.81**       |

**Bold** = S@2m success, *Italic* = declared but >2m error

## Cross-House Summary

| Method | H1 Med | H2 Med | H3 Med | H1 S@2m | H2 S@2m | H3 S@2m |
|--------|--------|--------|--------|---------|---------|---------|
| Random       | 5.02 | 4.49 | 1.81 | 2/5 | 2/5 | 4/5 |
| GreedyMAP    | 5.02 | 4.49 | 1.81 | 1/5 | 2/5 | 4/5 |
| Infotaxis    | 2.98 | 2.52 | 1.81 | 1/5 | 2/5 | 4/5 |
| KLD          | 2.98 | 5.47 | 1.81 | 1/5 | 2/5 | 4/5 |
| DQA_AS       | 3.31 | 4.19 | 1.81 | 1/5 | 2/5 | 4/5 |
| DQA_AS_V2    | 5.02 | 1.67 | 1.81 | 0/5 | 3/5 | 4/5 |

## Honest Assessment

1. **House03**: All methods show identical performance (med=1.81m, S@2m=4/5). This indicates the start positions, after BFS correction to nearest free cells, are nearly identical for all methods. The environment may also be simpler (large open space).

2. **House01**: Start positions (0,-5) and (-4,-3) are in walls → corrected by BFS. Seeds 2 (0,0) and 4 (-4,-3) start in genuinely free cells. DQA_AS achieves best_err=0.85m on seed 2 but doesn't consistently outperform baselines.

3. **House02**: DQA_AS_V2 shows best median error (1.67m) and most S@2m successes (3/5). This is the most differentiated house.

4. **DQA_AS crash fix**: The ACCESS_VIOLATION was caused by massive per-step scalar function calls (11,000+ `hit_prob` calls) which likely triggered memory fragmentation. Vectorization reduced this to ~5 batch calls per step.

5. **Limitation**: Start positions mostly in walls, forcing similar corrected starting positions. Future experiments should use verified free-cell starts.
