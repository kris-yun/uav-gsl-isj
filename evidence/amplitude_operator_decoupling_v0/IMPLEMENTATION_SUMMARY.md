# Implementation reproduction completed — OPEN only

No new scientific PASS/FAIL label. Historical D0 remains `ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE`.

- Branch: `research/amplitude-operator-decoupling-v0-20260927`
- Base: `c557ec04e07f0ace12df2b535b79a8a37078f407`
- Initial implementation: `a91d4dc9a4ffe88249ba5a3e630f68547bd4eca5`
- Executed implementation: `8c164f01b7b2705881015054cbbded24e9853d44`
- Output-order correction: `ff70ece9` (CSV traversal only); cross-runtime verification correction: `8c164f01` (comparison only). No science formula changed.

## Four-arm reproduction

| Environment | Arm | Mean rank | Unique Top-1 |
|---|---|---:|---:|
| 0 | rawu_footprint | 1.333333 | 0.750000 |
| 0 | rawu_nearest | 1.333333 | 0.750000 |
| 0 | u_footprint | 1.333333 | 0.750000 |
| 0 | u_nearest | 1.333333 | 0.750000 |
| 1 | rawu_footprint | 1.291667 | 0.791667 |
| 1 | rawu_nearest | 1.291667 | 0.791667 |
| 1 | u_footprint | 1.500000 | 0.583333 |
| 1 | u_nearest | 1.500000 | 0.583333 |
| 2 | rawu_footprint | 1.208333 | 0.791667 |
| 2 | rawu_nearest | 1.208333 | 0.791667 |
| 2 | u_footprint | 1.458333 | 0.583333 |
| 2 | u_nearest | 1.458333 | 0.583333 |

Max absolute numeric deviation versus supplied Pro: 1.0913936421275139e-11; max relative deviation using denominator 1+abs(reference): 3.6774247914710476e-14. All ranks, unique Top-1 and summaries agree exactly. Projection agrees bitwise with the unchanged Pro code on this runtime; archive matrix deviation is 2.220446049250313e-15.

All 12 Pro CSVs reproduced. Tests: 8 original + 9 implementation regression tests passed. Repeated gains/SSE agree byte-for-byte. 1,584 native p products retain SHA256; preexisting occurrence/blur/planner/simulator code remains unchanged. Rawu rescues 10 targets, harms 0 previously correct targets, across 4 source units.

## Costs (local CPU, one thread)

| Environment | Both map kinds + operators + four template arms (seconds) | Array payload bytes |
|---|---:|---:|
| 0 | 9.084227 | 698112 |
| 1 | 8.459083 | 669888 |
| 2 | 9.100580 | 669888 |

Online median: 19.4–20.2 us/target/arm; q95: 21.9–28.6 us. Each call scores six candidates using 10x30 observations. Cost timing repeats already OPEN observations without fitting. Memory is array payload, excluding Python overhead/process RSS. Shared arrays counted once; extraction/hash checks excluded from preparation timing.

## Scope and artifacts

New PMFS forward: 0; new GADEN: 0; training: 0; closed loop: 0. No House03/sealed scientific data opened. Footprint D1 replay cancelled. Standalone development readout, not a live planner deployment.

Authoritative outputs: `verified_implementation/`. Earlier runtime/pre-comparison/output-order attempts retained separately. No source, seed, threshold, template formula or scoring formula tuned. A reporting-only Git path check was corrected to use NUL-separated paths for Chinese filenames; no computation changed.

Templates, map-kind labels, operators, gains, SSE, ranks, unique Top-1, paired margins, rescue/harm and costs are saved. Exact task/Pro/D0 ZIPs are embedded in the portable review. `SHA256SUMS` inventories the review archive.

STOP. Fresh House03 gate was not frozen or run.
