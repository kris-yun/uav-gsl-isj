# CODEX DASN RAW-FIELD SUBSET HANDOFF — 2026-09-25

## Objective

Package the already-existing pre-frozen D1R raw-field subset needed for the next plume-deformation/meandering mechanism screen.

**This is file retrieval only. Do NOT run GADEN.**

## Branch

`research/displacement-aligned-shared-noise-v0`

Read first:

- `01_idea/DASN_RAW_FIELD_SUBSET_FREEZE_20260925.md`
- `research/displacement_aligned_shared_noise_v0/package_dasn_raw_field_subset.sh`

## Required action

On the VM containing the completed D1R bank:

```bash
git checkout research/displacement-aligned-shared-noise-v0
git pull --ff-only

bash -n research/displacement_aligned_shared_noise_v0/package_dasn_raw_field_subset.sh

bash research/displacement_aligned_shared_noise_v0/package_dasn_raw_field_subset.sh
```

Expected existing D1R root:

`/home/zyc/cess_d1r_168x16_reference_20260925`

Expected archive:

`/home/zyc/DASN_RAW_FIELD_SUBSET_8x16_20260925.tar.gz`

## Hard constraints

- exactly 8 frozen source IDs;
- exactly 16 existing realizations/source;
- exactly 128 concentration cubes;
- cube shape exactly `(10,83,119)`;
- paired pooled arrays shape `(10,30)`;
- do not regenerate a missing file;
- do not change source list;
- do not add sources after inspecting cubes;
- do not run any mechanism analysis;
- do not generate new seeds or targets.

If any required raw file is missing:

**STOP and report the missing path(s).**

Do not rerun GADEN.

## Return only

1. branch;
2. commit;
3. state = `DASN_RAW_FIELD_SUBSET_READY` or missing-assets STOP;
4. cube count;
5. source count;
6. realizations/source;
7. archive path;
8. archive bytes;
9. archive SHA256;
10. whether internal `SHA256SUMS.txt` verifies.

Then stop.
