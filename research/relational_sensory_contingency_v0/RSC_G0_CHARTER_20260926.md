# RSC-G0 — Relational Sensory Contingency Falsification Gate

Date: 2026-09-26

Status: **NEW MAINLINE CANDIDATE DISCOVERY / ZERO-PLUME / PHYSICAL-CONTEXT PREDICTION TEST**

Frozen upstream facts:
- JTD mainline STOP remains final.
- NPG mapping STOP remains final.
- SPX-G0 diagnostic = `SPX_G0_SOURCE_PROBE_INTERACTION`.

This is NOT a JTD rescue and NOT an active-sensing planner.

## 1. Provisional mother-theory family

Biological anchor: sensorimotor contingencies / context-dependent sensory gating.

Core biological idea:
the meaning and utility of sensory input depend on the relation between environmental state and the way sensing is performed, rather than on the sensory signal alone.

Recent anchor:
- Hafed et al., Current Opinion in Neurobiology 2025, `Statistical regularities and the sensory consequences of self-action: A multi-species, multi-modal perspective`, DOI 10.1016/j.conb.2025.103087.
- Waiblinger et al., Nature Neuroscience 2026, `An adaptive and flexible role for primary sensory cortex`.

Domain grounding, NOT mother-theory novelty:
- Stark et al., PRX Life 2026, `Temporal Reformatting of Odor Signals by Flow Environments`, which treats flow as a signal-processing stage between source and sensor.

Active sensing itself is established in robotic olfaction and is NOT claimed as novel.

## 2. Scientific hypothesis

SPX showed that the benefit of temporal cross-block modeling changes when the same raw plume is observed through a different probe layout, and neither source-only nor probe-only rules explain the result.

RSC-G0 tests the stronger, falsifiable hypothesis:

> A target-blind relational descriptor of SOURCE PAIR × PROBE LAYOUT × FLOW × OCCUPANCY can prospectively predict the change in temporal-model utility caused by switching the observation protocol, better than source/probe geometry alone and better than ordinary reference-only model-instability diagnostics.

The object is not `temporal dependence` itself.

The object is the sensing contingency:
`C(a,b,P,W,O)`
for source pair (a,b), probe protocol P, wind W and occupancy O.

## 3. Data scope

House02 only.
Wind only: `3,5-1_slow` W0.

Use:
- the 84 CENTRAL frozen 0.3 m pairs from SPX;
- both exact probe protocols P_G1A and P_E2;
- the same raw cube / reference assets already audited by SPX;
- numeric House02 occupancy grid;
- all 11 audited W0 wind arrays.

OFFSTRIP three pairs are reserved as an external stress test only.

0 new plume.
No H01 DEV.
No House03.
No H02 W2.

## 4. Prediction target

For each CENTRAL pair i and comparator X in {BP,MBD}:

`U_i^X(P) = 20%-trimmed mean over SPX target-level [NLL_X - NLL_FULL] under protocol P`.

Positive means FULL helps.

Primary target:
`E_i^X = U_i^X(P_E2) - U_i^X(P_G1A)`.

`E_i^X` is the robust probe-switch utility effect.

Also report the untrimmed pair-mean probe-switch effect as a mandatory sensitivity analysis.

Do not redefine the target after scoring.

## 5. Target-blind physical contingency descriptor

For a source s and probe p, construct an occupancy-aware shortest free-space path on the frozen House02 2-D occupancy slice corresponding to z=0.20 m.

Use 8-neighbor movement with metric edge cost.

For every one of the 11 W0 wind arrays, bilinearly interpolate horizontal wind on the path.

For each source-probe-wind tuple compute:
- Euclidean distance;
- occupancy-aware geodesic distance;
- direct-line visibility indicator;
- mean wind speed along path;
- mean normalized along-path wind alignment;
- fraction of path with adverse alignment (<0);
- standard deviation of along-path alignment;
- positive-advection travel-time proxy: sum(path_segment_length / max(projected_positive_speed, 0.05 m/s));
- source-local wind speed;
- probe-local wind speed;
- source-vs-probe wind-direction cosine.

If a source/probe cell is not free or no free path exists, record a frozen missing/disconnected indicator rather than silently dropping it.

Across 11 winds, summarize each quantity by:
- mean;
- standard deviation.

For a source pair (a,b) and one probe protocol P:
- compute every source-to-probe quantity for all 30 probes;
- for each scalar quantity form the 30-vector for a and for b;
- summarize pair discrimination by:
  - L1 mean absolute difference;
  - L2 RMS difference;
  - Pearson/cosine similarity where defined;
  - maximum absolute difference;
  - 25/50/75th percentiles of absolute difference.

Also include source-pair midpoint x/y, pair orientation, and protocol probe-cloud centroid/spread.

