# Signed AOD House03 F1 full624 execution

Decision: **AOD_F1_HOLD_TIMEBASE**. Execution stopped at signed stage B.
No scientific PASS/FAIL or source-discrimination result was produced.

## Frozen provenance

- Branch: `research/aod-house03-f1-full624-20260927`
- Base: `1008e2db20e74cfdcbdcb511d484e64a4bc6e49a`
- Pre-target freeze: `10dd251eba10b14bca3e0334dbac6ae8af93911a`
- Timebase HOLD freeze: `c5223b092f217d5bd4fb8063e0d5ae3f4e6761f4`
- Original signed ZIP: `1318dd08c0754800b6fcea33100443ed6ebe77b72adb75fcb622b7cbaaa75502`
- Seed manifest: `00bf64ab0d1ce55fda58303b11208019473313b97c4de11f7a2305d16143327d`

## Candidate bank and capacity

All **54,912 / 54,912** scheduled PMFS forwards completed, covering all 624
candidates, 11 states and 8 replicas. Four map channels came from each identical
realization. The row keys, requested seeds, complete template support, array
hashes and unchanged geometry/wind/executable/object hashes were independently
validated before the first GADEN run.

Candidate wall time was **5597.447198803013 s** (93.29 minutes), using four
single-threaded workers on a 12-vCPU VM. The full bank remains at
`/home/zyc/aod_house03_f1_full624_20260927/candidate_forward`.
Allocated bank size is **2,041,757,696 bytes**. After the first metadata run,
available VM disk was **1,520,279,552 bytes**, and available RAM was
**4,846,854,144 bytes**. No old data was deleted.

## First-run metadata gate

Exactly one scheduled fresh plume was generated, for `pmfs_24_13`, replica 0,
requested seed `869241781`, duration 510 s. The remaining **95 runs were not
started**. Only configuration, release, writer and wind-index metadata were read.

Release was enabled at 0 s, but the first nonzero filament appeared at
**0.10000000149011612 s**. All ten required exact timestamps had zero matching
saved records at the signed tolerance of 1e-9 s.

The following nearest timestamps are metadata diagnostics only and were never
substituted as observations:

| Required time (s) | Nearest actual writer time (s) | File ID | Wind index |
| --- | --- | --- | --- |
| 50 | 50.2998046875 | 92 | 8 |
| 100 | 100.09904479980469 | 175 | 3 |
| 150 | 149.79994201660156 | 265 | 10 |
| 200 | 199.80299377441406 | 365 | 10 |
| 250 | 249.80604553222656 | 465 | 10 |
| 300 | 299.80908203125 | 565 | 10 |
| 350 | 349.8121337890625 | 665 | 10 |
| 400 | 399.815185546875 | 765 | 10 |
| 450 | 449.8182373046875 | 865 | 10 |
| 500 | 499.8212890625 | 965 | 10 |

The original seeded numerical core, float clock, release, RNG, save interval and
wind schedule were preserved. The independent metadata verifier reproduced the
HOLD and returned byte-identical output in two executions.

## Scientific evaluation status

Concentration extraction and all scoring were blocked by the signed timebase
gate. Nominal/stress Delta_acc, bootstrap CIs, rank/Top1/Top3/MAP diagnostics,
six pair margins, rescued/harmed counts, secondary B0/ICRA results and zero-target
counts are **not computed**. The requested scientific scoring repeat was not run.
The metadata-verification repeat is a separate integrity check.

## Infrastructure repairs

The isolated logger required two dependency repairs before any actual plume:

- `1fd219be8870a307c876bb41819c7cec100ba805`: explicit linkage to the existing
  historical `libbsc.so`.
- `661bbd88aa8858a61c1541336c4e352209635c7c`: runtime codec search path and loaded
  library/hash verification. The failed loader did not enter the simulator.

Failed build and loader metadata were preserved. Numerical libraries, scientific
parameters and all frozen contracts were unchanged.

## Review scope and stop boundary

The review ZIP includes the original signed package, source/seed manifests,
all frozen full-map and path templates, all 54,912 forward hash records,
implementation sources, exact historical kernels/parity records, logger sources
and build provenance, timestamp/release metadata, independent verification and
execution reports. The unread raw target gas is excluded from the review ZIP.
All raw candidate products and the first raw GADEN output remain preserved on VM.

No nearest-frame substitution, clock repair, extra source/path/seed selection,
additional GADEN run, neural training or closed loop followed the HOLD.
