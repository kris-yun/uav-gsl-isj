# PHIC M1 implementation status (2026-09-09)

## Current state

The PHIC redesign is now represented in the repository by:

- the theory/data package in `docs/PMFS_M1_THEORY_DATA_REVIEW_PACKAGE_20260909.md`;
- the frozen design in `docs/PMFS_CORE_M1_PHIC_DESIGN_20260909.md`;
- the analytic contract self-test in
  `experiments/ctpi_cstar/selftest_m1_phic.py`;
- a diagnostic runtime export of candidate x transport-member x event rows;
- optional aggregate forward exposure values for each member.

The reference, environment, provenance, and PHIC analytic self-tests pass.
The PHIC analytic report is stored at
`evidence/cstar_m1_phic_analytic_selftest_20260909/report.json`.

## What the exporter proves

When the existing context-bank export is enabled, the runtime writes
`contrastive_event_attribution.csv`.  Each row is bound to the run UUID,
source-update ID, candidate, transport member, event block, event cell,
observed hit, concentration, threshold, legacy hit-map probability, aggregate
forward exposure, and context value.  The export is write-only and cannot
change the online score or navigation state.

## Remaining scientific blocker

The aggregate exposure is produced by the complete PMFS forward simulation.
It is not yet a block-level exposure sequence, so it cannot by itself drive a
sensor-consistent FOPDT replay.  A real PHIC attribution gate still requires
block-level exposure logging (or an equivalent frozen forward replay) and then
candidate-level likelihood/margin/calibration reports on H01/H02/H03.

Until that replay passes, no new closed-loop result is labelled PHIC-effective
and no cross-dataset M1 claim is made.
