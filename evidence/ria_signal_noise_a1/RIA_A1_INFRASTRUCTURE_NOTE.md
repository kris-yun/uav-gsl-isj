# RIA-A1 infrastructure-only correction

The first diagnostic invocation stopped at the first bootstrap correlation because `bootstrap_rho` referenced undefined `den` instead of the already computed `denom`. It wrote no association, bootstrap, or decision output.

The one-token correction was committed separately as `90031faf` before the successful diagnostic run. The pre-run code hash was refreshed; all scientific formulas, folds, seeds, thresholds, tensor inputs, and output labels remained unchanged. The reference-only decomposition was recomputed under the corrected code and all frozen decomposition file hashes remained identical. No observed correlation or decision guided the correction.
