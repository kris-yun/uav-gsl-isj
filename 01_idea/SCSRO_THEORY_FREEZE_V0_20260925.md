# SC-SRO Theory Freeze V0 — Source-Conditioned Correlated Stochastic Response Operator

Date: 2026-09-25

Status: MAIN-INNOVATION CANDIDATE, EXISTING-D1R D1 ONLY

## 1. Scientific problem

Repeated failures of deterministic source-to-field routes showed that a single source does not induce one stable plume realization. D1R further shows that the stochastic structure is source dependent.

The forward object should therefore be a distribution-valued response operator, not a deterministic plume field.

## 2. Random response object

For source context c_s, environment E and registered observation field Y(q), q=1..300, model

Y_s = mu(c_s,E) + U(E) diag(sqrt(lambda(c_s,E))) xi + sqrt(tau(c_s,E)) epsilon,

with xi ~ N(0,I_K), epsilon ~ N(0,I).

Equivalently,

Y_s | c_s,E ~ N(mu_s, K_s),

K_s = U diag(lambda_s) U^T + tau_s I.

U captures shared correlated turbulence modes; lambda_s captures source-conditioned modal uncertainty; tau_s captures unresolved residual variance.

This is a finite-rank covariance-operator approximation. Positive semidefiniteness is guaranteed by construction.

## 3. Inverse localization

For each PMFS candidate source cell s_i, evaluate the explicit stochastic forward likelihood

log p(y | s_i,E)

and update

P(S=s_i | y,E) proportional to pi_i p(y|s_i,E).

The final output remains the original PMFS source probability map.

## 4. Why this is not the stopped deterministic Green/operator route

Earlier deterministic Green/operator routes attempted to learn or replay a stable source-to-sensor response.

SC-SRO instead models the entire source-conditioned response distribution. The correlated covariance modes are part of the inferential signal rather than nuisance that is averaged away.

## 5. D1R linear lower-bound evidence

Use complete source holdout: 84 source cells are absent from model fitting, and evaluation uses the opposite 8-realization half with all 168 source candidates in the posterior.

Mean-only raw/PCA+KRR baseline mean true-source log2 scores:
- direction0 parity0: -4.48136
- direction0 parity1: -4.48578
- direction1 parity0: -4.49860
- direction1 parity1: -4.50111

Low-rank global-covariance baseline:
- -4.42779
- -4.45319
- -4.39143
- -4.38928

Source-conditioned low-rank covariance model:
- -4.40688
- -4.38973
- -4.30622
- -4.33291

Source-conditioned modal amplitudes therefore add, over the same constant-covariance low-rank model:
- +0.02092 bit/target
- +0.06346 bit/target
- +0.08521 bit/target
- +0.05637 bit/target.

Fixed heldout-source / realization-bootstrap 95% intervals for these paired gains:
- [0.01501, 0.02701]
- [0.05856, 0.06825]
- [0.06786, 0.10285]
- [0.04980, 0.06334].

Thus the source-conditioned covariance structure is predictive on source classes excluded from training.

## 6. Negative controls already passed

Source-dependent scalar variance alone degrades proper score relative to the mean model.

A globally shared full covariance / Mahalanobis model also does not explain the signal.

Therefore the positive result is specifically associated with correlated low-rank turbulence modes whose amplitudes vary with source.

## 7. Far-domain mother theory

Relevant 2025/2026 theory families:
- probabilistic neural operators for function-space uncertainty;
- stochastic operator networks for noisy/stochastic operators;
- stochastic closure modeling via conditional diffusion + neural operators;
- neural operators for SPDE solution distributions.

Key recent anchors include:
- Buelte, Scholl, Kutyniok, TMLR 2025, Probabilistic Neural Operators for Functional Uncertainty Quantification;
- Dong, Chen, Wu, Journal of Computational Physics 2025, Data-driven Stochastic Closure Modeling via Conditional Diffusion Model and Neural Operator;
- Bausback et al., Journal of Machine Learning 2026, Stochastic Operator Network;
- Berner et al., Nature Machine Intelligence 2026, Principled Approaches for Extending Neural Architectures to Function Spaces for Operator Learning.

## 8. GSL prior-art boundary

Neural operators are no longer novel in GSL: a 2026 IROS work is titled A physics-informed neural operator for gas source localization in turbulent environments.

Probabilistic GSL is also occupied: arXiv:2608.16221 uses physical-dependency-guided sequential probabilistic inference and predicts heteroscedastic diagonal-Gaussian fields.

That 2026 probabilistic GSL work explicitly treats diagonal Gaussian uncertainty as a simplification and discards spatial correlation structure.

Therefore the candidate novelty is NOT neural operator or probabilistic GSL.

The candidate novelty is:
source-conditioned correlated stochastic response operators whose covariance structure itself contributes to source localization.

## 9. Deployment principle

Repeated source releases are an offline training mechanism, not an online requirement.

At flight time, one observation is scored against operator-predicted distributions for all PMFS candidate sources.

A valid final method must transfer the operator across source positions and eventually across wind/geometry with limited calibration, rather than rebuild a full source-wise bank in every real environment.

## 10. Current status

D0 = positive mechanism signal only.
No new GADEN runs are authorized.
D1 must use existing D1R and test a predeclared stochastic-operator parameterization against the linear low-rank covariance lower bound and strong diagonal/global-covariance baselines.