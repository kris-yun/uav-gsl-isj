# M1 v2.3 — Coupled Transport Adversary for PMFS

Date: 2026-09-23
Status: preferred mathematical realization of DRT-PMFS; empirical decision waits for repaired Native PMFS
Branch: research/maximin-transport-design-v1

## 1. Correction to the independent-interval relaxation

M1-v2.2 allowed each source candidate's predicted hit probability to move independently inside an interval.

That is useful only as a deliberately conservative Level-A probe.

It is not the preferred physical model because the real environment has ONE transport error field. A wind/model perturbation should act simultaneously on all candidate-source simulations.

The preferred object is therefore a **shared transport adversary**:

\[
h_s(x;\theta), \qquad s=1,\ldots,K,
\]

where one common transport perturbation \(\theta\) changes every candidate source's plume.

Nature chooses one \(\theta\), not one unrelated perturbation per candidate source.

This coupling is essential. It prevents the ambiguity model from erasing source separability using mutually incompatible environments.

## 2. Transport perturbation and KL geometry

Represent drift-model error by a low-dimensional field basis

\[
\delta w(z)=B(z)\theta.
\]

For the official PMFS free-space filament step

\[
X_{k+1}|X_k=z
\sim
N(z+\Delta t\,w(z),\,\Delta t^2\sigma^2I),
\]

the perturbed kernel with drift \(w(z)+B(z)\theta\) has one-step KL divergence

\[
D_{KL}(K_\theta(\cdot|z)\Vert K_0(\cdot|z))
=
\frac{\theta^TB(z)^TB(z)\theta}{2\sigma^2}.
\]

Choose a source-independent reference distribution \(\mu(z)\) over free cells and define the mean transition-KL rate

\[
\bar D_{KL}(\theta)
=
\frac{1}{2\sigma^2}
\theta^T
\left[
\sum_z\mu(z)B(z)^TB(z)
\right]
\theta.
\]

Let

\[
M=\sum_z\mu(z)B(z)^TB(z).
\]

Then a physically interpretable ambiguity set is

\[
\mathcal U_\rho
=
\{\theta:\theta^TM\theta\le\rho^2\}.
\]

For a global 2-D wind-bias perturbation, \(B(z)=I\) and \(M=I\), so the ellipsoid reduces to an ordinary bound on common wind-vector bias.

Important:
- \(\mu\) must be source-blind;
- the radius must not be tuned using source truth;
- this mean-KL-rate construction is not the same as a uniform per-state KL guarantee.

## 3. First-order transport response

For candidate source s and hit-map cell i,

\[
h_{s,i}(\theta)
\approx
h^0_{s,i}+g_{s,i}^T\theta,
\]

with sensitivity

\[
g_{s,i}=
\nabla_\theta h_{s,i}(\theta)|_{\theta=0}.
\]

Estimate this source-blind using symmetric simulator perturbations:

\[
g_{s,i,k}
\approx
\frac{
h_{s,i}(+\epsilon e_k)-h_{s,i}(-\epsilon e_k)
}{2\epsilon}.
\]

Use **common random numbers** for the +epsilon and -epsilon filament simulations whenever possible. Otherwise PMFS Monte-Carlo filament noise can dominate the transport derivative.

The linearization is a computational approximation, not the scientific assumption. It must later be checked against held-out finite perturbations.

## 4. Robust source ranking with one shared adversary

Let ordinary PMFS candidate score be \(S_s(\theta)\) and log-score

\[
L_s(\theta)=\log S_s(\theta).
\]

Linearize

\[
L_s(\theta)
\approx
L_s^0+a_s^T\theta.
\]

For the native PMFS factor

\[
1-c_i\gamma|m_i-h_{s,i}|,
\]

away from the zero-residual kink,

\[
a_s
=
\sum_i
\frac{
c_i\gamma\,sign(m_i-h^0_{s,i})
}{
1-c_i\gamma|m_i-h^0_{s,i}|
}
g_{s,i}.
\]

Finite differences of the complete PMFS log-score are also acceptable and may be more robust to implementation details.

### 4.1 Worst-case regret score

Define source-s worst-case regret relative to the best competitor:

\[
R_s(\rho)
=
\max_j
\sup_{\theta\in\mathcal U_\rho}
[
L_j(\theta)-L_s(\theta)
].
\]

