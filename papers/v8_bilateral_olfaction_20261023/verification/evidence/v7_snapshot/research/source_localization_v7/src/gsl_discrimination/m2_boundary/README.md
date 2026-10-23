# M2: relative return memory and source-response contrast formations

This module changes the **next observation geometry**. It does not update a
source posterior, allocate hypothesis clusters, or count a memory as evidence.
All numerical scales must be supplied for the target sensor and platform.

## Provenance and modifications

The event memory comes from Siliciano et al., *A vector-based strategy for
olfactory navigation in Drosophila*, Nature (2026),
https://doi.org/10.1038/s41586-026-10827-7. Author code examined:
https://github.com/rutalaboratory/Edge-Tracking-Model/blob/225dc7ddbebb30d5f092f7144db02216fd1271b6/state_space_model/simulation_agent.py.

For an entry (or qualified exit), the original update is

\[
m^{in}\leftarrow a_{in}m^{in}+b_{in}\hat v,
\qquad m^{out}\leftarrow a_{out}m^{out}+b_{out}\hat v.
\]

The coefficients are not silently replaced by an exponential average with
`b = 1-a`. The original model stores a **directional goal**, not coordinates of
the previous boundary. Our return tube is anchored to the current observed
position. Translation of an entire trajectory translates the tube.

The `entry_only` mode is an explicit no-wind adaptation. The `wind_gated` mode
initializes an upwind exit bias and gates exit updates by their angle to measured
upwind. `LocalWind.velocity_xy` means air velocity pointing **downwind**, so its
negative defines upwind. A valid current measurement is required at wind-biased
initialization and at every exit update. This implementation does not reproduce
the paper's negative-binomial state durations or noisy autoregressive velocity
controller. Its uncertainty estimates, response-gradient planning, and escape
rule are engineering additions.

## Causal memory contract

`CausalBoundaryMemory.update` accepts `timestamp_s`, `position_xy`, `heading_rad`,
an optional `BoundaryEvent`, and optional timestamped `LocalWind`. Times are
real seconds; positions, speed bounds, tube radii, and geometry must share one
declared distance unit. `heading_rad` is the odometric **travel** heading of the
segment ending at the observation, not aircraft yaw.

The upstream detector must first confirm the event from uninterrupted odor
occupancy and align its crossing timestamp to the sample time using calibrated
sensor/pipe latency. The module checks the pre/post durations, available motion
window, event ordering, and absence of future observations. The crossing direction
averages observed velocities in a qualified window ending after the minimum
post-event confirmation interval. Delayed receipt does not rejuvenate the physical
event: memory age uses the aligned direction-window time, separately from its
confirmation timestamp. A stationary filament passing the sensor cannot establish
a motion direction here.

Unknown timing qualification, repeated/reversed clocks, excessive observation
gaps, future/stale wind, missing required wind, motion-bound violations, or
unconfirmed events raise `ValueError` without partially changing the memory.
After a long gap, call `reset()` and establish new qualified events. Interpolating
50-second snapshots into millisecond steps does not satisfy this contract.

`make_return_tube` requires a recent entry and current position consistent with
the observed motion bound. It propagates an engineering direction covariance
through normalization and defines a finite tube around the relative ray. With
normal `n`, forward distance `s`, and physical event age `age`,

\[
R(s)=r_0+k\sqrt{n^T[P_x+Q\,age+(v_{max}\sigma_{delay})^2I+s^2P_u]n}.
\]

`k` is a conservatism setting, not a claimed probability quantile. The covariance
includes calibrated direction noise, within-window direction scatter, and
between-entry disagreement. This bookkeeping was not inferred in the Nature
experiment and is not a source likelihood.

## Static paired-response operator

For center `q`, separation `d`, and unit baseline direction `u`, the endpoints are
`q + d*u/2` and `q - d*u/2`. The observed even and odd channels are

\[
E=(c_++c_-)/2,\quad O=(c_+-c_-)/2.
\]

