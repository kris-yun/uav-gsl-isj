# R2 execution-only correction

The first independent Native executions used the HCMC branch's clean-build algorithm SHA `265c5afe...`. That branch did not contain the already-qualified TNQC R2 terminal lifecycle correction, so the 300-s runs could finish without emitting Native PMFS `RESULT IS`. Those attempts are retained under the VM evidence tree's `failed_attempts/` and are excluded from scientific evaluation.

Before any independent HCMC posterior or linked-native truth evaluation was generated, the exact three-file execution patch from frozen commit `b24da77fd24bd5ea2cbb33caf856f80b9d7670e4` was ported:

- `Algorithm::OnUpdate()` stops advancing scientific work at the frozen deadline;
- `Algorithm::FinalizeTimeBudget()` performs terminal Native result I/O once;
- the action-server-level deadline calls that finalizer for PMFS instead of bypassing it.

No PMFS likelihood, source update, planner, sensor, HCMC formula, gate threshold, truth coordinate, or data realization changed. The rebuilt R2 runtime has algorithm SHA `b06c2036da91ef22285d1cb5d4d08172e828956fc5844d8a2044a4221a8c2cce`. The linked-native endpoint remains byte-identical at SHA `9d0954c32021f6b808ba4bec06e98ea9fe8193b25cc4ed33d4189330d40c9ac6`.

A source-blind 5-s smoke run emitted both `BUDGET_FINALIZE` and `RESULT IS`, confirming that the correction restores the required anchor without extending the scientific budget.