Under the first-order model,

\[
R_s(\rho)
=
\max_j
\left[
L_j^0-L_s^0
+
\rho
\sqrt{
(a_j-a_s)^TM^{-1}(a_j-a_s)
}
\right].
\]

Include \(j=s\), which contributes zero, so \(R_s\ge0\).

**Ranking rule:** smaller \(R_s\) is better.

### 4.2 Exact native limit

At \(\rho=0\),

\[
R_s(0)=\max_j L_j^0-L_s^0.
\]

Therefore ranking candidates by ascending \(R_s(0)\) is exactly the same ranking as descending native PMFS score.

This is a hard design requirement: zero transport ambiguity must recover PMFS rather than create a new estimator.

### 4.3 Robust dominance certificate

A candidate has \(R_s=0\) iff its linearized score remains at least as large as every competitor throughout the ambiguity ellipsoid.

Thus robust source declaration can be based on a physically meaningful dominance condition rather than an arbitrary posterior threshold.

Do NOT yet freeze a final declaration rule; first test source ranking.

## 5. Robust movement with the SAME shared adversary

At a candidate measurement location x, collect the hit predictions across source candidates:

\[
h^0(x)=[h_1^0(x),...,h_K^0(x)]^T.
\]

Let G(x) be the K-by-d sensitivity matrix whose s-th row is the transport sensitivity of candidate source s at x.

For normalized current source weights w define

\[
C_w=diag(w)-ww^T.
\]

Native PMFS candidate variance is

\[
V_0(x)=h^0(x)^TC_wh^0(x).
\]

Under the common transport perturbation,

\[
V(x,\theta)
=
(h^0+G\theta)^TC_w(h^0+G\theta).
\]

Define guaranteed source separability

\[
V_{shared}(x)
=
\min_{\theta^TM\theta\le\rho^2}
V(x,\theta).
\]

Expand:

\[
V(x,\theta)
=
c+2b^T\theta+\theta^TA\theta,
\]

where

\[
A=G^TC_wG,\quad
b=G^TC_wh^0,\quad
c=(h^0)^TC_wh^0.
\]

Because \(C_w\) is positive semidefinite, A is positive semidefinite. The inner problem is a convex ellipsoidal trust-region problem.

After whitening \(z=M^{1/2}\theta\), it becomes

\[
\min_{\|z\|\le\rho}
z^T\tilde A z+2\tilde b^Tz+c.
\]

If the unconstrained minimizer lies inside the ball, use it. Otherwise

\[
z(\lambda)=-(\tilde A+\lambda I)^{-1}\tilde b
\]

with \(\lambda>0\) chosen so \(\|z(\lambda)\|=\rho\). This is a one-dimensional root solve.

Therefore the shared-adversary movement score is tractable online for a small transport latent dimension.

At \(\rho=0\), \(V_{shared}=V_0\): exact native-PMFS recovery.

## 6. Why shared-adversary v2.3 is stronger than interval v2.2

Independent interval relaxation:
- each candidate can move independently;
- physically incompatible worst cases can be combined;
- likely over-conservative with 100+ candidate sources;
- may collapse source lower probabilities toward zero.

Shared transport adversary:
- one environment perturbation acts on all source candidates;
- explicitly preserves cross-candidate physical correlations;
- directly inherits KL geometry from the PMFS filament transition;
- yields a closed-form/low-dimensional robust source-regret metric;
- yields a tractable trust-region robust movement metric;
- uses the same perturbation set for inference and action.

The interval method remains only a cheap diagnostic/null baseline.

## 7. Minimal perturbation basis for first falsification

Do not start with a large learned wind-error field.

Use the smallest physically interpretable shared perturbation first:

### B0: global drift bias
\[
\theta=(\delta u,\delta v).
\]

This asks whether source identity is fragile to a common bias in the wind field used by PMFS.

Advantages:
- exact direct interpretation in the filament KL;
- only four additional forward evaluations per source for symmetric finite differences;
- no learned model and no training data;
- easy destructive-null construction.

If B0 is positive, later extend to a small spatial basis or dispersion-noise perturbation.

If B0 is negative, do not rescue the candidate immediately with a high-dimensional basis.

## 8. Required linearization audit

For predeclared finite perturbations \(\theta_q\):

