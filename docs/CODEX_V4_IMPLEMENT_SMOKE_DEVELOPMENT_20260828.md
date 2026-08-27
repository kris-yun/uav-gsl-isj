# Codex execution contract — V4 implementation -> smoke -> fixed development closed loop

## Mandatory branch

`research/cg-pc-ctt-v4-residual-assimilation`

Do not use the old V4 draft as the normative source. The normative files are:

- `docs/CG_PC_CTT_V4_FINAL_THREE_MODULE_FREEZE_20260828.md`
- `docs/CG_PC_CTT_V4_PREIMPLEMENTATION_VALIDATION_20260828.md`
- `experiments/cg_pc_ctt/v4_final_reference.py`
- `experiments/cg_pc_ctt/selftest_v4_final_reference.py`

## Task

Implement `pfdi_mode=v4_ocsla` as a direct C++ translation of the frozen reference. Do not redesign the method.

### Runtime data contract

1. Keep the existing 8 keyed transport members. Members 0..3 are calibration/resolution; 4..7 are source-outcome scoring.
2. A scoring member keeps the same identity across all physical stops before member marginalization.
3. Record an explicit monotonically increasing `physical_stop_id` from PMFS movement/iteration state. All 8 completed measurement blocks collected before a move share that id. Do not infer stop identity from float position equality.
4. Collapse block predictions/outcomes to physical stops before M2. Prediction drift within one stop is a hard contract failure.
5. Use `eps_T=0.5/(iterationsToRecord+1)`.

### M2

Use actual physical stops only. Never use unobserved full-field stable modes online.

Implement strict LOSO exactly as the Python reference:

- >=3 distinct physical stops;
- all training folds agree on one observation-resolved component B;
- B cannot lose to a rival on any held-out stop;
- B must beat the geometry-prior source-independent context mixture on every held-out stop;
- >=2 held-out stops must be strictly source-informative;
- scoring-member leave-one-out may not reverse B.

Any failure -> ABSTAIN.

### M3

ABSTAIN -> output current native PMFS posterior exactly.

ACCEPT -> update independent causal region-vs-complement state, then apply KL/I-projection mass floor to current native PMFS posterior.

If native mass beta on B is already >= causal mass alpha, output native PMFS exactly. Never flatten a better native state.

Do not clear accepted stable state. Do not replay consumed raw windows.

## Logging required for every source update

- run uuid / house / seed / source-update id;
- explicit physical stop ids and block counts;
- within-stop prediction drift;
- candidate/member/stop dimensions and hash;
- observation-resolved component labels;
- all LOSO training best sets;
- selected component B;
- held-out context-null gains;
- held-out rival margins;
- informative-heldout count;
- scoring-member LOO result;
- ACCEPT/ABSTAIN reason;
- pre/post causal state hash;
- alpha, native beta, I-projection active flag;
- exact-native equality residual on ABSTAIN or inactive projection;
- output probability mass / NaN audit;
- wall time.

## Required tests before ROS smoke

Run:

`python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py`

Then add C++ parity tests for the same cases. Python and C++ must agree on ACCEPT/ABSTAIN, selected mask, alpha/beta and output posterior within numerical tolerance.

## Infrastructure smoke

Use one non-development smoke seed not in 0..19 (recommended 314159) on House02.

Smoke is not a performance experiment. It checks only:

- correct mode dispatch;
- physical-stop grouping;
- no old V3/EC-ECDL fallthrough;
- no truth leakage;
- exact native on ABSTAIN;
- finite/mass-conserving posterior;
- accepted state persists;
- 300 s stop works;
- audit files complete.

Do not tune from smoke localization error.

## Fixed development closed loop

After smoke PASS, freeze git SHA / binary SHA / launch SHA and run exactly:

`H01,H02,H03 × seeds 0..9 × OFF/ON`, 60 arms total.

- OFF = frozen Classic PMFS;
- ON = V4 OC-SLA;
- `TIMEOUT_SEC=300`;
- `STEPS_SOURCE_UPDATE=3`;
- same native deterministic contract and paired environment;
- no mid-matrix changes;
- no House/seed-specific parameter edits;
- no 2/3/5-seed pilot.

Aggregate only after all 60 arms finish.

### Development GO

- 30/30 valid pairs;
- pooled top-5 expected-location error reduction >=10%;
- >=20/30 pairs improve;
- no House pooled degradation >5%;
- ON introduces 0 new false-confident collapses;
- all runtime contract checks pass.

If development GO: freeze and then run fresh confirmatory seeds 10..19.
If development NOT-GO: stop; return full evidence package and failure audit. Do not tune seeds 0..9 again.
