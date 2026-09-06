# Bounded controlled screen before any production run

Input checkpoint: `61ef472`. This is the next authorized development screen,
not the full CSTAR causal gate and not a production/12-run authorization.

Freeze CSTAR_CONTROLLED_SCREEN_CONFIG_20260907.json and controlled_screen.py
before training. Use seed12, the existing 12 parent realizations and original
three LOHO folds. No new outcomes, routes, seeds or gas-field queries. At 200
fixed updates per model, compare PICR (source cross-entropy + same-source MSE
invariance + different-source separation), matched unconstrained encoder,
context-only and consistently permuted source labels. This is a bounded
implementation of the existing pair-loss reference, not the full constrained
dual/adversary/reconstruction system described by the theory document.

All models use the same initialization, four-record batches, paired prefixes
and optimizer budget. Geometry-only candidate support is every frozen free
cell (6,866 / 6,811 / 7,258), not the old 9x9 route envelope. The physical source
is mapped to its nearest XY cell only for supervised labels and scoring; the
projection distance is reported. There is no learned held-out normalization.
All metadata and source labels remain outside the eight-channel model input.

Report proper score, localization error, same-source distance, different-source
distance and their ratio. The ratio prevents claiming invariance by shrinking
all zS values. Evaluate zS zero/swap and zero-gas/wind controls. Evaluate all
15 prefixes and all four held-out parents; do not discard uninformative cases.
At least two Houses must pass every preregistered directional/control screen
check to advance. Even then, these checkpoints cannot authorize closed loop:
the full required artifacts and additional theoretical tests remain necessary.

M2 first reports a strong source/route-free baseline: train-fold conditional
categorical first-hit histogram given current gas above/below threshold, with
one total Dirichlet pseudocount. Its NLL and Brier are evaluated only on the
held-out House. Compare an unconditional train histogram. This distinguishes
calibrated predictive skill from the prior 98% post-hoc deterministic label
diagnostic. It is not a substitute for either required physics/FOPDT prior,
and no arbitrary plume formula will be renamed a verified prior.

Stop after the frozen screen and report its evidence, including negative
controls or failed checks. Do not add training steps, change regularization,
retune M2 event definition or expand seeds in response to held-out results.
