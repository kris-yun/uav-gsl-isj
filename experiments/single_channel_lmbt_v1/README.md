# LMBT V1: single-channel failure-driven premise test

`LMBT` means **Lag-Marginalized Backward Transport**.  This directory is an
isolated, evaluator-only premise test.  It does not modify PMFS, the frozen M1R
implementation, CCDE, or any protected response bank.

Read in this order:

1. `RESULT_VERDICT.md`
2. `NEXT_ROUTE_DECISION.md`
3. `FAILURE_ROOT_CAUSE.md`
4. `THEORY_AND_NOVELTY.md`
5. `LITERATURE_TRACE.md`
6. `H03_SEED11_PREREG.json`
7. `lmbt_oracle_wind_gate.py`

The formal run was restricted to the historical failing case H03 seed 11. It
used the saved single gas channel, pose history, occupancy support, and the
simulation-known CFD wind sequence.  The full CFD wind is evaluator-only: a
positive result would have established the transport-attribution premise, not
real-flight deployability. The negative result stops this line before any PMFS
or ROS integration.

The formal gate has completed. The primary LMBT premise is `NO_GO`; the
sensor-memory attribution passes as a component result. No rescue tuning or
cross-House expansion is authorized by this result.
