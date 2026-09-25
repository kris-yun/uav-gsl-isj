# LSC Cross-Wind D0 Protocol — 128 New Runs

Date: 2026-09-25

Status: **FROZEN MECHANISM CONFIRMATION DESIGN; NO PMFS CLOSED LOOP**

## 1. Scientific question

Does the already observed local stochastic source-distinguishability mechanism survive a physical wind/operator change under the same House geometry and observation protocol?

This experiment does **not** test a new localization algorithm.

It tests only the mechanism:

> source-pair stochastic distinguishability estimated from one independent plume half should predict source-pair confusion on the opposite fresh plume half.

If this relation does not survive wind changes, LSC is downgraded and must not be promoted as the paper main innovation.

## 2. Fixed environment

House: **House02**

Occupancy SHA256:

`9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`

Existing anchor wind:

- W0 = `3,5-1_slow`
- reuse D1R only; no new W0 generation.

Two new physical canonical winds:

- W1 = `3,5-1_fast`
- W2 = `4,5-3_slow`

Both must match the frozen canonical inventory:

`evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json`

Inventory SHA256:

`dec3b877783b606fc3bd1fceaa06acb32e6616b2cae2d2f2e2f7f52fc4ed71fb`

No rotated, scaled, synthetic or interpolated wind is allowed.

## 3. Geometry-only source panel

The source panel was chosen before any W1/W2 plume generation by a deterministic central 2×4 rectangular geometry rule.

| source_id | pmfs_i | pmfs_j | x_m | y_m |
|---|---:|---:|---:|---:|
| pmfs_9_15 | 9 | 15 | -2.54273 | -2.80088 |
| pmfs_10_15 | 10 | 15 | -2.24273 | -2.80088 |
| pmfs_11_15 | 11 | 15 | -1.94273 | -2.80088 |
| pmfs_12_15 | 12 | 15 | -1.64273 | -2.80088 |
| pmfs_9_16 | 9 | 16 | -2.54273 | -2.50088 |
| pmfs_10_16 | 10 | 16 | -2.24273 | -2.50088 |
| pmfs_11_16 | 11 | 16 | -1.94273 | -2.50088 |
| pmfs_12_16 | 12 | 16 | -1.64273 | -2.50088 |

This panel contains exactly ten frozen four-neighbor edges.

No source may be replaced because of low concentration, poor ranking, excessive stochasticity or inconvenient results.

## 4. New simulation budget

For each of W1 and W2:

- 8 sources;
- 8 independent plume realizations/source.

Thus:

[
2	imes 8	imes 8 = 128
]

new GADEN runs.

No additional source, seed or wind may be added after outcomes are inspected.

## 5. Seed namespace

Use exactly:

- W1 reps: `2026110001` through `2026110064`;
- W2 reps: `2026110065` through `2026110128`.

Map in source-table order, then replicate 1..8.

Before execution Codex must audit the repository seed registry/evidence tree for collisions.

If any collision exists, STOP before generation and report it; do not silently choose a replacement range.

## 6. Observation contract

Use exactly the D1R/Gate1A measurement operator:

- simulator iteration indices: 100,150,200,250,300,350,400,450,500,550;
- 30 frozen probes;
- average-pool 2×2 then sample;
- source z = 0.20 m;
- output tensor per wind: `[8,8,10,30]`;
- retain raw ppm;
- binary encounter support may be derived, never substituted for raw data.

Reuse the same extractor/binary hashes as D1R unless an integrity mismatch is detected.

## 7. Primary split

For every wind independently:

Direction A:
- train/reference reps 1..4;
- fresh reps 5..8.

Direction B:
- train/reference reps 5..8;
- fresh reps 1..4.

The two directions are symmetric robustness views, not independent experiments.

## 8. Primary mechanism statistic

For each of the ten frozen neighbor edges:

1. standardize 300-D `log(1+ppm)` using only the four training realizations from the eight panel sources;
2. compute the nonparametric multivariate energy distance between the two source distributions using the training four realizations/source;
3. fit the ordinary training-half nearest-centroid two-source classifier;
4. measure binary confusion error on the opposite four fresh realizations/source.

The primary mechanism relation is:

[
ho_w^{(d)}
=
operatorname{Spearman}
(
	ext{train energy distance},
	ext{fresh binary confusion error}
).
]

Expected sign: negative.

## 9. Primary ADVANCE gate

The mechanism advances cross-wind only if all are satisfied:

### G1 — pooled cross-wind prediction

Pool the 20 edge×wind observations from the two new winds.

Require in **both** split directions:

[
ho_{m pooled}le -0.50.
]

### G2 — no sign reversal by wind

For each of W1 and W2, in both split directions:

[
ho_w < 0.
]

No individual new wind may show a positive distinguishability-vs-confusion relation in either direction.

### G3 — hard/easy edge ordering

Within each new wind and each direction:

- rank the ten edges by training energy distance;
- define the three smallest-distance edges as HARD;
- define the three largest-distance edges as EASY.

Require:

[
overline e_{m HARD}
-
overline e_{m EASY}
ge 0.10
]

for at least 3 of the 4 wind×direction cells, and the remaining cell must have nonnegative difference.

### G4 — distinguishability reproducibility

Pool the 20 edge×wind units and compare energy-distance estimates from reps1..4 vs reps5..8.

Require:

[
ho_{m split}ge 0.50.
]

### G5 — W0 anchor integrity

On the same geometry-only 8-source panel in existing D1R/W0:

- first4/second4 energy-distance ordering must reproduce the pre-run anchor approximately;
- if the frozen analyzer cannot reproduce the stored W0 sanity values within numeric tolerance, STOP as an analysis-integrity failure before interpreting W1/W2.

Pre-run W0 sanity values:

- energy-distance split stability Spearman ≈ 0.697;
- direction-A energy-distance vs fresh confusion Spearman ≈ -0.369;
- direction-B ≈ -0.557.

These W0 values are development/integrity anchors only and are not counted toward the new-wind PASS gate.

## 10. Secondary corroboration

Compute the previously frozen one-dimensional plug-in Bhattacharyya confusion proxy on each edge.

Report:

- proxy vs fresh binary error Spearman;
- split-to-split proxy stability.

No secondary metric may rescue a failure of G1–G4.

## 11. Decision

PASS:

`LSC_CROSSWIND_D0_PASS_MECHANISM_GENERALIZES`

Only means:

> local stochastic source distinguishability predicts fresh source-pair confusion under two additional House02 physical wind operators.

It does not prove cross-House, a new algorithm, or closed-loop benefit.

STOP:

`LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY`

If any primary gate fails.

No HOLD by adding more seeds after reveal.

A technical integrity failure before valid new-wind scoring is not a scientific STOP; it must be repaired without inspecting plume outcomes.

## 12. After PASS

Only after PASS may the primary thread:

1. promote LSC as the main scientific mechanism candidate;
2. design one cross-House mechanism gate;
3. decide whether a distinguishability-aware PMFS method is worth closed-loop testing.

No closed-loop PMFS execution is authorized by this file.
