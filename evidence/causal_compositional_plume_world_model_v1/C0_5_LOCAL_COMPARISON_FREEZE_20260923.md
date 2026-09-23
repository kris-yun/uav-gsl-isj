# C0.5 House02 local comparison freeze

This is a bounded same-House mechanism diagnostic on the existing eight GADEN
realizations. It cannot satisfy the separate G3 unknown-House transfer gate.
No new House, plume seed, PMFS/ROS code change, or closed-loop run is allowed.

## Frozen split and endpoint

- Train only on S1-W1, S2-W1, S1-W2, both plume seeds and ten fixed spatial
  snapshots per realization. S2-W2 A/B target files are unopened during training.
- Evaluate S2-W2 A and B separately after both models and both training-seed
  checkpoints are frozen and hashed.
- Compare free-space mean squared error of `log1p(concentration)` at the fixed
  2× spatial reduction. Treat each plume seed as one replicate; the ten times
  are correlated snapshots, not ten independent experiments.
- The operator must improve over the monolithic model for **both** training
  seeds and **both** held-out plume seeds before any source-rank replay or null.
  A tie/reversal stops the local positive-signal claim without retuning.

## Frozen models and training

The implementation is `research/causal_compositional_plume_world_model_v1/c05_frozen_local_comparison.py`.
The operator injects the source field into a hidden state, then applies five
wind/obstacle/time-conditioned transport steps. The monolithic predictor takes
all six channels together. Five spatial dilations are 1, 2, 4, 8, 16.
Trainable parameter counts must differ by at most 10%. Both use the same
training examples, unweighted free-space loss, 80 epochs, Adam learning rate
0.001, weight decay 0.00001, batch size 10, and fixed training seeds 1729/2718.
No validation set or early stopping uses the held-out cell.

The models use the frozen iteration-1 wind slice as a coarse transport input;
the true GADEN simulation uses a time-varying wind sequence. Any positive
result is therefore restricted to this coarse local diagnostic. This input
limitation cannot be solved by looking at S2-W2 and changing architecture.

## Decision boundary

This local field comparison is a prerequisite screen only. A favorable field
metric alone never establishes M4-v2; the original C0.5 charter still requires
truth-source candidate rank and destructive nulls. The G3 gate additionally
requires at least two genuinely held-out Houses with independent plume seeds,
unseen physical wind and sensor shift. Existing G3 status is HOLD.
