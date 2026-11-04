# CODEX EXECUTION PROTOCOL — CG-PC-CTT Gate V2
Date: 2026-08-27
Branch: `research/cg-pc-ctt-gate-v2`
Status: **PROTOCOL REPAIR / DATA PRODUCT NOT YET QUALIFIED**

This document supersedes the V1 protocol. V1 is `INVALID_PROTOCOL` and must not be used for H03/H02 claims.

## 0. Binding scientific verdict at protocol start

V1 failed its own scientific contract:

- weak case produced a false PASS;
- a true null could produce rank 3 and raw alpha around one;
- collapse could also pass;
- the intended House03 `206×8×10` M1 data product was not present in the branch/worktree search.

Therefore:

1. no H03/H02 offline claim may be made from V1;
2. no 300 s closed-loop experiment is authorized;
3. ME-ACI V10 `6/6` / pooled improvement is unrelated development evidence and cannot validate CG-PC-CTT;
4. threshold tuning is not an admissible repair.

## 1. The V1 statistical error

V1 used a finite-member candidate mean

`mu_hat_s = (1/M) sum_m phi_{s,m}`

and interpreted the whitened source contrast of `mu_hat_s` as absolute source information. Under a source-null,

`phi_{s,m} = mu_0 + eps_{s,m}`,

`mu_hat_s - mu_0 = O_p(M^-1/2)`.

With M=8, random candidate-mean differences remain non-negligible. Whitening by a member-residual covariance changes scale but does not remove this finite-M term. Squaring / taking singular values makes the null contribution positive. Hence V1 alpha was not an unbiased absolute source-strength statistic.

## 2. V2 model and member semantics

For each decision context, define

`phi[s,m,d]`

where `s` is candidate source, `m` is transport member and `d` is an M1 response feature.

Before any inference, the eight transport members MUST be classified from provenance, not guessed from filenames:

### A. `exchangeable_realizations`

Members are independently generated / exchangeable realizations from one declared transport-nuisance generating process. Examples: independent plume/transport seeds drawn under the same frozen nuisance law.

Only this mode is eligible for the V2 inferential sign-flip gate.

### B. `fixed_nuisance_design`

Members are deterministic support points, hand-selected discrepancy settings, quadrature nodes, alpha/beta variants, fixed wind families, or otherwise non-random design points.

If this is the true semantics:

- V2 may print descriptive replicated spectra;
- `inferential_valid=false` is binding;
- no source update may be released from the V2 p-value;
- verdict is `BLOCKED_FIXED_DESIGN` until a separate robust-set protocol is written or genuine exchangeable realizations are generated.

Do not relabel fixed members as random replicates to obtain a PASS.

## 3. V2 replicated-completeness statistic

Assume inferential mode:

`phi[s,m,d] = mu[s,d] + eps[s,m,d]`.

The stable source response is `mu`; `eps` is unresolved member variation with zero center across repeated realizations.

### 3.1 Nuisance scaling without a source mean

Estimate feature-wise member noise using pair differences:

`v_d = mean_{s,m<n} (phi[s,m,d]-phi[s,n,d])^2 / 2`.

Under exchangeable equal-variance realizations this estimates the member-noise variance without squaring a noisy source mean.

Whiten feature d by

`w_d = 1/sqrt(v_d + lambda)`.

`lambda` is deterministic scale-relative ridge (`ridge_rel=1e-3`).

### 3.2 Per-member source centering

For every member separately:

`C_m = P_S Phi_m W`,

where `P_S = I - 11^T/S`.

Do not first average members.

### 3.3 Cross-member replicated source operator

Define

`K = [sum_{m != n} C_m^T C_n] / [M(M-1)S]`

or equivalently

`K = [C_sum^T C_sum - sum_m C_m^T C_m] / [M(M-1)S]`.

This is the key V2 repair. Same-member squares are explicitly subtracted. Under independent/exchangeable member noise, `E[K]` contains the stable between-source contrast operator rather than the V1 finite-M mean-noise square.

Let

