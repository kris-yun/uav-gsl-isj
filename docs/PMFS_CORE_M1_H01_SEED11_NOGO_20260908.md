# CORE-M1 H01 seed11 early-stop result

Status: **M1C_NO_GO; M1S_EVENT_TIME_REPAIR_PENDING**.

## Result

Both A0 and M1C reached the frozen 240 s horizon with terminal status
`time_budget_timeout` and binary SHA256
`ede83cfd8e4bd3a12ccf805541b8a2f2f37bc67f23ebc07ba0bc63e16b12a05c`.
The environment guard accepted the corrected H01 map with algorithm seed 11
and independently frozen sensor seed 12.

| Arm | Final error (m) | Distance AUC (m s) |
|---|---:|---:|
| A0 | 6.7250947949 | 1735.7753697 |
| M1C | 8.0877005385 | 1669.7813101 |
| A0 minus M1C | -1.3626057436 | +65.9940597 |

The preregistered one-world early gate required both final error and AUC to
improve. It failed, so H02/H03 and additional seeds were not run.

## Failure attribution

M1C reached 5.2529 m error around 120--150 s, then regressed to 8.0877 m by
240 s. The runtime log shows all accumulated events being rescored at every
source update (`events=32,56,80,104`) using the current transport simulation.
Thus an observation generated under event-time context `H_i` is later assigned
a likelihood generated under `H_t`. Candidate-common odds centering cannot
repair this cross-time consistency violation.

## Next falsifiable repair

M1S keeps the CORE candidate-centred log-odds operator but changes assimilation
from retrospective rescoring to a sequential Bayes update:

1. score only events not committed by a previous source update;
2. condition their likelihood on the current event window and the immediately
   preceding sensor concentration;
3. multiply the resulting incremental likelihood by the previously committed
   cell posterior;
4. commit the new posterior and never reinterpret that event under a future
   wind field.

This is an event-time consistency repair, not a fitted weight, House switch or
truth-guided rule. It receives a new arm identity `M1S`; the failed `M1C`
evidence remains immutable.

