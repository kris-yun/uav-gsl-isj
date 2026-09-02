# Codex directive — repair `ba0de54` before generating M2 CAL

Base for comparison: `ba0de54311b762a22ba43a712b4f60a37b08ff5e`.

Read first:

1. `docs/CTPI_M2_BA0DE54_CODE_AUDIT_20260902.md`
2. `docs/CTPI_M2_BA0DE54_AUDIT_BLOCKERS_20260902.json`

Do not generate CAL or CONFIRM until all P0 blockers are closed in committed code and the terminal marker is `CTPI_M2_BA0DE54_PREGEN_AUDIT=PASS`.

## Required repair order

### 1. Preserve M1 cadence exactly

Historical/frozen M1 has 15 completed stops and 5 source updates, each update after three completed stops. Do not silently recompute M1 after every stop.

Freeze the pre-event posterior schedule used by M2. Preferred parity-preserving schedule:

- before stops 1,2,3: initial frozen M1 prior;
- before stops 4,5,6: frozen M1 posterior after stop 3;
- before stops 7,8,9: frozen M1 posterior after stop 6;
- before stops 10,11,12: frozen M1 posterior after stop 9;
- before stops 13,14,15: frozen M1 posterior after stop 12.

Add a selftest for this exact schedule. Any alternative requires an explicit M1 parity audit before data generation.

### 2. Replace the rectangular cross-House interface

Do not pad H01/H02/H03 into one undocumented source dimension. Frozen carrier counts are H01=210, H02=201, H03=206.

Implement one of:

- per-House/ragged batch objects and pool only calibration sufficient statistics plus event/tape losses; preferred;
- or an explicit valid-source mask frozen in the contract.

The fit must pool `W_k/A_k` across House batches without assuming equal source counts. Confirmatory evaluation must compute each House with its own source dimension and then pool event/tape losses.

Add a selftest with deliberately unequal source counts.

### 3. Add explicit action metadata

Every forecast row must carry at least:

- `house`;
- `tape_id`;
- `stop_index` / decision index;
- action cell or `(x,y)`;
- forecast time;
- M1 source-update ID whose posterior is being used.

Remove the current claim that `axis=0` row variation proves action variation. A row can differ because of history/time alone.

The M2 confirmatory Gate may require nonconstant forecasts, but true counterfactual action discrimination belongs to the later M3 offline Gate.

### 4. Make frozen M1 posterior input fail closed

Do not silently renormalize arbitrary M1 posterior rows. Verify finite/nonnegative mass and `abs(sum-1)<=frozen_tolerance`; reject otherwise. Return/copy the frozen values without semantic repair.

### 5. Replace hand-written RNG proof with an asset-derived inventory

Create a tool that scans authoritative prior manifests/evidence and emits a canonical legacy RNG inventory containing every resolvable numeric seed and RNG domain used by:

- frozen predictive members;
- historical observation worlds/tapes;
- default/fallback generator seeds;
- prospective transport gates where relevant.

Hash the inventory. `ctpi_m2_make_provenance.py` must consume this inventory and fail if it is absent. New seeds must be checked against the inventory, not only a hard-coded list.

If some historical world does not expose a numeric seed, record its immutable world/hash identity and state explicitly that numeric disjointness cannot be proved for that asset; do not convert an unknown into `true`.

### 6. Freeze generator runtime, not only binary/source

Prior evidence showed the same native generator depends on OpenMP configuration. Restore at least:

- `OMP_NUM_THREADS=4`;
- `OMP_DYNAMIC=FALSE`;
- `OPENBLAS_NUM_THREADS=1`;
- `MKL_NUM_THREADS=1`;
- `NUMEXPR_NUM_THREADS=1`;
- `PYTHONHASHSEED=0`;
- exact ROS/GADEN overlay order;
- hashes for the RNG hook, MathUtils, RunningSimulation, and relevant loaded GADEN libraries/sources.

The generation runner must preflight these before every batch and record them in each world manifest.

### 7. Commit the tape materializer before CAL generation

The materializer must enforce:

- bank root read-only/no writes;
- fresh output root;
- one tape identity per independent native-generator invocation;
- exact source, House, route, seed/domain, binary/runtime hashes;
- 1500 physical samples;
- causal FOPDT forward state over the complete route, including motion samples;
- 1502 forward samples including the two-sample tail;
- exactly 15 completed stop events from the first 1500 aligned sensor samples;
- strictly `>0.1 ppm` event threshold;
- output SHA-256 for every tape;
- terminal per-tape PASS/FAIL status.

Do one disposable smoke world first. Do not count it as CAL or CONFIRM unless its identity was preregistered before execution.

### 8. Fix selftests

The current synthetic confirmatory test constructs the pre-event posterior directly from future `y`. Replace it with a fixture whose posterior/history/action are fixed before the generated outcome.

Add negative tests for:

- posterior mass drift;
- unequal House source dimensions;
- wrong M1 source-update ID for a stop;
- duplicate action/stop identity;
- future-index mismatch;
- missing runtime provenance;
- RNG inventory collision;
- padding or invalid-source contamination.

## Scientific boundary for the current isotonic M2

Do not rename the nine-value isotonic reliability table into a new physical theory. Treat it as a candidate calibration implementation inside the broader action-conditioned predictive-law module.

The current one-shot Gate scores posterior-mixture forecasts. This is necessary but not sufficient to certify the source-conditioned forecast contrasts that M3 uses. Before M3 authorization, add a separately frozen source-conditioned predictive validation or explicitly narrow the claim and stop before M3.

Do not use localization error, true-source rank, planner reward, or CONFIRM outcomes to choose a new formula after generation.

## Required deliverables before generation

Commit:

1. corrected ragged/per-House forecast core;
2. corrected selftests;
3. M1 pre-event cadence manifest/test;
4. authoritative legacy RNG inventory + hash;
5. generator runtime environment manifest + hashes;
6. fail-closed tape materializer + dry-run selftest;
7. updated freeze addendum reflecting these repairs;
8. `PREGEN_AUDIT_REPORT.json` with every P0 item PASS.

Only then emit:

`CTPI_M2_BA0DE54_PREGEN_AUDIT=PASS`

Before that marker, CAL/CONFIRM generation remains forbidden.