Given source-ensemble mean `mu_j(q)` and its response gradient `g_j(q)`, a local
linear proposal model is

\[
\bar z_j=(\mu_j(q),(d/2)u^Tg_j(q)),\quad
D_{jk}=(\bar z_j-\bar z_k)^T
(\Sigma_j+\Sigma_k+\lambda I)^{-1}(\bar z_j-\bar z_k).
\]

`E` preserves amplitude information. `D` uses a full joint even/odd covariance
once, so correlated derived features are not multiplied as independent evidence.
It is a planning distance, **not a probability or sequential test statistic**.
The first-order approximation ignores curvature in the even channel; the caller
must supply a local validity radius. For longer baselines, exact predicted endpoint
responses are needed instead. A seven-meter pair is not automatically a small
baseline or a motion-qualified fly-style measurement.

The static interface is:

```python
score_paired_formations(
    center_xy=...,             # [N, 2]
    source_means=...,          # [N, S]
    source_gradients=...,      # [N, S, 2]
    joint_covariance=...,     # [N, S, 2, 2] or [N,D,U,S,2,2]
    costs=...,                # positive scalar, [N], or [N,D,U]
    separations=...,          # D values, declared distance units
    orientations_rad=...,    # U angles
    geometry=FormationGeometry(...),
    return_tube=None,         # or a causally created ReturnTube
    ridge_variance=0.0,
    contrast_threshold=...,
)
```

The covariance may depend on separation/orientation. Broadcasting `[N,S,2,2]`
asserts a fixed calibrated model for those actions; it does not estimate it from
the test world. Zero/singular variance is rejected unless the caller explicitly
supplies a positive regularizer. Regularization does not establish calibration.

`FormationGeometry` enforces endpoint bounds, minimum/maximum separation,
local linearization radius, and an optional endpoint legality callback. It does
not silently certify the intervening flight path. Actual travel, settling, sensor
recovery, and synchronized acquisition costs must be supplied by the caller.
For a static query study, use an explicitly declared query cost; no seconds-per-
decision claim follows. Both endpoints count toward the sensor budget.

All means and gradients must come from training worlds or the causally available
prediction model, not from an unobserved held-out field. There is no wind or true
source argument in this operator.

## Output and M3 boundary

`FormationDiagnostics` contains legal `actions`, `pair_indices[P,2]`,
`pair_contrast[A,P]`, `predicted_even_odd[A,S,2]`, separate even/odd deltas, costs,
the center's `in_tube` flag, an eligible action pool, and a status:

- `inside_tube`: an informative paired action exists within the return tube.
- `out_of_tube_retest`: the tube has no informative action and a legal outside
  action separates at least one requested source pair.
- `need_outside_proposals`: only uninformative inside proposals were supplied.
- `no_discriminating_action`: none of the supplied legal proposals separates
  the requested pairs under the prediction model.
- `no_legal_actions`: geometry invalidates every proposed pair.
- `static_unconstrained`: informative static pairs were evaluated without a tube.

By default the gate asks whether **any** source pair is separable. M3 can provide
`gate_pair_indices` for a particular challenge; the full matrix is always
returned. M2 does not choose clusters or eliminate hypotheses. `rank_by_maxmin`
is only a transparent reference ranking for tests, using minimum pair distance
per supplied cost. It can tie at zero when actions separate different subsets;
such a tie is not proof that all actions are useless.

## Verification

Run only this module's targeted tests with:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_m2_boundary.py -v
```

The 21 tests cover response-gradient rotation, equal-amplitude discrimination,
amplitude retention, full joint covariance, all-pair output, geometry gates,
causal clocks/events/wind, latency aging, non-teleporting relative tube origins,
source-independent memory, and explicit outside-tube retesting. These are
synthetic operator/causality checks, not validation on continuous gas filaments.
The OCB X00 50-second snapshots qualify only the static sensing branch.
