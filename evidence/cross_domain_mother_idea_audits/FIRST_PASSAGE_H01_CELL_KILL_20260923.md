# H01 cell-level first-passage / transport-age kill test

Date: 2026-09-23

Status: **NO_GO_H01_ORDER_SPECIFIC_FIRST_PASSAGE_PREAUDIT**

This is a Layer-1 mother-mechanism pre-screen, not a localization method.

## Frozen setting

- accepted run: H01_R2026092201
- terminal source candidates: 121
- observed-support cells: 212
- candidate transport age: 200 internal steps
- measured H01 field is all-miss / constant-prior: True

Because H01 contains no positive hit target, this pre-screen asks a narrower falsifiable question: after conditioning on each cell's final 200-step occupancy count, does the ordering / first-arrival age itself give the truth-nearest source candidate extra compatibility with the observed no-hit support?

## Results

| score | truth rank (avg ties) | Spearman vs -truth distance |
|---|---:|---:|
| native_score | 76.00/121 | 0.1576 |
| static_low_occupancy | 20.50/121 | 0.2663 |
| raw_first_passage_delay | 21.00/121 | 0.2901 |
| order_only_first_passage_delay | 101.50/121 | -0.1818 |

### Time-order destruction null

- repetitions: 500
- actual order-only truth rank: 101.50/121
- null median truth rank: 58.50
- null fraction with truth rank as good or better than actual: 1.0000

The null preserves every candidate×cell final occupancy count and destroys only the occupied-step order, so any surviving advantage is specifically attributable to first-passage order rather than the static hitMap frequency.

## Gate

- order-only rank must beat static occupancy rank: False
- time-destroyed null as-good-or-better fraction <= 0.05: False
- **PASS: False**

H01 does not show load-bearing order-specific first-passage information beyond static occupancy. Do not rescue this by tuning passage windows or target sets on H01. Positive reactive-flux testing would require new replay on hit-bearing H02/H03 and should only be undertaken if there is an independent reason to keep the mother theory alive.

Full machine-readable results: FIRST_PASSAGE_H01_CELL_KILL_20260923.json.
