# JTD-E1 — Cross-Environment Fresh Temporal-Dependence Gate

Date: 2026-09-25

Status: **FRESH-TARGET CROSS-ENVIRONMENT MECHANISM GATE**

Upstream:
- `JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL`;
- `JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE` (pooled-covariance bridge only);
- `JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED`, K_min=4.

## 1. Scientific question

Does preserving within-realization temporal joint dependence provide incremental source-location evidence across different transport environments, when the temporal-block marginals are held fixed?

This gate tests the existence of the JTD mechanism across environments.
It does NOT test dense-source localization and does NOT establish the main innovation.

## 2. Environments

Use only the three already-OPEN E2 environments:

E0: House01 / `1,3-2,4_fast`;
E1: House02 / `3,5-1_slow`;
E2: House02 / `4,5-3_slow`.

Do NOT open:
- House01 DEV;
- either House03 environment.

Do NOT use any E4/E5 postmortem data in this gate.

## 3. Frozen references

For each environment/source, the four existing E2 OPEN realizations are frozen as the reference set.

Reference depth:
`K=4`.

These four realizations must not be replaced, augmented, or reselected after target outcomes are generated.

## 4. Fresh targets

Generate exactly two new independent plume realizations for each frozen E1 source in each OPEN environment.

Total:
`3 environments × 6 sources × 2 fresh targets = 36 new plume runs`.

Fresh targets are evaluation-only:
- never enter scaler fitting;
- never enter PCA fitting;
- never enter source means/covariances;
- never enter null construction;
- never alter thresholds.

## 5. Deterministic fresh-target seeds

Environment indices:
- 0 = H01 `1,3-2,4_fast`;
- 1 = H02 `3,5-1_slow`;
- 2 = H02 `4,5-3_slow`.

Source indices use the frozen E1 six-source row order, 0..5.
Target replicate index t=0,1.

Use:
`seed = 2026120000 + 1000*environment_index + 10*source_index + t`.

Save requested and simulator-resolved seeds before scoring.

## 6. Representation

Exactly inherit JTD-G0/B1:
- frozen 10×30 observation contract per House;
- five contiguous two-time blocks;
- training/reference-only StandardScaler per block;
- PCA=2 per block;
- concatenated 10-D feature;
- source-specific mean and source-specific 10×10 OAS covariance;
- normalized posterior over the six frozen candidate sources in that environment.

No pooled covariance.
No alternate block partition.
No normalization search.
No neural model.

## 7. FULL model

For each environment, fit one source-specific Gaussian working likelihood from the four frozen reference realizations/source.

Evaluate the 12 fresh targets (6 sources ×2) without refitting.

## 8. Marginal-preserving SHUFFLED null

For each environment/source:
- anchor block 1 realization identity;
- independently derange blocks 2-5 across the four reference realizations;
- preserve the multiset of reference vectors within every block and source;
- destroy only cross-block realization identity.

Use 200 deterministic null realizations per environment.

Null seeds/derangements are fixed from SHA-256 keys using environment, source, block and null_id and must be frozen before the first fresh target is scored.

For each fresh target, SHUFFLED truth-source NLL is the median over the 200 null fits.

## 9. Primary effect

For every fresh target:
`delta = NLL_SHUFFLED - NLL_FULL`.

Positive delta means preserved temporal dependence provides additional source evidence.

Report per environment and pooled:
- mean delta;
- median delta;
- 20% trimmed mean delta;
- relative mean NLL improvement;
- source-level mean delta;
- positive-target fraction;
- FULL/SHUFFLED truth rank and top-3 as diagnostics;
- largest positive/negative target deltas.

## 10. Frozen GO gate

GO only if all conditions pass:

### E1-G1 — all environments point the same way
Mean delta > 0 independently in all three environments.

### E1-G2 — pooled cluster-robust evidence
Bootstrap the 18 environment×source units (resampling source units within environment, keeping both fresh targets together).
Require pooled mean-delta 95% CI lower bound > 0.

### E1-G3 — breadth
At least 13/18 environment×source units have positive mean delta, and each environment has at least 4/6 positive sources.

### E1-G4 — heavy-tail robustness
Pooled 20% trimmed mean delta > 0.

### E1-G5 — extreme-improvement robustness
After removing the largest positive 5% of target-level deltas (2 of 36 targets), retained pooled mean delta > 0.

### E1-G6 — practical signal
Pooled relative mean truth-source NLL improvement >= 10%.

### E1-G7 — no catastrophic environment reversal
No environment may have FULL mean truth-source NLL more than 10% worse than SHUFFLED.

## 11. Decision

GO:
`JTD_E1_GO_CROSS_ENVIRONMENT_TEMPORAL_DEPENDENCE`.

HOLD:
`JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL`
only if pooled G2/G4/G5 pass but exactly one environment fails G1/G3 and does not show catastrophic reversal.

STOP:
`JTD_E1_STOP_TEMPORAL_DEPENDENCE_NOT_GENERAL`
for all other failures.

## 12. Consequence

GO authorizes JTD-G1A dense-candidate confirmation using the existing House02 dense reference bank before any new dense-source simulation.

HOLD triggers mechanism diagnosis only; no model expansion.

STOP retires JTD as the main-innovation candidate, while preserving G0 as a valid single-environment finding.

No closed loop at E1.