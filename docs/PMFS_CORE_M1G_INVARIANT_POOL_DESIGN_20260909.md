# CORE-M1G: transport-invariant causal log pooling

Status: **IMPLEMENTATION CANDIDATE; CLOSED-LOOP EVIDENCE PENDING**.

## Failure mechanism

M1F aligns each causal update to one physical sensing stop and passes a new H01
seed, but House123 seed6 fails the joint-success gate.  H02 improves final
error only after accumulating more early error; H03 improves AUC but its last
update jumps to a distant candidate.  M1F averages the three transport-member
likelihoods arithmetically:

```text
L_mix(s) = (1/U) sum_u L_u(s).
```

This is appropriate if `u` is a latent mixture component with calibrated prior
mass.  It is not invariant to a member-specific candidate-common likelihood
scale: replacing every `L_u(s)` by `c_u L_u(s)` changes the posterior because
it changes the effective member weights.  That scale is nuisance here, not a
source-location effect.

## M1G operator

M1G retains M1F's one-stop event window, centered event log odds, sequential
single-use assimilation, and three native transport replicas.  It changes only
the cross-context aggregation to an equal log opinion pool:

```text
ell_G(s) = (1/U) sum_u log L_u(s)
L_G(s)   = exp(ell_G(s))
pi_t(s) proportional to pi_(t-1)(s) L_G(s).
```

For arbitrary positive member scales `c_u`,

```text
L'_G(s) = exp((1/U) sum_u log(c_u L_u(s)))
        = C L_G(s),
```

where `C` is common to every source candidate and therefore cancels exactly in
posterior normalization.  The geometric pool also cannot exceed the arithmetic
pool, so a candidate supported by only one transport realization cannot obtain
the same mixture boost.  No fitted weight or House-specific threshold is added.

## 2026 theory support and boundary

- Madaleno et al., *Bayesian Hierarchical Invariant Prediction*, CLeaR 2026,
  explicitly tests invariance of causal mechanisms under heterogeneous data in
  a hierarchical Bayesian formulation.  M1G uses the narrower principle that
  the source contrast must survive equal aggregation across transport contexts:
  <https://proceedings.mlr.press/v323/madaleno26a.html>.
- Asiaee, *Certified Interventional Fidelity*, UAI 2026, requires an explicit
  causal estimand and intervention distribution and provides anytime-valid
  evaluation under adaptive sampling.  It supports treating the executed
  sensing-stop distribution and transport-context distribution as part of the
  claim, rather than reporting a favorable point estimate:
  <https://proceedings.mlr.press/v337/asiaee26d.html>.
- Kim et al., UAI 2026, show that internal observable mixing inputs require
  explicit conditioning for causal representation identifiability.  It
  supports keeping wind/transport context inside each member before pooling:
  <https://proceedings.mlr.press/v337/kim26e.html>.

These papers do not derive M1G for gas dispersion.  The scale-cancellation
identity above, source tests, and held-out paired closed loop are the actual
task-specific evidence.

## First gate

After implementation/build tests, run one new algorithm seed on H01 with
sensor/replay seed12, paired A0 versus M1G, 240 s, and V3 joint-success
evaluation.  Expand to H02/H03 only if both final error and full-horizon AUC
improve.  Independent-plume validation remains a later gate requiring new
per-sensor-seed environment certificates.
