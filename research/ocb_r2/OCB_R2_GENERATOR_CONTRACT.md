# OCB-R2 prospective generator contract

Status: generator qualification only. No 96-run acquisition is authorized.

## Historical boundary

`HISTORICAL_SIMULATOR_RECOVERY_FAIL` remains the historical result. The current
ROS2 writer produces about 1803 records in the frozen 1000 s configuration;
its save and wind-update semantics differ from the unavailable historical
generator. Accordingly `OCB_R1_HISTORICAL_PARITY_UNRECOVERABLE` and
`CURRENT_1803_BINARY_NOT_ELIGIBLE_FOR_OCB_R1_REFERENCE` remain in force.
OCB-R2 does not claim historical same-seed replay. Historical outputs remain
legacy/discovery evidence.

## Frozen prospective physics

Parent source revision `17adaf650a4f11d29aa049cf0661e9f9ea2e636f`, core
submodule revision `9e93c36ae1af74f6a62c42f1c9d7b813153222ed`. The
isolated source/build/install root is `/home/zyc/ocb_r2_seeded_gaden`; the
existing ROS workspace and HCMC installation are untouched. The only source
patch appends the current internal float clock and wind index after each
written record. It does not call RNG, advance simulation state, or change
physics. The frozen current source includes its existing `GADEN_RNG_SEED`
initialization in `MathUtils.hpp`; no RNG engine or distribution was replaced.

Run parameters are frozen in `VALIDATION_CONFIG.json`. The chosen configuration
is original House02 configured source 1, gas type 10, wind `3,5-1_slow`, and
the approved reconstructed wind staging. The staging plan SHA256 is
`102ff41a87b0af5efcb369f5d60a64eb2e4a97aefc312617b7f395dd1eb3990a`.
Its separate asset audit established 176/176 staged-file checks and 44/44
historical wind-state lineage checks; neither establishes stochastic replay.
The current core cannot parse the staged legacy `999` header split-double
`_U/_V/_W` layout. Before the first successful plume run, an isolated,
hash-inventoried storage conversion casts each validated tuple to the core's
native interleaved float vector format with version `(3,0)`. It neither
interpolates nor rescales wind; the original staged files remain untouched.
The current simulator already stores wind vectors as floats. Conversion and
input/output hashes are recorded in `WIND_LAYOUT_CONVERSION_MANIFEST.json`.
Occupancy SHA256 is
`9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`.

The simulator's native timeline is authoritative. No resampling to a nominal
historical record ID or modification to achieve 2000 records is allowed.
`pre_calculate_concentrations=false` is required. The current legacy ROS2
adapter assigns temperature and pressure using `wind_time_step` in its
initialization; this effective behavior is frozen, not silently repaired.

## Master seed and stream ownership

`run_validation_vm.py` accepts only A/B/C from the frozen config and binds the
explicit `master_seed` to `GADEN_RNG_SEED` before process startup. The
existing source derives Gaussian and uniform `mt19937` seeds by folding the
64-bit parsed base into 32 bits and adding respective fixed salts
`0x9e3779b9` and `0x243f6a88`, modulo 2^32. Seeds in this qualification
are 32-bit and distinct. The run wrapper fixes `OMP_NUM_THREADS=1` and
`OMP_DYNAMIC=FALSE` so each thread-local RNG stream has a stable sole owner.
This single-worker setting is part of the prospective generator contract;
multiworker replay is not claimed. No clock, PID, or device entropy is used.

The validation order is A(S1), B(S2), C(S1), where S1=2026900501 and
S2=2026900502. Each run uses a distinct, absent leaf under
`/home/zyc/ocb_r2_validation`. Because the native constructor removes its
`results_location`, the wrapper refuses any pre-existing leaf. It also checks
the occupancy hash, 11 wind files, seed range, and a 700 MB free-space floor.

## Hard decision

All three runs must have identical deterministic parameter maps, timeline,
wind-index sequence, and record count. Every scientific `iteration_*` byte
must match between A and C. At least one scientific output must differ
between A and B, while their deterministic metadata/timeline remains exact.
Any failure is `OCB_R2_GENERATOR_REFOUNDATION_FAIL_STOP` with a specific
determinism or seed-effect substatus. If all checks pass and complete manifests
are present, the result is `OCB_R2_GENERATOR_REFOUNDATION_PASS`. Stop after
qualification; the next 12-configuration smoke matrix requires a separate
decision.
