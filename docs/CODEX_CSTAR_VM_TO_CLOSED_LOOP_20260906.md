# CODEX CSTAR — authoritative VM-to-closed-loop execution contract

Date: 2026-09-06
Branch: `g3-cstar-causal-redesign-20260906`
Base legacy snapshot: `2387668ec6345d273a8d630af069d65af710850f`
Status: **EXECUTION CONTRACT**. Scientific redesign is frozen. Codex may implement adapters, train/evaluate the frozen modules, integrate `cstar_v1`, run smoke, and—only after machine authorization—run the 12-case seed12 development closed loop.

## 0. One sentence

Do not invent another M1/M2/M3. Pull this branch, verify assets, run the frozen reference/offline gates, construct only scientifically legal controlled training/evaluation assets when existing data are insufficient, freeze M1/M2 checkpoints, build a bank-free `cstar_v1` runtime, pass causal smoke, obtain `CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZED=TRUE`, then run exactly H01/H02/H03 × seed12 × A0/F00/F10/F11 and stop.

## 1. Scientific identity — immutable during this execution

CSTAR = **Causal Source–Transport Active Resolution**.

- M1 PICR: perturbation-invariant causal source representation. Mother field: single-cell perturbation biology / functional genomics.
- M2 CPO: source- and route-conditioned first-passage/encounter predictive operator. Mother field: chemical physics / rare-event transition-path theory.
- M3 PHS: prospective hypothesis sweeps. Mother field: systems neuroscience / hippocampal prospective sweeps and information symmetry.

Closed causal loop:

`S -> stochastic transport -> sensor memory -> Y -> PICR pi(S) -> do(route) -> CPO future observation law -> PHS route -> new Y`.

Do not replace this with Bayesian nuisance marginalization, peak-SSE plume scoring, GMRF tuning, one-step EIG, MAP chase, or a new heuristic.

## 2. Deployment contract — immutable

Final CSTAR deployment is **bank-free**.

Allowed runtime inputs:
- navigation-height geometry;
- current/past stamped robot pose;
- current/past measured gas;
- current/past local wind;
- audited sensor-memory state;
- current map candidate source domain;
- navigation-feasible candidate future routes.

Forbidden runtime inputs:
- source truth;
- House ID as a model feature;
- simulator/transport-member identity;
- future gas or future wind;
- a site-specific predictive lookup bank;
- oracle full wind field;
- held-out evaluator outcomes.

Existing frozen banks/worlds may be used **offline only** for training/falsification. They must never be queried by `cstar_v1` during a deployment/closed-loop arm.

## 3. First commands on the VM

Use the repository already installed on the GADEN/ROS2 VM.

```bash
set -euo pipefail
REPO=/home/zyc/gsl_ws/src/GasSourceLocalization
BRANCH=g3-cstar-causal-redesign-20260906
cd "$REPO"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
git status --short
git rev-parse HEAD
```

If the working tree contains unrelated uncommitted edits, do not overwrite them. Record the paths and isolate CSTAR work in a clean worktree/branch based on this branch.

Create one fresh evidence root:

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVID=/mnt/hgfs/workspace/CSTAR_EXEC_${STAMP}
mkdir -p "$EVID"
git rev-parse HEAD > "$EVID/START_GIT_SHA.txt"
```

## 4. Mandatory reading before edits

Read in order:

1. `docs/CSTAR_CODEX_READ_FIRST_20260906.md`
2. `docs/CTPI_CSTAR_CAUSAL_THREE_MODULE_THEORY_20260906.md`
3. `docs/CTPI_CSTAR_COMPOSITION_THEORY_20260906.md`
4. `docs/CTPI_CSTAR_CURRENT_CODE_ALIGNMENT_20260906.md`
5. `docs/CTPI_CSTAR_M2_SPARSE_WIND_CONTRACT_20260906.md`
6. `docs/CTPI_CSTAR_2026_DISTANT_FIELD_LITERATURE_LEDGER.md`
7. `docs/CTPI_CSTAR_TERMINOLOGY_AND_LOADBEARING_CORRECTION_20260906.md`
8. `experiments/ctpi_cstar/CSTAR_INTERFACE_CONTRACT.json`
9. `experiments/ctpi_cstar/CSTAR_REQUIRED_EVIDENCE_CONTRACTS_V1.json`
10. this file again.

Executable references to inspect before modifying adapters:
- `experiments/ctpi_cstar/m1_picr/model.py`
- `experiments/ctpi_cstar/m2_cpo/model.py`
- `experiments/ctpi_cstar/m3_phs/phs.py`
- `experiments/ctpi_cstar/cstar_reference.py`
- `experiments/ctpi_cstar/common/trace_io.py`
- `experiments/ctpi_cstar/common/frozen_bank.py`
- `experiments/ctpi_cstar/authorize_closed_loop.py`

## 5. Phase A — reference and causal-contract selftests

Run before using any real outcome:

```bash
python3 experiments/ctpi_cstar/run_reference_selftests.py \
  2>&1 | tee "$EVID/reference_selftests.log"
