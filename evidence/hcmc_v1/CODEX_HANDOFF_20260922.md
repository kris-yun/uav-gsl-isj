# HCMC V1 — CODEX HANDOFF

Date: 2026-09-22
Branch: `research/hypothesis-conditioned-multiscaling-v1`
Status: **STAGE-1 DISCOVERY PASS / INDEPENDENT OFFLINE VALIDATION NEXT / CLOSED LOOP PROHIBITED**

## 0. Do not reinterpret the task

HCMC V1 is now frozen.

Codex must **not**:
- tune powers using source truth;
- tune spatial scales using source truth;
- change the confidence floor to improve a case;
- choose a different score after seeing independent-case endpoints;
- blend HCMC with native PMFS posterior during the independent gate;
- run ROS closed loop before the independent offline gate passes.

The next task is validation, not method search.

## 1. Authoritative discovery archive

GitHub Release tag:
`tnqc-v5-r2-execution-20260921`

Archive:
`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

SHA256:
`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Discovery matrix:
- House01 / House02 / House03
- seed0 / seed1
- 300 s native trajectories
- 1500 sensor samples per case
- native `ExpectedValue(sourceProbability, 0.05)` endpoint

## 2. Reproduction command

After extracting the release archive:

```bash
python reference/hcmc_v1_screen.py \
  /absolute/path/to/tnqc_r2_six_offline_20260921_authoritative/native
```

Expected frozen aggregate:

- native mean endpoint error: about **5.55506 m**
- HCMC mean endpoint error: about **2.44883 m**
- improved: **6/6**
- relative mean reduction: about **55.92%**
- final-leaf permutation null as-good fraction: about **1/300**
- simulated-field spatial-shuffle null as-good fraction: **0/30**

If these values are not reproduced within ordinary floating-point tolerance, stop and diagnose before running anything new.

## 3. Frozen HCMC V1 definition

For each authoritative final-leaf source hypothesis:

- field A: `measured_probability`
- field B: `simulated_hit_probability`
- confidence: `measured_confidence`
- include support rows only when confidence > `1e-6`
- fixed powers: `p = {1,2,3,4}`
- fixed grid separations: `{1,2,4,8}` cells
- fixed directions: +x and +y
- pair weight: `sqrt(conf_i * conf_j)`
- calculate weighted structure functions
- calculate adjacent log2 scale slopes
- candidate score = negative mean absolute measured-vs-simulated slope mismatch
- valid candidate scores -> average percentile ranks
- invalid candidate -> density 0
- every free PMFS cell inherits its authoritative final-leaf rank
- normalize density over free cells
- endpoint uses exactly `floor(0.05 * N_free)` highest-density cells
- endpoint x/y is density-weighted ExpectedValue over those cells

Authoritative final-leaf IDs come from:

`tnqc_fixed_trajectory_evaluation.json`
→ `tnqc_gate_scope_audit.final_leaf_candidate_ids`

Do not substitute all evaluated candidates.

## 4. Frozen discovery evidence

Per case, native -> HCMC endpoint error (m):

- House01 seed0: 5.5273 -> 2.0541
- House01 seed1: 4.0016 -> 2.1946
- House02 seed0: 4.1070 -> 1.2290
- House02 seed1: 3.7007 -> 3.1110
- House03 seed0: 7.7821 -> 1.2829
- House03 seed1: 8.2116 -> 4.8213

Fixed-order and scale-family audits are already frozen under:

- `evidence/hcmc_v1/POWER_ORDER_ABLATION_20260922.md`
- `evidence/hcmc_v1/SCALE_FAMILY_ABLATION_20260922.md`

Do not use those discovery ablations to select a new V1.

## 5. Independent validation gate

Obtain genuinely independent VGR/GADEN realizations that were not used in HCMC discovery.

Preferred:
- same House01/02/03 environments;
- new stochastic seeds/realizations (e.g. seed2/seed3 if available);
- original 300 s horizon;
- same PMFS source-update machinery and frozen endpoint;
- no truth-dependent calibration.

The independent matrix must be generated without changing HCMC V1.

Minimum promotion conditions before closed loop:

1. pooled endpoint error reduction >= **10%** versus native;
2. majority of independent cases non-worse, with at least **4/6** non-worse for a six-case matrix;
3. no new false-confident-collapse pathology;
4. improvement must not disappear under the predeclared spatial-destruction null;
5. fixed p=1..4 and fixed physical scale family remain unchanged;
6. all provenance hashes, runtime manifests, and source-update scopes are archived.

If the independent gate fails, mark HCMC NO-GO or revise only on a new development set. Do not tune on the failed validation set and call it the same V1.

## 6. Closed-loop integration is not yet authorized

If independent offline validation passes, create a new branch for HCMC V2 closed-loop integration.

The first closed-loop architecture to test should treat HCMC as an **alternative source-evidence/source-density semantics**, not merely a small multiplicative factor on the already false-confident native posterior.

Reason: the frozen TNQC evidence shows the native posterior can be extremely sharp and wrong; weak multiplicative gates can fail to move its dominant mode even when the auxiliary source score contains useful information.

## 7. Scientific claim boundary

Safe working claim:

> A source hypothesis should be judged by whether its simulated plume reproduces the measured plume's multiscale turbulent-scalar increment laws, rather than by pointwise instantaneous agreement alone.

Do not claim yet:
- a universal indoor Kolmogorov exponent;
- a formal multifractal spectrum;
- universal turbulence class invariance;
- independent generalization;
- closed-loop superiority.

## 8. Required output from Codex

For the independent gate commit:

- exact branch and commit;
- independent-data provenance;
- data/run hashes;
- per-case native and HCMC endpoint errors;
- pooled statistics;
- null-control results;
- source-update/final-leaf scope audit;
- PASS / HOLD / NO-GO decision;
- no method changes hidden in the validation commit.