`lambda_1 >= lambda_2 >= ...`

be eigenvalues of symmetric `K`.

Primary rank is frozen at `k=3`:

`alpha_cf = sqrt(max(lambda_3,0))`

`gamma_cf = sqrt(max(lambda_3,0) / max(lambda_1,eps))`.

`alpha_cf` is now a replicated cross-member amplitude, not the V1 raw whitened mean singular value.

### 3.4 Exact member sign-flip null

For a no-stable-source-contrast null, flip the whole member contrast matrix:

`C_m -> eta_m C_m`, `eta_m in {-1,+1}`.

Global sign is redundant, so fix `eta_0=+1`. With M=8 there are exactly `2^(8-1)=128` unique patterns.

The code enumerates all patterns. The minimum exact p-value is therefore

`1/128 = 0.0078125`.

Frozen V2 gate:

- `rank_k = 3`
- `gamma_min = 0.05`
- `p_signflip <= 0.01`
- `lambda_3 > 0`
- `member_semantics == exchangeable_realizations`

There is **NO alpha_min calibration in V2**.

### 3.5 Assumptions and limits

The sign-flip test additionally assumes the member-level deviations are sufficiently sign-symmetric under the no-stable-source-contrast null. This is an operational finite-sample screen, not a general causal-identification theorem.

The statistic is motivated by replicated source contrast / weak-identification logic. Do not claim that the exact formula is inherited as a theorem from proximal causal inference.

## 4. Mandatory Phase A — local scientific regression tests

Run first:

```bash
git fetch origin
git checkout research/cg-pc-ctt-gate-v2
git pull origin research/cg-pc-ctt-gate-v2
cd experiments/cg_pc_ctt
python3 -m py_compile completeness_gate.py run_gate_eval.py proximal_bridge.py selftest.py find_m1_bank.py qualify_m1_bank.py
python3 selftest.py
```

Required output:

`SELFTEST V2 PASS`

The selftest must enforce all of the following:

1. strong rank-3 replicated signal PASS;
2. weak signal FAIL;
3. true source-null FAIL;
4. collapsed third source direction FAIL;
5. independent candidate-label shuffle across members FAIL;
6. member-axis reordering leaves statistic unchanged;
7. `fixed_nuisance_design` cannot be inferentially accepted;
8. undeclared member semantics cannot be accepted;
9. ABSTAIN leaves posterior exactly unchanged.

If any assertion fails: verdict `INVALID_PROTOCOL_V2`; stop.

Do not alter thresholds or random seeds to make the selftest pass.

## 5. Mandatory Phase B — recover and freeze the real M1 data product

The new branch does not itself contain the previously described House03 `206 candidates × 8 transport members × 10 contexts = 16,480 traces` bank. It must be located or reconstructed from the original M1 generation pipeline before real evaluation.

Start with:

```bash
python3 find_m1_bank.py \
  /mnt/hgfs/workspace \
  "$HOME" \
  /tmp \
  --out /tmp/m1_bank_candidates.json
```

Narrow the roots if the VM layout differs. Do not scan `/proc`, `/sys`, or unrelated mounted archives.

For every candidate artifact, establish:

- absolute path;
- SHA-256;
- creation/generation command or source script;
- source candidate list and coordinates;
- transport member IDs;
- whether member IDs are random seeds or deterministic support points;
- wind/context identifiers;
- M1 feature definition and normalization;
- whether data are current physical replay or an obsolete static bank;
- whether any members are exact clones.

### Required provenance file

Before conversion/evaluation create:

`results/cg_pc_ctt_v2/M1_BANK_PROVENANCE.json`

with at least:

```json
{
  "source_artifact": "...",
  "sha256": "...",
  "generator_commit": "...",
  "generator_command": "...",
  "shape_expected": [10, 206, 8, "D"],
  "member_ids": ["..."],
  "member_semantics": "exchangeable_realizations OR fixed_nuisance_design",
  "member_generation_evidence": "...",
  "exact_clone_check": "PASS/FAIL",
  "current_transport_context_check": "PASS/FAIL"
}
```

