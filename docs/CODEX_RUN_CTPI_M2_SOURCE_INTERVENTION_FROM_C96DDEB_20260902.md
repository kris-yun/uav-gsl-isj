# Codex execution directive — CTPI M2 source-intervention path

Authoritative branch:

`research/ctpi-m2-ba0de54-audit-fix-20260902`

Start from remote HEAD at or after:

`c96ddeb586b9f1a75a0af9e1b6750dccd9da917f`

Read these files first:

1. `docs/CTPI_M2_SOURCE_INTERVENTION_PREGEN_STATUS_20260902.json`
2. `docs/CTPI_M2_BA0DE54_CODE_AUDIT_20260902.md`
3. `experiments/cg_pc_ctt/ctpi_m2_source_intervention_forecast.py`
4. `tools/ctpi_m2_select_controlled_sources.py`

## Scientific freeze

The old `GLOBAL_POSTERIOR_WEIGHTED_ISOTONIC_EVENT_RELIABILITY` candidate is deprecated and must not be revived for CAL/CONFIRM. Its posterior-weighted construction can improve posterior-mixture NLL while collapsing source-conditioned contrasts required by M3.

The authoritative M2 target is the controlled-source action-conditioned forward predictive law:

`P(Y_next | do(S=s), A=a, frozen physical/source contract)`.

For M2 calibration/confirmation, the source is a simulator intervention chosen by the experimental protocol. It is not a runtime localization truth input. Do not pass M1 posterior, localization error, source rank, or planner reward into the M2 fit.

Do not regenerate the frozen predictive bank.

## Phase 0 — pre-generation completion

Do not generate any CAL or CONFIRM observation world until all items below are committed and a machine report emits exactly:

`CTPI_M2_SOURCE_INTERVENTION_PREGEN=PASS`

### A. Freeze controlled-source manifest

Run `tools/ctpi_m2_select_controlled_sources.py` only on the authoritative frozen bank assets. Commit the exact per-House:

- 10 CAL carrier IDs;
- 10 CONFIRM carrier IDs;
- one-to-one assignment to frozen route0..9;
- selector code commit/hash;
- input bank hashes;
- expected K-level coverage.

Selection must use bank-only features and must not inspect any new observation outcome.

### B. Resolve carrier -> physical source placement correctly

A carrier is a source region, not a quadtree-center point. Resolve the existing reserved V3 latent placement `U` for every selected carrier from authoritative source/placement manifests.

For every world record:

- carrier ID and region;
- reserved placement quantile/index;
- exact physical source xyz;
- placement/source-contract file/hash;
- proof that no ad-hoc center/representative coordinate is used.

If the authoritative reserved placement cannot be resolved for any selected carrier, fail closed and stop.

### C. Build authoritative legacy RNG inventory

Do not rely on a hand-written forbidden-seed list. Scan authoritative prior assets and emit a canonical inventory with hashes for every resolvable:

- predictive-member RNG seed/domain;
- historical observation-world seed/domain;
- prospective-gate seed/domain;
- fallback/default generator seed where applicable.

If a historical asset's numeric seed is unavailable, record its world/hash identity and mark numeric disjointness UNKNOWN for that asset. Never turn UNKNOWN into TRUE.

New CAL/CONFIRM transport seeds and domains must be mutually distinct and checked against this inventory.

### D. Freeze generator runtime identity

Preflight and record at minimum:

- `OMP_NUM_THREADS=4`;
- `OMP_DYNAMIC=FALSE`;
- `OPENBLAS_NUM_THREADS=1`;
- `MKL_NUM_THREADS=1`;
- `NUMEXPR_NUM_THREADS=1`;
- `PYTHONHASHSEED=0`;
- exact ROS/GADEN overlay order;
- native multistream binary SHA-256;
- its source SHA-256;
- loaded GADEN library SHA-256;
- RNG hook source SHA-256;
- MathUtils source SHA-256;
- RunningSimulation source SHA-256.

The same numeric seed under a different runtime environment is not accepted as the same world identity.

### E. Commit fail-closed world materializer

Before CAL, commit a materializer/runner that enforces one controlled observation world per native-generator invocation.

