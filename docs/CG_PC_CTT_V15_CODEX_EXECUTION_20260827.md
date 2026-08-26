# CODEX EXECUTION — CG-PC-CTT V15 completeness gate + proximal bridge

Date: 2026-08-27

Branch to pull:

`cg-pc-ctt-v15-completeness-bridge-20260827`

Parent/frozen checkpoint:

`codex/ctt-v13-m1-go-checkpoint-20260826`

## Mission

Test the highest-probability next version of the main innovation without
changing the already successful CTT M1.

The order is mandatory:

1. qualify the dual completeness gate (`gamma + alpha`);
2. materialize a valid proximal-bridge data contract;
3. qualify the bridge on development then untouched final panels;
4. attack the historical hard H02 failures;
5. only if those gates pass, prepare a 300 s closed-loop integration.

Do not start by editing ROS2 runtime code.

## Zero-tolerance invariants

Do not modify:

- frozen CTT V13 M1 scripts or weights;
- M1 trace-bank content;
- `main_v8`;
- source candidate coordinates;
- transport-member split;
- CTT train/validation/test wind contexts;
- V11/PMFS baseline results;
- any existing frozen evidence artifact.

Runtime-deployable inputs only:

- processed gas;
- local wind;
- pose/odometry/yaw;
- velocity/action history;
- map/occupancy;
- timestamps;
- queried candidate-source coordinates;
- posterior/history when explicitly allowed.

Forbidden runtime information:

- source truth;
- wind ID;
- route ID;
- plume seed;
- simulator transport-member ID;
- simulator phase;
- oracle flow/plume fields;
- future measurements.

Truth is allowed only in a post-hoc offline evaluation panel.

No final-test tuning. No House-specific threshold. No seed-specific threshold.

## Phase 0 — checkout and provenance

```bash
git fetch --all --prune
git checkout cg-pc-ctt-v15-completeness-bridge-20260827
git rev-parse HEAD
git status --short
```

Record:

- repository commit SHA;
- Python version;
- numpy/scipy/torch versions;
- absolute bank root;
- absolute frozen M1 direct-gate output root;
- SHA256 of all scripts used.

Create a new result root. Never overwrite prior result directories.

## Phase 1 — direct completeness-gate qualification on frozen House03 M1

Required code:

`analysis/cg_pc_ctt_v15/completeness_gate.py`

Run:

```bash
python3 analysis/cg_pc_ctt_v15/completeness_gate.py \
  "$CTT_H03_BANK" \
  "$CTT_M1_DIRECT_GATE_ROOT" \
  "$OUT/01_completeness_house03"
RC=$?
echo "completeness_rc=$RC"
```

Do not change constants after seeing final-test output.

Inspect:

- `completeness_gate_result.json`
- `gate_atoms.csv`
- `completeness_gate_contract.json`

Report at minimum:

- development thresholds for gamma-only, alpha-only, dual;
- final accepted coverage;
- accepted vs rejected M1 positive-margin fraction;
- accepted vs overall M1 margin mean;
- gamma-only vs dual accepted positive fraction;
- gamma-only vs dual mean margin;
- source-identity-break control alpha collapse ratio;
- per-test-context results.

### Phase 1 GO logic

The script returns GO only when the development-calibrated dual gate:

- has nontrivial final-test coverage;
- selects test atoms with better M1 source ordering than the overall set;
- improves mean M1 margin;
- and alpha adds value over gamma-only by accuracy or margin.

If it returns `NO_GO`, do not manually move thresholds.

Instead perform one forensic decomposition only:

1. check whether response summary features are degenerate;
2. check whether all local candidate sets are too similar;
3. check whether transport covariance is dominated by a few dimensions;
4. report the singular spectra.

No new threshold search on CTT test contexts.

## Phase 2 — runtime-equivalent gate materialization

Phase 1 uses the frozen simulator first-hit bank to test the principle. If it
passes, materialize the same mathematical object from the deployable M1
candidate x transport-ensemble representation.