If provenance cannot determine member semantics, stop with `BLOCKED_MEMBER_SEMANTICS`.

If the historical bank is absent, reconstruct it only from the frozen/current M1 physics that previously passed G0/G1. Do not rebuild it from ME-ACI V10 evidence, and do not change M1 physics while reconstructing.

## 6. NPZ contract

Real gate input:

`phi[N_context,S_candidate,M_member,D_feature]`.

Recommended metadata:

- `context[N]`
- `house[N]`
- `split[N]`
- `candidate_id[S]`
- `member_id[M]`
- scalar `member_semantics`
- optional evaluation-only `margin[N]`

Run:

```bash
python3 qualify_m1_bank.py /path/to/m1_context_ensemble.npz \
  --json-out results/cg_pc_ctt_v2/M1_BANK_QUALIFICATION.json
```

Structural PASS is necessary but not sufficient; provenance is binding.

Forbidden runtime/proxy inputs remain: source truth, wind ID as an oracle label, route ID, plume seed as an oracle label, simulator phase, future observations, source truth coordinates, or other oracle fields. Truth may exist only in evaluation metadata used after gate output is frozen.

## 7. Decision after member-semantics audit

### If `fixed_nuisance_design`

Stop H03/H02 inferential evaluation for this gate. Write verdict:

`BLOCKED_FIXED_DESIGN`.

Then choose one scientifically explicit route:

A. generate a new set of independent/exchangeable transport realizations under a frozen nuisance law; or

B. create a separate deterministic robust-set completeness protocol (worst-case/set-identifiability), versioned independently. Do not retrofit a p-value to the fixed design.

### If `exchangeable_realizations`

Proceed with the frozen V2 gate. No threshold calibration step exists.

## 8. Phase C — House03 offline gate evaluation

Only after A+B pass:

```bash
python3 run_gate_eval.py \
  --npz /path/to/frozen_house03_m1_bank.npz \
  --out results/cg_pc_ctt_v2/H03_GATE_V2.csv \
  --member-semantics exchangeable_realizations \
  --gamma-min 0.05 \
  --p-max 0.01 \
  --rank-k 3
```

Do not tune `gamma_min`, `p_max`, rank, ridge, feature set, or member definition on H03/H02 outcome margins.

Report:

- coverage;
- distribution of `alpha_cf`, `gamma_cf`, `p_signflip`;
- accepted vs rejected true-vs-hard-negative margin;
- accepted vs rejected positive-margin rate;
- true-source rank as evaluation-only secondary endpoint;
- context-level/bootstrap uncertainty where multiple independent contexts exist.

Gate success cannot be declared if it accepts almost nothing. Pre-register:

`coverage >= 0.10`

as the non-degenerate minimum for later bridge testing. Below that: `DEGENERATE_ABSTENTION`.

## 9. Phase D — mandatory historical H02 28-case hard challenge

No retuning after H03.

Historical reference:

- 28/28 simple transport-gate margins were negative;
- mean margin approximately `-34.22`;
- true rank median approximately `118.5/201`;
- wrong rank median approximately `5/201`.

For each of the 28 cases record gate output before inspecting margin.

The gate's purpose is not to magically make an M1 score positive. It must identify when source evidence is not replicated enough to update.

Required report:

- H02 coverage;
- accepted/rejected margin distributions;
- accepted/rejected catastrophic negative-tail statistics;
- exact ABSTAIN invariant for every FAIL;
- no posterior entropy decrease on FAIL.

If PASS cases are as catastrophic as FAIL cases, gate is `NO_GO_IDENTIFIABILITY`.

## 10. Phase E — Proximal Causal Bridge M2

Run only after a non-degenerate gate that meaningfully stratifies source-margin reliability.

Keep the first bridge deliberately small. Use `proximal_bridge.py` before any transformer.

Hidden nuisance:

`U_t = unresolved plume/transport realization`.

Outcome:

`Y_t = deployable gas encounter response`.

Candidate-side proxy:

`Z_t(s)` from candidate-dependent M1 physical predictions only.