```

Required: all tests PASS. Correctness/interface defects may be fixed. Do **not** alter the scientific objectives, gate definitions, or data split after looking at performance outcomes.

At minimum the tests must preserve:
- probability normalization;
- hazard -> first-passage algebra;
- encounter CDF monotonicity;
- route committor = `1 - P(no hit by horizon)`;
- Bhattacharyya extrema;
- PHS identical-law resolution 0 / disjoint-law resolution 1;
- source-region placement marginalization;
- PICR arbitrary-map posterior normalization;
- source posterior cannot bypass `zS` through `zN` or unconstrained temporal hidden state;
- latest-at-or-before pose/wind joining;
- candidate domain independence from evaluator source truth;
- future-wind mutation after a decision cannot change that decision's M2 input/features.

## 6. Phase B0 — find and verify all existing VM assets

Run:

```bash
python3 experiments/ctpi_cstar/vm_asset_preflight.py \
  --output "$EVID/VM_ASSET_PREFLIGHT.json" || true
cat "$EVID/VM_ASSET_PREFLIGHT.json"
```

Expected default frozen-bank root:
`/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1`

Expected placement manifest:
`/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/frozen_region_placement_manifest.json`

For every available House bank, run the existing strict verifier:

```bash
BANK=/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1
for H in H01 H02 H03; do
  python3 closed_loop/cpir/verify_cpir_bank.py \
    --root "$BANK/$H" --house "$H" \
    --report "$EVID/${H}_BANK_INTEGRITY.json"
done
```

Do not continue using a bank whose verifier fails.

Audit source-placement versus transport identity:

```bash
PLACEMENT=/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/frozen_region_placement_manifest.json
python3 experiments/ctpi_cstar/audit_bank_causal_pairs.py \
  --placement-manifest "$PLACEMENT" \
  --output "$EVID/BANK_CAUSAL_PAIR_AUDIT.json"
```

### Hard identity rule

**Never** assume `member_00..07` means “same exact source under eight transport realizations.”

A legal exact-source transport intervention pair requires:
- identical `(house, carrier_id, source_xyz)`;
- different transport realization/seed;
- no difference in source position hidden inside the pair.

Same `carrier_id` with different `source_xyz` is only a region-level identity and must not be described as an exact-source transport intervention.

If the audit reports no legal exact-source repeated-transport groups, do not relabel different placements. Use the controlled materialization route in Phase B2.

## 7. Phase B1 — spent seed12 replay is a premise screen only

The old H01/H02/H03 × seed12 A0/F00/F01 traces are valuable for:
- real stamped gas/pose/wind parsing;
- no-future-data audits;
- fixed-trajectory temporal prediction;
- checking that the new representation/operator can consume real historical trajectories.

They are **not** enough by themselves to qualify the final M1/M2 because each House has only one historical true source and source/route are entangled.

Use the selected spent root from `VM_ASSET_PREFLIGHT.json`, or locate it manually without launching a simulator. Then:

```bash
RUN_ROOT=$(python3 - <<'PY' "$EVID/VM_ASSET_PREFLIGHT.json"
import json,sys
p=json.load(open(sys.argv[1]))
print(p.get('selected_spent_root') or '')
PY
)
[[ -n "$RUN_ROOT" ]]

