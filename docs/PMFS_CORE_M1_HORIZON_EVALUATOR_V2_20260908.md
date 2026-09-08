# CORE-M1 full-horizon evaluator V2

Status: **FROZEN BEFORE THE NEXT CONFIRMATORY SEED**.

The V1 evaluator required the last row of `source_estimate_trace.csv` to occur
after 235 s.  H01 seed7 exposed a measurement error in that rule: the M1F
posterior updated at 232.329 s, then remained the active estimate during a
navigation action that completed at 239.73 s, while the independent terminal
record certified the 240 s time-budget termination.  No new source posterior is
expected during navigation, so absence of a later row is not absence of an
estimate at the horizon.

V2 treats the posterior as the state it is.  After verifying
`run_status.status == time_budget_timeout`, it carries the first logged estimate
back to 0 s and the last logged estimate forward to 240 s.  Between logged
updates it uses a left-continuous zero-order hold, rather than linearly
interpolating a posterior jump.  The rule is symmetric for A0 and M1, covers
exactly 0--240 s, and never invents an unlogged posterior update.

H01 seed7 was already visible when this instrumentation defect was found.  Its
V2 score is diagnostic only.  The first confirmatory M1F screen under V2 must
use a new algorithm seed and must still improve both final error and full-horizon
distance AUC before any House2/House3 expansion.
