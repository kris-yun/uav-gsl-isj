# CODEX — PF-DEI Direct Set-NRE V3 spatial-structure audit

Date: 2026-08-30
Branch: `research/pf-dei-direct-set-nre-v3-spatial-audit-20260830`
Parent branch: `research/pf-dei-direct-set-nre-v2-20260829`
Execution class: EXISTING FROZEN OUTPUTS / NO TRAINING / NO GADEN / NO CLOSED LOOP

## Objective

The frozen Direct Set-NRE V2 result is still `PF_DEI_DIRECT_SET_NRE_V2_NO_GO`. Do not change that verdict.

This task answers one new question only:

> The V2 network improved all 50 true-carrier ranks and strongly improved centroid expected error, but exact Top-10 remained weak. Is the learned information spatially coherent around the physical source, or is it merely a non-actionable carrier-rank reshuffle?

The answer determines the next scientific design. It must not be used to post-hoc retune V2.

## Hard prohibitions

Do NOT:

- retrain any network;
- change the frozen V2 checkpoint;
- change NRE architecture, optimizer, source proposal, loss, temperature, blend, or prior;
- run GADEN;
- generate a new physical bank;
- run H02/H03;
- run ROS closed loop;
- feed the new regional summary into PMFS or planner;
- tune any distance radius from H01 outcomes;
- reinterpret this audit as V2 passing its old gate.

If any required frozen artifact is missing, stop with `PF_DEI_V3_SPATIAL_AUDIT_INPUT_MISSING` rather than regenerating/retraining.

## Files added by this branch

- `docs/PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_DERIVATION_20260830.md`
- `experiments/cg_pc_ctt/evaluate_pf_dei_direct_set_nre_v3_spatial_structure.py`
- `experiments/cg_pc_ctt/selftest_pf_dei_direct_set_nre_v3_spatial_structure.py`

The parent V2 files are frozen and must remain byte-identical.

## Step 0 — identity and diff

Run:

```bash
git fetch origin
git checkout research/pf-dei-direct-set-nre-v3-spatial-audit-20260830
git status --short
git rev-parse HEAD
git diff --stat research/pf-dei-direct-set-nre-v2-20260829...HEAD
git diff --name-only research/pf-dei-direct-set-nre-v2-20260829...HEAD
```

Expected: only the three V3 files above differ from the frozen V2 parent.

Also record SHA-256 for the frozen V2 checkpoint and confirm it is the previously frozen checkpoint. Do not accept a newly trained checkpoint.

## Step 1 — static checks and deterministic self-test

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

The self-test proves:

1. a coherent local cluster can beat an isolated point MAP in regional mass without truth;
2. carrier permutation leaves the physical regional solution unchanged;
3. prior==posterior gives zero local log Bayes factor;
4. geometry graph is symmetric and self-inclusive.

## Step 2 — locate frozen V2 artifacts only

Locate the existing V2 evidence directory. Required inputs are:

- frozen dataset root containing `H01_carriers.json`;
- frozen PMFS posterior NPZ used by the V2 historical evaluator;
- frozen V2 `historical_evaluation.json`;
- frozen V2 `historical_direct_logits.npy`.

Use `find`/manifest inspection only. Do not regenerate them.

The historical evaluation must declare:

```text
contract = PF_DEI_DIRECT_SET_NRE_V2_H01_HISTORICAL_HOLDOUT_EVAL
cases = 50
```

The V3 script reconstructs each frozen direct posterior and requires the exact true-carrier rank to match the V2 JSON case-by-case. Any mismatch is a provenance failure.

## Step 3 — execute one frozen spatial audit

Run exactly once after the paths are identified:

