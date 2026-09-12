# Active user execution target: M1 only

The user explicitly requested a goal and continued execution until real
closed-loop effectiveness. This repository note records that scope; it does
NOT claim to create, resume or replace a Codex product goal.

Product get_goal currently returns an unfinished usageLimited M1/M2 goal.
The attempted create_goal for M1 only was rejected because that goal is
unfinished. No false completion/status change was used to bypass it. Normal
task tools remain usable and execution continued.

## Scientific completion criterion

Only M1 is in current scope. Preserve negative evidence and the causal main
innovation requirement. Finish the source-conditioned observation chain,
verify its assumptions and matched-baseline mechanism benefit, then run the
existing frozen House1/2/3 seed12 closed-loop screen without changing the
controller. Component/synthetic tests and two-source ranking are not success.
Do not tune by House, use evaluator truth as runtime input, lower performance
gates, change seed to find wins, expand multiseed, or resume M2/M3.

If the candidate fails, preserve the result and improve the demonstrated
mechanism deficiency. A single development seed does not prove unseen-dataset
generalization. A genuine guarantee of positive results cannot be made.

## Implementation checkpoint

Added m1_causal/filament_transport.py and its synthetic selftest. One member
has a fixed 3D source, explicit empty t=0 plume, release count accumulator,
mass per filament, physical sigma units, observed wind snapshot, stochastic
velocity noise, buoyancy and Euler growth. Gas/transport parameters are
mandatory, not tuned defaults. Boundary and free-cell callbacks are mandatory;
outlets explicitly remove mass. Invalid wind time/geometry cannot partly
commit the internal state/RNG.

This is a reference integrator, not bitwise GADEN parity or a validated
deployment model. Point release differs from GADEN emission-region sampling.
Empty t=0 is valid only for a matching declared physical start, not an
arbitrary plume replay frame or unknown sensor prehistory.

Passed synthetic tests: fractional release count, mass of surviving particles,
advection, growth, outlet removal, seeded repeatability, prefix replay,
future-wind rejection, and concentration observation integration. Existing
filament-observation and causal-likelihood selftests also pass.

## Next executable dependency

Need audited map/boundary adapter plus actual transport/gas constants and
causal field histories. Current controlled measured_history logs provide local
wind at sensor poses, not a 3D estimated field at every filament. Existing
evaluator exports are single navigation-height wind slices; do not call them
complete 3D deployed wind. Source height must be a candidate/support dimension
or explicitly justified assumption, not read from evaluator truth online.

Compare on a fixed existing route after these inputs are bound. Do not insert
the reference model into ROS or launch expensive closed loops before this
comparison. Correct observation/transport code is necessary infrastructure;
it is not, by itself, the causal contribution beyond standard Bayesian inversion.
