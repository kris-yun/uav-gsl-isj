# CODEX TASK — V5 direct closed-loop implementation and falsification

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v5-active-sequential-intervention`

Base V4 STOP commit: `aa57af74a54dcdf746052e5b2477ac3a7180a3a8`

Normative science contract: `docs/CG_PC_CTT_V5_ACTIVE_SEQUENTIAL_INTERVENTION_FREEZE_20260828.md`

## Objective

Implement and test V5 as the first version that can **actively acquire new causal-identification evidence in closed loop** when passive M2 evidence is insufficient.

Do not loosen V4/V5 scientific checks after seeing coverage or localization performance.

Do not use true-source coordinates, localization error, ON/OFF improvement, House-specific thresholds, or seed-specific thresholds in M1/M2/probe decisions.

## Stage 0 — sync and prove the Python reference

1. Pull the current branch HEAD and record the exact SHA in the report.
2. Run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py
python3 experiments/cg_pc_ctt/selftest_v5_active_sequential_reference.py
```

Both must PASS. Any reference failure blocks C++.

Also run the existing CTT bank I/O selftest.

## Stage 1 — truth-blind cumulative replay using the already materialized 150 contexts

Do **not** rebuild the 150 trace banks unless an input is missing. Reuse:

`/home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/contexts`

Export only spatial physical-cell identities from the archived OFF runtime:

```bash
python3 experiments/cg_pc_ctt/export_v5_stop_manifest.py \
  --archive-root /home/zyc/CG_PC_CTT_V3_ORR_MULTI30_20260827 \
  --out-csv artifacts/v5_truthblind_ledger/v5_stop_manifest.csv
```

Then run:

```bash
python3 experiments/cg_pc_ctt/v5_truthblind_run_coverage.py \
  /home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/contexts \
  --stop-manifest artifacts/v5_truthblind_ledger/v5_stop_manifest.csv \
  --out-csv artifacts/v5_truthblind_ledger/v5_passive_ledger_coverage.csv \
  --out-json artifacts/v5_truthblind_ledger/v5_passive_ledger_coverage.json
```

Required integrity checks:

- 30 runs and 150 contexts present;
- no truth/performance keys opened;
- one stable PMFS physical-cell key per actual stop;
- repeated spatial cell does not increase evidence-ledger sample size;
- candidate and scoring-member permutation invariance remains valid;
- minimum effective-covariance eigenvalue remains positive;
- no old observation is counted twice when the causal posterior is recomputed.

Write:

`docs/V5_PASSIVE_LEDGER_COVERAGE_REPORT_20260828.md`

Report, without reading localization truth:

- runs with any passive V5 ACCEPT, total and by House;
- first ACCEPT source-update per run;
- final unique-stop count per run;
- context-blocked abstention reason distribution.

### Interpretation

If passive cumulative replay already yields `>=20/30` runs with at least one ACCEPT, record:

`V5_PASSIVE_LEDGER_ACTIONABLE_FOR_CPP = YES`

If it yields `<20/30`, record:

`V5_PASSIVE_LEDGER_ACTIONABLE_FOR_CPP = NO_ACTIVE_PROBE_REQUIRED`

**Do not stop the V5 research path merely because passive replay is <20/30.** Archived OFF trajectories contain no counterfactual gas outcomes at probe locations. The fixed V5 active intervention exists specifically to create those new observations in ON closed loop.

## Stage 2 — C++ mode

Add a new mode only:

`pfdi_mode=v5_active_sequential`

Do not alter Classic PMFS OFF and do not mutate the frozen V4 mode.

Implement formula-for-formula parity with:

`experiments/cg_pc_ctt/v5_active_sequential_reference.py`

### 2A. Persistent ledger

Runtime state must retain across source updates:

- stable physical PMFS cell ids already admitted to evidence;
- one fractional stop outcome per unique cell;
- the contemporaneous truth-free `p[s,m,stop]` for all 8 keyed members;
- the source-update context id that first admitted each cell;
- frozen geometry prior and persistent carrier ordering.

Eight raw blocks at one stationary stop remain one unit-weight physical-stop observation.

A later revisit to the same PMFS cell may update native PMFS but must not increase V5 evidence sample size.

### 2B. Context-blocked M2

At each source update:

- build M1 components over the cumulative unique-stop predictor matrix;
- use source-update context as the validation block;
- require at least 3 effective contexts and 6 unique stops;
- preserve one source/member identity across all training stops;
- require one common best component across context-LOO folds;
- require every held-out context to beat both its strongest rival and the Jeffreys-Beta source-independent null;
- require at least two informative held-out contexts;
- require scoring-member LOO not to reverse the accepted component.

No threshold sweep is allowed.

### 2C. M3 no-double-counting rule

On ACCEPT:

- recompute `q_causal` from geometry prior `q0` and the complete ledger exactly once;
- do not use previous `q_causal` as a prior on the same old stops;
- apply the V4 minimum-KL/I-projection mass floor to the current native PMFS posterior.

