# RPO-G0 — Relational Physical Observability Gate

Date: 2026-09-26

Status: **NEW MAINLINE CANDIDATE / ZERO-PLUME / PHYSICAL-PREDICTION ADMISSION GATE**

Frozen upstream facts:
- JTD mainline STOP remains final.
- NPG mapping STOP remains final.
- SPX diagnostic remains `SPX_G0_SOURCE_PROBE_INTERACTION` with strict exclusion-only interpretation.
- RIA-A0 = `RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED`.

This is NOT a JTD rescue and NOT yet a mother-theory confirmation.

## 1. Scientific target

RIA-A0 established that two reference-only observation-distribution separation quantities track independent held-out bounded discrimination quality:
- D_CNR;
- normalized energy distance D_ED.

RPO-G0 asks:

> Can source-pair × probe-layout × flow × occupancy context, computed without concentration targets or model scores, prospectively predict how those observation-level identifiability quantities change when the probe protocol changes?

The target is NOT FULL-vs-BP/MBD NLL utility.

## 2. Provisional far-domain interpretation

Biological inspiration: sensory/sensorimotor contingencies — sensory usefulness depends on the relation between environmental state and how sensing samples that state.

Physics grounding: turbulent flow acts as a transformation between source and sensor and can reformat temporal odor signals.

These are motivation only. RPO-G0 must first establish a predictive physical relation before any theory claim.

## 3. Data scope

House02 only.
Wind only: `3,5-1_slow` W0.

Primary fitting/gating panel:
- 84 frozen CENTRAL 0.3 m source pairs;
- exact P_G1A and P_E2 30-probe protocols;
- numeric House02 occupancy grid;
- all 11 audited W0 wind arrays;
- source coordinates and probe coordinates;
- RIA-A0 frozen D_CNR and D_ED targets.

OFFSTRIP 3 source pairs:
- descriptive stress test only after all gates are frozen.

0 new plume.
No H01 DEV.
No House03.
No H02 W2.

## 4. Prediction targets

For every CENTRAL pair i:

`Y_CNR(i) = D_CNR_i(P_E2) - D_CNR_i(P_G1A)`

`Y_ED(i) = D_ED_i(P_E2) - D_ED_i(P_G1A)`.

These values are imported from the frozen RIA-A0 result and must not be recomputed with a changed formula.

Both targets must be predicted successfully.

## 5. Physical relational descriptor

For each source s, probe p, and each of the 11 W0 wind arrays, use the z=0.20 m horizontal slice.

Build an 8-neighbor occupancy-aware shortest path from source to probe using metric edge length.

Along each path compute, with bilinear wind interpolation:
- Euclidean source-probe distance;
- occupancy-aware geodesic distance;
- line-of-sight indicator;
- mean wind speed;
- mean signed along-path wind projection;
- mean positive along-path wind projection;
- fraction of path with negative along-path projection;
- RMS cross-wind component;
- standard deviation of signed along-path projection;
- positive-advection travel-time proxy: sum(ds/max(v_parallel_positive,0.05 m/s));
- source-local wind speed;
- probe-local wind speed;
- cosine between source-local and probe-local wind directions.

If a path is disconnected, retain a frozen disconnected flag and finite sentinel only after the sentinel convention is frozen in the pre-run lock.

Across the 11 winds, summarize every wind-dependent scalar by mean and standard deviation.

## 6. Pair × protocol observability features

For a pair (a,b) and one probe protocol P:

For every scalar source-to-probe descriptor h, form 30-vectors:
`h_a(P)` and `h_b(P)`.

Summarize their difference using exactly:
- mean absolute difference;
- RMS difference;
- maximum absolute difference;
- median absolute difference;
- cosine similarity where defined.

Also include:
- pair midpoint x,y;
- pair orientation;
- protocol probe-cloud centroid x,y;
- protocol probe-cloud x/y spread;
- fraction of probes with line-of-sight disagreement between a and b.

Call the resulting vector `C_i(P)`.

Primary physical input:
`DeltaC_i = C_i(P_E2) - C_i(P_G1A)`.

No concentration, D_CNR/D_ED component, heldout score, posterior, PCA, OAS or model output may enter DeltaC.

