# CG-PC-CTT / CG-PCI offline falsification protocol — 2026-08-27

> Status: **CURRENTLY TESTING**. This document is an experiment contract, not a paper claim.
>
> Goal: determine whether a **Completeness-Gated Proximal-Causal Transport Tomography** mechanism is strong enough to become the paper's main innovation.
>
> Do **not** modify the frozen ME-ACI V10 `main` implementation or its reported evidence. Work only on branch `exp/cg-pc-ctt-identifiability-bridge-20260827` or a child branch.

## 0. Scientific question

The known failure mode is not merely noisy transport. In hard H02 cases the current statistical object can rank the wrong source above the true source even when a simple transport score is applied. The new hypothesis is:

1. source evidence should be released only when the current source-response operator is **identifiable relative to unresolved transport uncertainty**; and
2. in identifiable windows, a **proximal causal bridge（近端因果桥）** can remove remaining transport/context confounding without explicitly recovering the hidden plume realization.

The gate is not a confidence heuristic. It is an operationalized **causal identifiability/completeness gate（因果可辨识性/完备性门）**.

## 1. Frozen project facts

- ROS2 Humble + GADEN + PMFS.
- `main_v8` remains the authoritative forward contract.
- `dataset_v1` remains excluded.
- M1 = wind-conditioned first-arrival transport field and is already **GO** on House03.
- V11/ME-ACI-style reversible fixed-prior sequential bookkeeping is the preferred outer posterior mechanism after offline qualification; do not invent another irreversible accumulator in this experiment.
- Runtime-deployable inputs only: processed gas, local wind, pose/odometry/yaw, velocity/action history, map/occupancy, timestamps, queried candidate source coordinate, posterior/history.
- Forbidden runtime features: source truth, wind ID, route ID, plume seed, simulator phase, oracle fields, future samples.
- 300 s closed-loop experiments are **blocked** until the offline gates in this document pass.

## 2. Rejected ideas that must not be resurrected

Do not spend cycles on any of the following as the main mechanism:

- RMFE macro ranking.
- SCTT downstream module.
- naive `Y - mean_context` source correction.
- the old H02 scalar transport penalty/gate.
- contrast-direction cosine stability as a second gate.
- raw rank / `gamma` alone as the full runtime gate.
- naive standalone survival penalty as immediate M3.

## 3. M1 ensemble table contract

Build one long-form CSV from the existing House03 M1 bank with one row per:

`(context_id, candidate_id, transport_member)`.

Required columns:

- `context_id`: current source-update context. Must not encode truth.
- `candidate_id`: queried source candidate.
- `transport_member`: M1 transport ensemble member.
- `f_*`: numeric response features. Use the same physical response family across all candidates/members in a context.

Preferred physical features are compact, interpretable M1 quantities, not arbitrary neural embeddings. Include a stable subset such as:

- arrival-probability / hazard integrals over fixed bins;
- first-arrival quantiles;
- never-arrival probability;
- candidate-to-query travel-time moments;
- source→query wind-alignment/path quantities already available in M1.

Standardize feature definitions once. Do not select different features per test world.

The existing House03 bank should contain approximately 10 contexts × 206 candidates × 8 transport members = 16,480 traces. Verify the actual count and log any discrepancy.

## 4. Gate mathematics — frozen for this experiment

For context `t`, candidate `s`, member `m`:

`phi[s,m,t]` = M1 response feature vector.

Candidate mean:

`mu[s,t] = mean_m phi[s,m,t]`.

Pooled within-candidate transport covariance:

`Sigma_tr[t] = sum_s sum_m (phi[s,m,t]-mu[s,t]) (.)^T / sum_s(M_s-1)`.

Regularized whitening:

`W_t = (Sigma_tr[t] + lambda I)^(-1/2)`

with relative ridge `lambda = 1e-3 * trace(Sigma_tr)/d` and eigenvalue floor `1e-8 * lambda_max`.

Whitened candidate response means:

`M_tilde[t] = center_s(mu[s,t]) W_t^T / sqrt(K)`.