RUN_ROOT="$RUN_ROOT" \
OUT_ROOT="$EVID/spent_replay" \
bash experiments/ctpi_cstar/run_spent_seed12_offline.sh || true
```

`run_offline_gates.py` has been deliberately changed so spent replay can **never** set formal closed-loop authorization true.

Interpretation:
- failure = real premise/implementation problem; stop and report;
- pass = proceed to controlled source-diverse training/falsification;
- do not call it paper-level M1/M2 validation.

## 8. Phase B2 — construct scientifically legal controlled training/falsification assets

This is the only phase allowed to create additional **offline training data** if existing frozen assets are insufficient. It is not a deployment bank and is not a closed-loop campaign.

### 8.1 First reuse existing frozen assets

Inventory before generating anything:
- full-grid CPIR banks;
- `PF_DEI_V3_REGION_PLACEMENT_V1` placement manifest;
- any existing CTPI source-intervention world manifests/materialized worlds;
- old wind-iteration inputs required to reconstruct local wind at sampled poses;
- source-selection / RNG-inventory artifacts used by `tools/ctpi_m2_freeze_world_manifest.py` and `tools/ctpi_m2_materialize_world.py`.

Use `experiments/ctpi_cstar/common/frozen_bank.py` for strict `PFV3STR1` decoding. Do not write another informal binary parser.

### 8.2 M1 controlled data requirement

PICR needs episodes containing deployment-visible channels:
`(time, pose, gas, local wind, sensor state)` plus source label **offline only**.

Required controlled comparisons:
1. same exact source position, different transport realizations;
2. same exact source, different allowed source-strength/release realizations when available;
3. same exact source, different allowed sensor-memory context when available;
4. different source positions under matched/controlled nuisance contexts;
5. House/geometry held out from model features.

The candidate search domain must come from map/free-space/route geometry, never from evaluator truth.

If existing bank identity does not supply same-xyz repeated transport, generate a **bounded offline controlled dataset** at frozen exact source placements with independently seeded transport. Reuse existing world/materialization tooling and freeze the source list/seeds before looking at model outcomes. This is permitted because it trains one general model; it must not become a site-specific deployment lookup bank.

Do not generate more data after seeing which source/seed makes PICR look good. If the preregistered controlled set fails, report M1 NO-GO.

### 8.3 M2 controlled data requirement

CPO cannot be qualified from only three historical true sources. Training/evaluation must contain source diversity across the free source domain / reserved source placements.

For each training/evaluation example, record:
- exact source hypothesis/placement;
- current causal history and local wind only;
- known candidate future route intervention;
- first-passage target `T` / no-hit-by-H from an independent realized future;
- geometry/source-relative features;
- physical-prior outputs.

Split transport realizations and source placements before model selection. Leave one House out for geometry generalization. The held-out side must not be used to tune thresholds or planner coefficients.

The deployable CPO must still accept arbitrary current-map source hypotheses. Offline bank data are examples for learning the operator, not runtime lookup entries.

### 8.4 No fabricated wind

If a full-grid concentration bank does not carry the local wind channel needed by PICR/CPO, do not fill it with a guessed constant or truth field. Recover the audited corresponding wind asset or materialize the controlled episode through the existing simulator/world tooling so stamped local wind is recorded causally.

## 9. Phase C — M1 controlled causal gate

Train:
- PICR with intervention constraint;
- a matched unconstrained temporal encoder with the same capacity/input budget;
- destructive controls: source-label permutation and removal of intervention constraint.

Freeze the train/validation/held-out split before checkpoint choice.

Produce exactly:
`CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1.json`
with contract `CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1` and fields required by `CSTAR_REQUIRED_EVIDENCE_CONTRACTS_V1.json`.

M1 PASS requires all of the following mechanism-level conclusions:
- held-out source proper score improves over matched unconstrained encoder;
- held-out source localization error improves directionally across Houses, not one lucky House carrying the mean;
- same-exact-source nuisance interventions move `zS` less than the unconstrained encoder;
- different-source separation does not collapse;
- source-label permutation destroys source gain;
- removing intervention loss measurably worsens invariance;
- no candidate-domain source-truth leakage;
- source-strength intervention does not recreate the historical fixed-amplitude failure when that controlled factor is available.

If task accuracy improves but these causal tests fail, M1 is NO-GO as the paper's causal contribution. Do not proceed to closed-loop integration.

Freeze the chosen PICR checkpoint and SHA-256 before any closed-loop outcome.

## 10. Phase D — M2 source-diverse predictive gate

Use the frozen M1-independent M2 data split. M2 conditions on a source hypothesis; it does not receive the M1 posterior when estimating `P(O_future | S, do(route))`.

Compare the identical held-out examples against:
1. frozen causal Gaussian-plume/FOPDT provider;
2. uncorrected verified physics prior;
3. full CPO residual operator.

Primary M2 objects:
- first-passage categorical law `P(T=1..H,T>H)`;
- encounter CDF `P(T<=h)`;
- terminal route committor `P(T<=H)`;
- marked log-ppm distribution as secondary diagnostics.

Produce exactly:
`CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1.json`
with contract `CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1`.

PASS requires held-out source-diverse first-passage NLL and Brier to improve over both baselines with cross-House direction reported; calibration cannot be hidden by mean RMSE. Report encounter and non-encounter tails separately.

No future wind/gas is an input. No held-out House bank may be queried by the deployable provider.

Freeze CPO checkpoint and SHA-256 before any closed-loop outcome.

## 11. Phase E — M3 true counterfactual gate

Do not use a single spent route as if all unexecuted routes had realized outcomes.

Build `CSTAR_M3_COUNTERFACTUAL_PANEL_V1` only from genuine same-context multiple-route evaluator outcomes. Preferred low-cost route:
- reuse frozen source/transport assets offline;
- use disjoint planning-provider and outcome-evaluator realizations;
- use placement manifest to keep source-position and transport identity explicit;
- native PMFS route is one candidate whenever feasible;
- route outcomes used for evaluation must not be used to construct the PHS route laws.

If member IDs change source placement, respect that identity. Either evaluate region-level source alternatives explicitly or materialize exact-source independent outcome repeats. Never call different source placements “transport replicates.”

Run:

```bash
python3 experiments/ctpi_cstar/m3_phs/offline_panel.py \
  --panel /path/to/CSTAR_M3_COUNTERFACTUAL_PANEL_V1.json \
  --output "$EVID/CSTAR_M3_COUNTERFACTUAL_GATE_V1.json"
