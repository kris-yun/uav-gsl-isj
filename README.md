# UAV Gas Source Localization — ME-ACI V10

This repository contains the frozen **ME-ACI V10** main-innovation implementation for PMFS-based single-UAV gas-source localization. It replaces the previous DQA-AS/SDR/TDC/MHC development version; that version remains recoverable from Git history at commit `647b0bb94a23cbd75dd4cca6377bd8be5c85a887`.

## Current scientific status

The frozen online implementation passed the requested development boundary on three real VGR/GADEN House datasets and two seeds per House. The primary endpoint is the original PMFS top-5% probability-weighted source-location error, `ExpectedValue(sourceProbability, 0.05)`.

| House | Seed | Native PMFS (m) | ME-ACI V10 (m) | Reduction |
|---|---:|---:|---:|---:|
| H01 | 0 | 5.152589 | 2.501097 | 51.459% |
| H01 | 1 | 6.928495 | 5.006343 | 27.743% |
| H02 | 0 | 2.926781 | 2.271832 | 22.378% |
| H02 | 1 | 1.813416 | 1.307146 | 27.918% |
| H03 | 0 | 6.652648 | 2.863832 | 56.952% |
| H03 | 1 | 5.219942 | 2.982003 | 42.873% |

- Pass rate: **6/6** at the frozen `>=10%` individual-improvement threshold.
- Pooled error: **4.782312 m -> 2.822042 m** (**40.990% reduction**).
- Worst individual reduction: **22.378%**.
- First accepted update: **72.851–217.811 simulation seconds**, within the 300 s budget.

These are real online closed-loop, first-identifiable-intervention comparisons on an identical trajectory up to posterior release. They are strong mechanism/development evidence, not yet an unseen-seed population-level paper claim. The next confirmatory experiment must keep the formula, source, binary, cadence, metric and stopping rule frozen.

## Method

ME-ACI treats gas-source localization as conditional inverse transport. It stores completed hit/miss events in a sequential reservoir, splits them into two disjoint temporal folds, and releases source evidence only when both folds contain hit/miss contrast and hits replicate at at least two occupied locations. Conditioning on the observed hit count removes an unknown release/sensor intercept. A fixed 54-member transport-discrepancy family is marginalized, the two temporal rank channels are combined, and the resulting likelihood updates an independent causal source posterior. Rejected windows are retained and do not alter that posterior.

The validated role of SD-TFEI is therefore a **sequential temporal-replication inference channel**, rather than the earlier stand-alone generalized-eigenvector feature.

## Frozen identifiers

- Run contract: `MEACI_SEQUENTIAL_SPATIAL_REPLICATION_V4`
- Formula marker: `inverse_transport_sequential_replication_v3`
- Source-update cadence: `stepsSourceUpdate=3`
- Runtime budget: `300 simulation seconds`
- Online binary SHA-256: `14133117b9d24502acc8e45ad7c72fbd668fbe867fd73aeee17b70e52cfbe938`
- `Simulations.cpp` SHA-256: `6f3955eef884f804df725eb0b39d39c3abe1c436b9f9cbb6419e6df881ef5198`
- `Simulations.hpp` SHA-256: `ea358f1f23cefb807d7daf0f4efc31dd91e29c45717277f976955aa7109a8e00`

## Repository layout

- `ros2_package/` — captured ROS 2 `gsl_server` package; the frozen implementation is in `src/gsl_server/algorithms/PMFS/internal/Simulations.{cpp,hpp}`.
- `reference/` — frozen runner, evaluator and PMFS metric reference files.
- `docs/METHOD_AND_RESULTS.md` — mathematical contract, results and scientific limits.
- `docs/THEORY_LINEAGE.md` — PMFS, inverse-causal and robust-inference lineage.
- `evidence/RESULT_MATRIX.csv` — compact six-case result matrix.
- `evidence/cases/` — per-case manifests, evaluations and update summaries.
- `evidence/MEACI_V10_MAIN_INNOVATION_HOUSE123_SEED01_6OF6_20260824.zip` — complete frozen evidence package with raw traces and original verifier.
- `artifacts/gsl_actionserver_node` — exact qualified Linux binary.

See [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) before rebuilding or running. Do not silently replace the frozen binary with a new build when reproducing the reported 6/6 result.

Run `python3 verify_repository.py` for a repository-level integrity check.

