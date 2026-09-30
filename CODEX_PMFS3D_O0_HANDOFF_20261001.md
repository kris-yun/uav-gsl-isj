# CODEX HANDOFF — PMFS3D O0 fixed-z mechanism gate

Branch: `research/pmfs3d-o0-mechanism-ready-20261001`

## Purpose

Run exactly one House02 / W1 / fixed-source-height development pilot to test whether full 3-D transport preserves more source-discriminative spatial information than a projected 2-D wind counterfactual.

This is not a PMFS closed-loop test and not an outdoor-generalization claim.

## Preconditions

Expected local assets:

- repository: `kris-yun/uav-gsl-isj`
- GADEN scenarios: `/mnt/hgfs/workspace/GADEN_files/scenarios`
- GADEN filament binary:
  `/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator`
- extractor:
  `/home/zyc/rmfe_filament_extractor_omp`

The runner verifies the frozen hashes itself.

## Exact execution

```bash
cd /home/zyc/uav-gsl-isj   # or the actual local repository root
git fetch origin
git switch research/pmfs3d-o0-mechanism-ready-20261001
git pull --ff-only
git status --short

bash research/pmfs3d_o0/run_pmfs3d_o0_remote.sh
```

Do not edit parameters before the first result.

## What the runner does

1. synthetic self-test of legacy/modern GADEN wind read/write;
2. synthetic self-test of the source-discrimination metric;
3. audits that Native PMFS transport is 2-D (`Vector2` filament/source/wind path);
4. reads the already-open fixed-z House02 C0.5 development bank;
5. constructs a projected-2D wind counterfactual:
   - take `u,v` at z=0.2 m;
   - extrude them through all z layers;
   - set `w=0`;
6. runs only four new GADEN counterfactuals:
   - S1/A, S1/B, S2/A, S2/B;
7. compares existing full-3D target plumes with cross-replicate FULL3D and PROJECTED2D candidate templates;
8. writes the frozen decision and stops.

## Forbidden

Do not:
- run H01 or H03;
- open confirmation;
- run R3A;
- run PMFS/ROS closed loop;
- train GenDA/world models;
- tune thresholds/metrics after seeing results;
- add a second wind condition;
- change source positions, z, simulator physics, or RNG seeds.

## Expected outputs

Small evidence in Git worktree:

`evidence/pmfs3d_o0_projected2d_20261001/`

Required:
- `PMFS_2D_CONTRACT.json`
- `PMFS_2D_CONTRACT.log`
- `SELFTEST_WIND.log`
- `SELFTEST_GATE.log`
- `O0_RUN.log`
- `O0_RESULT.json`
- `SHA256SUMS.txt`

Raw generated projected-2D data remain outside Git:

`/home/zyc/PMFS3D_O0_PROJECTED2D_20261001`

## Allowed final decisions

- `PMFS3D_O0_REFERENCE_3D_NOT_STABLE`
- `PMFS3D_O0_VERTICAL_INFORMATION_STRONG`
- `PMFS3D_O0_VERTICAL_INFORMATION_PROMISING`
- `PMFS3D_O0_NO_VERTICAL_INFORMATION_GAIN`

After any decision: STOP and return `O0_RESULT.json`, logs, SHA256 and branch/commit.

Do not infer an outdoor/lakeshore result from this gate.
