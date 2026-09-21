# CODEX — Export MIPO probe data only

Branch:

`research/mipo-active-observability-v1`

Base runtime:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

Read first:

`docs/MIPO_V1_PROBE_DATA_CONTRACT_20260921.md`

## Goal

Do **not** implement a new planner.

Do **not** run 300-s closed-loop comparisons.

Only export the source-blind local spatiotemporal gas/wind patches specified
by the data contract and push them to this branch.

This dataset is intentionally richer than one predefined probe trajectory so
that downstream analysis can synthesize multiple motion patterns without
re-running the VM.

## Hard prohibitions

Do not modify:

- PMFS likelihood;
- R2 lifecycle;
- TNQC;
- DRPE;
- planner;
- GADEN data;
- source-update cadence.

Do not use source truth when:

- selecting anchors;
- querying patches;
- choosing time windows;
- filtering data.

Do not optimize any probe amplitude/frequency.

## Preferred fastest implementation

Prefer a direct read/query of the existing GADEN realization / FrameQuery /
raw helper over launching a full ROS navigation experiment.

The export must use the exact same case realization and simulation-time
mapping as the six frozen R2 cases.

If direct querying is impossible and ROS/GADEN playback is required, keep the
robot/planner disabled and use a deterministic query-only node. Do not create
a closed-loop experiment.

## Required output

For each valid anchor produce the 7x7 x 160-row patch exactly as defined in
the contract.

Expected maximum dataset:

18 anchors x 7 x 7 x 160 = 141,120 rows.

This should remain small enough for GitHub when gzip-compressed.

Commit:

- all scripts;
- manifests;
- small metadata files;
- compressed raw patch CSVs;
- logs;
- SHA256SUMS.

If the total raw artifact unexpectedly exceeds normal GitHub limits, create a
GitHub Release on this research branch/tag and attach one `.tar.gz` artifact,
while still committing the manifest and SHA256SUMS in Git.

## Stop condition

After the integrity-only audit is PASS, push and STOP.

Do not interpret the science.

Return only:

1. final branch;
2. final commit SHA;
3. number of valid/invalid anchors;
4. row count per raw file;
5. total compressed size;
6. runtime/tree/data hashes;
7. SHA256 verification result;
8. GitHub paths or Release asset URL.