## 7. Ordinary baselines

### GEOM
Same aggregation but only:
- source/probe coordinates;
- Euclidean distance;
- geodesic distance;
- line-of-sight;
- probe-cloud centroid/spread.

Input `DeltaG_i`.

### SOURCE-ONLY
Pair midpoint, orientation, x/y coordinates and source separation only.

### SIMPLE-WIND
Frozen low-capacity features:
- direct source-to-probe unit-vector alignment with source-local wind;
- source-local wind speed;
- Euclidean distance;
aggregated using mean and RMS source-pair difference across probes and winds.

This checks whether the full path/occupancy descriptor adds value beyond a simple local-wind rule.

## 8. Predictor family

Ridge regression only.

Predict Y_CNR and Y_ED separately from:
- SOURCE-ONLY;
- GEOM;
- SIMPLE-WIND;
- PHYS = DeltaC.

Feature standardization and ridge alpha are fit on training bands only.

Frozen alpha grid:
`[1e-4,1e-3,1e-2,1e-1,1,10,100,1000]`.

No feature selection.
No trees.
No kernels.
No neural networks.

## 9. Outer validation

Use the same four frozen CENTRAL x macro-bands as grouped outer folds.

For each held-out band:
- train on the other 3 bands only;
- choose ridge alpha by leave-one-training-band-out nested validation;
- predict every pair in the held-out band.

Every CENTRAL pair receives exactly one out-of-band prediction.

## 10. Frozen admission gates

### G0-1 — physical prediction exists
For PHYS, for BOTH Y_CNR and Y_ED:
- out-of-band Spearman >= 0.30;
- 10,000 pair-bootstrap 95% CI lower bound > 0.

### G0-2 — physical relation beats geometry
For BOTH targets:
`mean[(err_GEOM^2 - err_PHYS^2)] > 0`
with pair-bootstrap 95% CI lower bound > 0.

### G0-3 — path/flow relation beats simple local-wind heuristic
For BOTH targets:
`mean[(err_SIMPLE_WIND^2 - err_PHYS^2)] > 0`
with 95% bootstrap CI lower bound > 0.

### G0-4 — sign prediction
For BOTH targets:
- PHYS balanced accuracy >= 0.60 on sign(Y);
- PHYS balanced accuracy >= GEOM;
- PHYS balanced accuracy >= SIMPLE-WIND.

Exact numerical ties |Y|<1e-10 are excluded from sign scoring.

### G0-5 — spatial robustness
For BOTH targets:
- PHYS squared-error advantage over GEOM is positive in at least 3 of 4 held-out macro-bands;
- PHYS squared-error advantage over SIMPLE-WIND is positive in at least 3 of 4 bands.

## 11. OFFSTRIP stress test

Only after the CENTRAL decision is frozen:
- fit PHYS on all 84 CENTRAL pairs;
- predict Y_CNR and Y_ED for the 3 OFFSTRIP pairs;
- report predicted and observed values/signs.

Descriptive only; n=3 cannot alter the decision.

## 12. Decision

PASS:
`RPO_G0_PASS_PHYSICAL_RELATIONAL_CONTEXT_PREDICTS_IDENTIFIABILITY`
only if G0-1..G0-5 all pass.

STOP:
`RPO_G0_STOP_PHYSICAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES`
if any gate fails.

DATA STOP:
`RPO_G0_DATA_CONTRACT_STOP`
if SPX-audited wind/occupancy/probe/source assets cannot be reproduced exactly.

## 13. Consequence

PASS does NOT establish the final main innovation.

PASS authorizes one fresh-confirmation design for a NEW relational observation model whose scientific target is source identifiability, not estimator NLL gain.

Only after PASS may the project formally map the mechanism to a far-domain mother theory such as biological sensory contingencies/context-dependent sensory gating.

Any later method must:
- condition candidate evidence on source–sensor–flow context;
- retain a normalized PMFS-style source probability map;
- not require the target environment's dense stochastic source bank at deployment;
- distinguish physical identifiability from estimator calibration.

STOP means the RIA target is real, but current source–probe–flow physics does not prospectively explain it; do not build a context-gating network.