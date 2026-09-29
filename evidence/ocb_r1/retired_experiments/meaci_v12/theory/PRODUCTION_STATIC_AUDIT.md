# V12-M production static audit

Date: 2026-08-25

## Verdict

**PRODUCTION BUILD AND STATIC FORMULA WIRING PASS; RESPONSE BANKS AND LAUNCHER
ARE NOT FROZEN; HOUSE EXECUTION REMAINS FORBIDDEN.**

No House launch, ROS action, GADEN process, source truth, final error or V11
event replay was used in this audit.

## Isolated build

- Source root: `/tmp/meaci_v12_buildcheck_20260825/src/gsl_server`
- Install root: `/tmp/meaci_v12_buildcheck_20260825/install_compile1`
- Build result: `1 package finished`
- Binary: `gsl_actionserver_node`
- Pre-freeze binary SHA-256:
  `ebd199a29e014310367cd4e3852127501e1c44b0edcdfdb423a3ceb1eedcc01a`
- Active `/home/zyc/ros2_ws/install/gsl_server` was not modified.

With the isolated message/GADEN/VGR overlays sourced and
`/home/zyc/ros2_ws/install/gmrf_msgs/lib` explicitly appended to
`LD_LIBRARY_PATH`, `ldd` reports `LDD_ALL_RESOLVED`. The explicit gmrf library
path is therefore a mandatory launcher shield, not an optional environment
repair.

## Frozen-V11 source-diff boundary

Compared with the frozen V11 source at
`/dev/shm/meaci_v11_luna_handoff_20260825/frozen_runtime/meaci_v11_rc_20260825/source`,
only these production files differ:

1. new `RCSDTFEIV12.hpp`;
2. new `V12ResponseBank.hpp`;
3. mode-specific additions in `Simulations.hpp`;
4. mode whitelist, event capture, fixed-carrier dispatch and
   `applyRCSDTFEIV12Main()` in `Simulations.cpp`.

The diff has no modification to the native PMFS scoring equations, movement
controller, navigation code or official metric. OFF qualification will use the
separately frozen native baseline binary rather than treating a V12-disabled
build as a new baseline.

## Formula-to-production checks

- V12-M member counts are emitted from `kTransportMembers=8` and
  `kMainModelErrorMembers=1`; metadata cannot claim 8 x 8.
- The fixed `2 x 2` carriers cover every free cell exactly once. Adaptive native
  quadtree nodes cannot enter the V12 hypothesis ledger.
- `transportEventKey()` exposes only method seed, transport member and
  substream; the legacy update slot is pinned to zero.
- One rate group is constructed for each new immutable likelihood increment,
  not for every StopAndMeasure block.
- Fold A and fold B increments are accumulated in separate trajectory ledgers;
  the 1/2 mixture is performed once after accumulation.
- Every update writes a truth-free immutable event ledger before inference and
  writes candidate fold scores and the eigen spectrum after a valid commit.
- Posterior and cumulative ledgers are committed only after finite-likelihood,
  replay and unit-mass checks pass.
- V12 never reads the native PMFS posterior as its causal prior and never reads
  a source-truth field.

## Response-bank checks

`V12ResponseBank.hpp` performs atomic creation and refuses overwrite. Runtime
validation compares the complete map dimensions, occupancy bytes, cell
geometry, ordered carrier IDs/coordinates/free counts, simulator recording
settings, method seed, transport substream and transport-member count. Missing
or mismatched banks fail before posterior mutation.

The runtime deliberately does not implement its own cryptographic library.
The frozen absolute-path launcher must verify the bank with `sha256sum -c`
before starting the binary. A House-specific bank has not yet been created, so
no ON arm is currently permitted.

## Test evidence

- Deterministic Python reference: 10/10 PASS.
- C++ formula/core/RNG/bank contract: 14/14 PASS.
- AddressSanitizer + UndefinedBehaviorSanitizer: 14/14 PASS, no finding.
- Complete isolated production build: PASS.

The only optimized-compile warnings originate inside Eigen 3.4 templates
(`maybe-uninitialized`); no V12 source warning or sanitizer finding occurred.
