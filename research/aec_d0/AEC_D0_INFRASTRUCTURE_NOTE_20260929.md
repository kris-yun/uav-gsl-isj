# AEC-D0 simulator-only operator parity repair

The first pseudo-vector build under `/home/zyc/aec_d0_20260929` verified all reproduced H01/H02 PMFS forward-product SHA256 values against their original inventories. It also verified H03 per-run product hashes. No target concentration was read.

The first host scoring attempt stopped at the preregistered simulator-mean parity check: H02 W2 `route_37_u_pmfs_12_20` had relative L2 mean mismatch `0.001362253518227404`; a source-blind scan of the other routes found up to `0.0291454650643984` on low-signal `route_48_u_pmfs_2_37`. `rawu` did not show this mismatch.

Cause: the historical ABS-B2 `u` reference bank is the Python/OpenCV `GaussianBlur(rawu)/GaussianBlur(free_mask)` reconstruction, whereas the first pseudo-vector builder used the C++ per-run `.u.f32` product. These are different numerical observation operators at some low-signal cells. The repair reconstructs each pseudo `u` from that realization's frozen `rawu` using the **same archived OpenCV blur** as `score_shadow.bank_for_env`. It retains verification of all four PMFS output hashes and does not change EPS, B2, routes, candidate support, source set, Top10, or target outcome.

The first VM output is preserved. The corrected builder writes a new `/home/zyc/aec_d0_20260929_v2` namespace and must independently pass the same mean-bank parity gate before any target outcomes are opened.
