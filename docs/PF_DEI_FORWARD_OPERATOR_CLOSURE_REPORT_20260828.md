# PF-DEI forward-operator closure report

Date: 2026-08-28  
Branch: `codex/pf-dei-forward-closure-20260828`  
Normative upstream: `research/cg-pc-ctt-v6-dynamic-transport-sbi` at `66b1070813f0c5cd4d4fddb714194780c51790dc`

## Decision

`PF_DEI_FORWARD_OPERATOR_CLOSED`

This verdict is limited to closure of the physical observation operator. It does **not** authorize a new likelihood, SBI architecture, C++ integration, source-localization claim, or 60-arm performance experiment.

## Closed causal chain

`S -> Z_c -> C_t -> R_t -> M_t -> Y_b`

where `C_t` is native GADEN physical concentration, `R_t` is the run-persistent sensor state, `M_t` is the measured ppm stream, and `Y_b = 1[mean(M_i) > thresholdGas]` for the exact ten samples consumed by PMFS.

## Stage results

### O2 source proof

The CTT/GADEN source path counts a cell at most once per simulator timestep when one or more filaments occupy it and divides by timestep count. It is therefore an occupancy event/frequency, not ppm. The PMFS path consumes measured sensor samples, averages a completed ten-sample block, and compares the mean against `thresholdGas` to emit `GAS HIT/NOTHING`. Occupancy-to-ppm or occupancy-to-HIT conversion is not used.

### Historical observed stream

- 30/30 OFF runs contain `sensor_trace.csv`.
- 0/30 contain a dedicated continuous-measurement file.
- 4,049 completed blocks were reconstructed from runtime state/action provenance.
- All 4,049/4,049 recomputed `mean > thresholdGas` decisions equal the archived PMFS event.
- No `true_gas_ppm`, true source, localization error, or performance label was materialized.
- The raw ten-sample streams are correlated and are not treated as independent Bernoulli/Gaussian replicates.

Artifact: `artifacts/pf_dei_forward/observed_block_manifest.csv`  
SHA256: `e41937ff436e191210622aee056f02afaf32d2a051a33be2b43bdce38d3ff94c`

The trace serializes measured ppm to six decimal places; therefore archived printed means are provenance checks, while the binary HIT parity is the exact acceptance gate.

### Sensor dynamics

The authoritative sensor implementation is `vgr_bridge/sensor_model.py`. The state is instantiated once in `vgr_sim_node.py` and is not reset at movement, StopAndMeasure completion, or source-update context boundaries. The archived launch sets `sensor_model_mode=dynamic`; all other sensor fields are explicitly supplied by the VGR declared defaults, yielding the used symmetric configuration:

`gain=1`, `baseline=0`, `tau_rise=tau_recovery=1.2 s`, `dead_time=0.4 s`, `noise=0`, `drift=0`, saturation `[0, 1e6]`, initial state/input `0`.

The implementation uses causal delayed-input interpolation and a first-order branch update. These dynamics are applied continuously across the whole run. Source hashes:

- `sensor_model.py`: `423042f94315a35ca83aa929d42a32633d94ea819b8e15639e26039073c549bc`
- `vgr_sim_node.py`: `4056ff603e6defffc087430acecafe85ebbdeef8e2f70bbc6d828ac800bf3222`

The exact `/dev/shm` runtime overlay used by the historical runs was erased by VM reboot and was not separately hashed in the prior full60 package. The persistent-state semantics and launch parameter values are nevertheless established by the surviving source, launch files, sensor traces, and source behavior. Future qualification must preserve/hash the deployed overlay before launch.

### Native physical concentration path

An isolated GADEN build was made under `/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828`; the legacy House02 wind files were converted into an isolated `converted_wind_house02` directory without modifying shared data. A controlled synthetic source `(-2.0, 0.07, 0.2)` was simulated for 30 s.

The shared-library query path uses the same `gaden::PlaybackSimulation` and `Scene::SampleConcentrations` code as the ROS player. The independent ROS `frame_query` path uses `gaden_player`'s `Scene->SampleConcentrations`/`SampleWind`. Both returned 50/50 samples with exact equality for concentration, wind, pose, iteration, and time.

Native query executable SHA256: `f6070d681b7e738bf8713a5462e0bbb7aaf1c1f30ea62bd4b7bbc83a9b1f50fc`  
GADEN player source SHA256: `df14510bba2a4d2a8d500b5b8feb68ad6f22a6d3066c9276e67eaaa1a649bc16`  
Playback source SHA256: `458a7e2987c482898190f9208c5223ce9365f0b8b85c39410668d680363faed3`

### End-to-end synthetic parity

- 50 physical concentration samples: exact shared-query/ROS-player parity.
- 50 measured samples: exact parity under identical sensor configuration and seed.
- 5 exact ten-sample block means: exact parity.
- 5/5 HIT/NOTHING decisions: exact parity.
- Persistent state regression: resetting the sensor at the second block changes the first sample by 10.0681640908 ppm, so the test exercises persistence rather than merely passing a zero signal.
- Minimal sensor-aware forward payload: `validate_forward_payload(...) = PASS`.

Summary: `artifacts/pf_dei_forward/synthetic_parity_summary.json`  
Payload: `artifacts/pf_dei_forward/minimal_forward_payload.npz`

## Frozen prohibitions for the next task

Do not use CTT occupancy as the main observation variable. Do not fit occupancy-to-ppm/HIT mappings. Do not reset sensor state per context. Do not treat ten correlated samples as ten independent evidence units. Any next inference model must be trained/evaluated on the same native physical-to-sensor chain and must preserve source truth separation.

## Handoff design note

The next task may generate truth-free candidate examples by varying global source `S` and coherent context transport `Z_c`, running native physical concentration through the same run-persistent sensor model, and storing measured ppm/time/pose plus exact block membership. Random sequential prefixes are allowed only after a separate inference contract is frozen; no architecture or performance threshold is frozen by this report.
