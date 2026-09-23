# Transport-uncertainty interface audit — PMFS x GMRF-wind

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Purpose: determine whether DRT-PMFS can obtain ambiguity geometry from the existing wind estimator without truth-tuned robustness parameters.

## 1. Current GMRF service interface

Current MAPIRlab/GMRF-wind defines:

\`\`\`
float64[] x
float64[] y
---
int64 map_width
float64[] u
float64[] v
float64[] var_u
float64[] var_v
float64[] cov_uv
\`\`\`

Thus the service API can carry a 2x2 marginal covariance for each queried wind vector.

## 2. PMFS currently consumes only the mean

In MAPIRlab/GasSourceLocalization humble, \`PMFSLib::EstimateWind()\` reads:

\`\`\`cpp
estimatedWind.dataAt(pair.x, pair.y) =
    Vector2(response->u.at(ind), response->v.at(ind));
\`\`\`

It does not consume \`var_u\`, \`var_v\`, or \`cov_uv\`.

Therefore the PMFS forward simulator uses a point wind field even when the connected GMRF service can expose uncertainty fields.

Important nuance:
the official PMFS simulation launch uses ground-truth wind. This observation matters primarily for estimated-wind / real-deployment mode, not for strict synthetic Native-PMFS parity.

## 3. The covariance channel is not automatically valid online

Current normal GMRF node \`Cgmrf::update()\` performs:

\`\`\`cpp
my_map->MAP_estimation_GMRF(num_iterations_MAP);
\`\`\`

but does NOT call:

\`\`\`cpp
my_map->computeUncertainty_GMRF();
\`\`\`

The latter explicitly computes covariance from the inverse Hessian:
\`C = H^{-1}\`, extracting per-cell \`varX\`, \`varY\`, and \`covXY\`.

The validation code calls this uncertainty computation only for selected uncertainty-aware metrics such as NLPD/ANLPD.

Moreover \`getEstimation()\` applies a floor:

\`\`\`cpp
vx = max(0.0001, m_map[index].var);
vy = max(0.0001, m_map[index+N].var);
\`\`\`

Therefore the mere presence of \`var_u/var_v/cov_uv\` in the service response does NOT prove that a normal online run is returning freshly computed posterior covariance.

## 4. Consequence for DRT-PMFS

Do not claim:
"PMFS ignores a valid online GMRF covariance that is already available for free."

The defensible statement is narrower:

> The GMRF core and service contract contain a route for posterior wind uncertainty, but the ordinary online update path currently propagates only the MAP wind estimate into PMFS. DRT-PMFS can investigate whether explicitly computing and propagating that uncertainty yields a physically grounded transport ambiguity geometry.

This is an implementation opportunity, not the main novelty.

## 5. Two-track ambiguity design

### Track T0 — baseline-independent research test

On repaired Native PMFS / ground-truth wind:
- inject predeclared common wind perturbations;
- build a low-dimensional shared-adversary sensitivity model;
- evaluate robust source rank and robust movement;
- use a fixed preregistered radius panel only for falsification;
- do not claim deployment calibration.

This lets M1 live or die independently of GMRF implementation details.

### Track T1 — practical estimated-wind deployment

After T0 gives a positive signal:
- explicitly call \`computeUncertainty_GMRF()\` after MAP estimation at the source-update cadence, or derive an efficient approximation;
- export each cell's 2x2 covariance;
- verify PSD, magnitude, spatial behavior, and empirical calibration against held-out wind observations;
- use the covariance only to define ambiguity SHAPE / metric;
- retain a separate statistically justified scale if the covariance is miscalibrated.

Do not assume Hessian-inverse covariance is calibrated merely because it exists.

## 6. Relation to the shared transport adversary

For local wind-error covariance \(\Sigma_w(z)\), a Mahalanobis perturbation has the form

\[
\delta w(z)^T\Sigma_w(z)^{-1}\delta w(z)\le r^2.
\]

A low-dimensional shared field \(\delta w(z)=B(z)\theta\) induces

\[
\theta^T
\left[
\sum_z\mu(z)B(z)^T\Sigma_w(z)^{-1}B(z)
\right]
\theta
\le r^2.
\]

This gives the common-adversary ellipsoid matrix M from forward-estimator uncertainty rather than arbitrary Euclidean scaling.

Caution:
GMRF's service exposes only per-cell marginal covariance, not the full cross-cell covariance through this service. A field-level shared perturbation therefore still needs either:
- a low-dimensional basis B(z), or
- access to / approximation of cross-cell precision from the GMRF Hessian.

Do not pretend independent per-cell ellipses are a fully coherent joint wind-field posterior.

## 7. Auxiliary A1 decision

Inverse Conformal Risk Control (ICML 2026) remains scientifically relevant but is **demoted from preferred immediate auxiliary**.

Reason:
its finite-sample guarantees assume calibration/test exchangeability, while online active robot sampling changes the spatial sampling distribution. The official ICRC repository explicitly lists online/sequential calibration as future work.

Use ICRC only if we later have an independent, defensible calibration bank matching the deployment distribution.

For now:
- main innovation M1 must not depend on ICRC;
- radius calibration remains an open implementation/scientific subproblem;
- T0 falsification uses a predeclared sensitivity panel;
- T1 first tests whether GMRF uncertainty geometry plus source-blind scale validation is sufficient.
