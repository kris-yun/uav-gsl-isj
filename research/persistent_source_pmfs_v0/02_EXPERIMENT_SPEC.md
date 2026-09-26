# Experiment specification — R1 persistent-source ablation

## Inputs

Use only the already frozen House01/seed0 R1 source-blind inputs:

- `measurement_events.csv`
- `measured_map_at_update.csv`
- `frozen_candidate_geometry.csv`
- `wind_source_update.csv`

Truth (`source_x=-0.40`, `source_y=-2.90`, truth leaf `quadtree_23_14_1_3`) MUST NOT be read until source-blind scores are written and hashed.

The canonical prior truth-evaluation file may be used only after freeze:
`evidence/native_pmfs_baseline_recovery_v1/R1_R2_source_corrected_House01_seed0_20260923/R1_three_arm_truth_evaluation.json`
on branch `research/native-pmfs-baseline-recovery-v1`.

## Frozen PMFS observation/forward settings

Use the official R1 C-arm settings:

- ground-truth `wind_source_update.csv`
- `sourceDiscriminationPower=0.3`
- `iterationsToRecord=200`
- `deltaTime=0.1`
- `noiseSTDev=0.5`
- `blurSigmaX=blurSigmaY=1.5`
- hit prior `0.3`
- maxUpdatesPerStop `5`
- kernelSigma `1.5`
- kernelStretchConstant `1.5`
- confidenceMeasurementWeight `1.0`
- confidenceSigmaSpatial `1.0`
- localEstimationWindowSize `2`

The reconstructed measured hit map must match the frozen R1 map to <=1e-6 in log-odds and confidence before scoring.

## Three source-blind arms

Use K=8 transport replicas and M=8 persistent source samples.

All transport replicas use the same candidate-independent EventKey:
`(global_seed=20260926, source_update_id=1, replica_id=r, transport_substream=0x50535452414E5350)`.

Source draws use a *different* substream so source and transport randomness cannot share the same keyed bits.

### R — resampled-source control

Preserve the Native geometric semantics: within a forward realization, each emitted filament redraws a point uniformly in the leaf.

Use a separate source RNG:
`(20260926, 1, r, 0x52534D504C535243)`.

Primary R score for a candidate is the arithmetic mean of the K likelihood-like PMFS scores.

### C — fixed-center diagnostic

Hold the exported leaf center fixed through each complete forward realization. Average the K scores.

This is a diagnostic only; it is not the proposed marginal method.

### P — persistent-source marginal

For each source sample `m=0..7`, draw one pair of common uniform quantiles from:
`(20260926, 1, m, 0x5052535352434452)`.

Map those same quantiles into each leaf rectangle. Thus every candidate gets the same relative within-leaf source samples.

For each fixed source point `S_m`, run K transport realizations and keep `S_m` fixed for the whole realization.

Candidate evidence:

`L_P(leaf) = mean_m mean_r L(Y | S_m, Z_r, leaf)`

This is the direct Monte-Carlo approximation of a persistent unknown source marginalized outside the nonlinear observation score.

## Required outputs

Before truth is opened:
- `candidate_summary.csv`
- `scores_long.csv`
- `persistent_source_samples.csv`
- `source_blind_audit.txt`
- `SCORES_SHA256.txt`

After freeze:
- `truth_evaluation.json`
- `DECISION.md`

Report:
- truth leaf rank for R/C/P;
- rank change P-R;
- truth leaf score R/C/P;
- top-1 candidate center and distance to truth R/C/P;
- Spearman rank correlation R vs P;
- median and maximum absolute candidate-rank displacement;
- score/rank changes grouped by leaf area;
- the five 1×1 leaves as a diagnostic for sub-cell persistence effects.

## Development interpretation

Do not call a main innovation PASS.

- `MECHANISM_SIGNAL_POSITIVE`: P improves truth-leaf rank versus R and does not worsen top-1 spatial error.
- `MECHANISM_SIGNAL_STRONG`: additionally improves truth-leaf rank by >=10 positions.
- `MECHANISM_NULL_OR_ADVERSE`: no truth-rank improvement, or top-1 spatial error worsens materially.

Always report raw values even if the label is NULL/ADVERSE.

No new plume, no GADEN, no House03, no network training, no ROS closed loop.
