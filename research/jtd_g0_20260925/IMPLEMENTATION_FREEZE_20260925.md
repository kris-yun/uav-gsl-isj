# JTD-G0 implementation freeze before scoring

This branch starts at the exact R0 PASS commit. A0 independently verified all
288 pooled arrays against their raw 10-frame concentration cubes, per-run
seeds, and the Gate1A probe contract. The canonical cache is lossless raw ppm.

`run_jtd_g0.py` follows the supplied frozen config: five disjoint pairs of
ordered times, two unsupervised pooled-reference PCs per block, four fixed
realization folds, source-specific 10D OAS Gaussian likelihood, and 200
within-source block derangements per fold. The null preserves each 2D block's
complete empirical sample multiset and never changes eval targets. Full and
null use identical scalers and PCA transforms. OAS covariance receives only a
fixed relative numerical jitter of 1e-10 before Cholesky factorization.

The paired effect is the median null NLL for each held-out task minus FULL NLL.
Hierarchical bootstrap resamples sources and then their independent full
realizations, using the config's 5000 draws and seed. The shipped
`decision_gate.py` applies the supplied GO/HOLD/STOP thresholds without edits.

The exact frozen ZIP is copied under `frozen_package/`; its original
`PACKAGE_SHA256.txt` was verified before any code was written. No R0 evidence
or raw data is modified.
