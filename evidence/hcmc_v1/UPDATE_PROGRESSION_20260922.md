# HCMC V1 source-update progression diagnostic

Date: 2026-09-22

This is a diagnostic only. It does not alter the frozen HCMC V1 formula and must not be used to select an online release time from the six discovery cases.

For every source update, the active quadtree leaf set is reconstructed by assigning every free posterior cell to the unique smallest-area candidate that covers it. At update 5 this reconstruction exactly matches the authoritative `final_leaf_candidate_ids` set.

| update | mean simulation time | native mean error | HCMC mean error | cases improved |
|---|---:|---:|---:|---:|
| 1 | 67.0 s | 3.752 m | 3.679 m | 3/6 |
| 2 | 120.1 s | 4.456 m | 4.915 m | 2/6 |
| 3 | 174.6 s | 5.381 m | 3.819 m | 5/6 |
| 4 | 226.5 s | 5.465 m | 3.828 m | 4/6 |
| 5 | 277.8 s | 5.555 m | 2.449 m | 6/6 |

The important result is **not monotonic superiority**. HCMC is weak or harmful in several early updates and becomes useful only after sufficient spatial support has accumulated.

Scientific implication:

> multiscaling conformity appears to be an evidence-maturity phenomenon, not an immediately available sensor statistic.

This supports a future auxiliary innovation based on a truth-blind multiscale-support maturity gate, but **no release threshold is to be chosen from these six cases**.

The independent validation gate must keep HCMC V1 fixed and must separately determine whether a source-blind maturity condition transfers.
