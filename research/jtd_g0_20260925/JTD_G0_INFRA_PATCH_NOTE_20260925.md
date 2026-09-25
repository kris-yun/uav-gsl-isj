# Pre-result indexing repair

The first scoring invocation stopped while writing the first SHUFFLED fold
array. NumPy advanced indexing reordered the target axes from 18-by-4 to
4-by-18 in `null[k][mi, :, eval_ix]`, producing a shape-mismatch exception.
No null distribution, metrics, Gate decision, or review package was emitted.

The repair indexes the selected shuffle's 18-by-16 array first, then assigns
its four held-out columns. The fixed folds, 5x2 PCA, OAS, 200 derangements,
seeds, metrics, and thresholds are unchanged. The same frozen run is restarted.
