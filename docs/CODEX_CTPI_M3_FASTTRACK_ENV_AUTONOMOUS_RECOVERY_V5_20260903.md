# Codex — CTPI M3 fast-track autonomous VM environment recovery V5

This directive supersedes the prior one-overlay-at-a-time environment recovery workflow. The scientific method remains frozen.

## Current classification

The latest V4 failure is `BLOCKED_BY_VM_ENVIRONMENT`, not a scientific NO-GO.

Known facts from the V4 qualification evidence:

- `/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install` passed GADEN package structure, CMake config, local setup, ELF dependency, and ROS prefix checks for `gaden_msgs`, `gaden_common`, and `gaden_player`.
- The current `/home/zyc/ros2_ws/install` is incomplete for custom ROS packages: `olfaction_msgsConfig.cmake` and `gsl_actionsConfig.cmake` are missing.
- The system has `/usr/lib/x86_64-linux-gnu/cmake/spdlog/spdlogConfig.cmake`, but the previous isolated CMake probe did not include a search route that resolved it.
- Phase 0 V3, runtime patch materialization/application, TSDC selftest, M3 PIP selftest, Python/C++ parity, and truth-blind source preflight all passed before the environment failure.

## Environment-layer autonomy

Codex is authorized to solve VM/toolchain/dependency problems autonomously until the frozen Release build succeeds. Do not return for approval after each missing package or CMake-path issue.

Permitted environment-only actions include:

- search the VM for existing valid installs/builds/sources of required ROS packages;
- rebuild missing custom message packages such as `olfaction_msgs`, `gsl_actions`, and other required non-scientific ROS dependencies into a new isolated overlay;
- build a fresh dependency overlay from existing VM source trees when an old install is incomplete;
- repair `CMAKE_PREFIX_PATH`, `AMENT_PREFIX_PATH`, `LD_LIBRARY_PATH`, `PYTHONPATH`, package-specific `*_DIR` variables, and system CMake package discovery such as `spdlog_DIR`;
- use the already-qualified GADEN install or another VM-local GADEN install only after independently validating package identity, CMake discovery, ELF closure, and runtime package-prefix resolution;
- install a missing system development package if package management is available and the exact package/version/action is recorded in evidence;
- create/remove temporary `/dev/shm` compatibility symlinks or fresh build/install workspaces;
- modify environment recovery scripts, build wrappers, dependency qualifiers, and reproducibility manifests in this repository;
- iterate environment diagnosis/build attempts as needed without touching scientific code.

Codex must prefer isolated, reproducible overlays over modifying or trusting the broken aggregate `/home/zyc/ros2_ws/install/setup.bash`.

## Scientific files remain immutable

Environment autonomy does NOT authorize changing:

- M1/CREL formulas or runtime semantics;
- M2 TSDC beta, features, definition, or frozen Python source;
- M3 PIP objective, action domain, tie-break, information equation, or frozen Python/C++ scientific source;
- runtime integration scientific hunk content;
- 3/3/1 cadence;
- 240 s horizon;
- predictive bank content;
- smoke/screen/formal scientific Gates or their thresholds;
- source truth access or future-observation access in the planner.

If a build error appears to require changing one of those items, stop and report `BLOCKED_BY_SCIENTIFIC_SOURCE_OR_INTERFACE` instead of editing it.

## Required completion behavior

Codex should continue autonomously through:

1. environment recovery;
2. fresh Release build;
3. `CTPI_M3_FASTTRACK_VM_BUILD=PASS`;
4. bank integrity verification;
5. H01 seed0 F00/F10/F11 true-closed-loop smoke;
6. H01 seeds0-2 screening only if smoke PASS;
7. cross-House seeds3-5 formal confirmation only if screening PASS.

Any scientific Gate failure remains fail-closed. Environment/build failures may be diagnosed and repaired autonomously under the rules above.

## GitHub handback requirement

Before final handback, commit and push all reproducibility-relevant environment changes to branch `research/ctpi-m3-fasttrack-20260903`, including:

- environment/build scripts actually used;
- dependency-overlay construction or discovery scripts;
- package/version/path/hash manifests;
- qualification/build audit summaries;
- any environment-only errata;
- final exact Git commit SHA used for the successful build/smoke or the terminal blocked state.

Do not commit generated build trees, large binaries, banks, or transient VM caches.

At handback, report the final GitHub HEAD and one of:

- `CTPI_M3_FASTTRACK_VM_BUILD=PASS` plus downstream Gate results; or
- a terminal blocker that cannot be solved without changing frozen scientific code/interface.
