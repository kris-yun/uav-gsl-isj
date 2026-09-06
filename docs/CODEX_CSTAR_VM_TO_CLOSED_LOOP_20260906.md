# DEPRECATED — do not use for current execution

Date: 2026-09-06

The previous VM-to-closed-loop execution contract was reviewed and found to be
over-permissive in several places, including formal authorization evidence,
12-run arm identity checks, AUC handling of missing/late estimates, M1 `zS`
bypass, M2 route-intervention identity, and the distinction between spent
premise replay and formal gates.

Current project status is:

`REVISE_BEFORE_EXECUTION`

The active Codex authority is now:

`docs/CSTAR_REVISE_BEFORE_EXECUTION_CODEX_HANDOFF_20260906.md`

Also read:

- `docs/CSTAR_M1_IDENTIFIABILITY_BOUNDARY_20260906.md`
- `experiments/ctpi_cstar/CSTAR_CONTROLLED_CAUSAL_ASSET_CONTRACT_V1.json`
- `experiments/ctpi_cstar/CSTAR_REQUIRED_EVIDENCE_CONTRACTS_V1.json`
- `experiments/ctpi_cstar/CSTAR_CASE_AUDIT_SCHEMA_V1.json`

Do **not** start the H01/H02/H03 × seed12 × A0/F00/F10/F11 12-run matrix from
this deprecated document. The current Codex task stops after finite revision
validation and evidence bundling.

The previous full text remains recoverable from Git history at reviewed snapshot
`0866ad8b3b6af6ba46ad125e74508ff2b5ede503`.