Let singular values be `sigma1 >= sigma2 >= ...`.

For the current experiment use retained contrast order `r=3` unless the evaluated local candidate subset has fewer than four candidates.

Two required gate statistics:

- relative conditioning: `gamma = sigma_r / sigma1`
- absolute weakest retained contrast: `alpha = sigma_r`

`gamma` asks whether the retained source directions are non-degenerate; `alpha` asks whether the weakest retained source direction is strong enough relative to transport uncertainty.

A gate PASS requires **both** criteria. A FAIL must produce exact abstention in later online integration:

`q_t(s) = q_{t-1}(s)`.

No low-weight update, no posterior sharpening, no hidden fallback correction.

### Important threshold rule

The historical raw source-response threshold `gamma_raw >= 0.05` remains a useful frozen V2 diagnostic, but it is **not automatically the threshold for whitened gamma** because the operator definition changed.

Whitened `gamma` and `alpha` thresholds must be calibrated only on development contexts, frozen once, then evaluated on held-out wind/transport contexts. Never tune them on the final test or on H02 confirmatory cases.

## 5. Gate calibration protocol

### 5.1 Data split

Use the existing House03 M1 qualification split:

- development transport members: 0–5;
- held-out transport members: 6–7;
- preserve the two previously held-out wind contexts as test contexts if available from the frozen M1 qualification.

If the exact old split metadata exists, reuse it verbatim. If not, reconstruct the split from the M1 qualification artifacts and record the mapping before any tuning.

### 5.2 Calibration target

On development contexts only, create truth-vs-hard-negative evaluation atoms using the same definition used in the previous M1 source-ordering gate:

- true source candidate;
- eight nearest hard-negative candidates.

For each atom compute the frozen downstream endpoint:

`margin = score(true_source) - max score(hard_negative)`.

The gate should identify windows where this margin is trustworthy.

### 5.3 Pre-registered threshold selection

Evaluate a finite grid on **development only**:

- `gamma` candidate thresholds = empirical deciles of development `gamma` plus 0;
- `alpha` candidate thresholds = empirical deciles of development `alpha` plus 0.

For every pair report:

- coverage;
- false-pass rate = fraction of PASS atoms with `margin <= 0`;
- PASS mean/median margin;
- FAIL mean/median margin.

Choose the pair lexicographically:

1. require development coverage >= 20%;
2. minimize false-pass rate;
3. among ties maximize PASS median margin;
4. among remaining ties maximize coverage.

Freeze this pair to a JSON file **before** held-out evaluation.

Do not change the rule after seeing held-out/H02 results.

## 6. Held-out gate success criteria

Run on held-out wind + held-out transport members.

Minimum GO criteria for `G_id`:

1. PASS coverage >= 10% (gate cannot trivially reject everything).
2. PASS true-vs-hard-negative mean margin > 0.
3. PASS median margin > FAIL median margin.
4. Bootstrap 95% CI for `(PASS margin - FAIL margin)` should preferably exclude 0; if it overlaps 0, classify as weak/partial, not GO.
5. Gate FAIL windows must not produce a sharper source posterior in any integration test.
6. Negative control: candidate/source-response permutation must destroy or materially reduce the PASS advantage.

Also report the raw historical `gamma_raw>=0.05` diagnostic separately if reconstructable. Do not mix it numerically with whitened `gamma`.

## 7. Immediate H02 hard challenge

Only after freezing thresholds, run the 28 historical H02 hard cases where the old gate failed:

- 28/28 had `delta = true_score - wrong_score < 0`;
- mean delta approximately -34.22;
- range approximately -81.76 to -8.12;
- true-source rank median approximately 118.5/201;
- wrong-source rank median approximately 5/201.

Questions to answer in order:

### H02-A: Can the new gate recognize untrustworthy cases?

Report:

- number/percentage of the 28 cases classified FAIL;
- delta distribution among PASS vs FAIL;
- whether the worst false-source cases are preferentially rejected.

