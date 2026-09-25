# SPX-G0 reference-rank implementation correction

The first scoring invocation stopped after its first pair-progress marker,
before writing any pair utility, summary or diagnostic result. The scorer had
added a guard requiring at least two varying raw coordinates in every
two-time reference block. This guard was stricter than the frozen SPX charter,
which specifies `PCA(n_components=2)` and prohibits pair deletion.

A reference-only audit of all frozen pair/protocol/fold/block cells found 29
rank-deficient cases out of 3,480, affecting 11 of 87 pairs; one reference
block was all zero. No held-out utility or pair result was inspected in this
audit. The guard was removed so the specified deterministic scikit-learn full
SVD PCA2 is used for every pair, including rank-deficient blocks. This is a
numerical implementation correction, not a change of probe, pair, fold,
feature count, Gaussian family or diagnostic thresholds. The complete SPX-G0
score is rerun from the beginning under the updated pre-score lock.

Rank deficiency is retained as an interpretation limitation in the result;
no source, pair or observation is excluded.
