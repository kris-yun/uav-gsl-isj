# CORE-M1: causal odds-residual evidence for PMFS

Status: **M1S_H01_SEED11_EARLY_SCREEN_PASS; CROSS_HOUSE_VALIDATION_RUNNING**.

## Failure mechanism addressed

Native PMFS repeatedly scores spatially propagated cells as if they were
independent measurements and treats transport-wide probability scale changes
as source-location evidence.  The first CER repair counted each completed
StopAndMeasure block once.  M1R then combined a persistence forecast with a
source/context odds ratio and passed the exposed House123 seed12 development
gate, but its context was `logit(mean_s p_s)`.  That quantity does not cancel a
candidate-common additive log-odds shift exactly.

## Frozen estimand and operator

At completed sensing intervention `A_i = do(X_i=x_i)`, let `Y_i` be the binary
block event and `S=s` a source candidate.  CORE-M1 assumes the local structural
form

```text
logit P(Y_i=1 | do(A_i), S=s, H_i) = b_i(H_i,U_i) + tau_s(A_i).
```

`b_i` collects candidate-common transport intensity, source-rate and sensor
memory nuisance; `tau_s(A_i)` is the relative source-location effect.  Define

```text
delta_i(s) = logit p_i(s) - mean_j logit p_i(j)
q_i(s)     = expit(logit p_persist,i + delta_i(s)).
```

Then `delta_i(s) = tau_s(A_i) - mean_j tau_j(A_i)`: every additive common
nuisance term cancels algebraically.  The M1S posterior uses each executed
sensing block exactly once through the Bernoulli likelihood of `q_i(s)`.  If
`W_t` is the set of completed blocks not previously committed, the update is

```text
pi_t(s) proportional to pi_(t-1)(s)
                         * product_(i in W_t) Bernoulli(Y_i; q_i(s)).
```

After the update, `W_t` is committed permanently.  A past event is therefore
never rescored under a future wind field.  This event-time consistency clause
is essential: the earlier M1C implementation satisfied common-shift
cancellation but failed H01 because it retrospectively reinterpreted all past
events at every source update.

This is a relative causal estimand over the candidate support.  It is not a
claim that the absolute source location is nonparametrically identifiable.

## Identification assumptions

1. Consistency: the logged block outcome is the outcome of the executed sensing
   intervention and is not duplicated by PMFS spatial smoothing.
2. Positivity on the visited support: candidate forecasts are finite and clipped
   away from zero and one.
3. Candidate-common nuisance is additive on the event log-odds scale over one
   source-update window.
4. The native forward model preserves the ordering of relative source effects
   well enough to guide the posterior.
5. The source candidate is represented by the frozen free-space support; truth
   is never read at inference.

## 2026 theory support and boundary

- Moran and Aragam, *Journal of the American Statistical Association* 121(553),
  2026, frames causal representation learning around latent-variable,
  interventional and identifiability questions.  It supports the need to state
  the intervention and equivalence class rather than calling any robust feature
  causal: <https://doi.org/10.1080/01621459.2026.2620154>.
- Markham et al., CLeaR 2026, use interventions across contexts and prove an
  identifiability result for causally disentangled representations.  It supports
  using a separate context mechanism to isolate intervention-responsive factors:
  <https://proceedings.mlr.press/v323/markham26a.html>.
- Asiaee, Aryan and Long, UAI 2026, show that only the intervention-target
  relationships required by the downstream validity claim need be learned, and
  quantify failure when an allegedly unaffected calibration intervention is not
  actually invariant: <https://proceedings.mlr.press/v337/asiaee26b.html>.

None of these papers proves the CORE-M1 equation for gas dispersion.  They
support the design principles; the task-specific proposition above and its
falsification tests carry the actual theoretical burden.

## Preregistered validation ladder

1. Analytic gate: exact common-shift cancellation, null-source zero residual,
   and candidate-permutation equivariance.
2. Runtime gate: implementation/build/startup, one event per completed sensing
   block, no truth access, and unchanged environment/map/wind contracts.
3. Held-out closed loop: freeze the operator before looking at new seeds;
   compare A0 vs M1S on House123 with final error and 0--240 s distance AUC.
4. Big-data claim only after both per-House consistency and aggregate paired
   uncertainty intervals are reported.  A seed12 development PASS alone is not
   enough.

## Current closed-loop evidence

The first held-out-style screen, H01 with algorithm seed 11 and independently
frozen sensor seed 12, passed both preregistered metrics: final error improved
from 6.7251 m to 1.0004 m and distance AUC improved from 1736.2324 m s to
1546.9054 m s.  This is a one-world screen, not yet a cross-House or big-data
claim.  H02/H03 seed11 validation must pass before any seed expansion.
