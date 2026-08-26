# CG-PC-CTT fast-track to full multi-seed closed loop
Date: 2026-08-27
Base frozen evidence: Gate V2 commit `c2b290e1a89a105eca3d5772f725ba8114d52691`.
Prep branch: `research/cg-pc-ctt-fasttrack-closedloop-prep`.

## Objective

Minimize turnaround after H02 hard-28 / bridge data arrive. The intended next performance experiment after an offline bridge GO is the complete **House01/02/03 × seeds 0..9 × OFF/ON = 60-run** closed-loop matrix, not another long chain of small seed sweeps.

Nothing in this prep branch changes the already-frozen H03 Gate V2 result. Diagnostics below cannot be used to retune `gamma_min`, `p_max`, rank, feature subset, or member definition.

## Work that can run now, before new H02 data

### 1. H03 representation stress

Run on the already-qualified H03 `phi[10,206,8,626]` NPZ:

```bash
python3 experiments/cg_pc_ctt/h03_representation_stress.py \
  /path/to/H03_phi.npz \
  --out-csv results/fasttrack/H03_REP_STRESS.csv \
  --out-json results/fasttrack/H03_REP_STRESS.json
```

Purpose: determine whether the nearly constant H03 `gamma_cf≈0.865` is highly dependent on treating all 626 free cells as separate features. Diagnostic only.

### 2. Known-limitation synthetic test

```bash
python3 experiments/cg_pc_ctt/synthetic_known_limitations.py
```

It deliberately demonstrates two boundaries of the global V2 statistic:
- `LOCAL_TWIN`: global replicated rank can PASS although one hard source pair is indistinguishable;
- `SHARED_BIAS_WRONG`: all transport members can reproducibly share the same wrong forward-model bias.

These are scientific limitations, not reasons to alter the H03/H02 V2 gate.

## Immediate action when H02 hard-28 data arrive

Prepare one NPZ with:

- `phi[28,S,8,D]`
- `margin[28] = true_score - max_false_score`
- `true_idx[28]`
- `hard_wrong_idx[28]`
- optional `case_id[28]`.

Then run, with no retuning:

```bash
python3 experiments/cg_pc_ctt/h02_hard28_fast_eval.py \
  H02_HARD28.npz \
  --out-csv results/fasttrack/H02_HARD28_V2.csv \
  --out-json results/fasttrack/H02_HARD28_V2_SUMMARY.json
```

### Interpretation

If H02 V2 coverage is `>=0.90`, record the global V2 gate as **MODEL_SIDE_PREMISE** rather than pretending it is a reliability selector. Do not tune it. The pair-specific statistic is diagnostic evidence about hard-negative separation.

If V2 creates a genuine accepted/rejected margin stratification, it remains a **RELIABILITY_SELECTOR_CANDIDATE**.

Either way, the bridge is the next falsifiable source-evidence module.

## Bridge fast-track gate

Prefer the stronger sieve-GMM bridge structure:

`E[g(Z,S) (Y - h(R,S))] = 0`.

At runtime, `Z` is not an input to `h`; only source-independent `R` and queried source coordinate `S` enter `h(R,S)`.

After the 28 H02 cases are scored, create CSV columns:

- `case_id`
- `m1_margin`
- `bridge_margin`
- `z_shuffle_margin`
- `source_shuffle_margin`
- optional `time_reverse_margin`.

Audit JSON must contain true booleans:

- `forbidden_feature_audit_pass`
- `r_candidate_independent`
- `test_not_used_for_tuning`.

Run:

```bash
python3 experiments/cg_pc_ctt/bridge_fasttrack_verdict.py \
  H02_BRIDGE_HARD28.csv \
  --audit-json BRIDGE_AUDIT.json \
  --gate-summary results/fasttrack/H02_HARD28_V2_SUMMARY.json \
  --out results/fasttrack/BRIDGE_FASTTRACK_VERDICT.json
```

### Frozen bridge-to-closed-loop criteria

Advance only if:

1. exactly 28 hard cases;
2. mean and median bridge margin improvement are both positive;
3. at least 19/28 cases improve (one-sided sign test `<0.05`);
4. every negative control preserves at most 50% of the real mean gain;
5. feature/R/test-leakage audit passes.