Required runtime-equivalent object at update `t`:

`phi[s,m,:]`

with:

- candidate source `s`;
- transport/predictive ensemble member `m`;
- no source truth;
- no environment label or member ID as a feature.

Compute exactly:

`mu_s = mean_m phi[s,m]`

pooled within-source `Sigma_tr`;

fixed 0.10 shrinkage;

local 9-candidate whitened spectrum;

`gamma`, `alpha`.

Do not copy the simulator source truth into the active candidate set.

For runtime, define the active set truth-blindly. Preferred order:

1. top native/outer-posterior candidate regions before causal injection;
2. if fewer than 9, fill by geometric nearest candidate regions;
3. freeze this rule before H02 final testing.

Gate FAIL means exact abstention. Log every gate decision.

## Phase 3 — build the proximal-bridge dataset

Required code:

`analysis/cg_pc_ctt_v15/proximal_bridge.py`

Read first:

`docs/CG_PC_CTT_V15_METHOD_DERIVATION_20260827.md`

The existing first-hit bank is not automatically a valid proximal dataset.
Construct rows only when a valid candidate-independent `R` exists.

### Required training/development arrays

NPZ keys:

- `y`: observed response vector, shape `[N]` or `[N,Dy]`;
- `r`: candidate-independent onboard proxy/history, `[N,Dr]`;
- `s`: synthetic source intervention coordinate/encoding, `[N,Ds]`;
- `z`: candidate/source-side M1 proxy, `[N,Dz]`.

Recommended minimal `R` from deployable history:

- recent local wind x/y sequence summaries;
- wind variance / direction-change summaries;
- recent UAV velocity and yaw-rate summaries;
- encounter count / inter-encounter gap summaries that are computed from past
  observations only;
- sensor transient state computed causally from past processed sensor values.

Every candidate evaluated for one event must see the same `R`.

Recommended minimal `Z(S)`:

- M1 expected arrival time;
- M1 arrival probability by fixed horizons;
- M1 never-arrival probability;
- source-to-query distance;
- source-relative wind parallel/perpendicular terms;
- fixed path/free-support fraction.

`Z` may depend on the queried candidate `S`; it may not use source truth.

### Split

Use development material only to select ridge/representation.

Final test must hold out both:

- external wind/context;
- transport member/replica.

If the dataset cannot provide both, report the exact limitation and keep the
bridge `CURRENTLY TESTING`.

### Sidecar contract

For every NPZ create:

`<name>.npz.contract.json`

with:

```json
{
  "runtime_forbidden_fields_absent": true,
  "r_candidate_independent": true,
  "source_coordinates_are_synthetic_interventions_or_queries": true,
  "test_not_used_for_tuning": true
}
```

Do not set these to true unless verified in code.

### Candidate panels

For dev and final test, produce candidate-panel NPZ with:

- `event_id`
- `candidate_id`
- `is_true`  (evaluation-only)
- `y`
- `r`
- `s`
- `z`

For each `event_id`:

- exactly one `is_true=1`;
- `y` identical across all candidates;
- `r` identical across all candidates;
- at least the true synthetic source + 8 nearest hard negatives.

The script audits these invariants.

## Phase 4 — bridge qualification

Run:

```bash
python3 analysis/cg_pc_ctt_v15/proximal_bridge.py \
  "$TRAIN_NPZ" \
  "$DEV_NPZ" \
  "$DEV_PANEL_NPZ" \
  "$FINAL_PANEL_NPZ" \
  "$OUT/02_proximal_bridge"
RC=$?
echo "bridge_rc=$RC"
```

Do not rerun with altered ridge grid after final test.

Report:

- selected ridge;
- dev moment loss and MSE grid;
- dev direct-vs-bridge Top-1 and mean source margin;
- final direct-vs-bridge Top-1 and mean source margin;
- final positive-margin fraction;
- Z-shuffle control;
- S-shuffle control.

