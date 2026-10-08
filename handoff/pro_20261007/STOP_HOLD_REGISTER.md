# STOP / HOLD register — do not silently resurrect

Any route below may be reconsidered only if a concrete fatal flaw in the previous experiment is identified and a new falsifiable test is proposed.

- TNQC v5: HOLD / no-go.
- Active Deconfounding: 0/6 passed; NO-GO.
- DRPE route: stopped as unsuitable / not the desired novelty direction.
- MIPO active observability: stopped as already-worked direction.
- HCMC v1: NO-GO.
- Dynamic-export parity route: stopped because historical estimated-wind could not be exactly recovered.
- M4-v2: field error improved but source ranking did not; HOLD.
- M4-v3: failed cosine/superposition gates; STOP.
- L1 / SLL V2: `L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`.
- AOD-R2 F0: NO_SIGNAL.
- PMFS3D R1P5: partial selectivity only; not stable.
- P3T Gaussian: `D0_NO_POSITIVE_TRUTH_SUPPORT_STOP`.
- TS_P3T H0: INVALID_STOP.
- R0C1 equal-height vertical confirmation: `R0C1_VERTICAL_SIGNAL_HEIGHT_CONFOUNDED_OR_UNSTABLE_STOP`.
- R0D factorial: `R0D_CONTEXT_EFFECT_HOLD`.
- P0 transferable plume dynamics / world-model route: stopped by transfer failure.

Important meta-rule:
Do not turn a negative result into a new method by merely adding model capacity (Transformer/GNN/PINN/etc.) after frozen gates fail.

- **M0 final 2026-10-08**: `M0_STOP` after 40/40 qualified runs, 2 matched-wind-error structural contrasts × 2 sources × 4 master seeds. The plume and sensor forward response changed, but maximum posterior ΔBrier was 8.85e-8 vs 0.10 threshold, both frozen source inference families correct 8/8 per wind; zero 3/4 same-seed intersections. No M0 rescue. Source model posteriors were almost saturated in this easy two-source box; cannot generalize null to all lakeshore flows. Details: `M0_FINAL_STOP_AND_FSR_PIVOT_20261008.md`.
