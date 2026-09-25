# YMPO D1 — Locked Cross-Wind Draft (96 New GADEN Runs)

Date: 2026-09-25

Status: **DRAFT/FROZEN FOR RED-TEAM — DO NOT EXECUTE YET**

## 1. Single scientific question

Does the D0 advantage of a protocol-conditioned spatial local-measure plume representation over point-valued / ordinary uncertainty representations survive a physically different canonical wind operator?

Target physical wind:

**House02 / 4,5-3_fast**

Compared with D1R W2 = House02 / 3,5-1_slow:
- W2 speed-weighted mean direction: -120.900 deg;
- target: +164.980 deg;
- shortest directional difference: about 74 deg;
- W2 median speed: 0.014586 m/s;
- target median speed: 0.004876 m/s;
- W2 p95 speed: 0.146744 m/s;
- target p95 speed: 0.204021 m/s.

This changes the canonical flow configuration, not merely fast/slow scaling of the same configuration.

## 2. Candidate support

Final posterior support remains the complete frozen 168-cell D1R panel.

The experiment generates plume data at only 48 geometry-predeclared source cells.

## 3. Geometry-only source selection

Anchor i values:

  {2,5,8,11,14,17,20,23}

Anchor j values:

  {13,15,17}

giving 24 anchor source cells.

For every anchor (i,j), the locked query source is its 0.30m east neighbor:

  (i+1,j).

Thus there are 24 anchors +24 locked query sources =48 generated source locations.

All are members of the already verified complete 168-cell House02 free-source rectangle.

No plume, source rank, LSC score, stochasticity metric or D1R outcome is used for source selection.

## 4. New-run budget

Exactly two new plume realizations per generated source:

  48 sources x2 seeds = **96 new GADEN runs**.

Proposed deterministic seed namespace:

  seed(k,r) = 2026112000 + 2*k + r,

where k=0..47 follows lexicographic (anchor pair, anchor-before-query) order and r in {1,2}.

Exact mapping must be emitted before execution.

## 5. Observation contract

Reuse exactly:
- same House02 occupancy;
- same GADEN binary/extractor hashes;
- same source z=0.20m;
- same 30 probe operator and coordinates;
- same 2x2 pooling;
- same iteration indices [100,150,200,250,300,350,400,450,500,550];
- preserve raw concentration so all baseline representations are derivable.

No observation-protocol tuning on the target wind.

## 6. Development / target firewall

### Anchor data

Both target-wind realizations at the 24 anchor sources may be used only to construct source->representation interpolation under already frozen W2 hyperparameters.

### Query data

Both realizations at the 24 query sources are locked targets.

No query plume value may be used for:
- representation choice;
- KRR length scale/ridge;
- covariance/metric estimation;
- calibration temperature;
- feature selection;
- threshold selection.

All such choices are frozen from W2 before target generation.

## 7. Frozen representation families

All models use the same source-coordinate interpolation machinery and complete 168-cell posterior support.

### B0 — point-valued mean field
Per probe: mean log(1+ppm) over the frozen ten-snapshot protocol.

### B1 — ordinary mean+variance map
Per probe: mean and standard deviation.

### B2 — full ordered raw field
All ordered 10x30 log(1+ppm) samples.

### B3 — mean+std+hit/intermittency
Strong compact ordinary stochastic baseline.

### C — YMPO empirical-measure field
Per probe:
- mean;
- std;
- q25;
- q50;
- q75;
- max;
- zero/nonzero hit fraction.

This hand summary is deliberately the primary candidate because it is stronger than KME, histograms, direct Wasserstein/Hellinger, and quantile-function PCA on W2.

No neural measure encoder is allowed in D1.

## 8. W2-frozen modeling

Before any target-wind plume generation, freeze per representation from D1R only:
- feature standardization;
- covariance/whitening rule;
- source-coordinate KRR length scale;
- KRR ridge;
- posterior temperature;
- probability floor;
- scoring code.

Target-wind data cannot retune them.

## 9. Primary endpoint

For target query source s and realization r:

  delta_b(s,r) = log2 q_YMPO(s|y_sr) - log2 q_b(s|y_sr)

for each baseline b.

YMPO D1 ADVANCE requires:

1. mean delta versus every registered baseline > 0;
2. versus the strongest W2 ordinary baseline, mean delta >= log2(1.15) ~= 0.2016 bit/target;
3. aggregate gain is positive separately on target seed-1 and target seed-2;
4. query-source median truth rank is no worse than the strongest ordinary baseline;
5. no probability-map integrity/calibration failure.

This is a mechanism/representation gate, not final journal confirmation.

## 10. Secondary mechanism diagnostics

Report:
- top1/top3;
- MAP error;
- local anchor-query pair error;
- predicted vs observed anchor/query distributional separation;
- whether local stochastic distinguishability ordering is preserved.

Field/feature reconstruction error is secondary and cannot rescue proper-score failure.

## 11. Decisions

ADVANCE:
`YMPO_D1_ADVANCE_CROSS_WIND_MEASURE_FIELD`

HOLD:
`YMPO_D1_HOLD_W2_SPECIFIC_OR_UNDERPOWERED`

STOP:
`YMPO_D1_STOP_MEASURE_FIELD_NOT_CROSS_WIND`

No closed loop and no cross-House acquisition before ADVANCE.

## 12. Execution status

**DO NOT RUN.**

Wait for independent Pro theory/prior-art/design red-team and primary-thread approval.