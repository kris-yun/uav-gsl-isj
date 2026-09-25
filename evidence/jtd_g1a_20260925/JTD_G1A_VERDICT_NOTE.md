# JTD-G1A frozen dense assessment result

Decision: `JTD_G1A_GO_DENSE_PROBABILISTIC_UTILITY_AND_CROSSBLOCK_CONTRIBUTION`. All frozen G1–G6 gates are `{'G1': True, 'G2': True, 'G3': True, 'G4': True, 'G5': True, 'G6': True}`.

- A0: 168 sources × 16 realizations, all 2,688 raw cube hashes, re-pooling and tensor entries exact; R0-18 intersection = 1 source.
- Reference/target split: four folds with 12 references and 4 held-out realizations per source; 0 new plume.
- Mean truth NLL: FULL 4.899556, BLOCK-PRODUCT 14.667428, MBD 6.409661.
- Source-panel Delta BP 9.767873, 95% source-panel sensitivity interval [1.735125210115219, 24.73634769480298]; positive sources 142/168.
- Source-panel Delta MBD 1.510106, interval [1.2407980421924945, 1.7519348533405639]; positive sources 158/168.
- BP comparison remains positive after 20% trimming (0.513133) and removing the largest positive 5% of targets (0.515064). The largest positive target effect is 17613.589; report tail-sensitive mean with the robust metrics.
- FULL vs BP mean Brier: 0.939401 vs 1.024381; 1.0 m posterior mass: 0.839074 vs 0.820551; expected distance: 0.523182 vs 0.551562.
- Independent recomputation of posterior-derived scores/gates passed. Separate all-fold model refits using Cholesky passed; maximum absolute log-posterior difference 2.38418579e-06; MBD block marginals checked 3360 times.

This is a historical same-House dense assessment, not a fresh blinded or cross-environment confirmation. E1 cross-environment HOLD remains unchanged. No dense source was removed, and H01 DEV/House03 were not accessed.
