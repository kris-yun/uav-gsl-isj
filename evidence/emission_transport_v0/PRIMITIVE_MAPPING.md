# Mapping from fixed code to implemented primitive

Evidence source: `fixed_source/src/GADEN/`; build manifest/source diff in
`source_inventory.txt`; simulator/library hashes in `NUMERICAL_CONTRACT.json`.
This mapping is to the retrieved fixed build source. The ports have limited
deterministic checks; no end-to-end numerical parity or distribution accuracy
certificate is claimed.

| Primitive | Fixed code | Implementation | Status / assumption |
|---|---|---|---|
| Point injection | PointSource.hpp `Emit` | supplied source xyz | deterministic, six-source/E2 assets not used |
| Release count | RunningSimulation.cpp `AddFilaments` | `schedule` | float32 accumulator, fixed count, no Poisson |
| Save clock | `AdvanceTimestep`, lastSaveTime=-FLT_MAX | `schedule` + C++ | 566 saves, exact selected-clock parity |
| Wind clock | `AdvanceTimestep`, WindSequence::AdvanceTimeStep | `schedule` | save before wind advance, loop1..10 |
| Legacy wind indexing | WindSequence::parseOldFile, MathUtils::indexFrom3D | `read_legacy_wind` | raw doubles -> float32, x fastest |
| Cell conversion | Environment::coordsToIndices | `Environment.indices` | glm truncation, not floor |
| Advection | MoveSingleFilament | `single_step` | conditional given input wind/clock, not a stochastic kernel |
| Noise | thread_local PrecalculatedGaussian<1000> | `CyclicTable` | **shared population clock; no independent closure** |
| Buoyancy | MoveSingleFilament, gas_type10 | `single_step` | equation port, full float-expression bit parity not proven |
| Growth | sigma+=gamma/(2*sigma)*dt | `grow_sigma` | float32 3000-step parity to standalone C++ |
| Wall/OOB | recursive StepTowards | `Environment.slide` | hand-entered wall check, explicit recursion-limit stop |
| Outlet | isActive=false then survivor compaction | single-step active flag | absorption, population clock coupling remains unresolved |
| Concentration | Simulation.cpp CalculateConcentration | `filament_mark` | strict3sigma, LOS, width-dependent center, algebraic constants cancellation not bit parity |
| Observation | official extractor native centers, then pooling | `pooled_probe_points` | all four samples retained, no center substitute |
| Full population sum | ordered float32 concentration sum | not instantiated | rounding/quantization bound missing, no added noise |
| Probability kernel | not supplied by simulator API | closure guard | refuses unsupported independent composition |
| Source likelihood and posterior | upstream finite-state solver | retained but not connected | no bank results manufactured |

## Reproducible closure witness

`PRIMITIVE_CHECKS.json` uses a supplied deterministic sentinel table to check
the original indexing operation. After one prior tick, one surviving packet
uses next entries4,5,6; two surviving packets use7,8,9. The sentinel values are
not simulated Gaussian draws and do not quantify GSL performance. They show
that the packet's next increment cannot be assigned from its isolated state.

The original C++ class independently confirms `draw[k] == draw[k+1000]`.
Under an ideal random table prior, using the same table entry twice makes
`Var(G+G)=4 Var(G)`; replacing it by independent entries makes `2 Var(G)`.
The algebra explains why averaging a shared clock separately per release is
not the same joint law. No Gaussian prior approximation is used for scoring.

## Remaining numerical-contract gaps

1. Exogenous common-context conditioning that closes all packet paths, or
   an explicit coupled solver/error-controlled approximation.
2. Law of the seed/table/thread process and legal per-source comparator at
   the same precision; recorded generation provenance does not include RNG
   states or a full OpenMP call trace. The runner deletes raw filament states.
3. Deterministic concentration-bin width and total error bound including
   dynamics, state discretization, ordered float32 summation and pooling.
4. Boundary probability mass and likelihood/posterior-odds precision.

None can be replaced by estimating candidate variances from the assessment
bank. No Monte Carlo or new plume was launched to fill the gaps.
