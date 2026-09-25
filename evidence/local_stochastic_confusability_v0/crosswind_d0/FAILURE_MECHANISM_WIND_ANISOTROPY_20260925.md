# LSC Cross-Wind Failure Mechanism — Wind-Relative Anisotropy Audit

Date: 2026-09-25

Status: **DESCRIPTIVE FAILURE EXPLANATION ONLY; DOES NOT RESCUE LSC**

## 1. Cross-wind edge-rank reordering

Across the ten frozen local source edges:

Energy-distance rank correlation:
- W0 vs W1: rho = 0.503 / 0.552 for split A/B;
- W0 vs W2: rho = -0.345 / -0.345;
- W1 vs W2: rho = -0.430 / -0.418.

Fresh pair-confusion rank correlation:
- W0 vs W1: rho = 0.506 / 0.576;
- W0 vs W2: rho = -0.299 / -0.575;
- W1 vs W2: rho = -0.079 / -0.196.

Thus W2 does not simply rescale the same confusion geometry; it reorders which local source pairs are hard.

## 2. Wind-relative orientation

Using the frozen House02 wind inventory and averaging the horizontal mean wind vectors over the eleven iterations gives approximate mean directions:

- W0 `3,5-1_slow`: -119.4 deg;
- W1 `3,5-1_fast`: -116.9 deg;
- W2 `4,5-3_slow`: +160.0 deg.

For the 2x4 source panel, local edges are horizontal (x-displacement) or vertical (y-displacement).

Absolute source-pair displacement alignment with the mean wind:
- W0: horizontal 0.490, vertical 0.872;
- W1: horizontal 0.453, vertical 0.891;
- W2: horizontal 0.940, vertical 0.342.

Therefore W0/W1 make the vertical source-pair displacement more wind-aligned, while W2 makes the horizontal pair more wind-aligned.

## 3. Fresh confusion follows the orientation flip

Mean fresh binary error by edge orientation:

Direction A:
- W0: horizontal 0.042, vertical 0.375;
- W1: horizontal 0.188, vertical 0.469;
- W2: horizontal 0.354, vertical 0.094.

Direction B:
- W0: horizontal 0.083, vertical 0.250;
- W1: horizontal 0.104, vertical 0.344;
- W2: horizontal 0.354, vertical 0.219.

In all six wind x split cells, the source-pair orientation that is more aligned with the mean wind has the higher fresh confusion error.

Across all 30 edge x wind units:
- alignment vs fresh error Spearman = +0.470 for split A;
- +0.332 for split B.

These are descriptive statistics only; the two symmetric splits are not independent experiments and the panel contains only two edge orientations.

## 4. Interpretation

The cross-wind LSC failure is consistent with a wind-conditioned anisotropic identifiability geometry:

> changing the physical wind/operator can rotate which source-displacement directions are difficult to distinguish.

This explains why a wind-invariant scalar source-confusability map is not scientifically adequate.

## 5. Novelty boundary

Wind-relative organization of olfactory navigation and upwind/crosswind anisotropy are established prior ideas.

Therefore this observation is retained as a physical mechanism constraint, not promoted as the main innovation.

## 6. Consequence for future routes

Any future representation or statistical-experiment model must condition on wind/operator state and preserve the **wind-conditioned likelihood-ratio geometry** between source hypotheses.

Do not seek a representation that removes wind variation if doing so destroys source-decision information.

The next mainline search should distinguish:
- nuisance variation that can be discarded;
- environment/operator variables that change the source statistical experiment itself.