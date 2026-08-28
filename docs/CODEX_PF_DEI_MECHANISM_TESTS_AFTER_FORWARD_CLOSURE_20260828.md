# CODEX TASK — PF-DEI mechanism isolation immediately after forward closure

Date: 2026-08-28

Precondition: `PF_DEI_FORWARD_OPERATOR_CLOSED` must already hold.

This task does **not** authorize H01/H02/H03 source-truth inspection, C++, Active Probe or the 60-arm matrix.

Read:

- `docs/PF_DEI_FAILURE_MECHANISM_DERIVATION_20260828.md`
- `docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`

## M1 — sensor-history counterfactual

Generate at least one controlled synthetic scenario with two history arms:

- identical chosen source;
- identical transport seed/realization;
- identical robot pose and physical concentration sequence during the evaluation window;
- different pre-evaluation exposure histories;
- native run-persistent sensor state, no manual reset at the evaluation boundary.

Export CSV columns required by:

`experiments/cg_pc_ctt/pf_dei_sensor_history_counterfactual.py`

Run its selftest first, then the synthetic result.

If measured ppm or the final block event changes despite an identical evaluation concentration suffix, record:

`SENSOR_HISTORY_LOCALITY_FALSIFIED = YES`.

This is a mechanism result, not a performance result.

## M2 — ideal versus native sensor matched ablation

Using exactly the same candidate-source physical concentration traces and nuisance draws, compute truth-blind source evidence under two observation operators:

A. ideal sensor: direct physical concentration sampled/averaged according to the PMFS block schedule, with no dynamic memory;
B. native sensor: exact persistent sensor dynamics and native measured ppm.

Do not tune thresholds from H01/H02/H03 localization outcomes.

Report the same cross-context transfer and absolute-adequacy diagnostics for A and B.

Interpretation is frozen:

- A substantially recovers while B fails -> sensor dynamics/history are a dominant blocker;
- both fail -> transport/source forward family remains inadequate;
- B recovers while the historical occupancy proxy fails -> observation proxy was dominant.

## M3 — transport-family sufficiency test

Only if the native sensor path B remains inadequate, compare the frozen finite transport family with a broader, source-independent physics-randomized GADEN nuisance distribution while keeping source candidates, poses, timestamps and sensor model fixed.

Do not use localization error to choose randomization ranges. Ranges must come from simulator/config physical provenance or pre-frozen uncertainty.

If only the broader physics-randomized family restores predictive adequacy, record:

`FINITE_TRANSPORT_FAMILY_INSUFFICIENT = YES`.

## Required verdict

Return exactly one provisional mechanism label:

- `OBSERVATION_PROXY_DOMINANT`
- `SENSOR_MEMORY_DOMINANT`
- `TRANSPORT_FAMILY_DOMINANT`
- `MIXED_OBSERVATION_SENSOR_TRANSPORT`
- `FORWARD_OPERATOR_STILL_UNRESOLVED`

Do not choose the label from localization error. The label must follow the matched mechanism tests above.
