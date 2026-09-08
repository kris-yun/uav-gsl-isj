# CORE-M1E H01 seed9 early-screen result

Status: **H01_SEED9_EARLY_SCREEN_PASS; CROSS_HOUSE_PENDING**.

Both arms used binary SHA256
`2a92c82e7cb2d3bab043a95ed18eb394c41ca3edc934ade8dd5f99de43f47400`
and reached the frozen 240 s horizon.  The runtime logged three transport
members at each of four source updates and sequentially committed disjoint
event windows.

| Arm | Final error (m) | Distance AUC (m s) |
|---|---:|---:|
| A0 | 6.9020938852 | 1726.3638847860 |
| M1E | 6.4220635313 | 1644.0845176301 |
| A0 minus M1E | +0.4800303539 | +82.2793671559 |

Both frozen metrics improve, so the early screen passes.  This authorizes the
same-version H02/H03 seed9 pair and nothing more.
