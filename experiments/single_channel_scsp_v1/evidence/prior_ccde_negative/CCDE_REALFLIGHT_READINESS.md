# CCDE real-flight readiness (R0/R1/R2/R3 preflight)

Date: 2026-08-07

Status: **NOT READY for real-flight source trials.**

The simulation held-out gate returned
`CCDE_WIND_MOMENT_NOT_PHYSICALLY_SPECIFIC` (with A1 ~= A2), so no real-flight
transfer experiment may claim CCDE main-innovation support. Per
`05_REAL_FLIGHT_TRANSFER/REAL_FLIGHT_TRANSFER_CONTRACT.md`, the following
preconditions are still open:

1. Wind-direction calibration with an independent reference anemometer
   (`realflight_wind_calibration.py wind_calibration.csv`); predeclare and
   freeze `delta_theta_real` before source trials. No gas-source truth may be
   used in calibration.
2. Rotor-wash / stabilization characterization at hover and after motion;
   minimum post-movement stabilization interval; sensor placement away from
   the strongest wash region if platform permits.
3. MOX temperature/humidity logging with every gas sample plus a gas-free
   baseline session across the expected humidity range; humidity is NOT added
   as a CCDE nuisance moment unless a repeatable calibrated response and a
   held-out nuisance-control Gate pass.
4. First real experiment at one fixed sensing altitude; a varying-altitude
   experiment must not be interpreted with the 2D PMFS source model.
5. A2 > A1 (not only A2 > A0), correct wind-nuisance association > shuffled
   association, no degradation in benign wind, and improvement in at least one
   genuinely difficult wind condition without simply widening the posterior.

The strongest transferable component remains the wind-direction perturbation
structure, but its width must be recalibrated from real wind uncertainty; the
fixed +/-15 deg simulation moment is not validated for the field.