On ABSTAIN, posterior output must remain native PMFS exactly.

### 2D. Active probe on ABSTAIN

This is the direct-closed-loop fix and must not be omitted.

Before the next gas outcome exists:

1. ask the **native planner** for its normal feasible next physical-stop candidate set and native chosen candidate;
2. obtain truth-free CTT hit probabilities at those candidate cells for the same persistent source carriers and all 8 keyed members;
3. mark already admitted V5 physical cells as visited;
4. compute `robust_probe_override(...)` exactly as the Python reference;
5. use current native PMFS posterior as `source_weight`;
6. if V5 returns `PROBE`, replace only the next measurement target;
7. if V5 returns no strict gain, use the native target exactly.

The V5 probe may not enlarge the native planner's motion horizon or choose an infeasible target.

Crucial runtime contract:

- `ABSTAIN + PROBE`: posterior exactly native, planner target may differ;
- `ABSTAIN + no PROBE`: posterior and planner target both exactly native;
- `ACCEPT`: M3 may change posterior, then planner consumes the projected posterior normally.

For an override, require strict native dominance:

`U(x*) > U(x_native) + numerical_zero`

where

`U(x)=min_{m=4..7} IG_m(x)`.

No travel-cost coefficient, temperature, blend weight, House threshold, seed threshold, or tuned information-gain cutoff may be added.

## Stage 3 — Python/C++ parity

Create deterministic parity fixtures for all of:

1. three-context consistent ACCEPT;
2. contradictory held-out context ABSTAIN;
3. `.01 vs .005` all-hit absolute-null rejection;
4. source-candidate permutation;
5. scoring-member permutation;
6. repeated physical-cell deduplication;
7. full-ledger causal-state no-double-counting;
8. active-probe candidate permutation;
9. visited best probe exclusion;
10. native-dominance override and no-override cases.

Python and C++ must agree on:

- cumulative component partition;
- unique-stop ledger membership;
- ACCEPT/ABSTAIN reason;
- selected component mask;
- held-out context absolute gains;
- rival margins;
- `alpha`, native `beta`, projection-active flag;
- active-probe utility for every feasible candidate;
- native utility;
- chosen probe cell or exact native fallback;
- final posterior.

## Stage 4 — real closed-loop infrastructure/actionability smoke

Use only fixed non-development, non-confirmatory smoke seeds:

- `314159`
- `271828`

Run H01/H02/H03 with `pfdi_mode=v5_active_sequential` under the existing 300 s contract.

The smoke is **not** a localization-performance experiment. Do not tune from final error.

Audit only:

- process stability / no SIGSEGV;
- CTT member identity remains coherent;
- physical-cell ledger deduplicates correctly;
- source-update context blocks advance correctly;
- `ABSTAIN + PROBE` leaves posterior bitwise/numerically native before planner selection;
- every probe target is native-feasible and spatially unvisited in the V5 ledger;
- every probe override strictly dominates the native target in robust information gain;
- a probe observation enters the ledger only after it is physically measured;
- q_causal does not double-count older stops;
- no truth/performance field appears in decision audit.

Required smoke report:

`docs/V5_DIRECT_CLOSED_LOOP_SMOKE_20260828.md`

If the active-probe path never executes in all six fixed smoke runs while passive replay is `<20/30`, stop and report `V5_ACTIVE_PATH_NOT_ACTIONABLE`; do not lower the scientific gate.

Otherwise continue.

## Stage 5 — frozen 60-arm development matrix

Run exactly:

`H01,H02,H03 x seeds 0..9 x OFF/ON = 60 arms`

- OFF = frozen Classic PMFS;
- ON = frozen `v5_active_sequential` binary/config;
- paired deterministic environment;
- `TIMEOUT_SEC=300`;
- no mid-matrix code or parameter edits;
- no pilot tuning on seeds 0..9.

Freeze git SHA, binary hash, launch/config hash before the first arm.

Development GO remains exactly:

- 30/30 valid pairs;
- pooled top-5 expected-location error reduction `>=10%`;
- `>=20/30` paired runs improve;
- no House pooled mean degradation `>5%`;
- zero new false-confident collapses;
- all V5 runtime contracts pass.

If GO, freeze everything and only then use fresh confirmatory seeds `10..19`.

If NOT-GO, stop and return the evidence. Do not retune development seeds 0..9.

## Required final deliverables

Commit all code plus:

- `artifacts/v5_truthblind_ledger/v5_stop_manifest.csv`
- `artifacts/v5_truthblind_ledger/v5_passive_ledger_coverage.csv`
- `artifacts/v5_truthblind_ledger/v5_passive_ledger_coverage.json`
- `docs/V5_PASSIVE_LEDGER_COVERAGE_REPORT_20260828.md`
- Python/C++ parity artifacts
- `docs/V5_DIRECT_CLOSED_LOOP_SMOKE_20260828.md`
- if Stage 5 executes, the full fixed development matrix CSV/JSON/report

Do not claim >=10% improvement until Stage 5 actually demonstrates it.
