# M6 G1-C/G1-D full offline result — pretrained versus scratch

Date: 2026-09-23  
Code: `g1c_train_rank_gate.py`, commit `9409467`  
Status: **NO-GO AS MAIN INNOVATION; retain only as a House02-local engineering diagnostic**

## Frozen run

The run used the frozen House02 G1-B compact bank, 12 pre-registered source
candidates, and two process-level plume seeds. Seed `2026092311` was used for
training/validation and independent seed `2026092312` was used for the held-out
rank query. The candidate count was 12 (`train1..train8`, `val1..val2`,
`test1..test2`). No source locations, thresholds, optimizer, or test scores
were tuned after seeing the smoke result.

Remote command:

```text
python3 /tmp/g1c_train_rank_gate_20260923.py \
  --bank /mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923/full_final \
  --grid /mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923_grid.csv \
  --occupancy /mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv \
  --wind /mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind/wind_iteration_0 \
  --official /tmp/geopt_official_20260923 --checkpoint /tmp/GeoPT_8layers.pt \
  --out /mnt/hgfs/workspace/M6_G1_STAGE1_C_FULL_20260923 --epochs 20
```

The VM run exited with status 0. The frozen raw result is in
`G1C_FULL_RAW_20260923/g1c_g1d_results.json`; its SHA256 is
`2d073d62ade65f927762a914b8827ccdf51d6f3c8ebdae26fffdc09cb9d7ba0a`.
The grid SHA256 is
`f30c7de2ea892120b70411edb7187f2769246896152f9bb9b8181e15f749a397` and the
GeoPT checkpoint SHA256 is
`c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`.

The scratch arm is a fully trainable random-initialized 8-layer Transolver
(3,880,577 trainable parameters). The pretrained arm freezes the loaded GeoPT
backbone and trains only the source adapter plus scalar task head (17,729
trainable parameters). Both use the same 4->64->256 source adapter and 20
training epochs.

## Held-out results

The table reports validation RMSE on seed `2026092311` and truth-source rank on
independent seed `2026092312`.

| training fraction | arm | validation RMSE | test1 rank / 12 | test2 rank / 12 |
|---:|---|---:|---:|---:|
| 25% | pretrained GeoPT + adapter | 0.30416 | 1 | 2 |
| 25% | scratch full Transolver | 0.32680 | 2 | 2 |
| 50% | pretrained GeoPT + adapter | 0.29965 | 3 | 2 |
| 50% | scratch full Transolver | 0.35851 | 1 | 3 |
| 100% | pretrained GeoPT + adapter | 0.29669 | 5 | 1 |
| 100% | scratch full Transolver | 0.29488 | 1 | 1 |

Pretraining gives a small validation-field advantage at 25% and 50%, but the
advantage disappears at 100%. The source-rank result is not stable: the
pretrained average rank is 1.5, 2.5, and 3.0 across the three fractions,
whereas scratch is 2.0, 2.0, and 1.0. The 100% pretrained model is worse on
`test1` (rank 5 versus scratch rank 1). Therefore the required held-out
source-identity gain does not repeat across the frozen low-data curve.

## Native-arm boundary

The offline run contains an explicitly labelled analytical PMFS-like proxy,
which ranks both test sources 1/12 at all fractions. It does **not** invoke the
repaired Native PMFS simulator or ROS/live loop. Consequently this proxy cannot
be reported as the required Native PMFS Arm A, and the three-arm scientific
comparison is incomplete even though the scratch and pretrained arms ran.

## Decision

This is a bounded House02-local diagnostic, not a main-innovation pass. It fails
the M6 advance requirement because pretrained GeoPT does not robustly improve
truth-source rank over scratch, and the required Native PMFS arm was not run.
Under the preregistered rule, mark:

```text
NO-GO AS MAIN INNOVATION
```

No closed-loop PMFS run, ROS modification, candidate tuning, extra source,
unknown-House transfer, or claim of real-world generalization was performed.
