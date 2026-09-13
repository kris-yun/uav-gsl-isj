# LMBT V1: single-channel failure-driven premise test

`LMBT` means **Lag-Marginalized Backward Transport**.  This directory is an
isolated, evaluator-only premise test.  It does not modify PMFS, the frozen M1R
implementation, CCDE, or any protected response bank.

Read in this order:

1. `FAILURE_ROOT_CAUSE.md`
2. `THEORY_AND_NOVELTY.md`
3. `LITERATURE_TRACE.md`
4. `H03_SEED11_PREREG.json`
5. `lmbt_oracle_wind_gate.py`

The first formal run is restricted to the historical failing case H03 seed 11.
It uses the saved single gas channel, pose history, occupancy support, and the
simulation-known CFD wind sequence.  The full CFD wind is evaluator-only: a
positive result would establish the transport-attribution premise, not real
flight deployability.  A negative result stops this line before any PMFS or ROS
integration.

