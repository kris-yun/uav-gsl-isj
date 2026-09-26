# Release–transport all-source distribution: development implementation

## One decision

`DEVELOPMENT_IMPLEMENTATION_BLOCKED_PRIMITIVE_CLOSURE`

Scientific decision is **null**. No GADEN likelihood, posterior, NLL/Brier,
source-cluster effect, or matched-accuracy speed advantage was computed.
The original candidate has not received a valid scientific assessment.

This is the stopping boundary in the supplied `CODEX_NEXT_ACTION.txt`: do not
replace a missing primitive with the educational kernel, an invented IID
noise law, bank-fitted variance, Gaussian sensor noise, or a probability floor.
No further experiment is launched by this package.

## Implemented code

- `gaden_primitive.py`: deterministic conditional packet step, explicit cyclic
  table clock, actual float32 release/save/wind schedule, sigma growth,
  buoyancy, wall sliding/outlet handling, concentration cutoff/LOS, four-cell
  probe operator, and correctly indexed legacy wind loader. These are equation
  ports, **not** certified byte-identical substitutes for libgaden.
- `build_clock_cpp.py`: extracts the original `PrecalculatedGaussian` class
  and checks it with deterministic sentinel entries. It does not generate
  GADEN random samples. A standalone C++ float32 schedule independently
  verifies the Python clock.
- `test_gaden_primitive.py`: 51 deterministic checks using only House02 W0
  numerical primitives and hand-entered unit inputs.
- `write_development_record.py`: binds intended assets, writes numerical
  contract before scoring, refuses invalid packet composition, and records
  the single development decision. It does not open concentration values.
- `upstream/code/emission_transport.py`: original finite-state all-source
  backward law solver, release composition, shared-regime mixture, noiseless
  binned likelihood, and posterior; all 17 supplied mathematical tests passed.

## Exact obstruction

The proposed multiplication of single-packet response transforms requires
closed packet dynamics conditional on an exogenous common context. In the
fixed simulator, a thread has a 1000-entry cyclic table and one cursor shared
by all packets assigned to it. Each moving packet consumes three entries.
After outlets remove packets, the survivor vector is compacted. Future
table indices and OpenMP assignments therefore depend on the full evolving
population, which depends on source location and its paths through obstacles
and outlets. Position, age, sigma, wind and a packet's present cursor do not
determine that packet's future noise-clock history.

Shared randomness alone is not an impossibility: the upstream solver already
mixes exogenous common regimes outside the release product. The obstruction
is specifically the **endogenous, population-dependent clock**. Conditioning
on seed/table makes the full population deterministic, but obtaining each
packet's future clock then requires solving the coupled population; it does
not furnish the proposed shared, source-independent single-packet response
field. This report does not rule out a joint-state solver or an approximation
with a proved error bound. Neither exists here with the required likelihood
precision, and no bound has been fabricated.

## Frozen inputs and findings

House02 / `3,5-1_slow`; CENTRAL 168 sources; 16 OPEN realizations/source;
30 separate two-reading protocols, same pooled probe each time; uniform prior.
The bank hash is bound but target values were not read or scored.

The original parameters imply deterministic release at 7 filaments/s via a
float32 accumulator, despite the unused ROS `variable_rate` argument. Noise
uses the compatibility factor `10 × configured_std × dt`, not Brownian
`sqrt(dt)`. Width is updated by Euler growth in centimeters.

Snapshots do not serialize seconds and cubes record only iteration indices.
The exact float32 save-loop reconstruction, matched by C++, gives:

| snapshot | pre-increment simulation clock (s) | completed moves | births total |
|---|---:|---:|---:|
|100|55.0997314453125|552|386|
|550|292.3086242675781|2924|2046|

These are code-derived clock values, not falsely claimed snapshot timestamps.
The queried states include the move made at the stated pre-increment clock.

Each pooled probe is the mean of four native cell-center readings. Replacing
it with a concentration query at the pool center would change the operator.
Legacy wind uses `x+y*nx+z*nx*ny`, different from occupancy text row ordering;
the new loader follows the actual C++ index explicitly.

The wrapper also reads temperature and pressure from `wind_time_step`. That
historical behavior was recorded and preserved, not silently repaired.

## Evidence and reproducibility

`evidence/emission_transport_v0/NUMERICAL_CONTRACT.json` names unresolved
required fields with null values: legal probability kernel, shared-clock law,
quantization/error bounds, boundary mass/odds precision and matched-accuracy
baseline. Status is BLOCKED, so this is not a ready-to-score contract.

`PRIMITIVE_CHECKS.json`, `CPP_CONFORMANCE.json`, `DEVELOPMENT_DECISION.json`,
`COST_REPORT.json`, and `POSTERIOR_OUTPUT_STATUS.json` distinguish executed
checks from missing method results. Cost arithmetic shows that a single
native-grid dense transition matrix would occupy 527,578,137,632 bytes;
this invalidates directly allocating the toy dense implementation, **not**
all possible sparse algorithms. No method speedup is claimed.

The supplied `upstream/` package is restored byte-for-byte and its original
17-entry manifest verifies. This execution's solver-test and toy-demo outputs
are separately preserved as `UPSTREAM_UNIT_TEST_RESULTS.json` and
`UPSTREAM_SYNTHETIC_168_*` under the new evidence directory.

Review ZIP includes the actual 11 W0 wind arrays and occupancy, exact source
excerpts, frozen panel/probe contracts, code and checksums. Large downloaded
source archives are retained locally, excluded from the review ZIP and Git.

No new full plume or primitive random draw, no network, no sealed H01/House03
access, no old STOP-route continuation, no scoring/parameter rescue.