Verdict required:

`BRIDGE_FASTTRACK_GO_TO_FULL_MULTI_SEED`.

This is permission to spend the next experiment on the full closed-loop matrix; it is not `CG_PC_CTT_OFFLINE_GO` or a paper claim by itself.

## Frozen runtime bridge interface

A fitted sieve-GMM bridge should export:

- `beta`
- `rs_mean`
- `rs_std`
- `h_basis_scale`
- `r_dim`
- `s_dim`

into one immutable NPZ. `closed_loop/cg_pc_ctt/frozen_bridge_runtime.py` evaluates `h(R,S)` without Z.

No score temperature or M1/bridge blend coefficient is allowed.

## Candidate reversible posterior

`closed_loop/cg_pc_ctt/reversible_rank_posterior.py` supplies a scale-free V11-style outer update:

1. candidate bridge score is rank-normalized within each accepted event;
2. accepted events are split into even/odd folds;
3. each fold is aggregated with `1/sqrt(n_fold)` normalization;
4. fold aggregates are rank-normalized again;
5. `g=(z_even+z_odd)/sqrt(2)`;
6. `q(s) proportional to q0(s) exp(g(s))`.

Gate-FAIL events are permanently excluded. Posterior release requires both folds to contain accepted evidence. The fixed prior is rebuilt on every release, so later evidence can reverse an earlier basin.

This outer update remains a candidate integration contract until the bridge fast-track gate passes; do not claim a validated formula from the prep branch alone.

## Infrastructure smoke test

After the online binary and frozen bridge artifact are built, run only a short infrastructure smoke test (not a performance result) to verify:

- ON binary starts;
- OFF/ON use the same frozen source/seed contract;
- no forbidden runtime input;
- posterior export exists;
- first release is logged;
- exact ABSTAIN is respected before release;
- run terminates cleanly.

Do not tune method parameters from the smoke run.

## Full closed-loop matrix

The first complete performance sweep is:

- Houses: `House01,House02,House03`
- Seeds: `0..9`
- Arms: `OFF,ON`
- 300 simulation seconds per arm
- 30 matched OFF/ON pairs / 60 runs
- pair order: OFF then ON
- primary endpoint: PMFS `ExpectedValue(sourceProbability,0.05)` error.

Launch with:

```bash
CASE_RUNNER=/absolute/path/to/frozen/run_cg_pc_ctt_case.sh \
RUN_ROOT=/dev/shm/cg_pc_ctt_confirmatory \
MAX_PARALLEL=3 \
TIMEOUT_SEC=300 \
bash closed_loop/cg_pc_ctt/run_multiseed_matrix.sh
```

The batch orchestrator runs each OFF/ON pair sequentially while allowing up to three independent pairs in parallel using ROS domains 120..122 by default. This remains below the Fast DDS domain limit 232.

Each arm must emit a standard `case_result.json`. `evaluate_case_posterior.py` computes the external truth-only PMFS top-5 metric from a final posterior CSV.

## Frozen full-matrix success criteria

For the complete 30-pair matrix:

1. **30/30 valid matched pairs**;
2. **pooled PMFS top-5 error reduction >=10%**;
3. **one-sided paired sign test p<=0.05** (20/30 improved pairs is sufficient);
4. **no House pooled mean degrades by >5%**;
5. **zero false-confident-collapse flags**.

`aggregate_multiseed.py` computes these criteria and a pair-bootstrap 95% CI.

Required final batch verdict:

- `CG_PC_CTT_MULTI_SEED_GO`, or
- `CG_PC_CTT_MULTI_SEED_NOT_GO`.

No House-specific tuning, seed-specific tuning, stopping-time tuning, score temperature, or blend-weight tuning is permitted after the full matrix begins.

## Most important fast-track rule

Do not spend time repeatedly repairing the global H03 V2 gate if H02 shows it is all-pass. In that case record its scientific role honestly as model-side replicated identifiability and let the hard-28 bridge falsification decide whether the method is worth the complete closed-loop experiment.
