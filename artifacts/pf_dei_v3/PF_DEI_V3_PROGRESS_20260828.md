# PF-DEI V3 progress record (2026-08-28)

## Frozen method and provenance

- Method contract: `docs/PF_DEI_FINAL_METHOD_FREEZE_V3_REGION_LATENT_20260828.md`.
- Execution contract: `docs/CODEX_PF_DEI_FINAL_AUTONOMOUS_CLOSED_LOOP_V3_20260828.md`.
- Repository HEAD after merging the requested V3 branch: `a50efd2`.
- Historical evidence commits preserved in ancestry: `a504e0e`, `6fbf08c`, `33f9a80`, `55dd893`, `2fc133f`, and `a2b8040`.
- No V1/V2 verdict was overwritten.

## Completed V3 gates

The region-valued source support has been reconstructed from the native PMFS free-cell grid, not from a carrier centroid. All 150 geometry-only historical contexts reproduced the carrier rectangle and prior mapping (`PF_DEI_V3_REGION_IDENTITY=PASS`). Every carrier has at least one legal 3-D placement in its own region (`PF_DEI_REGION_3D_SUPPORT=PASS`).

| House | persistent carriers | PMFS free cells | carriers with legal 3-D support | empty carriers |
|---|---:|---:|---:|---:|
| H01 | 210 | 626 | 210 | 0 |
| H02 | 201 | 631 | 201 | 0 |
| H03 | 206 | 626 | 206 | 0 |

The old V2 representative-centroid invalid counts are retained only as a diagnostic (H01 182, H02 186, H03 186); they do not invalidate V3 because V3 marginalizes placement inside the carrier region.

The V3 math/static selftests passed on the VM, including bank I/O, quotient posterior, adequacy, Bernoulli adequacy, and direct-runtime contracts (`CG_PC_CTT_V3_STATIC_AND_MATH_SELFTEST PASS`).

## RNG hook gate

An isolated GADEN build was compared with an unmodified reference build. The hook is opt-in; with no `GADEN_RNG_SEED`, all 100×30 concentration queries per controlled run were bitwise identical. With the same non-RNG configuration and two frozen non-default seeds (101 and 211), seeded realizations differed in every House tested.

| House | default reference vs patched max abs diff | seed 101 vs 211 max abs diff | seed 101 vs 211 differing queries |
|---|---:|---:|---:|
| H01 | 0.0 | 7.3534469 | 290/3000 |
| H02 | 0.0 | 0.0* | 0/3000* |
| H03 | 0.0 | 8.6618691 | 290/3000 |

`*` H02's selected fast wind input is numerically invalid at the tested cell (a non-finite advection value), so the simulator truncates the filament path before stochastic transport can affect concentration. This is a test-input failure, not evidence of seed ineffectiveness; H02 must be rerun with a supported native wind field before declaring the RNG gate. The H01/H03 runs use supported native wind fields and pass seed-effect.

## Current stage and stop condition

The current active work is therefore **RNG-contract closure**, not model training or localization. The first probe used an invalid H01 fast-wind fixture; after switching to supported native wind fields, default parity passed exactly and seed effects were observed. The remaining action is one supported H02 seed-effect probe, then freeze the hook/source/binary hashes. No V3 training, closed-loop smoke, 60-arm, or confirmatory run has started yet.

If supported H02 seed-effect passes, proceed automatically to the V3 native trace generator and subsequent contractual gates. If it fails, terminal state is `PF_DEI_GADEN_RNG_CONTROL_NO_GO`; downstream stages must not be run.
