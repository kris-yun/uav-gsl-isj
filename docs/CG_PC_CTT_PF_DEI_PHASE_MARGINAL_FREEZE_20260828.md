# SUPERSEDED — PF-DEI phase-marginal occupancy likelihood

Date superseded: 2026-08-28

This science contract is retained only for historical reproducibility and must not be used as the current PF-DEI method.

Reason: source audit established an observation-operator mismatch.  The old reference treated ordered CTT filament occupancy as if it were a probabilistic observation of PMFS block HIT/NOTHING.  In the actual system, PMFS consumes measured gas concentration produced by a dynamic sensor, averages the consumed measurement block, and thresholds that mean.  CTT occupancy is not physical concentration and is not the native measured sensor variable.

Current normative science contract:

`docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`

Current execution task:

`docs/CODEX_PF_DEI_FORWARD_OPERATOR_CLOSURE_20260828.md`

No occupancy-to-ppm/HIT conversion, no new likelihood, no C++, and no 60-arm performance experiment are authorized until the exact physical concentration -> persistent sensor -> measured concentration -> PMFS block observation operator is closed.
