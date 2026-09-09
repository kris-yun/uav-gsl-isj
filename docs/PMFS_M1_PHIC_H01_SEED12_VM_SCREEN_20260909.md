# PHIC M1 H01 seed12 VM screen (2026-09-09)

## Scope

One real VM run was executed after the provenance gate passed, using the new
isolated `cer_core_phic_m1` mode, the original numeric-wind helper, the frozen
z=0.3 m geometry/map binding, and sensor seed12.  No H02/H03 or additional
seed was launched.

## Runtime result

```text
run_id: CTPI_H01_S12_M1PHIC_20260909T052951Z
terminal_status: time_budget_timeout
final_error_m: 2.646
localized2: false
attribution_rows: 268224 (+ header)
```

The run proves that the PHIC branch is wired into the real closed loop and
produces `fopdt_exposure_rate` attribution rows.  It does **not** prove a
closed-loop gain.  The true-source candidate (`quadtree_23_16_1_1`) had zero
exposure at all exported event cells in this trajectory, so the observation
history was not source-identifying; this is a route/observability failure, not
evidence that the PHIC formula should be tuned after the fact.

The replay report returned `ABSTAIN_OVERLAPPING_INTERVALS`; therefore no
source decision is authorized from this run.  The large raw attribution CSV
is retained outside the git commit and is bound by SHA-256:

`0c20fc4691885ba3156a2a9228d87713678edc7d0dd71d3b01751ef624115e27`

## Corrective implication

The next implementation task is M2 route-law integration: freeze a
truth-blind route intervention and make the online predictor choose or score
routes before future gas is observed.  Re-running PHIC on the same
uninformative route would not be a scientific improvement.  Until a route
case is independently controlled and the source-identifying observation gate
passes, M1 remains **mechanism wired / closed-loop effectiveness unproven** and
M2 remains **not yet route-controlled**.
