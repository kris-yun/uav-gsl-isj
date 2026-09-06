# CSTAR — controlled-data qualification handoff after environment PASS

Date: 2026-09-06  
Branch: `g3-cstar-revise-before-exec-20260906`  
Status: **ENVIRONMENT_ALIGNMENT_PASS / RAW_PROVENANCE_NOT_YET_QUALIFIED**

This is the active next-step contract. The environment checkpoint is frozen and
must not be confused with M1/M2/M3 scientific effectiveness. This run stops at
raw-realization provenance qualification; it does not train PICR/CPO, build
`cstar_v1`, or launch the 12-run matrix.

## 0. Frozen facts

The portable R2 environment bundle and repository evidence establish only:

- `CSTAR_ENVIRONMENT_ALIGNMENT=PASS` for H01/H02/H03;
- actual map parity at z=0.3 m;
- local stamped downwind wind decoding and observation position/time identity;
- all-free-cell candidate support and the preregistered stationary endpoint;
- 1.6 s of real shared-loader input per House.

They do **not** establish general route feasibility, four-arm production wiring,
or any CSTAR module gain.

The prerequisite inventory contains 12 raw GADEN directories: two apparent
source locations per House and fast/slow variants. Its own contract says names
and file counts only; `payload_read=false`. Directory names are not physical
provenance.

## 1. Pull the current branch in a clean worktree

Use the real VM checkout/worktree discovered in the environment phase. Do not
restore the obsolete `/home/zyc/gsl_ws/src/GasSourceLocalization` assumption.

```bash
set -euo pipefail
cd "$REPO_ROOT"
git fetch origin
git checkout g3-cstar-revise-before-exec-20260906
git pull --ff-only origin g3-cstar-revise-before-exec-20260906
git status --short
git rev-parse HEAD
```

Preserve the environment evidence directory and raw GADEN files read-only.

## 2. Re-run mandatory implementation tests

The branch now includes a raw-provenance auditor and its destructive selftest.
Run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 experiments/ctpi_cstar/run_reference_selftests.py
```

Required final line:

`CSTAR_ALL_REFERENCE_ENVIRONMENT_PROVENANCE_AND_REVIEW_SELFTESTS PASS`

Do not proceed if this fails.

## 3. Do not reopen the environment gate

Reverify the existing environment bundle/repository evidence once. Do not rerun
ROS probes or regenerate maps unless the stored evidence fails integrity checks.
The environment checkpoint is already the accepted prerequisite.

## 4. The realization split is already frozen before payload read

Use exactly:

`experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json`

It was derived from prerequisite inventory SHA-256:

`ca0cb0bcc9133b4f9b0d2441bac8b8171a7e3560b6bc3eb38bf0897030acddab`

while every inventory row still had `payload_read=false`.

Hard rule: every future prefix, causal history, route case and outcome inherits
its parent realization's role in the outer leave-one-House-out fold. Do not
re-split after inspecting gas outcomes.

## 5. Provenance-only inspection before any gas-payload extraction

Read the 12 realization directory identities from:

`evidence/cstar_environment_20260906/CONTROLLED_PREREQUISITE_INVENTORY.json`

For each realization locate **authoritative, immutable evidence** that existed
when the simulation was generated. Acceptable evidence kinds are listed in:

`experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_PROVENANCE_CONTRACT_V1.json`

Examples:

- generator configuration;
- exact generation command/script/log;
- frozen run manifest;
- simulation metadata/header;
- transport/wind configuration;
- release/source configuration.

Do not use `sourcePosition_...` in the directory name as the sole source
identity. Do not infer source/release/transport settings from gas outcomes.

At this stage, do not inspect iteration gas values merely to decide whether a
pair looks useful. Provenance must come from how the realization was generated,
not from its result.

## 6. Normalize each realization

Create `CSTAR_RAW_REALIZATION_PROVENANCE_V1.json` with one row for every frozen
realization_id. Each row must bind at least:

- `realization_id`;
- `house`;
- environment-passed `geometry_identity`;
- `config_id`;
- exact `simulation_dir_path`;
- exact `source_xyz_m`;
- `gas_type_id`;
- `source_authority`;
- `release_fingerprint`;
- `transport_fingerprint`;
- `sensor_mechanism_fingerprint`;
- one or more `provenance_evidence` objects.

Each evidence object contains:

- kind;
- path;
- SHA-256;
- literal tokens that must actually appear in that evidence file.

The normalized fingerprints are scientific identities, not labels chosen to
make fast/slow pair cleanly.

## 7. What counts as a qualified M1 pair

The auditor groups by:

`House + geometry_identity + exact source_xyz_m + gas_type_id`.

A pure transport pair requires:

- same exact source;
- same geometry;
- same gas type;
- same release fingerprint;
- same sensor-mechanism fingerprint;
- different transport fingerprint;
- all claims bound to checked provenance files.

If release or sensor mechanism also changes, it may be reported only as a
`QUALIFIED_M1_GENERAL_NUISANCE_PAIR` when the changed mechanisms are explicitly
provenanced. Do not call it a pure transport pair.

Source/geometry/gas-type mismatch, missing authority, directory-name-only source
identity, undeclared changes, or missing evidence is `BLOCKED_PROVENANCE`.

## 8. Run the fail-closed auditor

```bash
python3 experiments/ctpi_cstar/audit_raw_realization_provenance.py \
  --manifest /path/to/CSTAR_RAW_REALIZATION_PROVENANCE_V1.json \
  --output "$EVID/CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json"
```

Formal provenance PASS requires all of the following:

- every one of the 12 frozen realizations has acceptable evidence;
- every exact-source group has a legal nuisance pair;
- every House contains at least two source groups;
- every source group in every House is qualified.

The report separately counts pure transport pairs and general nuisance pairs.

## 9. M2 remains zero qualified route cases at this checkpoint

Even when a raw realization passes provenance, it is only eligible for later
truth-blind route outcome extraction.

The provenance auditor must still report:

`qualified_m2_route_case_count = 0`

and:

`m2_status = NOT_YET_ROUTE_CONTROLLED`.

Do not call an existing raw field `do(route)`. A future route set must be frozen
from geometry/navigation information before any gas outcome is queried for that
route. Only then may controlled open-loop route outcomes be extracted and passed
through the frozen sensor model.

This offline use of existing raw realizations is training/evaluation data; final
CSTAR deployment remains bank-free.

## 10. Stop point

If provenance is blocked, stop and push the exact missing evidence list. Do not
repair it by reading outcomes or by trusting directory names.

If provenance passes, also stop at this checkpoint. Push:

- final git SHA;
- mandatory selftest log;
- unchanged environment PASS identity;
- frozen realization split SHA;
- all provenance evidence paths/hashes;
- `CSTAR_RAW_REALIZATION_PROVENANCE_V1.json`;
- `CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json`;
- exact count of pure transport vs general nuisance pairs;
- exact list of raw realizations eligible for later route extraction.

Do **not** yet:

- read gas iteration payloads to choose routes;
- train M1/M2;
- create a scientific M2 PASS;
- claim four-arm production integration;
- run `cstar_v1` smoke;
- run H01/H02/H03 × A0/F00/F10/F11.

The next review decision after this bundle is whether the project may move from
`RAW_PROVENANCE_NOT_YET_QUALIFIED` to `READY_TO_FREEZE_TRUTH_BLIND_CONTROLLED_ROUTES`.
