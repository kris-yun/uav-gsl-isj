# RCEC V13 build-closure fix — READ FIRST

Branch: `codex/rcec-v13-materialized-20260826`

## Why the first isolated build stopped

The materialized RCEC source inherited a dormant `rc_sd_tfei_v12` implementation from the earlier development checkpoint. That implementation includes:

- `RCSDTFEIV12.hpp`
- `V12ResponseBank.hpp`

Neither file exists in the committed history of `kris-yun/uav-gsl-isj`. Therefore their exact original content cannot be recovered from this repository, and copying arbitrary workstation files would change the frozen source boundary.

RCEC V13 does not use this legacy mode. Its runtime contract remains:

- `pfdi_mode=me_aci`
- `RCEC_V13_ARM=v11_stouffer | crei_latest | rcec_full`

The scientifically clean repair is therefore to **fail-close and compile-isolate the unreproducible V12-M path**, not fabricate its missing dependencies.

## Required action

From this branch, run:

```bash
python3 tools/close_rcec_v13_build_dependency.py
python3 reference/verify_rcec_v13_build_closure.py
python3 reference/verify_rcec_v13_source.py
```

Expected:

```text
RCEC_V13_BUILD_CLOSURE=PASS
RCEC_V13_BUILD_CLOSURE_CONTRACT=PASS
RCEC_V13_SOURCE_CONTRACT=PASS
```

Then run the existing RCEC core unit test and isolated ROS build.

## What the closure patch is allowed to change

Only build exposure of the incomplete legacy V12-M path:

- remove includes of the two uncommitted V12 headers;
- replace the V12-M implementation with an explicit fail-closed stub;
- stop advertising `rc_sd_tfei_v12` as a supported mode.

It must **not** change:

- ACIT 54-member inverse-transport family;
- even/odd causal folds;
- spatial replication gate;
- native-increment CREI definition;
- TMEM definition;
- geometry-only design prior;
- PMFS OFF behavior;
- planner configuration;
- any experimental seed or truth-aware decision.

## After build succeeds

Commit the materialized closure source before viewing any new-seed truth. Record:

- commit SHA;
- `Simulations.cpp` SHA-256;
- `PMFS.cpp` SHA-256;
- final binary SHA-256;
- linked GADEN/ROS provenance.

Then continue exactly with `CODEX_RCEC_V13_EXPERIMENT.md`: OFF parity -> A1 parity -> revealed mechanism regression -> freeze -> genuinely unseen H01/H02/H03 pairs.

Do not resume CTT/HMM/count-survival experiments in this RCEC branch.
