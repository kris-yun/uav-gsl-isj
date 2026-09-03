# CTPI M3 fast-track VM environment recovery implementation V5

## Scope

This is an environment-only implementation of the autonomy authorized by
`CODEX_CTPI_M3_FASTTRACK_ENV_AUTONOMOUS_RECOVERY_V5_20260903.md`.  It does not
change M1, M2, M3, the runtime integration scientific hunk, cadence, horizon,
banks, or any scientific Gate.

## Reproducible dependency overlay

`closed_loop/ctpi/build_ctpi_vm_dependency_overlay_20260903.sh` rebuilds only
the two incomplete non-scientific ROS interface packages into a fresh isolated
overlay:

- `olfaction_msgs` from `/home/zyc/ros2_ws/src/olfaction_msgs`;
- `gsl_actions` from `/home/zyc/ros2_ws/src/GSL/gsl_actions`.

The script refuses an existing destination, verifies both generated CMake
configs and ROS package prefixes, and records source-tree, package-file,
installed-tree, critical-output, and system-package hashes in
`DEPENDENCY_OVERLAY_MANIFEST.json`.

## Qualified runtime environment

`tools/ctpi_vm_dependency_qualifier.py` now qualifies the rebuilt message
overlay together with the frozen GADEN overlay.  It also resolves the VM's
system `spdlog` and `fmt` CMake packages explicitly, runs a C/C++
`find_package(...)` probe, performs ELF closure checks under the constructed
loader path, and emits a selective `CTPI_VM_ENV.sh`.  The broken aggregate
`/home/zyc/ros2_ws/install/setup.bash` remains unused.

## Resource-bounded Release build

The prepare script builds serially and enables the repository's pre-existing
`PFDI_LOW_MEMORY_BUILD` Release option.  That option retains `-O3` and changes
only debug/sanitizer compile overhead.  This reduced the observed peak compiler
RSS for `Simulations.cpp` from about 4.8 GiB to about 1.5 GiB and reduced the
complete build workspace from roughly 1.0 GiB at failure to 51 MiB after a
successful build.

The binary identity check materializes `strings` once and then matches exact
lines.  This avoids the false negative caused by `set -o pipefail` when
`grep -q` exits early and `strings` receives `SIGPIPE`.

## VM prototype evidence

At source HEAD `c44b204731f976f6aac1de2af71b53a0ed828b9d`, with only the
environment files in this implementation overlaid on the VM checkout:

- TSDC frozen selftest: PASS;
- M3 PIP frozen selftest: PASS;
- Python/C++ TSDC parity: PASS, maximum absolute difference
  `2.2204460492503131e-16`;
- truth-blind runtime preflight: PASS;
- isolated message overlay build: PASS;
- VM dependency qualification: PASS;
- Release build: PASS in approximately 238 seconds;
- installed runtime SHA-256:
  `4a8221732b040400b6c2e3cc9da058db731f3b11bbe328ec3d1ae960dc654995`;
- exact `ctpi_f10` and `ctpi_f11` binary strings: PASS;
- H01/H02/H03 frozen bank integrity: PASS for all three Houses.

This prototype establishes the environment fix.  The true closed-loop smoke
must be run from a fresh checkout/build of the committed implementation HEAD.
