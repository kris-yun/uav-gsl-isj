# CODEX TASK — PF-DEI sensor-memory mechanism and SBI Stage 1

Date: 2026-08-28

Precondition: an independently verified run has returned

`PF_DEI_FORWARD_OPERATOR_CLOSED`.

This task begins the next scientific stage.  It does **not** authorize C++ or the 60-arm performance matrix.

Read first:

- `docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`
- `docs/PF_DEI_SENSOR_MEMORY_ROOT_CAUSE_DERIVATION_20260828.md`

## Stage 0 — merge/freeze forward-closure provenance

The closure commit/report may live on a Codex work branch before it reaches this research branch.  Do not discard it.

Record exact:

- forward-closure commit SHA;
- native GADEN shared-library/source hashes;
- native sensor source/config hashes;
- deployed ROS overlay source/config hashes for every new formal run.

The historical `/dev/shm` overlay loss is a reproducibility limitation, not a reason to reinterpret the already closed physical operator.

## Stage 1 — reproduce the truth-blind sensor-memory lower bound

Run on the forward-closure observed manifest:

```bash
python3 experiments/cg_pc_ctt/pf_dei_sensor_memory_bound.py \
  <PF_DEI_FORWARD_CLOSURE_ROOT>/artifacts/pf_dei_forward/observed_block_manifest.csv \
  --tau 1.2 --sample-dt 0.2 --samples-per-block 10 --threshold 0.1 \
  --out-json artifacts/pf_dei_mechanism/sensor_memory_bound.json \
  --out-csv artifacts/pf_dei_mechanism/sensor_memory_transitions.csv
```

Expected evidence-package reference values to check, not fit:

- physical stops: 514;
- inter-stop transitions: 484;
- history-alone guaranteed next-block HIT transitions: 102/484;
- House01 0/161;
- House02 37/163;
- House03 65/160.

A mismatch must be explained from manifest/provenance before continuing.  Do not tune sensor parameters to recover these counts.

Freeze:

`SENSOR_HISTORY_LOCALITY_FALSIFIED = YES`

because the already closed synthetic parity case contains an identical zero-concentration evaluation suffix whose native measured/block outcome changes when the prior sensor history is reset.

## Stage 2 — generate one coherent candidate-source forward dataset per archived OFF run

Use the closed native GADEN concentration path and exact native run-persistent sensor model.

For each House/seed OFF trajectory:

1. use only observed poses/timestamps/wind/runtime context;
2. never read the true source or localization error;
3. evaluate the frozen source candidate grid;
4. sample transport nuisance independently of source truth/performance;
5. generate physical concentration along the **complete run timeline**, including movement intervals required to propagate sensor state;
6. run one continuous native sensor state from run start to run end;
7. retain measured ppm only at the exact historical consumed sample times for inference, but preserve full state/time provenance;
8. do not reset sensor state at stop or source-update context boundaries.

Required paired payloads from the exact same physical concentration trace:

- `ideal`: measured ppm = physical ppm at the observed sample schedule, no dynamic memory;
- `native`: exact persistent native sensor output.

The two arms must differ only by the observation/sensor operator.

## Stage 3 — freeze a single run-prefix ratio estimator for the matched A1/A2 test

Do not return to context-independent likelihood multiplication.

Train a candidate-conditioned neural ratio estimator on forward simulations only.

### Statistical target

For observable trajectory/runtime context `kappa`, complete measured prefix `D`, and candidate source `S`, estimate

`log r(D,S,kappa) = log p(D|S,kappa) - log p(D|kappa)`.

Generate classification examples by:

- positive: `(D, S)` from the same simulation;
- negative: `(D, S_minus)` where `S_minus` is sampled from the same House/context geometry prior but is independent of `D`.

Never use development true-source labels to build negatives.

### Input contract

The sequence encoder receives the complete run prefix, not isolated contexts.  At minimum include:

- measured ppm;
- sample timestamp / delta time;
- robot pose;
- causally available wind;
- stop/block/context boundary markers;
- candidate-source coordinates or candidate-relative geometry features.

Do not expose House/seed IDs as predictive shortcuts.  If a separate model is trained per House for this diagnostic, use exactly the same architecture/hyperparameters and state that this is a within-environment mechanism test, not zero-shot cross-House generalization.

### Architecture freeze before observed evaluation

Use one modest architecture chosen before looking at H01/H02/H03 localization outcomes.  Record random seed, optimizer and all hyperparameters.  The A1/A2 arms must use the same architecture/training protocol and matched simulation counts.

Random-prefix augmentation is allowed so the model can support sequential online inference later.

## Stage 4 — synthetic-only qualification before historical observed data

Before evaluating the 30 historical OFF runs, require on held-out forward simulations:

- source-candidate permutation equivariance / posterior permutation consistency;
- negative-source shuffle test is live;
- transport randomization is source-independent;
- sensor state is not reset in the native arm;
- random-prefix posterior uses only prefix observations;
- posterior normalizes and is finite;
- simulation-based calibration / rank behavior is reported on synthetic draws;
- A1 and A2 use identical source/transport/trajectory simulations.

If the ratio estimator cannot recover source information on synthetic held-out simulations, stop and fix the inference implementation without opening development localization outcomes.

## Stage 5 — truth-blind matched A1/A2 mechanism evaluation

Evaluate the same 30 historical observed OFF trajectories under:

- A1: ideal-sensor forward model;
- A2: native persistent-sensor forward model.

Do not inspect true source or localization error.

Report only truth-blind predictive/adequacy quantities, including whether source evidence learned from earlier run prefixes remains predictive for later observations.

The primary scientific question is not whether A1 or A2 localizes the true source yet.  It is whether the native persistent observation process changes the cross-prefix source evidence relative to the same physical transport traces under an ideal sensor.

Frozen interpretation:

- A1 adequate, A2 inadequate -> `SENSOR_MEMORY_DOMINANT`;
- A1 and A2 both adequate, old occupancy proxy inadequate -> `OBSERVATION_PROXY_DOMINANT`;
- A1 and A2 both inadequate -> proceed to Stage 6 transport-family test;
- A2 adequate despite A1 failure -> investigate inference/calibration pathology before any performance claim.

## Stage 6 — broaden transport only if both A1 and A2 remain inadequate

Use source-independent physics-randomized GADEN nuisance ranges from simulator/config provenance or a pre-frozen physical uncertainty specification.

Do not tune ranges from H01/H02/H03 localization outcomes.

Retrain/re-evaluate the exact same run-prefix ratio architecture with the broader transport distribution and native sensor chain.

If adequacy restores only here, freeze:

`FINITE_TRANSPORT_FAMILY_INSUFFICIENT = YES`.

## Stage 7 — required scientific verdict before any localization performance

Return exactly one:

- `OBSERVATION_PROXY_DOMINANT`
- `SENSOR_MEMORY_DOMINANT`
- `TRANSPORT_FAMILY_DOMINANT`
- `MIXED_OBSERVATION_SENSOR_TRANSPORT`
- `SBI_INFERENCE_NOT_QUALIFIED`

No localization error is allowed in selecting this mechanism label.

## Stage 8 — only after a mechanism-qualified source model

Only after the truth-blind mechanism stage identifies an adequate native sensor-aware source model may a separate frozen task inspect development source/localization performance and test the existing GO requirements:

- pooled expected-location error improvement >=10%;
- at least 20/30 paired improvements;
- no House pooled degradation >5%;
- no new false-confident collapse;
- all runtime contracts pass.

Do not start C++/60 arms in this task.
