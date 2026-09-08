# CORE-M1S House123 seed11 result

Status: **PREREGISTERED_CROSS_HOUSE_PASS; UNIVERSAL_HOUSE_PASS_NOT_MET**.

All six arms reached the 240 s horizon under the same frozen binary SHA256
`31db663d5a0db9a379deed8bb40927dcca14152ced2e6f3be4835790b533b8f8`.
Algorithm seed 11 was separated from the certified sensor/replay seed 12.

| House | Final improvement (m) | AUC improvement (m s) | Both positive |
|---|---:|---:|:---:|
| H01 | +5.7246448961 | +189.3269434757 | yes |
| H02 | +1.7069644209 | +153.9661282898 | yes |
| H03 | -0.2492929280 | -6.4970207905 | no |

The frozen majority gate passes: 2/3 Houses improve on both metrics and the
pooled mean improvements are +2.3941054630 m final error and
+112.2653503250 m s AUC.  This is real cross-House closed-loop evidence, but it
is not evidence of benefit in every House and not yet a multi-seed claim.

## Failure mechanism exposed by H03

At the end of H03, A0 retained posterior entropy 3.65941 over 46 candidates,
whereas M1S collapsed to entropy 0.694881 over two candidates and selected a
nearby but slightly worse mode.  Runtime inspection then found an estimand-unit
mismatch: PMFS holds one chosen sensing position for eight internal 2 s
measurement blocks (`maxUpdatesPerStop=8`), but M1S recorded all eight as
independent position interventions.  A typical source window therefore used 24
likelihood factors for only three newly executed sensing positions.

This is temporal composite-likelihood overconfidence.  It is distinct from the
retrospective wind rewrite already fixed by M1S.

## Frozen next version

M1P keeps the centered log-odds causal contrast and event-time sequential
posterior, but records only the terminal measurement block of each completed
physical sensing stop.  It has no fitted weight and no House-specific branch.
M1S remains frozen with the result above.  M1P must be evaluated on a different
algorithm seed; seed11 cannot be reused as confirmatory evidence.
