# Source-Lineage Lagrangian v2 — frozen L1 decision

Execution date: 2026-09-24. Frozen source HEAD: `26719355f9b11d0a238d2f95e8f5cb49e17d34fd`.
Input: existing House02 C0.5 raw GADEN bank, eight cells with 566 `iteration_*` snapshots each. The frozen `run_l1_vm.sh` completed without a source or parameter change.

FINAL DECISION:
`L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`

L2 is **not permitted** under the frozen L1 gate. No L2, closed loop, new GADEN data, new House, or new seed was run.

## Holdout evidence

Both S2_W2 realizations were held out from fitting and cross validation. The frozen training cells were S1_W1_A/B, S2_W1_A/B, and S1_W2_A/B. The audit sampled 8,000 adjacent transition pairs per cell and selected ridge alpha 10.0 by its frozen leave-combination-out CV search.

| Metric | S2_W2_A | S2_W2_B |
| --- | ---: | ---: |
| 2D / 3D physics / learned / destroyed-null XY RMSE (m) | 0.036366 / 0.022384 / 0.022317 / 0.022364 | 0.036150 / 0.021431 / 0.021341 / 0.021402 |
| 2D / 3D physics / learned / destroyed-null centroid error (m) | 0.037587 / 0.009924 / 0.009747 / 0.009860 | 0.039180 / 0.009681 / 0.009685 / 0.009579 |
| 3D centroid improvement over 2D | 73.60% | 75.29% |
| Learned centroid improvement over 3D physics | 1.78% | -0.04% |
| Learned XY RMSE improvement over 3D physics | 0.30% | 0.42% |
| 2D / 3D physics / learned direction cosine | 0.185 / 0.522 / 0.526 | 0.095 / 0.425 / 0.432 |
| Frozen lineage-null relative gap | 1.14% | -1.10% |
| State gate | PASS | FAIL |
| Operator gate | FAIL | FAIL |

The S2_W2_B 3D physics direction cosine is below the strict 0.5 state threshold. The learned transition fails the required 10% centroid and RMSE improvements in both realizations; lineage destruction does not worsen its centroid result by the required 10%. These observations trigger the frozen mainline stop. The large 3D versus 2D centroid reductions alone do not override the failed conjunctive gates.

The full precision metrics, individual Boolean gates, and CV scores are in `SLL_V2_L1_RESULT_20260924.json`. The eight export and lineage manifests in the review package record zero duplicate-lineage snapshots, zero invalid birth assignments, zero progression errors, zero maximum sigma-age error, and median 1,108 shared lineages across adjacent snapshots in each cell. The minimum is zero because at least one adjacent snapshot pair has no shared lineages.
