# SLL-v2 Independent Review — 2026-09-24

Status: **CONFIRMED NO-GO FOR LEARNED SOURCE-LINEAGE OPERATOR**

Reviewed package SHA-256:
`bed958d0eb8a896549aa9130efaea447b189fd9152006195691bbf0d6059811d`

Frozen result:
`L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`

## Independent verification

The review package is internally consistent:
- 8 factorial cells;
- 566 snapshots/cell;
- zero duplicate lineage snapshots;
- zero invalid birth assignments;
- zero lineage progression errors;
- zero maximum sigma-age reconstruction error;
- 20,000 independently sampled transitions/cell in the review package.

The frozen holdout results are reproduced conceptually by the compact samples.

### Holdout A

- 2-D particle XY RMSE: 0.036366 m
- deterministic 3-D physics: 0.022384 m
- learned lineage residual: 0.022317 m
- destroyed-lineage null: 0.022364 m
- 3-D centroid improvement over 2-D: 73.60%
- learned operator centroid improvement over 3-D: 1.78%
- learned operator RMSE improvement over 3-D: 0.30%

### Holdout B

- 2-D particle XY RMSE: 0.036150 m
- deterministic 3-D physics: 0.021431 m
- learned lineage residual: 0.021341 m
- destroyed-lineage null: 0.021402 m
- 3-D centroid improvement over 2-D: 75.29%
- learned operator centroid improvement over 3-D: -0.04%
- learned operator RMSE improvement over 3-D: 0.42%

The learned residual therefore has no load-bearing transferable effect.

## Why the learned operator has almost nothing left to learn

Frozen GADEN noise parameter:
`filament_noise_std=0.01`.

In the used GADEN core, backward-compatibility scales this by 10, and each
0.1-s integration step multiplies the sampled Gaussian perturbation by dt.
Therefore the stochastic position perturbation is approximately:

[
\sigma_{step} = 0.01\;m / axis.
]

Adjacent saved snapshots in the raw bank are separated primarily by 5 or 6
simulation steps. The theoretical random-walk floor is therefore:

[
\sqrt{5\text{--}6}\times0.01 \approx 0.0224\text{--}0.0245\;m/axis.
]

Independent review-package samples give a mixed-step RMS floor of about
`0.02269 m/axis`.

This is essentially the same magnitude as the deterministic 3-D physics
holdout RMSE:

- A: 0.022384 m
- B: 0.021431 m

Sampled deterministic-physics residuals are approximately zero-mean,
weakly cross-correlated in XY, and have standard deviations around
0.021--0.023 m in XY across cells.

Interpretation:

> deterministic 3-D physics already explains almost all predictable one-step
> transport; the remaining one-filament error is dominated by the simulator's
> injected stochastic walk.

A deterministic learned transition cannot reasonably obtain the frozen
10% improvement because the residual is predominantly unpredictable noise.

This does NOT retroactively change the frozen L1 decision.

## What is actually learned from the failure

1. **2-D projected transport is insufficient.**
   Deterministic 3-D physics reduces next-centroid error by about 74--75%.

2. **A learned deterministic source-lineage operator is not justified.**
   It improves over 3-D physics by only ~0--2% and survives lineage destruction.

3. **3-D physics should be retained only as a physical auxiliary/baseline.**
   It is not a learned main innovation.

4. **The next main innovation must operate at the inverse/probability level.**
   The forward mean dynamics are already near their stochastic error floor.
   The unresolved problem is how to infer source probability from a stochastic
   transport law without pretending realization-specific noise is predictable.

## Prior-art warning discovered after L1

A direct Schrödinger-bridge / backward-transport route is already occupied in
2026 chemical source localization:

Maurizio Carbone & Lorenzo Piro,
*Learning Backward Transport for Source Localization*,
arXiv:2607.26892 (July 2026).

Therefore generic claims such as:
- Schrödinger bridge for chemical-source localization,
- learned backward transport for plume source localization,
- Langevin sampling of candidate emission locations,

must be treated as occupied and are NOT available as the project's main novelty.

## Next screening target

Do not train another forward surrogate.

Screen a **stochastic transfer-density / Fokker-Planck belief operator** whose
state is a candidate-conditioned transition probability density, not a single
plume realization.

The first offline gate must ask whether a stochastic transition-density
likelihood improves source identifiability over:
- deterministic 3-D physics;
- Native PMFS;
- deterministic field likelihood;

without reproducing the already-published backward-transport/Schrödinger-bridge
formulation.

No closed loop is authorized from this document.
