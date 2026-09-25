# CODEX HANDOFF — SPOI Existing Context Asset Export Only

Date: 2026-09-25

Branch: `research/stochastic-plume-operator-v0`

## Mission

Export already-existing frozen House02 transport/context assets needed for the next offline stochastic-operator analysis.

This is **not a simulation task**.

Do not run GADEN, plume generation, DLL training, or PMFS closed loop.

## Assets

- `House02/OccupancyGrid3D.csv`
- W2 = `3,5-1_slow`
- `wind_iteration_0 .. wind_iteration_10`

These files already exist on the VM from Gate1A/M4.

## Checkout

```bash
git fetch origin
git checkout research/stochastic-plume-operator-v0
git pull --ff-only
git status --short
```

## Execute

```bash
bash research/stochastic_plume_operator_v0/export_existing_house02_w2_context.sh
```

Expected package:

`/home/zyc/SPOI_CONTEXT_ASSETS_20260925.tar.gz`

The exporter verifies:

- occupancy SHA256 `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`
- W2 `wind_iteration_1` SHA256 `54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8`

It copies all 11 wind iterations and produces a full SHA256 inventory.

## Report only

1. branch and HEAD
2. package path
3. bytes
4. package SHA256
5. occupancy SHA256
6. all 11 wind-file SHA256 values
7. any missing file or hash drift

Then stop. Do not generate any new plume realization.
