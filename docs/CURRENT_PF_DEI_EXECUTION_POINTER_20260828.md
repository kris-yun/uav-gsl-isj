# CURRENT PF-DEI EXECUTION POINTER — 2026-08-28

Current authorized task:

`docs/CODEX_PF_DEI_PHYSICAL_FORWARD_BANK_20260828.md`

Reason:

- the native single-source physical observation operator is already closed by preserved forward-closure work;
- sensor-memory lower bound and exact deconvolution are independently reproduced;
- run-level reference selftests and synthetic A1/A2 canonical parity pass;
- the current blocker is specifically the absence of a complete, auditable `candidate_physical_ppm[S,M,T]` bank for the frozen source support × transport ensemble on all 30 historical trajectories;
- occupancy/hit maps, historical `true_gas_ppm`, the 150 adaptive manifests by themselves, and the 12 fixed-source GADEN simulations are not admissible substitutes;
- source-index -> physical-coordinate -> geometry-prior identity must be proven before expensive full-bank simulation.

Operational status before completion:

`PF_DEI_PHYSICAL_BANK_NOT_MATERIALIZED`

Do **not** reinterpret this as failure of the already-closed single-source native concentration/sensor operator.

After the bank is complete and validated, the same current task immediately runs the already-frozen five-segment run-level energy diagnostic; no additional design review is required.

Do **not** execute older task documents as the current stage, including:

- `CODEX_PF_DEI_RUNLEVEL_SOURCE_EVIDENCE_20260828.md` directly without first materializing the physical bank;
- `CODEX_PF_DEI_EXACT_DECONVOLUTION_MATCHED_REPLAY_20260828.md`;
- `CODEX_PF_DEI_SENSOR_MEMORY_AND_SBI_STAGE1_20260828.md`;
- `CODEX_PF_DEI_MECHANISM_TESTS_AFTER_FORWARD_CLOSURE_20260828.md`;
- old occupancy/Markov PF-DEI tasks;
- V5 Active Probe.

No neural SBI, C++, localization-performance opening or 60-arm run is authorized.