Outcome/transport-side proxy:

`R_t` from source-independent onboard history only. Every candidate must receive byte-identical R at one context.

Primary endpoint on gate-PASS cases:

`Delta_margin = margin(M1+bridge) - margin(M1)`.

M2 GO requires:

1. positive held-out margin improvement;
2. improvement not reproduced by candidate-source shuffle;
3. improvement not reproduced by time reversal / proxy shuffle;
4. no forbidden feature leakage;
5. at least some historically hard H02 PASS cases move materially toward or through zero.

If the bridge remains strongly negative on hard H02 PASS cases: `GATE_GO_M2_NO_GO`.

## 11. Mandatory negative controls

Run exactly the same scoring pipeline with:

1. candidate identity shuffled independently across M1 members;
2. member order permuted globally — V2 gate statistic must remain invariant;
3. source-query / Z proxy shuffle;
4. temporal reversal for sequential bridge features;
5. R candidate-invariance audit;
6. forbidden-feature audit;
7. ABSTAIN exact equality audit;
8. member clone audit.

## 12. No closed loop yet

A 300 s closed-loop experiment is authorized only after all of the following:

- `SELFTEST V2 PASS`;
- real M1 bank frozen with SHA/provenance;
- valid member semantics;
- non-degenerate Gate V2 stratification on offline data;
- M2 held-out improvement on gate-PASS cases;
- all negative controls PASS.

Then run one historically failed scene OFF/ON first. Freeze code, formulas, thresholds, cadence and stopping rule before unseen H01/H02 seeds.

A later confirmatory closed-loop target may use pooled error reduction `>=10%`, but that target must not be used to tune the offline gate or bridge.

## 13. Required result tree

Create:

`results/cg_pc_ctt_v2/<RUN_ID>/`

containing:

- `RUN_MANIFEST.json`
- `M1_BANK_PROVENANCE.json`
- `M1_BANK_QUALIFICATION.json`
- `SELFTEST.txt`
- `H03_GATE_V2.csv`
- `H03_GATE_V2_SUMMARY.json`
- `H02_HARD28_GATE_V2.csv`
- `BRIDGE_METRICS.csv`
- `NEGATIVE_CONTROLS.csv`
- `ABSTAIN_INVARIANT.txt`
- `FORBIDDEN_FEATURE_AUDIT.txt`
- `VERDICT.md`

Every manifest must include repository commit SHA and every input SHA-256.

## 14. V2 verdict vocabulary

Use exactly one current-stage verdict:

- `INVALID_PROTOCOL_V2`
- `BLOCKED_M1_BANK_MISSING`
- `BLOCKED_MEMBER_SEMANTICS`
- `BLOCKED_FIXED_DESIGN`
- `DEGENERATE_ABSTENTION`
- `NO_GO_IDENTIFIABILITY`
- `GATE_V2_GO`
- `GATE_GO_M2_NO_GO`
- `CG_PC_CTT_OFFLINE_GO`

`CG_PC_CTT_OFFLINE_GO` still is not a paper-level main-innovation claim until closed-loop validation is completed.

## 15. Immediate Codex order

1. pull `research/cg-pc-ctt-gate-v2`;
2. run py_compile and `selftest.py`;
3. if selftest fails, stop with `INVALID_PROTOCOL_V2`;
4. locate the actual M1 bank with `find_m1_bank.py`;
5. establish and write member semantics/provenance;
6. if fixed design, stop with `BLOCKED_FIXED_DESIGN` rather than inventing inference;
7. if bank missing, reconstruct only from frozen/current M1 physics and record hashes;
8. create/qualify NPZ;
9. run H03 V2 gate with frozen parameters;
10. run H02 hard-28 with no retuning;
11. only after non-degenerate Gate GO, run minimal proximal bridge;
12. run all negative controls;
13. write `VERDICT.md`;
14. do not start 300 s closed loop unless `CG_PC_CTT_OFFLINE_GO`.

Priority is statistical validity and falsification, not manufacturing a GO.
