# SUPERSEDED — PF-DEI full-trace dynamic replay V2

Date superseded: 2026-08-28

This task is **NOT AUTHORIZED FOR EXECUTION**.

Independent source audit proved that the existing CTT ordered trace is an any-filament cell-occupancy process, while PMFS observes the mean of measured gas concentrations after the native dynamic sensor.  Therefore the former occupancy-to-Bernoulli PF-DEI likelihood has a decisive observation-operator mismatch even though its Python selftest passes.

The historical implementation remains available in git history for reproducibility only.

Current normative task:

`docs/CODEX_PF_DEI_FORWARD_OPERATOR_CLOSURE_20260828.md`

Current normative science contract:

`docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`

Binding rule: do not run the old occupancy-based full-trace likelihood, do not fit occupancy-to-ppm, and do not proceed to C++ or localization-performance experiments until the physical concentration + persistent sensor + measured-concentration forward operator is closed.
