# RCEC V13 build-closure fix — READ FIRST

Branch: `codex/rcec-v13-materialized-20260826`

Read `RCEC_V13_AUDIT_READ_FIRST.md` first. The native-absolute scientific correction must be materialized **before** the build-closure patch.

## Why the first isolated build stopped

The materialized RCEC source inherited a dormant `rc_sd_tfei_v12` implementation from an earlier development checkpoint. That implementation includes:

- `RCSDTFEIV12.hpp`
- `V12ResponseBank.hpp`

Neither file exists in the committed history of `kris-yun/uav-gsl-isj`. Their exact original content cannot be recovered from this repository, and copying arbitrary workstation files would change the frozen source boundary.

RCEC V13 does not use this legacy mode. Its runtime contract remains:

- `pfdi_mode=me_aci`
- `RCEC_V13_ARM=v11_stouffer | crei_latest | rcec_full`

The scientifically clean repair is to fail-close and compile-isolate the unreproducible V12-M path, not fabricate its missing dependencies.

## Required action

From a clean reset of the latest branch, execute in this order:

```bash
python3 tools/fix_rcec_v13_native_absolute.py
python3 tools/close_rcec_v13_build_dependency.py
python3 reference/verify_rcec_v13_build_closure.py
python3 reference/verify_rcec_v13_source.py
```

Expected markers include:

```text
RCEC_V13_NATIVE_ABSOLUTE_PATCH=PASS
RCEC_V13_BUILD_CLOSURE=PASS
RCEC_V13_BUILD_CLOSURE_CONTRACT=PASS
RCEC_V13_SOURCE_CONTRACT=PASS
RCEC_V13_PREVIOUS_INJECTED_STATE_IN_CREI=false
```

Then run the RCEC core test and isolated ROS build.

## What the closure patch may change

Only build exposure of incomplete legacy V12-M:

- remove includes of the two uncommitted V12 headers;
- replace the V12-M implementation with an explicit fail-closed stub;
- stop advertising `rc_sd_tfei_v12` as a supported mode.

It must not change:

- corrected native-absolute CREI;
- ACIT 54-member inverse-transport family;
- even/odd causal folds;
- spatial replication gate;
- TMEM definition/history reset;
- geometry-only design prior;
- PMFS OFF behavior;
- planner configuration;
- any seed or truth-aware decision.

## Transactional behavior

The current closure script locates standalone C++ blocks using lexical brace matching that ignores strings/comments/character literals. It constructs the full result in memory and writes only after all postconditions pass. A failure must leave source files unchanged.

## After build succeeds

Commit the fully materialized v2 + closure source before viewing any new-seed truth. Record:

- commit SHA;
- `Simulations.cpp` SHA-256;
- `Simulations.hpp` SHA-256;
- `PMFS.cpp` SHA-256;
- final binary SHA-256;
- linked GADEN/ROS provenance.

Then continue exactly with `CODEX_RCEC_V13_EXPERIMENT.md`.

Do not resume CTT/HMM/count-survival experiments in this RCEC branch.
