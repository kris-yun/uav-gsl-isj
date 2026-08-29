# CODEX — PF-DEI Direct Set-NRE V3 spatial-structure audit

Date: 2026-08-30
Branch: `research/pf-dei-direct-set-nre-v3-spatial-audit-20260830`
Parent: `research/pf-dei-direct-set-nre-v2-20260829`
Execution: EXISTING FROZEN OUTPUTS / NO TRAINING / NO GADEN / NO CLOSED LOOP

## Objective

Keep the frozen V2 verdict `PF_DEI_DIRECT_SET_NRE_V2_NO_GO` unchanged. This stage asks only whether V2's learned ranking signal is **spatially coherent and physically localizable** even though its exact-carrier Top-10 gate failed.

Do not use this audit to post-hoc retune V2.

## Hard prohibitions

Do not retrain any network, alter the V2 checkpoint, change architecture/loss/prior/temperature/blend, generate GADEN data, run H02/H03, run ROS closed loop, or feed the regional summary into PMFS/planner. If a frozen input is missing, stop with `PF_DEI_V3_SPATIAL_AUDIT_INPUT_MISSING`.

## Expected V3 diff

Exactly these **four** files may differ from the V2 parent:

1. `docs/CODEX_PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_AUDIT_20260830.md`
2. `docs/PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_DERIVATION_20260830.md`
3. `experiments/cg_pc_ctt/evaluate_pf_dei_direct_set_nre_v3_spatial_structure.py`
4. `experiments/cg_pc_ctt/selftest_pf_dei_direct_set_nre_v3_spatial_structure.py`

All V2 implementation/training/evaluation files must remain byte-identical.

## 0. Pull and verify identity

```bash
git fetch origin
git checkout research/pf-dei-direct-set-nre-v3-spatial-audit-20260830
git status --short
git rev-parse HEAD
git diff --name-only research/pf-dei-direct-set-nre-v2-20260829...HEAD
```

Record the frozen V2 checkpoint SHA-256 and reject any newly trained checkpoint.

## 1. Static checks and self-test

From `experiments/cg_pc_ctt`:

```bash
python3 -m py_compile \
  pf_dei_direct_set_nre_v2.py \
  evaluate_pf_dei_direct_set_nre_v3_spatial_structure.py \
  selftest_pf_dei_direct_set_nre_v3_spatial_structure.py
python3 selftest_pf_dei_direct_set_nre_v3_spatial_structure.py
```

Required terminal line:

```text
PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_STRUCTURE_SELFTEST_PASS
```

The self-test checks geometry-only regional aggregation, carrier-permutation invariance, neutral prior/posterior Bayes factor, and symmetric self-inclusive adjacency.

## 2. Reuse frozen V2 artifacts only

Locate, do not regenerate:

- dataset root containing `H01_carriers.json`;
- the PMFS posterior NPZ used by frozen V2 historical evaluation;
- frozen `historical_evaluation.json`;
- frozen `historical_direct_logits.npy`.

`historical_evaluation.json` must contain:

```text
contract = PF_DEI_DIRECT_SET_NRE_V2_H01_HISTORICAL_HOLDOUT_EVAL
cases = 50
```

The V3 evaluator reconstructs each V2 posterior and requires every exact true-carrier rank to match the frozen V2 result. A mismatch is a provenance failure.

## 3. Run exactly one spatial audit

```bash
python3 experiments/cg_pc_ctt/evaluate_pf_dei_direct_set_nre_v3_spatial_structure.py \
  --dataset-root <FROZEN_V2_DATASET_ROOT> \
  --pmfs-posteriors <FROZEN_V2_PMFS_POSTERIOR_NPZ> \
  --historical-evaluation <FROZEN_V2_HISTORICAL_EVALUATION_JSON> \
  --historical-logits <FROZEN_V2_HISTORICAL_DIRECT_LOGITS_NPY> \
  --out <NEW_ISOLATED_V3_AUDIT_DIR>
```

Do not rerun with changed settings based on the answer.

Expected outputs:

- `spatial_structure_cases.csv`
- `spatial_structure_audit.json`

## 4. Required metrics

Report overall and separately for source updates 1..5:

- exact true-carrier rank and frozen Top-1/5/10 reference;
- PMFS vs Direct posterior-mean error;
- PMFS vs Direct posterior expected radial error;
- PMFS vs Direct MAP error;
- PMFS vs Direct minimum truth distance among Top-1/5/10;
- PMFS vs Direct posterior mass within fixed descriptive radii 0.5/1.0/2.0 m;
- geometry-adaptive true-neighborhood posterior mass, geometry-prior mass, and local log Bayes factor;
- count of cases with true-neighborhood `log B > 0` and median `log B`;
- truth-blind regional mass-mode centroid error and regional-Bayes-factor-mode centroid error.

The fixed radii are descriptive only and may not be selected/tuned.

## 5. Frozen geometry-only regional rule

For carrier centroid `x_i`, width `w_i`, height `h_i`:

`a_i = 0.5*sqrt(w_i^2 + h_i^2)`

`A_ij = 1[||x_i-x_j|| <= a_i+a_j]`

For frozen posterior `p` and geometry prior `q0`:

`M_i = sum_j A_ij p_j`

`M_i^0 = sum_j A_ij q0_j`

`log B_i = log(M_i+eps) - log(M_i^0+eps)`

Truth-blind summaries:

- mass region mode `i_M = argmax M_i`;
- evidence region mode `i_B = argmax log B_i`;
- each reported location is the posterior-weighted centroid inside that selected neighborhood.

These are diagnostic decision summaries, not a new posterior and not a planner input.

## 6. Mechanistic classification only

Do **not** invent a new numerical GO threshold from H01.

Use one of:

- `PF_DEI_V3_SPATIALLY_COHERENT_SIGNAL`: several independent spatial diagnostics improve consistently; this authorizes only derivation of a new preregistered region/continuous-source method.
- `PF_DEI_V3_RANK_SIGNAL_NOT_SPATIALLY_ACTIONABLE`: exact rank improves but radial error/local mass/Top-K distance/regional mode do not; stop the NRE-sharpening route rather than increasing training capacity.
- `PF_DEI_V3_MIXED_SPATIAL_SIGNAL`: gains are update- or seed-specific; report exactly when the signal becomes available and require the next model to explain that condition.

None of these classifications authorizes closed loop.

## 7. Evidence package

Create an isolated directory containing:

- `REPORT.md` with complete tables and interpretation;
- `VERDICT.txt` with exactly one classification string;
- `spatial_structure_cases.csv`;
- `spatial_structure_audit.json`;
- `GIT_IDENTITY.txt`;
- SHA-256 manifest of all evidence files.

Do not commit H01 outcome files back to the source branch.

## STOP

After this one audit, stop. Do not train V3, smooth the PMFS posterior, or start closed loop. The next design decision must be made from the spatial mechanism result.
