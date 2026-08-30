# CTT NEXT AGENT — EXACT CONTINUATION CONTRACT

Date: 2026-08-30
Status: **resume execution; do not redesign paper-level method**

This document is the direct operational continuation from the previous Codex session.

---

## PHASE 0 — RESUME WITHOUT LOSING PROVENANCE

1. Checkout:

```bash
git fetch origin
git checkout handoff/ctt-final-agent-resume-20260830
```

2. Create a new work branch from this handoff branch. Do not work directly on PR #8/#9 review branches.

Suggested name:

```text
agent/ctt-final-hazard-closedloop-20260830
```

3. Record:

- parent SHA;
- clean/dirty worktree state;
- VM identity/IP;
- ROS/GADEN overlays;
- binary SHA-256;
- current bank/evidence paths and free disk.

4. Do not delete old bank/evidence roots.

---

## PHASE 1 — FIND THE REAL SHARED DATA FIRST

User-provided authoritative practical hint:

```text
Windows shared workspace:
D:\ZYC\A-gas\workspace
```

The dataset is already unpacked there. Do not resume the unnecessary Zenodo download unless the shared copy is proven incomplete.

Resolve VMware shared folders by inspecting:

- VMware configuration if needed;
- `/mnt/hgfs` and other mounted shares;
- path contents and hashes.

Do not assume mount name from memory.

### Required output before any model work

Create and commit:

```text
docs/FRESH_WIND_INVENTORY_20260830.md
experiments/cg_pc_ctt/ctt_final_hazard_20260830/FRESH_WIND_INVENTORY_20260830.json
```

Inventory every House01 item that could be a genuine independent wind context:

- absolute Windows/shared path;
- VM mounted path;
- airflow/config name;
- wind iteration/realization identifier;
- file count/format;
- SHA-256 of primary wind/config artifacts;
- map/scene hash;
- whether already consumed by contexts 0..9 or diagnostic contexts 1/2;
- eligible fresh? YES/NO and reason.

Inventory is metadata/provenance only; do not compute source-ranking/test performance from fresh fields yet.

### Fresh-wind requirement

Need six genuinely unused H01 wind contexts if available:

```text
4 -> final neural confirmatory test
2 -> later closed-loop development
```

Logical IDs `10..15` are labels only. They may point to differently named real wind realizations.

If >=6 eligible unused contexts exist, preregister the mapping.

If <6 exist:

```text
FRESH_WIND_INPUT_BLOCKED
```

Stop before test fabrication. Do not copy/perturb old fields and do not silently switch Houses.

---

## PHASE 2 — FREEZE ONE FINAL NEURAL PHYSICAL SOLVER

Only after the fresh-wind inventory is known, but **before opening/generating fresh confirmatory performance**, freeze one architecture.

No residual TCN. No 33-summary MLP rescue.

### Allowed scientific model

**Spatial physics-conditioned first-passage hazard solver**.

For bin `j=1..80`:

```text
h_j(s,X) = P(F=j | F>=j, s, X)
```

Induced distribution:

```text
P(F=j)     = h_j * Π_{r<j}(1-h_r)
P(F=never) = Π_{r=1..80}(1-h_r)
```

Loss:

```text
if F=j:
  -log(h_j) - Σ_{r<j}log(1-h_r)
if never:
  -Σ_{r=1..80}log(1-h_r)
```

### Representation requirement

Use a source-independent **spatial wind/map representation**, then condition on candidate source/query geometry.

Preferred family:

```text
spatial wind/map encoder
+ source/query geometric conditioning
+ hazard decoder
```

Do not reduce wind to the old fixed 33-D statistical summary as the only representation.

### Freeze every degree of freedom

Before fresh confirmatory data is opened, commit JSON specifying:

- exact input tensor/columns/order;
- coordinate frame/time semantics;
- map/obstacle channels;
- wind channels and source (`W_gen`, `W_online` classification);
- grid/corridor extraction procedure;
- architecture/layers/widths/activations;
- parameter count;
- normalization statistics source;
- optimizer;
- learning rate;
- batch size;
- max epochs;
- patience;
- training seed;
- checkpoint tie-break;
- STATIC comparator construction;
- wind-shuffle mapping/seed;
- TIME_PERMUTE mapping/seed;
- candidate temporal-shuffle mapping/seed;
- bootstrap repetitions and cluster unit.

