# W0-PRE offline screen using existing 64-run data — 2026-10-07

## Purpose

This is a **zero-new-simulation screening analysis** using the frozen 64-run R0C/R0D/P0 dataset.

Question:

> Under fixed House, gas and source, does switching the existing natural wind context change plume evolution more than within-wind stochastic realization variability?

This is **not** the decisive W0 matched-RMSE causal perturbation test. Existing wind contexts are naturally different and were not constructed to have equal global wind error. Therefore this analysis can only screen whether wind has downstream plume leverage in the existing data.

## Data and frozen interval

Source: `P0_ANALYSIS_EVIDENCE.zip`
- `RUNS_64_FROZEN.json`
- per-run `states/*.npz`
- interval: 100–700 s
- fixed comparisons:
  - House01: WA vs WB, separately for G10/G13 and source0/source1
  - House02: WC vs WD, separately for G10/G13 and source0/source1

No new GADEN runs, no model training, no source-feature selection.

## Distances

For every whole-run pair:

1. **shape-only footprint distance**:
   mean Jensen–Shannon divergence of the normalized 2D concentration footprint at aligned times.

2. **absolute footprint distance**:
   mean symmetric relative L2 difference of the 2D concentration footprint.

3. **plume-weighted wind trajectory distance**:
   RMS 3D wind-vector difference normalized by symmetric RMS speed.

For each fixed House×gas×source:
- between-wind = all 4×4 cross-wind run pairs
- within-wind = all realization pairs inside each wind
- leverage ratio = median(between-wind) / q95(within-wind)

Ratio > 1 means the wind-context difference exceeds the 95th-percentile within-wind realization variation for that diagnostic.

## Results

| House | Gas | Source | Wind | shape ratio | absolute footprint ratio | wind-trajectory ratio |
|---|---:|---:|---|---:|---:|---:|
| H01 | 10 | 0 | A/B | 16.312 | 4.187 | 10.079 |
| H01 | 10 | 1 | A/B | 25.571 | 4.555 | 11.408 |
| H01 | 13 | 0 | A/B | 6.630 | 1.552 | 7.885 |
| H01 | 13 | 1 | A/B | 13.174 | 2.611 | 11.859 |
| H02 | 10 | 0 | C/D | 0.862 | 1.153 | 5.536 |
| H02 | 10 | 1 | C/D | 4.244 | 2.165 | 3.082 |
| H02 | 13 | 0 | C/D | 0.785 | 1.099 | 1.223 |
| H02 | 13 | 1 | C/D | 2.696 | 1.741 | 1.325 |

## Interpretation

### House01
Very strong natural wind→plume leverage:
- shape-only ratios: 6.63–25.57
- absolute footprint ratios: 1.55–4.55
- plume-weighted wind ratios: 7.89–11.86

Thus in House01, switching WA↔WB changes the plume footprint far more than stochastic realization variability for both gases and both sources.

### House02
Mixed and source-dependent:
- absolute footprint ratio is >1 in all four source/gas comparisons (1.10–2.17);
- shape-only ratio is <1 for source0 under both gases (0.862, 0.785), but >1 for source1 (4.244, 2.696);
- the natural WC↔WD wind trajectory difference itself is weaker / noisier than House01 in G13.

This suggests that the downstream consequence of a wind-context change is strongly conditioned by source geometry / local transport path in House02.

## What this does establish

**W0-PRE_SCREEN = POSITIVE BUT NON-CAUSAL**

The existing dataset already shows:
1. wind-context changes can strongly alter plume footprints;
2. the magnitude of that effect is not universal — it is House/source dependent;
3. this is compatible with the candidate claim that transport relevance is spatial/structural rather than captured by one global wind metric.

## What this does NOT establish

It does not prove:
- global wind RMSE ≠ GSL utility;
- two matched-error wind fields cause unequal source-localization damage;
- any proposed task-oriented wind reconstruction improves source posterior;
- a lakeshore-specific mechanism.

Reasons:
1. WA/WB and WC/WD are natural contexts, not matched-RMSE perturbations.
2. source inference was not rerun for all 8 factorial wind×gas cells.
3. realizations are distributionally compared, not identical paired RNG counterfactuals.
4. H01/H02 are not lakeshore geometries.

Therefore the decisive next test remains a controlled simulator intervention, not another offline feature search.

## Next decision

Do **not** use public data for the first mechanism gate.

Next:
- use Codex/VM only for a small **W0 matched-error perturbation experiment** in GADEN;
- keep source/gas/geometry/RNG/route fixed;
- construct equal-global-error but structurally different wind perturbations;
- rerun plume and at least two source-inference baselines.

Public datasets should enter later as external evidence:
- Merced / PG&E / Blackpool: real controlled-release UAV GSL cross-scene validation;
- Lagoon Pingo / WiscoDISCO: shoreline/water-associated meteorology and transport plausibility;
- FSR: main lakeshore benchmark after preflight and controlled CFD/GADEN generation.