A useful gate should reject a substantial fraction of these historically deceptive cases. Do not call this localization improvement yet.

### H02-B: For PASS cases only, can a proximal bridge move the margin toward zero/positive?

Proceed to Section 8 only for PASS cases.

## 8. Minimal proximal bridge experiment

Hidden nuisance:

`U_t` = unresolved plume / transport realization.

Observed outcome:

`Y_t` = deployable gas encounter response or compact event target.

Candidate intervention:

`do(S=s)` = queried source candidate.

### 8.1 Proxy roles

Treatment/source-side proxy `Z_t(s)` must come from candidate-dependent M1 physics, e.g.:

- arrival hazard / arrival-bin probabilities;
- source→query travel-time/path statistics;
- source-relative wind alignment;
- candidate-specific M1 response summaries.

Outcome/transport-side proxy `R_t` must be candidate-independent and deployable, e.g.:

- recent local-wind sequence/variation;
- pose, velocity, action history;
- recent hit/miss/processed gas history;
- sensor transient state.

Every queried candidate for the same event must see the **same** `R_t` values.

### 8.2 Minimal bridge equation

Start with a small bridge, not a transformer:

`h_theta(R_t, s, C_t)`

with conditional moment target:

`E[Y_t - h_theta(R_t,s,C_t) | Z_t(s), C_t] ~= 0`.

Use the supplied `fit_proximal_bridge.py` two-stage ridge-IV baseline first. This is deliberately conservative. Only if it shows held-out signal should a nonlinear bridge be implemented.

### 8.3 Bridge-table contract

Construct a long-form CSV with:

- `y`: observed deployable target;
- `group_id`: route/world split unit, for splitting only;
- `gate_pass`;
- `b_*`: bridge regressors from candidate-independent R/history plus explicit queried-source geometry/interactions;
- `z_*`: candidate-dependent M1 physical proxies;
- `c_*`: optional deployable current context.

Never put route/world/wind IDs into model features; IDs may only be used for grouping/splitting.

### 8.4 Required comparisons

Run:

A. `M1` source score alone.

B. `M1 + bridge` on frozen `G_id PASS` windows.

C. bridge with `Z` shuffled within group (`shuffle_z_within_group`).

D. source/candidate-query permutation control.

E. time reversal or deterministic delay permutation if event chronology is used.

Primary bridge endpoint:

`true_source_score - max_false_source_score`.

Secondary endpoints:

- true-source rank;
- Top-1 / Top-k source accuracy if defined by the existing evaluator;
- held-out moment norm;
- calibration / posterior entropy only as secondary diagnostics.

### 8.5 M2 GO criterion

Call M2 GO only if, on held-out data and frozen `G_id PASS` windows:

1. `M1+bridge` improves the primary true-vs-hard-negative margin over M1 alone;
2. improvement is positive in each held-out wind context, not only pooled;
3. a paired route/context bootstrap 95% CI for the improvement excludes 0, or is at least strongly positive with a predeclared small-sample caveat;
4. `Z` shuffle/source permutation destroys the gain;
5. no forbidden runtime information is used;
6. H02 PASS cases move materially toward zero and preferably cross to positive margin.

If H02 PASS cases remain strongly negative, mark M2 **NO-GO**. Do not proceed by adding capacity until the failure is diagnosed.

## 9. Do not implement M3 yet

Causal transition dynamics / encounter-state dynamics is **HOLD** until M2 passes.

Do not add onset/decay/re-entry state models merely to rescue a failed bridge. If M2 passes, the next experiment may test:

`P(z[t+dt] | z[t-k:t], R_t, do(S=s))`

with Markov depths k in {1,2,4,8}.

## 10. Closed-loop promotion rule

Do not launch the full 300 s House experiments until:

- `G_id` held-out GO;
- M2 held-out GO;
- H02 hard challenge shows either correct abstention or material margin repair;
- all negative controls pass.

Then use this order:

