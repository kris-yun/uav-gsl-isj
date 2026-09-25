# JTD-E2 — Equal-Depth K=12 Cross-Environment Confirmation

Date: 2026-09-25

Status: **FRESH-TARGET CROSS-ENVIRONMENT CONFIRMATION AFTER DENSE G1A GO**

Upstream status:
- G0 discovery GO remains;
- B1 established source-specific OAS reliability from K=4, but is not the main gate;
- E1 cross-environment = HOLD;
- G1A dense 168-source assessment = GO, with FULL > BP and FULL > MBD.

## 1. Scientific question

At the same reference depth used by G0/G1A (K=12 per source), does source-specific cross-block temporal dependence provide reproducible probabilistic source evidence across different environments beyond:

1. a deployable BLOCK-PRODUCT model, and
2. MATCHED-BLOCK-DIAG, which preserves the FULL fitted block marginals and removes only cross-block covariance?

This is the required cross-environment confirmation before any mother-theory / representation innovation work.

## 2. Environments

Use only the three already-OPEN E2/E1 environments:

E0: H01 / `1,3-2,4_fast`
E1: H02 / `3,5-1_slow`
E2: H02 / `4,5-3_slow`

Do NOT open H01 DEV.
Do NOT open either House03 environment.
Do NOT generate reserve winds.

## 3. Reference construction

Each environment/source currently has six already-open realizations:
- four original E2 references;
- two E1 fresh targets, now reclassified as historical DEVELOPMENT data for this new stage.

Before any new target is generated, add exactly six new reference realizations/source.

Thus:
`6 existing development + 6 new references = 12 references/source`.

Reference acquisition budget:
`3 environments × 6 sources × 6 = 108 new plume runs`.

The former E1 targets are not treated as fresh evidence in E2 and may never be reported as E2 confirmation targets.

## 4. Fresh confirmation targets

After all 12-reference sets are complete and all FULL/BP/MBD model-building code, parameters, source order, transforms, randomization keys, gates and hashes are frozen, generate exactly four new independent target realizations/source.

Fresh target budget:
`3 × 6 × 4 = 72 new plume runs`.

Total new E2 budget:
`108 + 72 = 180 plume runs`.

Fresh targets are evaluation-only and may not enter any fit, PCA, OAS, source mean, calibration, null or threshold.

## 5. Deterministic seed domains

Use disjoint SHA256-derived seed domains rather than arithmetic aliases.

Reference key tuple:
`JTD_E2|REFERENCE|environment_id|source_id|reference_new_index`.

Target key tuple:
`JTD_E2|TARGET|environment_id|source_id|target_index`.

Map hash digest deterministically to a simulator-valid seed and store both key and resolved seed.

All 180 requested seeds must be frozen before the first new plume run.

## 6. Observation and representation contract

Exactly inherit the per-House E2/E1 observation contracts and G0/G1A feature model:
- frozen 10×30 observation;
- five contiguous two-time blocks;
- StandardScaler fit on 12 references only;
- PCA=2/block fit on pooled references within each environment only;
- concatenated 10-D feature;
- uniform prior over the six frozen sources;
- no target-driven tuning.

## 7. Models

Evaluate in each environment independently.

### FULL
Source-specific 10-D OAS Gaussian from 12 references/source, using the frozen original jitter rule.

### BLOCK-PRODUCT (BP)
Five independently fitted source-specific 2-D OAS Gaussians, same 12 references/source; target score is the sum of block log likelihoods.

### MATCHED-BLOCK-DIAG (MBD)
Take the stabilized FULL covariance and set all cross-block entries to zero.
Use the exact FULL mean.
Do not refit OAS.
Do not add a second jitter.

### DIAG-COV
Report as a secondary diagnostic only.

### SHUFFLED
Run the G1A-style domain-separated destructive null for continuity/diagnostics only.
It is not a primary GO comparator.

## 8. Primary paired effects

For each fresh target:
`delta_BP = NLL_BP - NLL_FULL`
`delta_MBD = NLL_MBD - NLL_FULL`

Positive values favor FULL.

Primary experimental units are the 18 environment×source units, each containing four fresh targets.

## 9. Required outputs

Per target, source-unit, environment and pooled:
- truth-source NLL;
- Brier score;
- truth rank and top-1/top-3;
- posterior mass within 0.5 m and 1.0 m;
- posterior expected source distance;
- MAP distance error;
- nearest-neighbor confusion;
- true-vs-nearest-neighbor log-odds;
- delta_BP and delta_MBD.

Also report:
- 10% / 20% trimmed deltas;
- removal of largest positive 1% / 5% target deltas;
- source breadth;
- fold not applicable: all 12 references are fixed and all 4 targets are genuinely new.

## 10. Cluster bootstrap

Use 10,000 bootstrap resamples of the 18 environment×source units.
Resample source units within each environment, keeping each unit's four fresh targets together.

Compute 95% intervals for pooled mean delta_BP and delta_MBD.

Label them environment-source panel sensitivity intervals; do not overclaim population-level environment generalization.

## 11. Frozen GO gates

GO only if all pass.

### E2-G1 — environment sign consistency
For each of the three environments independently:
- mean delta_BP > 0;
- mean delta_MBD > 0.

### E2-G2 — pooled robust evidence
For both delta_BP and delta_MBD:
- pooled environment-source bootstrap 95% CI lower bound > 0.

### E2-G3 — breadth
For both comparators:
- at least 13/18 environment×source units have positive mean delta;
- every environment has at least 4/6 positive source units.

### E2-G4 — heavy-tail robustness
For both delta_BP and delta_MBD:
- pooled 20% trimmed target mean > 0;
- pooled mean after removing the largest positive 5% targets > 0.

### E2-G5 — probabilistic/spatial utility versus BP
FULL must improve at least two of these three pooled metrics relative to BP:
- mean Brier score;
- mean posterior mass within 1.0 m;
- mean posterior expected source distance;

and none of the three may worsen by more than 5% in any single environment.

### E2-G6 — no catastrophic fresh-target reversal
In no environment may FULL mean truth-source NLL exceed either BP or MBD by more than 10%.

## 12. Decision

GO:
`JTD_E2_GO_EQUAL_DEPTH_CROSS_ENVIRONMENT_CONFIRMED`
only if E2-G1..G6 all pass.

HOLD:
`JTD_E2_HOLD_RESIDUAL_ENVIRONMENT_HETEROGENEITY`
only if E2-G1, G2, G4, G5, G6 pass and the sole failure is E2-G3 breadth.

STOP:
`JTD_E2_STOP_CROSSBLOCK_VALUE_NOT_ENVIRONMENT_GENERAL`
for any failure of E2-G1, G2, G4, G5 or G6.

## 13. Consequence

GO upgrades JTD from 'sole ADVANCE candidate' to:
`JTD_MAIN_MECHANISM_CONFIRMED_FOR_METHOD_DEVELOPMENT`.

GO then authorizes G2 mother-theory + secondary innovation design.

HOLD does not authorize theory/model inflation; diagnose heterogeneity before further simulation.

STOP retires JTD as the paper's main innovation while preserving G0/G1A as valid limited-setting findings.

House01 DEV and House03 stay untouched until after G2 is frozen.