```

The current gate also runs a deterministic route-law destructive shuffle. PASS requires:
- PHS selected routes reduce independently realized source risk versus native route;
- real wins > losses and mean risk delta < 0;
- the route-law shuffle reduces/removes the gain.

If the shuffle preserves the benefit, the supposed prospective mechanism is unsupported: M3 NO-GO.

## 12. Phase F — freeze model identities before production integration

Create `CSTAR_FROZEN_MODEL_MANIFEST_V1.json` with contract `CSTAR_FROZEN_MODEL_MANIFEST_V1`, `pass=true`, and at minimum:
- current git SHA;
- PICR checkpoint path + SHA-256;
- CPO checkpoint path + SHA-256;
- exact training config hash;
- exact M1/M2 gate hashes;
- normalization/scaler state hashes;
- model input/output schema version.

No checkpoint may be replaced after closed-loop outcomes are inspected. Any replacement creates a new experiment identity.

## 13. Phase G — production integration, isolated `cstar_v1`

Only after M1/M2/M3 gates pass.

### 13.1 Isolation

Add a new versioned `cstar_v1` mode. Preserve legacy CPIR, old CTPI M3, V3-ORR, and frozen negative code paths unchanged for reproducibility.

Do not edit old scientific formulas in place and call them CSTAR.

### 13.2 Runtime order

At each legal stamped frame:
1. strict ingress joins current gas/pose/local-wind with no future read;
2. sensor state advances causally;
3. PICR consumes executed history and outputs normalized `pi_t(S)`;
4. at a decision, navigation constructs feasible routes;
5. for every `(source hypothesis, route)`, CPO computes the route observation law using only causal history + `do(route)`;
6. PHS scores all routes; native route must be included whenever feasible;
7. execute selected route;
8. only the actual new observations return to PICR.

### 13.3 F00 adapter

F00 = PICR + native PMFS information planner.

Implement a coefficient-free adapter from PICR posterior to the source-hypothesis weights consumed by the native planner. Required parity test: if injected posterior weights equal native weights, the resulting native information-score vector and selected goal are exactly unchanged within numerical tolerance.

Forbidden in F00:
- MAP chase;
- fitted posterior-guidance lambda;
- PHS;
- learned CPO.

### 13.4 F10 provider

F10 = PICR + PHS + frozen **baseline** route-law provider.

The baseline provider uses the same `CPORouteLaw` schema but is a frozen causal plume/FOPDT or named unlearned physics provider. F10 and F11 must use identical PHS code. F11 changes only the provider to full CPO.

### 13.5 Actual future routes

Use the real navigation path sequence when the stack exposes it, sampled at the frozen prediction cadence.

If a real path API cannot be exposed without redesigning navigation, use the preregistered endpoint+dwell fallback described in the theory/code-alignment docs. Log the fallback mode.

**Never** draw a straight current-pose-to-goal line through obstacles and call it a route.

### 13.6 Model execution substrate

A Python/Torch ROS2 sidecar, TorchScript/libtorch, or equivalent engineering substrate is acceptable if it obeys the same frozen I/O contract and timing. This choice is engineering, not a new scientific contribution.

Load frozen models once. No online fitting, site-specific fine-tuning, House-specific normalization, or model replacement during a run.

### 13.7 Fail-closed fallback

On invalid input, model exception, missed deadline, invalid/non-normalized law, or route-provider failure:
- log the exact reason and timestamp;
- fall back to the native PMFS legal action for that decision;
- do not fabricate a CSTAR result.

Report fallback count/rate. A run dominated by fallback cannot be represented as successful CSTAR evidence merely because it terminates.

## 14. Phase H — production manifest and smoke

Create `CSTAR_PRODUCTION_MODE_MANIFEST_V1.json` with contract `CSTAR_PRODUCTION_MODE_MANIFEST_V1`, including SHA of `CSTAR_FROZEN_MODEL_MANIFEST_V1.json`.

Run one disposable smoke identity, not a formal performance arm. Smoke may use a previously spent/disposable source identity and must be excluded from later formal confirmation.

Smoke checks only:
- stamped monotonicity;
- future-read violations = 0;
- source truth/House runtime feature reads = 0;
- deployment bank queries = 0;
- M1 posterior sums to 1;
- every CPO first-passage law sums to 1;
- encounter CDF monotone;
- route committor consistent;
- every PHS route is navigation-feasible;
- native route included whenever feasible;
- inference latency/deadline recorded;
- fallback events/reasons recorded;
- no legacy scientific formula silently used as `cstar_v1` except named baselines/fallback.

Create `CSTAR_RUNTIME_SMOKE_V1.json` with contract `CSTAR_RUNTIME_SMOKE_V1`, `pass=true` only when these checks pass and with SHA of the production manifest.

Smoke is infrastructure evidence, not a scientific PASS.

## 15. Phase I — machine authorization before any formal closed loop

Run:

```bash
python3 experiments/ctpi_cstar/authorize_closed_loop.py \
  --m1 "$EVID/CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1.json" \
  --m2 "$EVID/CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1.json" \
  --m3 "$EVID/CSTAR_M3_COUNTERFACTUAL_GATE_V1.json" \
  --models "$EVID/CSTAR_FROZEN_MODEL_MANIFEST_V1.json" \
  --production "$EVID/CSTAR_PRODUCTION_MODE_MANIFEST_V1.json" \
  --smoke "$EVID/CSTAR_RUNTIME_SMOKE_V1.json" \
  --output "$EVID/CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1.json"