No edits after fresh test results except documented engineering-bug fixes that do not alter scientific semantics.

### Wind deployability audit

For every neural wind feature record:

```text
feature_name
training_source
runtime_source
frame
time semantics
simulator-only? yes/no
future-dependent? yes/no
```

If exact simulator wind field is used, explicitly label the experiment `SIMULATION_KNOWN_WIND`; do not claim real-flight deployment.

---

## PHASE 3 — FINAL FRESH NEURAL CONFIRMATORY TEST

Assign four genuinely fresh H01 wind contexts from the inventory as logical:

```text
10,11,12,13
```

These fields must not have been used for feature engineering, architecture decisions, training, validation, or prior diagnosis.

Training remains on old development contexts:

```text
TRAIN winds: 0,3,5,6,8,9
VAL winds:   4,7
DIAGNOSTIC-ONLY forever: 1,2
```

Transport:

```text
train keys: 0..5
fresh test keys: 6,7
```

Routes:

```text
train: 4001..4003
val:   4004
fresh test: 4005
```

Generate one coherent plume world per `(source, wind, key)` and sample routes from that world; route sampling must not consume new plume RNG.

For four new winds:

```text
4 x 210 x 8 = 6720 coherent worlds
```

### Capacity-matched comparator

Train a STATIC-WIND comparator with identical architecture/data/seed/order; replace dynamic wind representation with the preregistered TRAIN reference/mean representation without adding parameters.

### Fresh neural physical GO

All required:

1. `STATIC - CONDITIONAL` NLL paired clustered 95% CI lower bound > 0.
2. `STATIC - CONDITIONAL` integrated arrival-CDF Brier lower bound > 0.
3. All four fresh contexts 10..13 individually non-reversing for both metrics.
4. Matched wind-context shuffle worsens conditional NLL with lower 95% CI > 0.
5. Probability normalization max error < 1e-6.
6. Repeated inference deterministic within frozen tolerance.
7. No invalid/obstacle query receives illegal support under inherited mask semantics.

Failure terminal:

```text
CTT_FINAL_HAZARD_NEURAL_M1_NO_GO
```

If this fails, STOP the current neural CTT implementation. Do not create another network version.

---

## PHASE 4 — FRESH SOURCE-EVIDENCE GATE

Only if PHASE 3 PASS.

On fresh contexts 10..13, held keys 6/7, route4005, compare:

- `NEURAL_FULL_FIRST_PASSAGE`
- `SURVIVAL_ONLY`
- `TIME_PERMUTE`
- `CANDIDATE_TEMPORAL_SHUFFLE`
- `STATIC_WIND_FULL`
- `NATIVE_EMPIRICAL_FIRST_PASSAGE` as physical reference/upper comparator.

Report overall + each context:

- normalized true-source rank;
- median rank;
- Top-5;
- Top-10;
- win/loss/tie;
- one-sided exact sign tests.

GO all required:

1. FULL mean normalized rank < SURVIVAL, p<=0.01.
2. FULL Top-10 >= SURVIVAL.
3. FULL < TIME_PERMUTE, p<=0.01.
4. FULL < candidate temporal shuffle, p<=0.01.
5. FULL < STATIC_WIND_FULL, p<=0.01.
6. No fresh context 10..13 reverses the mechanism direction.

Failure terminal:

```text
CTT_FINAL_NEURAL_SOURCE_EVIDENCE_NO_GO
```

No runtime/closed loop after failure.

---

## PHASE 5 — FREEZE RUNTIME SOURCE UPDATE

Only after PHASE 3+4 PASS.

For stop `b`:

```text
L_b(s) = P_theta(F_b_obs | s, X_b)
```

Posterior:

```text
log q_b(s) = log q_{b-1}(s) + log L_b(s) - logsumexp(...)
```

### Exact single-consumption contract

For the same 80 measured gas samples:

CTT ON:

- native sensor processing: KEEP
- persistent sensor state: KEEP
- measured gas/environment map: KEEP
- wind mapping: KEEP
- occupancy/map: KEEP
- planner shell: KEEP
- native PMFS source HIT/NOTHING likelihood for those samples: DISABLE
- CTT first-passage source likelihood: ENABLE exactly once