1. House03 failed-scene 300 s OFF/ON development check.
2. Freeze code, thresholds, feature definitions, binary hash, source-update cadence, metric and stopping rule.
3. Run unseen H01/H02 seeds as confirmatory experiments.
4. Report the original PMFS endpoint `ExpectedValue(sourceProbability, 0.05)`.

Outer sequential update should remain reversible/fixed-prior in the V11/ME-ACI spirit: later evidence must be able to overturn an early false basin.

## 11. Commands

From repository root on the experiment branch:

```bash
python3 experiments/cg_pc_ctt/compute_identifiability_gate.py \
  --input /path/to/m1_ensemble_long.csv \
  --output /path/to/results/gate_dev.csv \
  --context-col context_id \
  --candidate-col candidate_id \
  --member-col transport_member \
  --feature-prefix f_ \
  --contrast-order 3 \
  --ridge-rel 1e-3 \
  --eig-floor-rel 1e-8 \
  --meta-output /path/to/results/gate_dev.meta.json
```

After development calibration and threshold freeze:

```bash
python3 experiments/cg_pc_ctt/compute_identifiability_gate.py \
  --input /path/to/m1_ensemble_test_long.csv \
  --output /path/to/results/gate_test.csv \
  --contrast-order 3 \
  --gamma-threshold <FROZEN_GAMMA> \
  --alpha-threshold <FROZEN_ALPHA>
```

Bridge baseline:

```bash
python3 experiments/cg_pc_ctt/fit_proximal_bridge.py \
  --input /path/to/bridge_table.csv \
  --output /path/to/results/bridge.csv \
  --y-col y \
  --group-col group_id
```

Negative control:

```bash
python3 experiments/cg_pc_ctt/fit_proximal_bridge.py \
  --input /path/to/bridge_table.csv \
  --output /path/to/results/bridge_shuffle_z.csv \
  --y-col y \
  --group-col group_id \
  --negative-control shuffle_z_within_group
```

## 12. Required result bundle

Create a single result directory containing at least:

- `DATA_CONTRACT.md` — exact input paths, hashes, row counts, candidate/member counts, split mapping.
- `gate_dev.csv`
- `gate_dev.meta.json`
- `gate_thresholds_frozen.json`
- `gate_test.csv`
- `gate_threshold_grid_dev.csv`
- `gate_margin_eval_test.csv`
- `h02_hard28_gate.csv`
- `bridge.csv`
- `bridge.csv.summary.json`
- `bridge_shuffle_z.csv`
- `bridge_shuffle_z.csv.summary.json`
- `negative_controls.csv`
- `RESULT_SUMMARY.md`
- exact git commit SHA, binary SHA-256 if ROS executable is touched later, and all command lines.

## 13. RESULT_SUMMARY required verdict format

Use exactly these headings:

### CONFIRMED
Only facts directly reproduced in this run.

### CURRENTLY TESTING
Items with suggestive but not promotion-level evidence.

### REJECTED
Failed modules/controls.

### G_ID VERDICT
One of `GO / PARTIAL / NO-GO` with numerical evidence.

### M2 PROXIMAL BRIDGE VERDICT
One of `GO / PARTIAL / NO-GO` with numerical evidence.

### H02 HARD-CASE VERDICT
State how many of 28 are rejected by the gate and, among PASS cases, how much the bridge changes the true-vs-wrong margin.

### CLOSED-LOOP DECISION
Exactly `PROCEED` or `DO NOT PROCEED`.

## 14. Scientific interpretation guardrails

If successful, the claim is not “we invented a singular-value confidence score.” The intended contribution is:

**A causal gas-source inference architecture that explicitly tests transport-relative source identifiability/completeness before intervention-specific evidence release, then uses physical M1 proxies to estimate a proximal causal bridge without explicitly recovering the hidden plume realization.**

The singular spectrum is only the operational gate. The main innovation requires the combination of physical transport operator + completeness gate + proximal bridge + abstaining/reversible posterior behavior.

If M2 fails, do not rename the gate as the main innovation. Freeze it as a useful diagnostic and return to mechanism design.
