# D0 pre-holdout batch-shape repair

The first VM launch at Git HEAD `2c92f89` stopped before wind export because
the VM exposes `python3` but no `python` command. A task-local executable
alias outside the repository resolved that environment issue without changing
the runner or scientific code.

The next launch exported the exact W1/W2 dynamic sequences and passed their
frozen iteration-1 SHA-256 anchors. Training then stopped at the first
backward pass with:

`ScatterAddBackward0 returned an invalid gradient at index 1 - got [1, 2520] but expected shape compatible with [3, 2520]`

No epoch completed, no checkpoint or `train_manifest.json` was written, and
the S2-W2 evaluation command was never reached. The failed output directory
and logs are preserved on the VM with a failure suffix.

Root cause: `conservative_local_mix` built one shared spatial destination
index of shape `[1, H*W]` for a three-cell training batch. Forward scatter
broadcasting accepted it, but backward required a `[3, H*W]` index. The sole
model-code change expands that same index across the batch. It changes no
destination, transport weight, wall rule, loss, optimizer, seed, duration,
threshold, or held-out split. The model's mathematical mapping is unchanged.

The mechanism test now includes a three-item batch backward check and
per-item mass conservation check. The repaired code was tested before any
S2-W2 target access. This is an engineering-only repair to the frozen D0
execution, not a new scientific method version or post-result tuning.
