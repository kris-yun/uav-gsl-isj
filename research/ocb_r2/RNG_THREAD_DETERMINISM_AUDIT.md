# OCB-R2 RNG and threading audit

The frozen core source uses two `thread_local` `std::mt19937` engines in
`MathUtils.hpp`: Gaussian and uniform. `PrecalculatedGaussian<1000>` is also
`thread_local` in `RunningSimulation.cpp`. The point-source emitter has no
position RNG. The inspected simulator/core source has no `rand`, `srand`,
`random_device`, clock-seeded engine, or stochastic wind generator. Wind files
are deterministic inputs. Geometric Box/Sphere/Cylinder/Line source classes
consume uniform RNG but are not selected by this point-source configuration.

`MoveFilaments` is an OpenMP loop. With multiple workers, static
thread-local engines do not provide stable per-filament stream assignment
under arbitrary scheduling, even when each engine is seeded identically.
`PrecalculatedGaussian` additionally has a per-worker index. Thus setting
only the master seed is insufficient for a multiworker exact-replay claim.

The prospective generator is explicitly single-worker: the wrapper exports
`OMP_NUM_THREADS=1`, `OMP_DYNAMIC=FALSE`, and `OMP_PROC_BIND=TRUE` before the
new process starts. This fixes RNG consumption order without changing its
engine, distributions, coefficients, emission logic, transport, or solver
order. Qualification does not certify multiworker runs. Any future performance
change to multiple workers requires a new deterministic ownership design and
qualification.

The current source already has an optional `GADEN_RNG_SEED` interface. The
wrapper makes it mandatory, validates its 32-bit range, and logs the value.
It uses the existing separate salts for Gaussian and uniform streams. The
only source patch adds a read-only writer timeline after a record is saved;
it does not request random numbers or mutate simulation variables.
