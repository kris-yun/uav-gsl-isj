# 02 — Code Map

This directory is the code entry point. The executable source files remain in
their historical locations so frozen manifests, SHA checks, scripts and
reproduction paths are not broken.

## A. Online ROS / PMFS implementation

Primary tree:

`ros2_package/`

Important TNQC files:

- `ros2_package/src/gsl_server/algorithms/PMFS/internal/TNQCScore.hpp`
  — quotient score and candidate-bank gate math.
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp`
  — PMFS integration, final-leaf bank construction, context-bank export and
  TNQC online application.
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp`
  — state/configuration declarations.
- `ros2_package/test/test_tnqc_score.cpp`
  — dependency-light scientific unit tests.
- `ros2_package/tools/tnqc_expected_value_native.cpp`
  — endpoint executable linked to the original
  `GSL::Utils::ExpectedValue(...,0.05)` implementation.
- `ros2_package/CMakeLists.txt`
  — build/install definitions.

The captured `gsl_server` package declares GPLv3 in
`ros2_package/package.xml` and contains upstream/third-party-derived
components. Do not treat the entire tree as newly authored project code.

## B. Offline scientific replay and evaluators

Primary tree:

`reference/`

Key TNQC files:

- `reference/tnqc_vgr_fixed_trajectory_replay.py`
  — authoritative fixed-trajectory TNQC replay.
- `reference/aggregate_tnqc_vgr_offline_gate.py`
  — six-case 300-s aggregate and GO/HOLD criteria.
- `reference/run_tnqc_vgr_offline_gate_20260920.sh`
  — authoritative House01/02/03 × seed0/1 offline driver.
- `reference/build_tnqc_v5_current.sh`
  — manifest verification, local preflight and clean ROS build.
- `reference/verify_tnqc_v5_manifest.py`
  — frozen byte-level manifest verification.
- `reference/tnqc_expected_value_eval.cpp`
  — historical/test-only standalone clone of the PMFS endpoint semantics.
- `reference/test_tnqc_vgr_fixed_trajectory_replay.py`
  — synthetic full replay contract test.
- `reference/check_tnqc_shadow_determinism.py`
  — OFF/SHADOW parity checker for the later closed-loop stage.
- `reference/run_tnqc_closed_loop_matrix_20260920.sh`
  — closed-loop matrix; prohibited until offline GO.

## C. Historical validated main line

The repository also preserves the frozen **ME-ACI V10** work and its
qualified binary/evidence.

Main implementation lives in the same PMFS tree, while the frozen evidence
and reproduction contract are documented under `docs/`, `evidence/` and
`artifacts/`.

TNQC is a later research-cycle candidate and must not overwrite historical
ME-ACI evidence.

## D. Execution branches

The main branch contains frozen scientific code and documentation.

Operational/experimental execution may use isolated branches, for example:

`codex/tnqc-v5-300s-offline-20260921`

Execution branches are for logs/results/infrastructure recovery. They should
not silently rewrite the frozen method.

## E. Why files are not physically moved

Several scientific controls depend on exact paths and bytes:

- manifest blob SHA checks;
- source-tree SHA checks;
- runner path references;
- evidence manifests;
- historical reproduction commands.

For this reason the repository uses this `02_code/` directory as a stable
navigation layer rather than relocating the executable files.

## F. Recommended reading order for code

1. `01_idea/README.md`
2. `CODEX_START_HERE.md`
3. `docs/TNQC_V5_SUPPORT_COVERAGE_GATE_20260921.md`
4. `TNQCScore.hpp`
5. TNQC sections of `Simulations.cpp`
6. `tnqc_vgr_fixed_trajectory_replay.py`
7. `aggregate_tnqc_vgr_offline_gate.py`
8. tests and execution scripts

## G. Code-status rule

A method is not considered validated because code compiles.

The required progression is:

unit math → synthetic replay → manifest/byte integrity → clean build →
fixed-trajectory 300-s localization gate → OFF/SHADOW determinism →
closed-loop FUSED.

Each layer has a different scientific meaning.
