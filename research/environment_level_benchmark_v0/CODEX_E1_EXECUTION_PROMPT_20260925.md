# CODEX TASK — E1 Cross-House Contract Freeze (ZERO PLUME)

Branch:
`research/generalization-refoundation-v0`

Authoritative charter:
`research/environment_level_benchmark_v0/E1_CROSS_HOUSE_CONTRACT_CHARTER_20260925.md`

## Hard stop

**Do not run GADEN plume simulation.**
**Do not create W3 plume.**
**Do not run a scientific mechanism model.**
**Do not start the provisional 96-run fill-in.**

Your only task is geometry/contract construction and compatibility audit.

## Required work

1. Load the canonical PMFS/occupancy/navigation geometry for House01, House02, House03.
2. Reuse repository-validated grid/world coordinate mapping and free-space rules; do not invent a replacement if a validated implementation exists.
3. Build the deterministic 30-probe geometry-only FPS contract for each House exactly as frozen in E1.
4. Build the deterministic six-source / three-local-pair source panel for each House exactly as frozen in E1.
5. For House02 compare the new FPS30 contract to the legacy D1R 30-probe contract using geometry only.
6. Decide E1A or E1B exactly as specified; no plume data may inform that choice.
7. Verify candidate environment roles are geometrically executable:
   - development: House01 + House02;
   - untouched final House: House03.
8. Produce the provisional fill-in budget using actual reuse compatibility, but **do not execute it**.

## Outputs

- `E1_HOUSE_PROBE_CONTRACTS.tsv`
- `E1_HOUSE_SOURCE_PANELS.tsv`
- `E1_H02_LEGACY_COMPATIBILITY.md`
- `E1_ENVIRONMENT_ROLE_SPLIT.md`
- `E1_PROVISIONAL_FILLIN_BUDGET.md`
- `E1_GEOMETRY_PROVENANCE.md`
- SHA256 manifest for all geometry/contract inputs and generated evidence files.

## Final decision

Return exactly one:

- `E1_PASS_CROSS_HOUSE_CONTRACT_READY_FOR_FILLIN_DESIGN`
- `E1_FAIL_CROSS_HOUSE_CONTRACT_NOT_COMPARABLE`

Report:
- branch;
- final commit;
- decision;
- 30 probe coordinates/indices per House;
- 6 source coordinates/indices per House;
- H02 legacy reuse decision;
- provisional new-run count only;
- review package path/bytes/SHA256.

Stop after E1. No plume generation under any condition.