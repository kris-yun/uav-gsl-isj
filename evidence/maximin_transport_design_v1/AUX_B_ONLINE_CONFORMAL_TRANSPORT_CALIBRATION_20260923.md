# Auxiliary B — Online Conformal Transport Calibration (OCTC)

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Status: KEEP AS AUXILIARY CANDIDATE; needs interface and empirical falsification

## 1. The exact problem this module solves

M1 defines a transport adversary. A probabilistic wind mapper such as GMRF-W provides a nominal posterior geometry,

\[
W(x)\sim\mathcal N(\hat w(x),\Sigma_w(x)).
\]

But posterior covariance is not automatically calibrated under:
- a new House;
- CFD-to-real shift;
- imperfect physical hyperparameters;
- sensor/model mismatch;
- an external dependency/version mismatch.

If the covariance is too small, M1 is falsely robust.
If it is too large, M1 becomes unnecessarily conservative.

Therefore the second auxiliary module should solve one narrow problem:

**calibrate the scale of transport uncertainty online using only source-blind wind innovations observed during the robot's own trajectory.**

No source coordinate or source-rank feedback is permitted.

Working name: Online Conformal Transport Calibration (OCTC).

## 2. Remote parent ideas

### ICML 2025 — Online Conformal Prediction via Online Optimization

Areces, Mohri, Hashimoto, Duchi, ICML 2025.

They formulate online conformal calibration through online optimization.

Relevant property:
- in adversarial/sequential settings, the method controls long-run coverage / miscoverage without requiring an exchangeable held-out calibration set;
- in stochastic settings they derive stronger conditional calibration behavior.

This makes it better matched to a moving robot than ordinary split conformal calibration.

PMLR:
https://proceedings.mlr.press/v267/areces25a.html

### ICLR 2026 — Online Conformal Prediction with Adversarial Semi-bandit Feedback

Yang, Kim, Park, ICLR 2026.

This work extends online conformal prediction to partial/adaptive feedback.

It is not necessary for the first OCTC implementation because the robot normally receives a local wind observation at every visited sensing location, but it is an important boundary if wind ground truth becomes intermittent.

### Robotics boundary

Recent robotics papers already use online/adaptive conformal inference for safe navigation, imitation learning and dynamics uncertainty.

Therefore we cannot claim:
- first online conformal uncertainty in robotics;
- first conformal calibration for dynamics;
- first conformal uncertainty under robot distribution shift.

The domain contribution, if useful, is specifically to **calibrate plume-transport ambiguity used for robust gas-source identification.**

## 3. Why not use Inverse Conformal Risk Control directly

ICML 2026 Inverse Conformal Risk Control (ICRC) is closely related conceptually: it calibrates robustness levels by estimating miscoverage/regret tradeoffs.

However its basic framework assumes an exchangeable calibration dataset of paired examples.

At our present data scale, using House/seed runs as a calibration set would be weak and could leak evaluation environments.

Therefore ICRC is a literature boundary / future extension, not the first implementation.

## 4. Predict-then-observe wind interface

At time t, before incorporating the new wind sensor measurement:

1. robot has chosen location x_t from past history;
2. wind posterior provider returns
   \[
   \hat w_t=\hat w(x_t),\qquad \Sigma_{w,t};
   \]
3. robot then observes local wind
   \[
   w_t^{obs}.
   \]

Critical anti-leak rule:

**the uncertainty score must use the PRE-UPDATE posterior.**

Do not first assimilate w_t^{obs} into GMRF and then evaluate the same observation.

## 5. Nonconformity score

For 2D wind, use a Mahalanobis innovation score

\[
\boxed{
R_t
=
(w_t^{obs}-\hat w_t)^T
\Sigma_{pred,t}^{-1}
(w_t^{obs}-\hat w_t).
}
\]

If sensor-noise covariance R_sensor is known,

\[
\Sigma_{pred,t}
=
\Sigma_{w,t}+R_{sensor}.
\]

If sensor noise is negligible in the simulator, this reduces to the wind-posterior covariance.

Use a small numerical floor only for matrix conditioning; predeclare it.

## 6. Online conformal scale

Let q_t be an online conformal threshold targeting wind-prediction miscoverage beta_w.

The prediction ellipsoid at the next step is

\[
\mathcal E_t
=
\left\{
w:
(w-\hat w_t)^T
\Sigma_{pred,t}^{-1}
(w-\hat w_t)
\le q_t
\right\}.
\]

The online conformal algorithm updates q_t after seeing R_t.

In the adversarial setting, interpret the guarantee correctly:

**it is a long-run coverage / miscoverage guarantee along the realized online sequence, not automatic pointwise conditional coverage at every unvisited map cell.**

Do not overclaim spatial field coverage.

## 7. Convert conformal scale into the M1 KL ambiguity radius

For a Gaussian wind posterior with unchanged covariance,

\[
P=\mathcal N(\hat w,\Sigma),\qquad
Q_\delta=\mathcal N(\hat w+\delta w,\Sigma),
\]

the mean-shift KL is

\[
D_{KL}(Q_\delta\|P)
=
\frac12\delta w^T\Sigma^{-1}\delta w.
\]

Therefore an ellipsoid

\[
\delta w^T\Sigma^{-1}\delta w\le q_t
\]

corresponds exactly to

\[
\boxed{\rho_t=q_t/2}.
\]

