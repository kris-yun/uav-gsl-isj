# C0.5 pre-holdout training repair

The first frozen training attempt is preserved in
`m4_c05_local_compare_20260923_frozen_v1/`. Its S2-W2 holdout was **not**
opened. In operator training seed 1729, all eight source-injection weights
were negative. A nonnegative source impulse passed through a bias-free 1x1
convolution and ReLU therefore produced exactly zero state. The training loss
was 0.3063303133 in both the first and last of 80 epochs. This is a dead
training path, not evidence about M4 generalization.

The only v2 change is `abs(source_projection)` in place of
`ReLU(source_projection)`. It preserves a nonnegative source-supported state,
keeps the same parameters and trainable capacity, and gives gradients for
negative initial weights. The data split, two training seeds, loss, optimizer,
epoch count, spatial reduction, comparison arms, and stop rule remain as in
`C0_5_LOCAL_COMPARISON_FREEZE_20260923.md`. No holdout target was used to
select the repair. The v1 checkpoints will not be evaluated on S2-W2.

If either v2 operator run still fails to reduce training loss, stop the local
comparison as a training-feasibility HOLD. If training succeeds, hash and
archive all four v2 checkpoints before opening S2-W2. Do not use a second
model repair after held-out results are read.