1. generate true perturbed PMFS hit maps;
2. predict them with \(h^0+G\theta_q\);
3. report map error and source-score error;
4. compare exact source ranking under the perturbed simulator against the linearized prediction.

If first-order response is poor at the ambiguity radius needed for robust gain, either:
- reduce radius according to source-blind calibration; or
- use direct small-dimensional simulator optimization.

Do not silently keep a bad linearization because it improves source truth rank.

## 9. Falsification sequence after repaired baseline

### C0 — sensitivity reproducibility
Independent filament random realizations, same candidate/source/wind field.

Gate:
transport derivative structure must be stable enough that it is not dominated by simulator Monte-Carlo noise.

### C1 — exact zero-radius recovery
Robust regret source ranking and robust movement ranking must equal native PMFS at rho=0.

### C2 — shared-adversary frozen replay
Use repaired Native candidate maps plus global wind-bias perturbation derivatives.

Compare:
- native PMFS source rank;
- independent-interval robust score (diagnostic);
- **shared-adversary robust-regret rank**.

Primary endpoint:
truth-containing candidate rank.

No rho selected using truth.

### C3 — movement intervention
Compare:
- native PMFS candidate variance;
- shared-adversary guaranteed variance.

Test whether measurements selected by the latter produce better subsequent truth-source rank.

### C4 — mismatch stress
Inject predeclared common wind bias unknown to the inference algorithm.

Expected signature:
- at zero mismatch and small rho: approach Native PMFS;
- as mismatch increases inside the calibrated ambiguity region: degrade more slowly than Native PMFS;
- outside the ambiguity region: guarantee may fail; report it rather than retune.

### C5 — wrong-coupling null
Randomly assign a different transport perturbation to each source candidate, destroying the physical common-environment coupling.

The advantage of the shared-adversary formulation should weaken/disappear.

This is a direct mechanistic null.

## 10. New novelty collisions

### 10.1 Zi et al., IEEE Sensors Journal 2022

"Distributionally Robust Optimal Sensor Placement Method for Site-Scale Methane-Emission Monitoring"
DOI: 10.1109/JSEN.2022.3214176.

They already:
- consider wind uncertainty in methane monitoring;
- use distributionally robust optimization;
- optimize sensor placement for better worst-case behavior.

Therefore forbidden claims include:
- first DRO for gas monitoring;
- first robust sensor placement under wind uncertainty;
- first worst-case gas-sensing design.

Remaining distinction:
- fixed site-scale monitoring network;
- detection-time objective over emission/wind scenarios;
- not sequential mobile source inference;
- not PMFS stochastic transition-law ambiguity;
- not one common transport adversary coupled into both source ranking and robot action.

### 10.2 "Actively inferring methane sources with drones", Environmental Data Science 2026

This recent work already:
- performs active drone source inference;
- jointly infers source location/emission rate with wind speed and wind direction as nuisance parameters;
- compares lawnmower, myopic expected-information-gain, and non-myopic RL policies.

Therefore forbidden claims include:
- first active drone source inference with uncertain wind;
- first joint consideration of source and wind nuisance variables;
- first non-myopic active methane-source inference.

Remaining distinction:
- Bayesian posterior over a low-dimensional parametric forward model;
- wind speed/direction are inferred as nuisance parameters;
- no worst-case distributional ambiguity around a PMFS stochastic transport kernel;
- no shared-adversary guarantee of source separability under an ambiguity set.

## 11. Main novelty statement under test

The only novelty wording currently worth defending is:

> **Distributionally robust transport inference for PMFS:** represent forward-model misspecification as a calibrated ambiguity set on the stochastic filament transport law; use one physically shared least-favorable transport perturbation across all candidate sources; and propagate that same ambiguity into source ranking, localization confidence, and active measurement selection.

This is narrower than "robust GSL", but substantially more defensible.

## 12. Kill conditions

Kill or demote v2.3 if:
- common-transport sensitivities are dominated by filament Monte-Carlo noise;
- shared-adversary robust regret does not improve truth-source rank under mismatch;
- robust movement does not improve later truth rank;
- useful rho must be selected using source truth;
- a simple Bayesian nuisance-parameter treatment matches/exceeds it with lower complexity;
- only the independent interval relaxation works while the physically coupled adversary does not;
- novelty audit finds prior mobile GSL work with essentially the same worst-case shared transport ambiguity and coupled inference/action mechanism.