```

Do not launch the formal matrix unless stdout contains:

`CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZED=TRUE`

The authorizer also verifies cross-file hashes and forbids runtime future reads, truth/House reads, deployment-bank queries, invalid routes, and missing native routes.

## 16. Phase J — authorized closed-loop development matrix

Only after Phase I PASS, run exactly:

- Houses: H01, H02, H03;
- seed: 12 only;
- arms: A0, F00, F10, F11;
- horizon: 240 s;
- total: 12 runs.

Use the same environment/source/wind/randomization identity policy across arms within each House. Do not give only the new arm a corrected map/wind interface.

Arm definitions:
- A0: unmodified Classic PMFS;
- F00: PICR + native PMFS information planner through coefficient-free adapter;
- F10: PICR + PHS + frozen baseline route-law provider;
- F11: PICR + PHS + frozen learned CPO.

Do not add F01 or old CTPI arms to this scientific attribution matrix unless reporting them separately as legacy references.

Every run must keep raw:
- source estimate trace;
- navigation trace / planned and executed routes;
- sensor trace;
- pose trace;
- local-wind trace;
- M1 posterior/audit trace;
- CPO law/calibration diagnostics used at decisions;
- PHS route-score and pair-confusion audit;
- fallback/timeout audit;
- terminal guard/result manifest.

## 17. Phase K — frozen analysis immediately after the 12 runs

Run the already-frozen evaluator:

```bash
python3 tools/cstar_seed12_crosshouse_performance.py \
  --run-root /path/to/CSTAR_12RUN_ROOT \
  --seed 12 \
  --output "$EVID/CSTAR_SEED12_CROSSHOUSE_PERFORMANCE_V1.json"