### Bridge GO logic

The current script requires:

- positive dev source-margin gain over same-sieve direct ridge;
- positive untouched final-test gain;
- no worse final positive-margin fraction;
- at least one causal destruction control erases at least half of the bridge
  margin gain.

If bridge is NO_GO, do not tune on final test. Diagnose whether:

1. `R` contains too little information about transport nuisance;
2. `Z` violates/exhausts proxy support;
3. bridge moment operator is weakly identified;
4. candidate panel source effects are below nuisance scale.

If the weakest operator singular values are effectively zero, mark
`WEAK_IDENTIFICATION`, not “model needs more epochs”.

## Phase 5 — historical hard H02 challenge

Use the frozen historical 28 hard H02 combinations where the simple transport
gate had:

- `28/28` negative `true_score - wrong_score`;
- mean approximately `-34.22`;
- true-source rank median approximately `118.5/201`;
- wrong-source rank median approximately `5/201`.

Preferred source artifact:

`h02_transport_gate_fast2.csv`

or its frozen archive copy. Do not regenerate it with changed formulas.

For every hard case:

1. compute runtime-equivalent `gamma,alpha` without truth;
2. apply the Phase 1/2 frozen threshold;
3. if gate FAIL: record exact abstention;
4. if gate PASS: evaluate direct M1 and M1+bridge using post-hoc truth only;
5. no parameter changes between cases.

Produce:

`h02_hard_case_matrix.csv`

columns at minimum:

- case id;
- seed/context;
- gamma;
- alpha;
- gate pass;
- original true-vs-best-false margin;
- bridge true-vs-best-false margin;
- margin delta;
- true-source rank before;
- true-source rank after;
- abstained.

### H02 success interpretation

A useful gate does not need to “fix” an unidentifiable case. Rejecting a
catastrophically misleading update is a valid success.

Strong evidence requires both:

- many historically catastrophic cases are rejected by G_id **or** become much
  less harmful;
- among G_id PASS cases, the bridge moves true-vs-false margins upward and
  ideally through zero.

Do not count an abstained case as a localization win. Report it separately as
error prevention.

## Phase 6 — freeze before closed loop

Only if Phase 1 and Phase 4 are GO and H02 hard-case behavior is non-catastrophic:

1. freeze all thresholds and bridge coefficients;
2. save SHA256;
3. create a single immutable method manifest;
4. no House/seed-specific branches;
5. integrate exact-abstention gate before source-state update;
6. reuse a separately frozen outer posterior/update mechanism;
7. planner unchanged.

Then run the first 300 s closed-loop OFF/ON qualification.

Do not start House01/House02/House03 sweeps all at once.

Recommended first closed-loop order:

1. hardest previously failed House03/House02 development scene;
2. freeze;
3. unseen House01/H02/H03 seeds.

Primary endpoint remains PMFS localization:

`ExpectedValue(sourceProbability, 0.05)` final error.

Also report:

- number/fraction of gate PASS updates;
- number/fraction of exact abstentions;
- posterior entropy only as secondary diagnostic;
- path divergence separately from localization gain.

## Mandatory final report

Create:

`CG_PC_CTT_V15_SCIENTIFIC_VERDICT_20260827.md`

with exactly these sections:

1. provenance;
2. immutable contracts;
3. Phase 1 completeness gate result;
4. Phase 2 deployability audit;
5. Phase 3 proxy/data-contract audit;
6. Phase 4 proximal bridge result;
7. Phase 5 H02 hard-case matrix summary;
8. negative controls;
9. failure analysis;
10. status table:
   - CONFIRMED
   - CURRENTLY TESTING
   - REJECTED
   - HOLD
11. one final verdict:
   - `MAIN_INNOVATION_CANDIDATE_GO`
   - `PARTIAL_GO_GATE_ONLY`
   - `NO_GO`
   - `INVALID_DATA_CONTRACT`

Do not call it a main innovation GO solely because an offline bridge loss
decreases.
