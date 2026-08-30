# CTT H01 Final Hazard Neural M1 — Verdict

Date: 2026-08-30
Verdict: **`CTT_FINAL_HAZARD_NEURAL_M1_NO_GO`**

This is a terminal failure. Per the execution contract, STOP the current neural
CTT implementation; do not create another network version.

---

## What was run

- Frozen architecture: `FREEZE_FINAL_HAZARD_SOLVER_20260830.json` — spatial
  wind/map encoder (CNN over 32×32 occupancy+wind_u+wind_v patch) + source/query
  geometric conditioning + discrete hazard decoder (80 hazards).
- Loss: proper discrete event-time hazard log-likelihood.
- STATIC comparator: identical architecture/data/seed/order, wind channels zeroed.
- Training: contexts `0,3,5,6,8,9`; validation `4,7`; held transport keys `0..5`.
- Fresh confirmatory test: contexts `10,11,12,13`, held keys `6,7`, route 4005
  (6720 coherent fresh worlds generated on the VM via
  `materialize_ctt_h01_fresh_bank.py`).
- Hardware: NVIDIA RTX 5060 Laptop GPU, torch 2.9.1+cu130.

## Result (physical gate)

`static - conditional` NLL = **-0.0357**, 95% CI `[-0.0449, -0.0267]` → **lower
bound is negative**, so the static-wind comparator is *not* worse than the
conditional model; the conditional model is actually worse on NLL.

Per fresh context (conditional vs static NLL):

| context | conditional NLL | static NLL | conditional better? |
|---|---:|---:|---|
| 10 | 1.5845 | 1.5616 | NO |
| 11 | 1.4196 | 1.3867 | NO |
| 12 | 0.3601 | 0.3833 | yes |
| 13 | 2.5877 | 2.4778 | NO |

Only 1 of 4 fresh contexts favors the conditional model → "all fresh contexts
non-reversing" fails.

`wind-shuffle - conditional` NLL = -0.0062 (negative) → shuffling the spatial
wind channels did not worsen NLL → the network did not extract load-bearing
spatial wind information.

Gate table:

```text
static_minus_conditional_nll_ci_lower_positive : false
static_minus_conditional_brier_ci_lower_positive: true   (margin +0.0036)
all_fresh_contexts_nonreversing                : false
wind_shuffle_worsens_nll                       : false
normalization                                  : false  (1.6e-06 > 1e-6)
repeat_determinism                             : true
all_queries_in_support                         : true
```

## Interpretation

The spatial wind/map hazard surrogate reproduces the same failure mode as the
rejected 33-feature MLP: conditioning on the (local) wind field does not beat a
capacity-matched static-wind comparator, and shuffling the wind does not hurt.
This is consistent with the handoff's reading that the neural NO-GO reflects a
representation/amortization failure rather than collapse of the underlying
native first-passage mechanism — but now even the preferred spatial
representation fails, indicating the `W_online` local-wind conditioning is not
a load-bearing source of first-passage information in this H01 setup.

The native cross-wind first-passage diagnosis remains
`CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS` and is unaffected by this neural result.

## Terminal boundary

- `CLOSED_LOOP_NOT_AUTHORIZED` remains in force.
- No runtime parity, single-consumption, or 300-s closed-loop development is
  authorized.
- No further neural architecture/version is permitted without a new
  scientifically justified preregistration.

## Evidence artifacts (in this directory)

- `07_M1_PHYSICAL_GATE.json`
- `06_TRAINING_CONTRACT.json`
- `conditional_history.json`, `static_history.json`
- `conditional_best.pt`, `static_best.pt` (checkpoints, SHA-256 below)

Checkpoint SHA-256:

```text
conditional_best.pt  77333d079570393832028f4c25fc0918a70ffe8ab5a5b9909f388c3304fda862
static_best.pt       1e50492fe479040a98a1913cc24dc4798a8e921d39adeb2963d4b8c3166b7844
```
