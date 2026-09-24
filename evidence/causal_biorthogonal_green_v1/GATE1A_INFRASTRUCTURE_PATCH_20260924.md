# Gate 1A pre-result execution repair

The first execution at source commit `ef4833e2ae7570610e2e87aee8a30bd1acdef875` stopped while `prepare_gate1a_bank.py` validated the frozen PMFS candidate manifest. The error was `ValueError: y-center drift for quadtree_1_1_5_4`.

The manifest records the center **support cell** of each quadtree leaf. For an even-sized leaf, its index is `origin + size // 2`. The validator instead assumed the geometric midpoint `origin + (size - 1) / 2`, producing a 0.15 m false mismatch. The corrected center-cell expression agrees with all 164 frozen manifest rows (maximum absolute coordinate difference below `8e-7 m`).

This change affects only the input-manifest consistency check. It does not alter the 631-cell support expansion, occupancy filter, true source, W2 wind, target or prediction seeds, 2×2 pooled probes, observation times, score, or PASS thresholds.

No prediction vector or target rank was produced before this repair. The output directory contained no `pmfs_*.npy` files. The unchanged frozen runner must be restarted from the same contract after this patch.