It must enforce:

- frozen predictive bank is read-only and never modified;
- fresh output root / no stale status reuse;
- House, carrier, reserved source xyz, route, set, index, RNG domain and numeric seed all match the frozen manifest;
- one independent transport world per invocation;
- full route has exactly 1500 physical samples at 0.2 s;
- causal FOPDT sensor forward operator includes motion and stop samples over the full route;
- 0.4 s dead time, tau=1.2 s, gain=1, baseline/input/state zero initial values;
- 1502 forward samples including the causal tail;
- exactly 15 completed stop events from the first 1500 aligned sensor samples;
- `Y=1` iff max measured concentration over the frozen 80 stationary samples is strictly `>0.1 ppm`;
- source intervention metadata is sealed from runtime localization/planner code;
- output SHA-256 and terminal PASS/FAIL are written per world.

### F. Disposable smoke

Run exactly one disposable smoke identity that is explicitly excluded from CAL and CONFIRM. Verify:

- preflight PASS;
- no write under bank root;
- reproducible rerun under identical runtime/seed;
- expected sample/event counts;
- stable output hash on deterministic rerun;
- source placement provenance;
- no stale output reuse.

Only after A-F pass, commit `PREGEN_AUDIT_REPORT.json` and emit:

`CTPI_M2_SOURCE_INTERVENTION_PREGEN=PASS`

## Phase 1 — CAL only

After the unlock marker, generate only the preregistered 30 CAL worlds: 10 per House.

For each of their 15 visited actions, pair the realized event with the frozen-bank member-hit count for the same controlled carrier/action.

Fit exactly one global table using:

`experiments/cg_pc_ctt/ctpi_m2_source_intervention_forecast.py`

No M1 posterior weighting is allowed.

Freeze and commit before opening/generating CONFIRM:

- CAL dataset manifest and hashes;
- fitted table;
- implementation commit;
- fit report;
- K-level coverage;
- all hyperparameters.

Do not use localization error, true-source rank, planner reward, or M3 metrics to choose the table.

## Phase 2 — one-shot CONFIRM

Only after CAL code/table/hash freeze, generate/open the preregistered 30 CONFIRM worlds exactly once.

Run direct source-conditioned predictive validation using the same controlled source/action pairs. Report at minimum:

- NLL baseline vs M2;
- Brier baseline vs M2;
- ECE baseline vs M2;
- paired tape wins/losses/sign p;
- per-House results;
- stable reverse Houses;
- K-level coverage.

Terminal verdict must be exactly one of:

`CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_PASS`

or

`CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_NO_GO`

On NO-GO: stop. Do not tune on CONFIRM. Do not start M3/C++/ROS.

## Phase 3 — only after M2 PASS

If and only if the direct source-conditioned Gate passes, freeze M2 and expose it to M3 Predictive Information Planning.

M3 must consume the full set of source-conditioned probabilities across candidate actions. Do not collapse them to the posterior-mixture probability.

Before closed loop, first prove offline that candidate actions produce nontrivial variation in predictive mutual information and that selected actions actually differ from the native planner on a smoke case.

Then proceed to C++ parity and true ROS/GADEN closed-loop smoke under the existing causal-chain guards.

## Forbidden

- Do not revive the posterior-weighted isotonic candidate.
- Do not use quadtree centers as physical source placements.
- Do not regenerate the predictive bank.
- Do not inspect CONFIRM before CAL freeze.
- Do not tune formula/source selection/route assignment after seeing new observations.
- Do not allow true controlled-source metadata into runtime localization or planner reward.
- Do not start M3, C++, or ROS before M2 direct source-conditioned PASS.

## Final report to user after the first resumed Codex run

Report only:

1. remote HEAD used;
2. whether A-F pre-generation items passed;
3. the exact `PREGEN_AUDIT_REPORT.json` path/hash;
4. whether `CTPI_M2_SOURCE_INTERVENTION_PREGEN=PASS` was emitted;
5. if PASS, whether CAL generation has started/completed and how many of 30 worlds passed;
6. if blocked, the single first blocking cause and exact evidence path.
