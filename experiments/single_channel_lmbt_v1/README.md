# LMBT V1: single-channel failure-driven premise test

`LMBT` means **Lag-Marginalized Backward Transport**.  This directory is an
isolated, evaluator-only premise test.  It does not modify PMFS, the frozen M1R
implementation, CCDE, or any protected response bank.

Read in this order:

1. `RESULT_VERDICT.md`
2. `DEVICE_CONTRACT_20260913.md`
3. `NEXT_ROUTE_DECISION.md`
4. `FAILURE_ROOT_CAUSE.md`
5. `THEORY_AND_NOVELTY.md`
6. `LITERATURE_TRACE.md`
7. `H03_SEED11_PREREG.json`
8. `lmbt_oracle_wind_gate.py`

The formal run was restricted to the historical failing case H03 seed 11. It
used the saved single gas channel, pose history, occupancy support, and the
simulation-known CFD wind sequence.  The full CFD wind is evaluator-only: a
positive result would have established the transport-attribution premise, not
real-flight deployability. The negative result stops this line before any PMFS
or ROS integration.

The formal gate has completed. The primary LMBT premise is `NO_GO`; the
sensor-memory attribution passes as a component result. No rescue tuning or
cross-House expansion is authorized by this result.
