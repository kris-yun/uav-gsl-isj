# START HERE — CPIR three-module theory handoff

Date: 2026-08-31
Status: THEORY FROZEN / RUNTIME NOT YET FULLY ALIGNED

This file exists because the active Codex worktree may still be on `codex/ctt-wonline-sufficiency-audit-20260830` and therefore may not see the new paper-level M2/M3 definitions automatically.

## Authoritative theory files on this branch

- `docs/CPIR_THREE_MODULE_THEORY_AND_FORMULA_FREEZE_20260831.md`
- `docs/CPIR_THREE_MODULE_FORMULA_CONTRACT_20260831.json`

These supersede the old paper-level three-module definition in `CTT_FINAL_THREE_MODULE_METHOD_REDERIVATION_20260830.md`.

## Final paper modules

### M1 — Causal Stochastic Physical Intervention (CSPI)

`C_{1:N}^{s,k}=F_GADEN(do(S=s),K=k,X_{1:N},E)`

`K` is an exchangeable nuisance sample only. It is NOT a temporal state. Coherent-K and dynamic Markov-K are permanently rejected.

### M2 — Persistent Sensor-State Transduction (PSST)

`R_n^{s,k}=alpha R_{n-1}^{s,k}+(1-alpha)C_{n-2}^{s,k}`

with frozen runtime constants:

- `dt=0.2 s`
- `tau=1.2 s`
- `alpha=exp(-0.2/1.2)=0.846481724890614`
- delay `2` samples = `0.4 s`
- threshold `0.1 ppm`
- first `80` samples per completed physical stop

Candidate event:

`Z_{sbk}=1[max_{n in I_b} R_n^{s,k} > 0.1]`

The sensor state is carried continuously through motion/stops/source updates and is never reset at a stop. The real measured tape is NOT filtered a second time.

IMPORTANT: current `CPIR.cpp` already contains this M2 operator. Therefore the historical software label `M1-only` is not a clean paper-level M1 ablation.

### M3 — Stop-Resolved Reachability/Detection Composite Likelihood (SRDCL)

For source `s`, physical stop `b`, and `M=8` predictive members:

`h_{sb}=sum_k Z_{sbk}`

`q_{sb}=(h_{sb}+0.5)/(M+1)=(h_{sb}+0.5)/9`

Observed event:

`Y_b=1[max_{n in I_b} M_n^obs > 0.1]`

FULL M3 score:

`ell_M3(s)=sum_b [Y_b log q_{sb} + (1-Y_b) log(1-q_{sb})]`

This MUST preserve stop identity. Do NOT average `q_{sb}` over stops before scoring.

Current `CPIR.cpp` does NOT yet implement this M3 score. It currently computes `q_{sb}`, averages over `b` to `qbar_s`, counts only total observed hits, and then applies a count-only binomial score. That count-collapse is the M3 ablation/comparator, not the final M3 method.

M3 is a composite likelihood over stop-specific marginal detection probabilities. Do NOT claim it is the exact joint turbulent-transport likelihood.

## Carrier-to-cell interface (not a fourth module)

Let carrier posterior be `Q_C(i)` and let `p_ref(c)` be a reference cell distribution that has not consumed the same gas evidence. For each free cell `c` in carrier `i(c)`:

`rho(c|i)=p_ref(c)/sum_{u in C_i} p_ref(u)`

`Q_cell(c)=Q_C(i(c))*rho(c|i(c))`

This is the KL/I-projection solution under carrier-mass constraints. Required tests:

- carrier mass conservation
- within-carrier odds preservation
- identity reconstruction
- row/tie order invariance

Current `CPIR.cpp` uniform carrier lifting is NOT the final interface.

## Required clean nested ablation

- A0 = authoritative `main_v8` PMFS
- A1 = M1 native physics + MEMORYLESS raw-event + count-only
- A2 = M1 + M2 stateful sensor + count-only
- A3 = M1 + M2 + M3 stop-resolved score

Only these comparisons isolate the scientific increments:

- M2 increment = A2 vs A1
- M3 increment = A3 vs A2

Historical `CPIR M1-only` fixed-trajectory result (`5.1823 -> 2.6808 m`, 48.27%, 23/7) must be relabeled `CPIR-base shadow`, because its runtime already contains M2 sensor state and count-collapsed evidence.

## Implementation order after bank integrity PASS

1. Do not regenerate the bank.
2. Add explicit A1/A2/A3 runtime modes or an equivalent offline parity evaluator using the same frozen bank/tape.
3. First prove formula parity against the machine-readable contract.
4. Run small fixed-trajectory A1/A2/A3 isolation tests.
5. Run H01/H02/H03 nested shadow only after parity.
6. Closed loop is authorized only after the nested evidence is understood and runtime M3 + carrier-to-cell I-projection are implemented.

## Terminal rejections — do not revive

- exact first-passage phase as primary signal
- coherent whole-run transport-member state
- dynamic Markov transport-member state
- local-wind neural hazard
- temperature/blend/Top-K/reliability rescue
- truth-conditioned nuisance/member selection

