# M1 Refinement — Physics-Shaped Wind-Posterior Adversary

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Status: preferred refinement of ambiguity calibration; empirical validation pending Native-baseline recovery.

## 1. Motivation

The Path-KL note gives a transport-native statistical metric, but a single hand-chosen global rho remains undesirable and path-level data-processing bounds can become overly conservative over long filament histories.

A cleaner deployment interface already exists in modern probabilistic wind mapping:

\[
W\sim\mathcal N(\hat W,\Sigma_W),
\qquad
\Sigma_W=H^{-1},
\]

where H is a physics-informed precision/Hessian.

The main framework should therefore accept a generic wind-field posterior. GMRF-W is one concrete provider, not the claimed innovation.

## 2. Current MAPIRlab GMRF-W interface

Repository: MAPIRlab/GMRF-wind.

Current ROS service:
gmrf_msgs/srv/WindEstimation.srv

returns:
- u
- v
- var_u
- var_v
- cov_uv

The current core computes marginal variances/covariance from columns of the inverse Hessian. In gmrf_map.cpp, for example, the variance of Wx at cell j is taken from the j-th diagonal element of H^-1.

The 2026 Building and Environment paper describes GMRF-W as a training-free physics-informed airflow posterior whose precision incorporates mass conservation, advection, diffusion and obstacle constraints.

This means a transport uncertainty geometry is available source-blind.

Reference:
Monroy, Ojeda, Gonzalez-Jimenez,
A physics-informed Gaussian Markov random field framework for indoor airflow field estimation,
Building and Environment 303 (2026) 114957.
DOI: 10.1016/j.buildenv.2026.114957

## 3. Wind-posterior ambiguity has an exact KL geometry

Suppose the nominal wind posterior is

\[
P_W=\mathcal N(\hat W,H^{-1})
\]

and nature is allowed to shift its mean while preserving covariance:

\[
Q_{\delta W}
=
\mathcal N(\hat W+\delta W,H^{-1}).
\]

Then

\[
D_{\rm KL}(Q_{\delta W}\|P_W)
=
\frac12\delta W^\top H\delta W.
\]

Therefore a KL ambiguity set is exactly the posterior ellipsoid

\[
\mathcal A_\rho
=
\left\{
\delta W:
\delta W^\top H\delta W\le2\rho
\right\}.
\]

Interpretation:

- wind modes strongly constrained by observations/physics are expensive for the adversary;
- poorly constrained but physics-compatible modes are cheap;
- obstacle, mass-conservation, diffusion and advection structure enter through H;
- source truth is nowhere used.

This is preferable to independent arbitrary perturbations at each map cell.

## 4. Main robust source-identification game

For current source belief pi(s), candidate sensing action x, and wind field W, let

\[
I_x(W)=I(S;Y_x\mid W)
\]

be source information induced by PMFS forward maps under W.

Define

\[
\boxed{
J_\rho(x)
=
\min_{\delta W^\top H\delta W\le2\rho}
I_x(\hat W+\delta W)
}
\]

and select

\[
\boxed{
x^\star=\arg\max_xJ_\rho(x).
}
\]

This is the desired scientific object:

**choose the next observation where source identity remains distinguishable even under the most damaging physically plausible wind-field error.**

It is not model averaging. It is not nominal expected information. It is not Renyi-infotaxis.

## 5. First-order closed form

If the ambiguity is local enough for first-order expansion,

\[
I_x(\hat W+\delta W)
\approx
I_x(\hat W)+g_x^\top\delta W,
\qquad
g_x=\nabla_W I_x(\hat W).
\]

The ellipsoidal trust-region inner problem has exact solution:

\[
\min_{\delta W^\top H\delta W\le2\rho}
g_x^\top\delta W
=
-\sqrt{2\rho}\sqrt{g_x^\top H^{-1}g_x}.
\]

Hence

\[
\boxed{
J_\rho^{(1)}(x)
=
I_x(\hat W)
-
\sqrt{2\rho}
\sqrt{g_x^\top\Sigma_Wg_x}
}.
\]

The robust action score is therefore:

**nominal source information minus posterior-wind uncertainty projected onto the information-sensitive direction.**

This is not an arbitrary weighted sum: the coefficient and metric arise from the KL ambiguity problem.

## 6. Scientific interpretation

The old failed "candidate variance" probe asked:

> where does the nominal simulator separate source candidates most?

This refined M1 asks:

> where is the source-discriminating information least sensitive to wind-field modes that are poorly constrained by current physics and measurements?

A cell can have large nominal information but low robust value if its source separation depends strongly on an uncertain wind mode.

Conversely, a moderately informative cell can be preferred if its source signature is invariant across the credible transport field.

This is exactly the failure mode we need to test after baseline repair.

## 7. Relation to Path-KL derivation

The two derivations are complementary.

Path-KL:
- uses PMFS stochastic filament dynamics directly;
- supplies a physical relative-entropy interpretation of drift error;
- remains available even if the wind provider exposes only a deterministic mean field.

Wind-posterior KL:
- exploits a probabilistic wind mapper when available;
- provides source-blind spatial structure and covariance;
- avoids treating all drift perturbations as equally plausible.

Do not multiply both into an ad-hoc combined penalty.

Empirically compare them only after the cheapest TCIF falsification shows a source-rank signal.

## 8. Radius calibration without source truth

For a Gaussian posterior, credible ellipsoids give a predeclared statistical interpretation:

\[
\delta W^\top H\delta W\le \chi^2_{d,1-\beta}.
\]

Equivalently,

\[
\rho=\frac12\chi^2_{d,1-\beta}.
\]

However, a full d=2N-dimensional ellipsoid may be too conservative or numerically awkward.

Practical candidates, in order:

1. use a fixed predeclared credibility level beta and an effective/low-rank wind subspace;
2. use local 2D marginal ellipsoids returned by WindEstimation;
3. calibrate a lower-dimensional ambiguity radius from source-blind wind innovations;
4. only if needed, investigate 2026 conformal robustness calibration.

No source-rank-based radius selection is allowed.

## 9. Current implementation risk

The exact inner minimization needs repeated PMFS hit-map evaluation under perturbed W and may be too expensive online.

The first-order form only needs the uncertainty-projected gradient

\[
g_x^\top\Sigma_Wg_x.
\]

Candidate ways to estimate it:
- common-random-number finite differences along posterior wind directions;
- score-function / likelihood-ratio sensitivity of Gaussian filament transitions;
- a small set of posterior sigma directions.

Do not train a neural surrogate unless simpler estimators fail.

## 10. Strong kill condition

If a source-blind wind uncertainty geometry does not improve truth-source rank beyond nominal Shannon information under deliberate transport mismatch, kill M1.

Also kill the first-order version if its ranking is effectively identical to nominal MI or if gains depend on truth-tuned rho.

## 11. Preferred paper-level narrative if it survives

Parent idea:
distributionally robust decision-making / robust active inference under environment-model ambiguity.

Domain transfer:
the uncertain environment model is not robot kinematics but the stochastic plume transport law.

PMFS-specific derivation:
use a probabilistic physics-informed wind field to define the adversary geometry and maximize worst-case source identifiability.

This remains valuable even if the repaired Native PMFS baseline performs well, because rho -> 0 recovers the nominal policy and nonzero uncertainty addresses realistic non-oracle wind knowledge.