This frozen vector is `C_i(P)`.

Primary predictor input is the paired contingency change:
`DeltaC_i = C_i(P_E2) - C_i(P_G1A)`.

No concentration, target score, posterior, OAS covariance, PCA output or label may enter `DeltaC`.

## 6. Geometry-only ordinary baseline

Construct `G_i(P)` using exactly the same aggregation framework but ONLY:
- source coordinates;
- probe coordinates;
- Euclidean/geodesic distances;
- occupancy visibility;
- probe-cloud centroid/spread.

No wind quantities.

Primary geometry input:
`DeltaG_i = G_i(P_E2) - G_i(P_G1A)`.

## 7. Reference-only model-instability baseline

Using only the 12 references in each frozen SPX fold/protocol, compute pair/protocol summaries:
- mean ppm;
- zero fraction;
- run-mean coefficient of variation;
- effective number of active probes;
- PCA rank-deficiency count;
- OAS shrinkage coefficient summaries;
- FULL covariance log condition number;
- FULL covariance log determinant.

Average these reference-only diagnostics across four folds.

Primary baseline input is the protocol difference `DeltaR_i`.

No held-out target result may enter DeltaR.

## 8. Frozen predictor family

Use ridge regression only.

For each comparator X separately predict `E_i^X` from:
1. GEOM: DeltaG;
2. REF: DeltaR;
3. PHYS: DeltaC;
4. PHYS+REF: concatenated DeltaC and DeltaR.

All feature standardization and ridge alpha selection are performed inside the training folds only.

Alpha grid fixed before scoring:
`[1e-4,1e-3,1e-2,1e-1,1,10,100,1000]`.

No tree model, neural network, nonlinear kernel or feature search at G0.

## 9. Outer validation

Use the four frozen CENTRAL x macro-bands from NPG/SPX as grouped outer folds.

For each held-out band:
- fit only on the other three bands;
- select alpha by leave-one-training-band-out nested validation;
- predict all pairs in the held-out band.

Every pair receives exactly one prospective out-of-band prediction.

## 10. Frozen gates

### RSC-G0-1 — physical context predicts probe-switch utility
For PHYS, for both BP and MBD:
- Spearman(predicted, observed robust E) > 0;
- 10,000 pair-cluster bootstrap 95% CI lower bound > 0.

### RSC-G0-2 — physical context beats geometry-only
For both BP and MBD:
`mean[(error_GEOM^2 - error_PHYS^2)] > 0`
with 95% pair-bootstrap CI lower bound > 0.

### RSC-G0-3 — physical context is not merely Gaussian-instability diagnosis
For both BP and MBD:
`mean[(error_REF^2 - error_PHYS+REF^2)] > 0`
with 95% bootstrap CI lower bound > 0.

This requires physical contingency to add predictive information beyond reference-only instability diagnostics.

### RSC-G0-4 — sign-change prediction
Define observed sign as sign(E), excluding exact numerical ties |E|<1e-10.

For PHYS+REF:
- balanced accuracy >=0.60 for BP;
- balanced accuracy >=0.60 for MBD;
- not worse than REF alone for either comparator.

### RSC-G0-5 — not one spatial band
PHYS+REF must have lower squared error than REF alone in at least 3/4 held-out macro-bands for both BP and MBD.

## 11. OFFSTRIP stress test

After all CENTRAL fitting/gates are frozen, fit PHYS+REF on all 84 CENTRAL pairs and predict the three OFFSTRIP pair probe-switch effects.

This is descriptive only because n=3.

Report all six comparator×pair predictions and signs.

Do not use OFFSTRIP outcomes to tune the model or gate.

## 12. Decision

PASS:
`RSC_G0_PASS_RELATIONAL_PHYSICAL_CONTEXT_PREDICTS_PROBE_EFFECT`
only if RSC-G0-1..5 all pass.

STOP:
`RSC_G0_STOP_RELATIONAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES`
if any of RSC-G0-1..5 fails.

DATA STOP:
`RSC_G0_DATA_CONTRACT_STOP`
if wind/occupancy/path/probe assets cannot be reproduced from the SPX audited hashes.

## 13. Consequence

PASS does NOT establish a main innovation.

PASS authorizes a fresh confirmation stage for a candidate-conditioned relational inference architecture inspired by biological sensory contingencies.

That later architecture must:
- condition candidate evidence on source–probe–flow context;
- retain the normalized PMFS-style source probability map;
- not require a dense stochastic source bank at deployment;
- not be presented as generic active sensing or sensor placement.

STOP means source×probe interaction remains a historical empirical diagnosis but does not yet yield a predictive physical mechanism; do not build a context-gating neural model.

H01 DEV and House03 stay sealed.