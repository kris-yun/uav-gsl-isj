# SAFE-F0 result — composite Bernoulli e-process

Date: 2026-09-23

Execution used `probe_safe_eprocess_f0.py` with deterministic seed 20260923.

```text
SAFE-F0: PASS
max_null_expected_factor=1.000000000000
violations=0
max_KL_identity_error=0.000e+00
max_zero_growth_inside_null=0.000e+00
adaptive_crossing_rate_alpha0.05=0.004335
final_mean_eprocess=2.026119e-06
```

Interpretation:

- the composite-null one-step e-factor satisfied the required conditional expectation bound over the dense numerical grid;
- expected log e-growth exactly matched Bernoulli KL to the clipped composite null;
- when the alternative prediction lay inside the null interval, safe evidence growth was exactly zero;
- a deliberately adaptive predictable alternative, chosen from past observations, retained conservative time-uniform crossing behavior in Monte Carlo.

The 0.4335% crossing rate is **not** a performance claim. It shows that this particular interval/alternative setup is conservative relative to the nominal 5% bound. Power / candidate-set contraction is the next bottleneck.

Status: `SAFE-F0 PASS; POWER NOT TESTED`.
