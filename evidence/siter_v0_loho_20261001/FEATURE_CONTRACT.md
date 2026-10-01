# SITER v0 implementation freeze

This implementation completes the supplied algorithm-family charter before any outer-fold evaluation. It does not tune definitions to held-out outcomes.

## Data and Native anchor

Exactly the six authoritative TNQC Native/off cases, all five source updates each. Each update has its own complete legal free-cell support. Final evaluation uses its last update at or before 300 seconds.

Active leaves are recovered from the candidate manifest by assigning each free cell to the smallest containing rectangle; candidate ID breaks equal-area ties. Reconstruct each candidate's Native score using the archived support alignment (confidence-zero cells contribute factor one). Reconstruct cell posterior proportional to exp(candidate log-score), preserving each leaf's free-cell measure. Require posterior max-absolute parity with the exported Native posterior <=1e-10 for all 30 updates.

No Oracle2D/3D scores or features enter this model. No concentration outside the archived observation stream is queried. Use archived GMRF estimated wind, not CFD wind.

## Fixed dictionary

For a legal cell, p is measured hit probability, c is confidence, h is the candidate hit probability, prior is the archived prior, r=p-h, w=c, and g=c*max(p-prior,0). EPS=1e-12 is only a denominator/wind norm guard. If an evidence denominator is zero, its descriptor is zero. All raw components are nonnegative.

Generalist components (8):

1. Native score badness: 1 minus within-update mid-ECDF of Native candidate log-score.
2. Confidence-weighted absolute residual mean: sum(w*abs(r))/sum(w).
3. Weighted absolute-residual q50.
4. Weighted absolute-residual q90. Weighted quantiles are the first ordered value whose cumulative weight reaches the requested fraction.
5. Unsupported observed-hit mass: sum(g*1[h==0])/sum(g).
6. Observed-miss predicted mass: sum(c*(1-p)*h)/sum(c*(1-p)).
7. Support disagreement: 1 - sum(c*min(p,h))/sum(c*max(p,h)); zero if the denominator is zero.
8. Leaf area fraction: number of owned free cells / total legal free cells.

Flow components (5): candidate source point is the archived Native sampled point, falling back to the manifest center only if the sampled point is unavailable/nonfinite. It is an intermediate physical hypothesis, not an absolute-coordinate model feature. Let d=x-source, uhat=u/(norm(u)+EPS), a=d dot uhat, b=norm(d-a*uhat).

9. Gas-weighted upwind violation: sum(g*1[a<0])/sum(g).
10. Cross-flow residual dispersion: weighted standard deviation of b with weights c*abs(r).
11. Along-flow residual asymmetry: abs(sum(c*r*a))/sum(c*abs(r*a)).
12. Wind incoherence: max(0,1-norm(sum(g*uhat))/sum(g)). This can be candidate-independent; it remains in the frozen dictionary rather than being dropped after outcomes.
13. Downwind observed-miss predicted mass: sum(c*(1-p)*h*1[a>0])/sum(c*(1-p)).

No optional streamline descriptor in v0: no numerical integration/termination contract was supplied. All 13 components are fixed across folds. Coordinates, House, seed, truth, truth distance, update ID and timing are not model input components.

## Preprocessing and objective

Per-component min/max fitted on training updates only. Transform to [0,1] and clip out-of-range inputs to that range; constant training components map to zero. Held-out features do not determine bounds. This is feature preprocessing, not clipping source posterior or target loss.

For each training update, compare the true-owner leaf with every wrong active leaf. Minimize mean softplus(native_wrong-native_truth - C_wrong+C_truth), averaging pairs within an update, then averaging updates equally. No replicated truth samples. The anchor remains unmodified.

Primary alpha>=0, sum(alpha)=1. Consequently 0<=C<=1; no extra penalty multiplier is introduced. This bound is part of v0, not adjusted after results.

L1 is constant on a nonnegative simplex and cannot create sparsity. Use hard feature-count candidates K={1,2,4,all available group components}, with duplicate K values removed. Within each training split, deterministic greedy forward selection minimizes its training objective; optimize each selected simplex using SLSQP, analytic gradient, ftol=1e-10, maxiter=500. Equal loss ties within 1e-12 choose the smaller feature index. Start each optimization uniformly. Select K by leave-one-run-out validation within the four outer-training runs, each validation run's five updates equally weighted. Equal validation-loss ties within 1e-12 choose smaller K. Refit the selected K on all outer-training updates.

Three independent outer fits are frozen before any outer result is evaluated. LOHO results must not feed back into feature, preprocessing, capacity or optimization choices.

## Ablations

Native (no correction); generalist-only (components 1..8); flow-only (9..13); full; signed diagnostic. Generalist/flow/full each use the same inner K procedure. Signed diagnostic uses all components with beta=alpha_plus-alpha_minus, alpha_plus/minus>=0 and total alpha=1, so ||beta||1<=1. It uses the same pairwise objective and training-only normalization, with no additional multiplier or tuning. It is never promoted to the primary model.

## Evaluation

Truth midrank =1+#strictly better wrong candidates+0.5*#exactly tied wrong candidates; pessimistic rank=1+better+wrong ties. Source margin=truth log-score-best wrong log-score. No tolerance is used to manufacture ties. Top-5% endpoint uses the frozen Native ExpectedValue(...,0.05) C++ implementation; verify its Native-posterior parity before evaluating corrected posteriors.

Reuse the original TNQC collapse definition: variance<1 m² and top-5% endpoint error>2 m. Report both baseline/corrected flags and newly created flags (corrected true, Native false). The charter's no-new-collapse condition uses newly created flags. Existing collapse is not concealed. Each House must have at least one seed with both rank and endpoint improvement to count as the stated improving seed; this conservative conjunction cannot rescue any other gate.

The charter's scientific GO gates remain unchanged. All six outputs are development LOHO on previously studied trajectories, not untouched confirmation. The historical OCB confirmation datasets remain sealed. Complete independent audit, package and STOP even if GO; do not start closed loop automatically.
