# Persistent-source PMFS R1 execution provenance

Scope: execute the supplied development-only R/C/P ablation, with no scientific
formula, parameter, seed, observation, scoring or decision changes.

Original ZIP:
`PERSISTENT_SOURCE_PMFS_V0_20260926.zip`
SHA256: `7c4fdc2e33ac1ec02db5382ed12f288b5fac26c50849f87d1014bf308b751798`.
All original package members passed the supplied SHA256SUMS.txt. Both the
copied executable source and evaluator are retained verbatim.

Base checkout: `ee746226a16a1f81582107ad08cb1439d994786b`.
Branch: `research/persistent-source-pmfs-v0-20260926`.
Only one isolated CMake target was added; PMFS library sources and online launch
files are unchanged. Build: Release, -O3, PFDI_LOW_MEMORY_BUILD=ON,
BUILD_TESTING=OFF, serial `cmake --build --target persistent_source_r1_replay`.
The existing ROS2 Humble dependency overlay under `/home/zyc/ros2_ws/install`
is sourced for compilation and shared-library resolution only.

Binary SHA256:
`64b2bb1e305b3bf03ecc5ec13761fe92af01da4a8bb86221063985ffd2aa8b21`.
Replay source SHA256:
`0d6af633d0ccd6e182d13ccf61cbc93cffef5a94598eccf60a555921bd1c2758`.

The existing VM source-blind input directory was
`/home/zyc/native_pmfs_recovery_v1/runs/R1_R2_SOURCE_CORRECTED_House01_S0_20260923`.
Only the four prescribed CSVs were copied to a fresh input directory after
verification against its historical `r1_scores_frozen_manifest.json`:

| Input | SHA256 |
| --- | --- |
| measurement_events.csv | f05114b558132a1c62d1ecf705d9bdd2f066905b9c48881b3457b9f0d9cd15e9 |
| measured_map_at_update.csv | dee2f4e154860ae74bf9fd5375b4721864cdd96dc775badfbdc4ee56f2019eab |
| frozen_candidate_geometry.csv | be200fe8623ff8626b60d01fbbfda67e08e095bab6527c205c5f2a70168e70cc |
| wind_source_update.csv | 08009a97893d8a2e10faad17e94101821849ce8b690513844e8c5a9895fa22ba |

The replay executable has no truth input. The first output directory is
`/home/zyc/persistent_source_pmfs_r1_20260926`; deterministic repeat uses
`/home/zyc/persistent_source_pmfs_r1_repeat_20260926`. OMP_NUM_THREADS and
OPENBLAS_NUM_THREADS are 1. K=8, M=8 and all RNG keys are those in the supplied
specification. Score freeze precedes loading the historical truth JSON.

No GADEN process, new plume, network training, House03 data, or closed loop is
authorized or launched. The evaluator's permitted development decision is
retained without rescue or retuning.

## Completed execution

The first source-blind score freeze was committed and pushed as
`fa90a2b6cd494dff8741c84fb69fefb7091d3e4b` before loading the historical
truth JSON. Truth SHA256:
`07ee4081fab67441f4bba9cde64f1828b369b6dca20b9c660dec9a5d542e4311`.
The reconstructed hit-map log-odds and confidence differences were both zero.
Each execution produced 6960 score rows: R=696, C=696, P=5568.
All four raw output files passed byte-for-byte deterministic repeat.

The supplied, unchanged evaluator returned `MECHANISM_NULL_OR_ADVERSE`:
R/C/P truth ranks 52/53/54 out of 87. Full metrics, area diagnostics, frozen
inputs and repeat outputs are committed under `evidence/persistent_source_pmfs_v0`.
There was no infrastructure-only patch to the supplied replay or evaluator.
Execution is complete and stopped without any follow-up experiment.