No product of native source likelihood and CTT likelihood for the same observation.

Ledger every assimilation:

```text
run_uuid
physical_stop_id
sample_start
sample_end
observation_hash
assimilation_method
```

Each observation hash may appear exactly once in source inference.

Threshold extraction remains:

```text
first j with measured_ppm > 0.1
```

not `>= 0.1`.

---

## PHASE 6 — RUNTIME QUALIFICATION

Do not run 300-s closed loop until all PASS:

1. Python neural probability vs deployment implementation parity.
2. First-passage extraction parity.
3. Posterior update parity.
4. Posterior normalization/finite values.
5. Single-consumption ledger.
6. No future leakage.
7. Persistent sensor semantics unchanged.
8. CTT OFF reproduces authoritative main_v8 native behavior.
9. Median total source-update wall time <= 1.30x native under same VM contract, or provide a preregistered accepted budget if the existing project contract specifies another exact bound.

The VM previously lacked ONNX Runtime/LibTorch. Do not force a deployment dependency before PHASE 3/4 pass. After pass, choose the smallest auditable deterministic deployment route and freeze it before runtime qualification.

If runtime fails scientifically:

```text
CTT_H01_RUNTIME_QUALIFICATION_NO_GO
```

Engineering-only bugs may be fixed without changing model/likelihood contracts.

If all pass:

```text
CTT_H01_CLOSED_LOOP_DEVELOPMENT_AUTHORIZED = YES
```

Then proceed automatically to PHASE 7; do not ask for method redesign.

---

## PHASE 7 — H01 300-S PAIRED OFF/ON DEVELOPMENT

Reserve two additional genuinely fresh wind contexts from the inventory as logical:

```text
14,15
```

They must not have been used for neural training/validation/confirmatory test.

Run four planner/search seeds per wind:

```text
seed0, seed1, seed2, seed3
```

Total:

```text
2 winds x 4 seeds x OFF/ON = 16 runs = 8 paired conditions
```

Pair-contract equality:

- source truth;
- generating wind;
- plume/source world RNG;
- initial UAV pose;
- planner RNG;
- map;
- horizon 300 s;
- all non-method parameters.

OFF:

```text
authoritative main_v8 Classic PMFS
```

ON:

```text
same main_v8 shell, only source gas-likelihood assimilation replaced by frozen CTT first-passage likelihood
```

Do not change planner objective, waypoint cost, controller, stopping criterion, horizon, or non-source PMFS state update.

### Official metrics only

Use existing project evaluation code; do not redefine metrics.

Primary:

- official 300-s normalized AUE/source-probability metric;
- final localization error via existing `ExpectedValue(sourceProbability, 0.05)` path.

Secondary:

- MAP error;
- localization-error time trace;
- source-posterior entropy;
- source-update runtime.

### H01 development GO

All preregistered:

1. equal-condition mean normalized AUE improvement >=10%;
2. equal-condition mean final expected-value localization-error improvement >=10%;
3. at least 6/8 paired conditions improve primary AUE;
4. neither wind14 nor wind15 has mean primary-metric degradation >5%;
5. no crash/NaN/posterior invalidity;
6. runtime qualification remains valid;
7. no result-dependent tuning.

Failure:

```text
CTT_H01_300S_CLOSED_LOOP_DEVELOPMENT_NO_GO
```

Stop. Do not rescue with another network/head/gate/planner change.

Pass:

```text
CTT_H01_300S_CLOSED_LOOP_DEVELOPMENT_GO
```

Then package and freeze binary/checkpoint/source for later H02/H03 external confirmation. Do not tune H01 further.

---

## NON-NEGOTIABLE SCIENTIFIC RULES

- No V8/V9 method rescue cycle.
- No post-test architecture changes.
- No blend/alpha/temperature.
- No learned fallback/reliability gate.
- No Top-K rescue or posterior projection.
- No source rank/localization error in neural training/checkpoint selection.
- No reuse of diagnostic wind contexts 1/2 as confirmatory test.
- No fake fresh winds by copying/noising old fields.
- No closed loop with the rejected old 33-feature MLP.
- Preserve all hashes, commits, scripts, manifests, stdout/stderr, and case-level CSVs.
- Push every new freeze/code/result to a new GitHub branch so a later Codex1 can audit exact bytes.
