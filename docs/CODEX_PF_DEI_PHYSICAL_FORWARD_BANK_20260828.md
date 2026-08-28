# CODEX TASK — PF-DEI native physical candidate forward bank

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Current scientific baseline before this task:

- preserved native forward closure: `a504e0e`;
- preserved sensor-memory audit: `6fbf08c`;
- preserved exact deconvolution replay: `33f9a80`;
- preserved run-level blocker evidence: `55dd893`;
- GitHub scientific baseline before bank additions: `dde7b6e94efb8572838beded6d198bbdb041312c`.

Read first:

- `docs/PF_DEI_PHYSICAL_BANK_MATERIALIZATION_CONTRACT_20260828.md`;
- `docs/PF_DEI_RUNLEVEL_SOURCE_EVIDENCE_DERIVATION_20260828.md`;
- `experiments/cg_pc_ctt/pf_dei_physical_bank_contract.py`;
- `experiments/cg_pc_ctt/pf_dei_runlevel_energy_reference.py`.

This task does not authorize source truth, localization error, C++, Active Probe, neural SBI or 60-arm performance experiments.

## Stage 0 — preserve work and freeze deployment provenance

Do not reset or overwrite the four preserved local work products above.

Because the historical `/dev/shm` overlay was lost after reboot, every new native GADEN simulation/query launched now must record the deployed overlay source/config/library SHA-256.  This does not retroactively repair historical overlay provenance.

Run:

```bash
python3 experiments/cg_pc_ctt/selftest_pf_dei_physical_bank_contract.py
python3 experiments/cg_pc_ctt/selftest_pf_dei_runlevel_energy_reference.py
python3 experiments/cg_pc_ctt/selftest_pf_dei_inverse_sensor_reference.py
```

All must PASS before materialization.

## Stage 1 — resolve source-support identity before launching full simulations

The blocker report found 150 adaptive candidate manifests and 1,229 distinct adaptive IDs.  Do not use their union blindly.

For every one of the 30 runs, inspect the exact V6-A/context payload and the provenance that generated `geometry_prior` / source index `s`.

Produce:

`artifacts/pf_dei_physical_bank/source_support_manifest.csv`

with at least:

- House;
- run seed or `COMMON_WITHIN_HOUSE`;
- source index;
- stable source ID;
- source x/y/z in native GADEN coordinates;
- geometry-prior mass;
- provenance file/hash that proves this index-coordinate mapping.

Mandatory contracts:

1. within a run, source index -> physical coordinate is identical for every chronological prefix used by the diagnostic;
2. geometry-prior mass is aligned to exactly that source order;
3. repeated stable source IDs map to identical coordinates;
4. no true source or performance label is consulted.

If source identity cannot be proven, stop:

`STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`.

Do not launch the full GADEN bank before this passes.

If supports differ legitimately by run, preserve run-specific supports.  Deduplicate expensive GADEN simulations later by exact `(House,x,y,z)` only; do not fake common source indices.

## Stage 2 — freeze native transport-member manifest

First look for a source-proven native GADEN transport/RNG manifest corresponding to a previously frozen member family.

Only reuse it if the mapping to actual native GADEN RNG/config is explicit and reproducible.  Old occupancy-member labels alone are insufficient.

If no such native manifest exists, define a fixed source-independent native GADEN transport ensemble before any run-level score is computed.  Record the legal RNG seed/substream and every relevant source-independent config/hash.

Required:

`artifacts/pf_dei_physical_bank/transport_manifest.csv`

No source-specific or outcome-specific member tuning.

Use at least the already-frozen ensemble size required by the run-level reference; do not reduce member count because simulations are expensive.

## Stage 3 — prove whether one field can serve all ten trajectories of a House

Before multiplying jobs by 30, compare the 10 historical OFF runs within each House for the source-independent environment contract:

- map/occupancy geometry;
- wind-field/environment files;
- GADEN simulator parameters relevant to concentration generation;
- plume simulation time origin / duration semantics;
- query coordinate frame;
- any non-source randomization that is already represented by transport member `m`.

If these are common, freeze:

`FIELD_REUSE_SCOPE = HOUSE_SOURCE_MEMBER`

and simulate one field per unique `(House,source,member)`, then query that field along all ten run trajectories.

If not common, record the exact mismatch and use the narrowest valid reuse scope.  Do not assume reuse merely to save time.

## Stage 4 — implement the VM-specific materializer around the already audited native query path