```bash
python3 experiments/cg_pc_ctt/evaluate_pf_dei_direct_set_nre_v3_spatial_structure.py \
  --dataset-root <FROZEN_V2_DATASET_ROOT> \
  --pmfs-posteriors <FROZEN_V2_PMFS_POSTERIOR_NPZ> \
  --historical-evaluation <FROZEN_V2_HISTORICAL_EVALUATION_JSON> \
  --historical-logits <FROZEN_V2_HISTORICAL_DIRECT_LOGITS_NPY> \
  --out <NEW_ISOLATED_V3_AUDIT_DIR>
```

Do not rerun with altered settings based on the result.

Expected outputs:

- `spatial_structure_cases.csv`
- `spatial_structure_audit.json`

## Step 4 — report the mechanism, not just one scalar

Report all of the following for overall 50 cases and updates 1..5 separately:

### A. Exact discrete identification

- Direct exact true-carrier rank distribution;
- frozen V2 Top-1/5/10 for reference only.

### B. Spatial localization risk

- PMFS vs Direct posterior-mean error;
- PMFS vs Direct posterior expected radial error;
- PMFS vs Direct MAP error.

### C. Distance-aware Top-K

- mean minimum truth distance among Top-1;
- Top-5;
- Top-10.

This reveals whether Top-10 candidates are physically near the source even when the exact carrier ID is absent.

### D. Fixed descriptive neighborhood mass

For 0.5 m, 1.0 m, and 2.0 m, report PMFS vs Direct posterior mass around truth.

These radii are descriptive only. Do not select a winner radius or build a new inference rule from them.

### E. Geometry-adaptive local evidence

Using only carrier geometry:

`a_i = 0.5*sqrt(width_i^2 + height_i^2)`

`A_ij = 1[distance(x_i,x_j) <= a_i+a_j]`

report:

- true-neighborhood Direct posterior mass;
- true-neighborhood geometry-prior mass;
- true-neighborhood `log B = log M - log M0`;
- number of 50 cases with `log B > 0`;
- median `log B`.

### F. Truth-blind regional decision summaries

Report localization error of:

- raw Direct point MAP;
- posterior-mass regional mode centroid `mu_M`;
- local-Bayes-factor regional mode centroid `mu_B`.

The regional modes must be computed before truth is read.

## Step 5 — classification

Do not create a numerical GO threshold after seeing H01. Classify mechanistically:

### `PF_DEI_V3_SPATIALLY_COHERENT_SIGNAL`

Use only if the result is directionally consistent across several independent spatial diagnostics, especially:

- Direct expected radial error improves over PMFS;
- Top-K minimum distance improves;
- local posterior mass around truth improves over PMFS/prior;
- true local log-BF is positive in a clear majority rather than a few outliers;
- the truth-blind regional mode improves over raw point MAP in a reproducible way across updates/seeds.

This classification authorizes **derivation of a new preregistered region/continuous-source method only**. It does not authorize closed loop.

### `PF_DEI_V3_RANK_SIGNAL_NOT_SPATIALLY_ACTIONABLE`

Use if exact rank improves but the spatial diagnostics above do not show coherent improvement.

Then stop the NRE sharpening route. Do not respond by increasing network capacity or training steps.

### `PF_DEI_V3_MIXED_SPATIAL_SIGNAL`

Use if gains appear only at particular update indices or a minority of seeds. Report exactly where the signal becomes available. The next method must explain that condition rather than hiding it in a learned gate.

## Step 6 — evidence package

Create an isolated evidence directory containing:

- `REPORT.md` with the complete tables and classification;
- `VERDICT.txt` with exactly one classification string;
- `spatial_structure_cases.csv`;
- `spatial_structure_audit.json`;
- `GIT_IDENTITY.txt` with repo/branch/HEAD;
- SHA-256 manifest of every file in the package.

Do not commit generated H01 outcome files back into the source branch unless explicitly instructed later.

## Stop condition

After the one audit and evidence package, STOP.

Do not train V3. Do not implement posterior smoothing. Do not run a closed loop.

The next design decision must be made from the spatial mechanism result, not by iterative H01 optimization.
