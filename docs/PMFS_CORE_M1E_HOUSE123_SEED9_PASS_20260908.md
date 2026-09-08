# CORE-M1E House123 seed9 result

Status: **CROSS_HOUSE_SEED9_PASS; MULTI_SEED_PENDING**.

All six arms used binary SHA256
`2a92c82e7cb2d3bab043a95ed18eb394c41ca3edc934ade8dd5f99de43f47400`
and reached the frozen 240 s horizon.  Each M1E source update logged three
transport members and disjoint sequential event windows.

| House | Final improvement (m) | AUC improvement (m s) | Both positive |
|---|---:|---:|:---:|
| H01 | +0.4800303539 | +82.2793671559 | yes |
| H02 | -1.5029282298 | +0.4403352747 | no |
| H03 | +2.2791706119 | +105.4690495142 | yes |

The preregistered cross-House gate passes: 2/3 Houses improve both metrics,
all three improve AUC, mean final improvement is +0.4187575787 m and mean AUC
improvement is +62.7295839816 m s.  The stronger all-pairs criterion does not
pass because H02 final error worsens.

This is one algorithm seed under one certified sensor/replay seed.  It is not a
multi-seed or independent-plume claim.  The M1E formula is now frozen; the next
step is a staged new algorithm-seed screen, starting with H01 only.