This is the key bridge.

The robustness radius is no longer selected by source-truth performance.

It is determined by the observed calibration state of the wind model.

## 8. Covariance-inflation version

When sensor noise is non-negligible or only a scalar global correction is desired, use q_t to compute a covariance inflation factor instead of directly setting rho.

For a nominal reference quantile q_ref, for example a predeclared chi-square reference,

\[
\kappa_t=\frac{q_t}{q_{ref}}.
\]

Then define

\[
\widetilde\Sigma_{w,t}
=
\kappa_t\Sigma_{w,t}.
\]

M1 uses the calibrated covariance in its first-order uncertainty term:

\[
J(x)
\approx
I(x)
-
\sqrt{2\rho_0}
\sqrt{
g_x^T\widetilde\Sigma_W g_x
}.
\]

This version cleanly separates:
- posterior geometry from GMRF;
- online scale calibration from OCTC;
- decision robustness from M1.

Do not simultaneously tune kappa and rho using source performance.

## 9. Why this is more than a generic confidence interval

The intended chain is:

\[
\boxed{
\text{pre-update wind posterior}
\rightarrow
\text{source-blind online innovation}
\rightarrow
\text{conformal uncertainty scale}
\rightarrow
\text{transport KL radius}
\rightarrow
\text{robust source-information decision}.
}
\]

The calibrated object is the uncertainty set that drives an active inverse problem, not the source location itself.

## 10. Spatial limitation

OCTC observes calibration errors only at robot-visited locations.

Therefore it cannot, by itself, prove calibrated coverage for every unvisited wind-map cell.

Three conservative deployment choices:

A. use q_t only as a global scalar inflation of the physics-shaped covariance field;

B. maintain coarse spatial/Mondrian calibration bins only if enough residuals are available;

C. keep the formal claim limited to trajectory-level calibration and evaluate off-trajectory generalization empirically.

Start with A.

Do not introduce a neural spatial calibration model.

## 11. Connection to GMRF-W

Current MAPIRlab GMRF-W already supplies:
- mean u,v;
- var_u;
- var_v;
- cov_uv.

Therefore OCTC needs no change to the wind estimator's scientific core.

At each visited cell:
- query pre-update mean/covariance;
- observe wind;
- calculate R_t;
- update q_t / kappa_t;
- then assimilate the wind observation.

This is a thin uncertainty-calibration layer.

GMRF-W is not itself an innovation claim.

## 12. Hard falsification plan

### B0 — calibration sanity

Use independent wind traces only; no gas/source data.

Compare nominal GMRF ellipsoids vs OCTC-scaled ellipsoids.

Report:
- realized wind miscoverage over time;
- target beta_w;
- ellipsoid area / inflation factor;
- adaptation after an induced wind-model shift.

Required signal:
OCTC should move empirical long-run miscoverage toward the target without exploding uncertainty.

### B1 — controlled covariance miscalibration

Artificially scale the wind provider's covariance by fixed hidden factors, for example under- and over-confidence.

OCTC must recover an appropriate compensating scale from wind innovations.

No source information may enter the update.

### B2 — source-localization utility

Only after B0/B1 pass:

compare M1 with
- raw posterior covariance;
- fixed hand-set inflation;
- OCTC-calibrated covariance.

Hard source endpoint:
truth-containing source-candidate rank.

Secondary:
path length / endpoint / declaration time.

If OCTC improves wind coverage but produces no repeatable source-rank benefit or robustness benefit, keep it as diagnostics or kill it as a paper module.

### B3 — environment shift

Freeze all hyperparameters.

Move from one plume/wind environment to another.

Expected signature:
- q_t / kappa_t rises when wind model becomes under-calibrated;
- falls/stabilizes when predictions become reliable;
- M1 avoids the false-certainty failure that raw covariance exhibits.

## 13. Novelty collisions

Do not claim conformal prediction itself is novel for source localization.

Known adjacent work includes:

- AAAI 2026 conformal prediction for multi-source detection on diffusion networks;
- ICASSP 2025 conformal acoustic-source localization;
- 2025/2026 conformal uncertainty in robotics and dynamical systems;
- conformal wind / renewable-flow forecasting work.

OCTC survives only as a supporting GSL-specific bridge from **online wind-model calibration to transport-robust active source identification**.

## 14. Kill conditions

Kill Auxiliary B if:
- pre-update wind covariance is unavailable in the actual runtime;
- wind observations are too sparse/noisy to calibrate;
- q_t is unstable over the 300 s search;
- long-run coverage improves but source localization is unchanged;
- the only good result requires House-specific beta_w or learning rate;
- calibration requires source truth;
- it materially duplicates M1 without adding a measurable capability.

## 15. Current verdict

KEEP as Auxiliary B, below M1 and Auxiliary A in priority until repaired Native data arrive.

Preferred three-module architecture if all survive:

M1:
**adversarial transport identifiability / distributionally robust active source search**

Aux A:
**anytime-valid transport-robust source confidence set / declaration**

Aux B:
**online conformal calibration of transport uncertainty**

This is scientifically coherent because each module solves a different question:

- M1: WHERE should the robot measure under model uncertainty?
- Aux A: WHEN is there enough evidence to declare a source?
- Aux B: HOW LARGE should the transport uncertainty set be online?

None of the three requires source-truth tuning.