```

Primary metric is fixed: 240 s localization error AUC, lower is better.

Attribution is fixed:
- M1 = F00 - A0;
- M3 = F10 - F00;
- M2 = F11 - F10;
- full CSTAR = F11 - A0.

Development gate:
- each module increment: improvement in at least 2/3 Houses and lower mean AUC;
- full method: improvement in at least 2/3 Houses, lower mean AUC, and at least 10% mean relative AUC improvement versus A0.

If any module increment fails: record NO-GO for that module and stop. Do not expand to multiple seeds and do not tune weights/thresholds on the same results.

If all pass: stop after the 12-run bundle. Do not automatically launch paper-level multiseed. A fresh confirmation seed set must be preregistered afterward.

## 18. What is allowed to change during execution

Allowed without redefining science:
- file-format adapters after auditing real headers;
- ROS2 topics/services/actions and serialization;
- build/overlay/TF/environment fixes applied symmetrically to baselines and CSTAR;
- batching/caching/vectorization that preserves exact outputs within tolerance;
- route API plumbing;
- robust timeout/fallback logging;
- deterministic checkpoint serialization;
- controlled offline data materialization exactly under Phase B2.

Not allowed:
- new scientific objective;
- House/seed-specific hyperparameters;
- changing PHS objective after outcomes;
- introducing source truth/House ID/future wind/gas;
- deployment bank lookup;
- changing the primary performance metric;
- selecting only favorable Houses/seeds;
- reusing held-out evaluator outcomes for training;
- adding arbitrary planner coefficients to force gains;
- turning a failed gate into PASS by redefining its name.

## 19. Evidence bundle that must be pushed back to GitHub

Before reporting completion, commit/push an indexed evidence bundle containing:
- start/final git SHA;
- `reference_selftests.log`;
- VM asset preflight;
- three bank integrity reports;
- bank causal-pair audit;
- spent replay reports;
- exact controlled-data manifests and hashes;
- M1 controlled causal gate + destructive controls;
- M2 source-diverse predictive gate + calibration/baselines;
- M3 counterfactual gate + destructive shuffle;
- frozen model manifest/checkpoint hashes;
- production-mode manifest and exact code diff summary;
- runtime smoke report;
- formal authorization JSON;
- all 12 raw run directories or immutable references/hashes to them;
- frozen 12-run performance JSON;
- fallback/timeout statistics;
- one final `CSTAR_EXECUTION_SUMMARY.json` with explicit M1/M2/M3/full PASS/NO-GO and no omitted negative result.

If large raw assets cannot be pushed, push immutable SHA-256 manifests plus their exact VM paths and retain the raw directory unchanged.

## 20. Required stopping behavior

Stop immediately and report evidence if any of these occur:
- no scientifically legal source/transport intervention identity can be built;
- M1 causal gate fails;
- M2 source-diverse predictive gate fails;
- M3 real counterfactual gate fails or the destructive shuffle keeps the gain;
- frozen checkpoints cannot be loaded reproducibly;
- production mode needs truth/future/bank input;
- smoke has any future/truth/bank read or invalid route;
- machine authorizer refuses formal closed loop;
- any of F00-A0, F10-F00, F11-F10 fails the 12-run development gate.

A negative result is an acceptable final result. Do not silently redesign CSTAR within this execution.

## 21. Codex autonomy

Codex is authorized to execute Phases A through K continuously on the VM without asking for a new algorithm design, provided every preceding machine/scientific gate passes.

If a required VM path differs from the default, discover the actual immutable asset and record it. If the asset truly does not exist, stop with `BLOCKED_ASSET_MISSING` and list the exact missing identity. Do not substitute synthetic evidence for a real gate.
