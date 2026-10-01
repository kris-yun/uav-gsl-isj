# R1P5 suppression audit summary

Decision: **PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY**. STOP.

Integrity PASS: all paired scores finite; matching supports; stored ranks and delta
margins reproduced; truth log-score shift is exactly zero in all four cases.

## Frozen gates

Broad selectivity PASS: 4/4 cases, versus required >=3/4.
Both-house stability FAIL: H01 Spearman is below 0.50, H02 passes.
The frozen partial-selectivity rule therefore returns HOLD, not STOP or promotion.

| Case | 2D-ahead wrongs | Fraction A>0 | Median A | Repaired crossings | Harmful crossings | Ties added | Ties removed |
|---|---:|---:|---:|---:|---:|---:|---:|
| House01_seed0_off_off | 58 | 98.2759% | 41.503304 | 13 | 32 | 12 | 0 |
| House01_seed1_off_off | 85 | 78.8235% | 12.373215 | 8 | 3 | 7 | 0 |
| House02_seed0_off_off | 90 | 93.3333% | 26.236819 | 4 | 4 | 2 | 0 |
| House02_seed1_off_off | 95 | 98.9474% | 38.560129 | 5 | 0 | 5 | 0 |

| House | Common finite wrong leaves | Spearman(delta0,delta1) | Frozen requirement |
|---|---:|---:|---|
| House01 | 54 | -0.136917080 | >=50 common leaves and rho>=0.50 |
| House02 | 79 | 0.570227459 | >=50 common leaves and rho>=0.50 |

## Interpretation

Suppression is broader than the single top wrong competitor, so it is inaccurate
to call the saved R1 effects only one-competitor coincidences. However, the
suppression pattern does not transfer across both House seed pairs: H01 fails.
Broad suppression among already-ahead candidates does not prevent other wrong
candidates from gaining relative advantage. H01 seed0 has 13 repaired crossings
but 32 harmful crossings, explaining why its truth rank deteriorates from 75 to 100.
Across all four cases: 30 repaired crossings, 39 harmful crossings and 26 added
truth ties, with zero removed truth ties. These are descriptive sums, not independent
scientific samples or additional gates.

The result does not establish a transport contradiction verifier, calibrated rejection
probability or safe online hypothesis elimination. It does not authorize a new
counterexample-guided source algorithm, weighting or closed-loop run.
The original R1 HOLD is preserved. All thresholds and analysis code were unchanged.

## Evidence and provenance

The exact eight small Oracle score CSVs and R1 result are now committed under
`inputs/`, avoiding the previous missing-score problem in the GitHub evidence tree.
`INPUT_SHA256.json` records their original absolute paths and byte hashes.
`RUN_PROVENANCE.md` records execution HEAD, Python, command and scope limits.
`INDEPENDENT_VERIFICATION.json` verifies ranks, pairwise gains, tie transitions
and Spearman against independent Numpy/SciPy computation.
`SHA256SUMS.txt` records all retained evidence hashes except itself.
