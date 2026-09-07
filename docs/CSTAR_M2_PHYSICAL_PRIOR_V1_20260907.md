# CSTAR M2 physical prior V1

This change adds the first executable causal prior behind the online M2
boundary. It is a deterministic finite-volume advection--diffusion model with
no-flux free-cell faces, explicit native field cadence, and an explicit FOPDT
sensor (`tau`, dead time). For each candidate source hypothesis it produces a
route-conditioned first-encounter law from the *past-only* local wind in the
latest stamped frame. The source location is a hypothesis supplied by the
caller, never simulator truth.

The implementation is `experiments/ctpi_cstar/m2_cpo/physical_prior.py` and the
two CPU checks are:

```text
CSTAR_M2_PHYSICAL_PRIOR_SELFTEST PASS
CSTAR_M2_ONLINE_PHYSICAL_INTEGRATION_SELFTEST PASS
```

These checks establish numerical shape, probability normalization, explicit
solid-cell rejection, and ingress-to-provider prediction-before-observation
wiring. They do **not** establish cross-language parity with the VM C++ core,
calibration on House data, predictive superiority over the current-value or
native-PMFS baselines, or closed-loop utility. Those remain mandatory gates.

The prior intentionally has no learned residual, future wind, future gas,
route outcome, House/member identity, or hidden bank. Its hazard scale and
source rate are manifest parameters; changing them requires a new protocol
manifest rather than rescue tuning.