The run-level blocker already established that a preserved native query binary can sample an existing fixed-source GADEN field.  Reuse that exact physical concentration path and its parity-tested library/source hashes.

The missing operation is field generation for arbitrary frozen candidate source coordinates.

Implement an isolated orchestration layer that for each required field:

1. copies/instantiates a source-independent House simulation config;
2. sets only the frozen candidate source coordinate and frozen transport member/RNG inputs;
3. runs native GADEN long enough to cover the maximum required historical query time;
4. verifies successful/native field output and hashes it;
5. queries physical concentration at the exact historical pose/time schedules;
6. writes physical ppm only, never occupancy-derived values.

Do not modify GADEN physics to make relocation cheap.  If arbitrary source relocation requires full native simulation, run full native simulation.

Workers must use isolated output directories.  Never mix source/member fields.

## Stage 5 — smoke materialization before scaling

Use one House, one historical run, two physically distinct source candidates and at least two frozen transport members.

Materialize a complete chronological bank:

`candidate_physical_ppm[S,M,T]`.

Pack it in the per-run NPZ contract defined by:

`experiments/cg_pc_ctt/pf_dei_physical_bank_contract.py`.

Run `validate_npz(...)`.

Additionally choose 50 `(source,member,time,pose)` entries by a deterministic pre-frozen index rule and compare the stored bank value against a fresh direct native query.  Require the already established native-query numerical tolerance.

Repeat a deterministic subset after a clean process restart.  Require identical output/hash if native GADEN is deterministic for the frozen seeds; otherwise document the exact reproducibility semantics and tolerance from source, not outcome.

If smoke fails, stop before full generation.

## Stage 6 — full materialization

Generate every required source/member trace for all 30 runs under the valid reuse scope from Stage 3.

Recommended expensive-job key when House-level reuse is valid:

`(House, source_id, transport_id)`.

After one field is generated, query every compatible run trajectory before discarding/archiving that field.

Per-run output:

`artifacts/pf_dei_physical_bank/run_<House>_seed<seed>.npz`

Then validate all banks and create a SHA-256 bank manifest.

Completeness is strict:

- 30/30 run bank files;
- every declared source index present;
- every declared transport member present;
- exact T aligned to that run's recovered physical observation/time/pose schedule;
- finite non-negative physical ppm;
- no missing `[s,m]` cells;
- source IDs/prior order exactly aligned;
- no forbidden truth/performance fields.

Do not silently drop a simulation that crashed.  Retry only as an engineering recovery with the same frozen inputs; record retries.

## Stage 7 — run the already-frozen science test immediately

Once the full bank contract passes, do **not** stop for another design review.

Run the existing five-segment chronological energy-score diagnostic on all 30 historical deconvolved physical observations.

Also run A1/A2 canonical source-score parity using the same bank and exact native sensor/inverse implementation.

Return:

- H01 predictive pass /10;
- H02 predictive pass /10;
- H03 predictive pass /10;
- total predictive pass /30;
- mean/segment absolute gains and rival margins;
- A1/A2 source-score/ranking parity tolerance;
- all bank/provenance hashes.

Frozen verdict:

### `PHYSICAL_RUNLEVEL_SOURCE_FORWARD_ACTIONABLE`

only if total >=20/30 and each House >=5/10, with A1/A2 canonical parity passing.

### `FINITE_TRANSPORT_OR_SOURCE_FORWARD_STILL_INSUFFICIENT`

otherwise, assuming the bank itself is valid.

If this failure occurs, do not retune energy score, transforms, thresholds or candidate support from localization performance.  The next task is broader source-independent physics-randomized GADEN nuisance/transport expansion.

## Stage 8 — status naming

Do not overwrite the historical report's stop label.  In the new report distinguish:

- `PF_DEI_FORWARD_OPERATOR_CLOSED = YES` for the preserved single-source native physical/sensor chain;
- `PF_DEI_PHYSICAL_BANK_MATERIALIZED = YES/NO` for the current full candidate ensemble.

Before full materialization, the current operational stop is:

`PF_DEI_PHYSICAL_BANK_NOT_MATERIALIZED`.

## Required report

Write:

`docs/PF_DEI_PHYSICAL_FORWARD_BANK_AND_RUNLEVEL_RESULT_20260828.md`

If Stage 7 cannot be reached, report the first exact failing contract and stop without substituting occupancy maps, `true_gas_ppm`, or the 12 fixed-source simulations.
