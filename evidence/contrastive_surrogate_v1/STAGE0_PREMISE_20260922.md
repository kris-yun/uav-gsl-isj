# CSL V1 — Stage-0 premise audit

Date: 2026-09-22
Status: **POSITIVE NECESSARY PREMISE / RAW-BANK STAGE-1 STILL REQUIRED**

## Question

Before spending any new forward simulation or ROS effort, does the already
frozen active-deconfounding evidence contain a reason to believe that a
transport-contrastive source representation could exist?

This is not a new experiment.  It is a read-only audit of the frozen
Active-Deconfounding V1 diagnostics.

## Frozen source

Active-Deconfounding V1 final commit:

`2bd715e3285b5f6cf77b490df14984d628424f95`

Relevant frozen files:

- `evidence/active_deconfounding_v1/CASE_SUMMARY.csv`
- `evidence/active_deconfounding_v1/REPORT.md`
- `evidence/active_deconfounding_v1/FINAL_GATE.json`

The old method remains **NO_GO_WITHIN_FROZEN_OFFLINE_SCREEN**.

## Observation 1 — most candidate source contrasts are not zero

The old screen separately reports nominal source leaves whose response contrast
is exactly zero.

| Case | Zero source contrasts | Total leaves | Nonzero fraction |
|---|---:|---:|---:|
| H01 seed0 | 27 | 123 | 78.05% |
| H01 seed1 | 28 | 121 | 76.86% |
| H02 seed0 | 19 | 123 | 84.55% |
| H02 seed1 | 22 | 119 | 81.51% |
| H03 seed0 | 37 | 160 | 76.88% |
| H03 seed1 | 43 | 160 | 73.13% |

Pooled over the six frozen partitions:

- total leaves = 806;
- zero source contrasts = 176;
- nonzero source-contrast fraction = **78.16%**.

Therefore the response bank is not globally source-indifferent.

## Observation 2 — tested nuisance directions do not span away source contrast

For the true representative versus a fixed high-native-mass false source, the
old screen reports the fraction of confidence-weighted source-contrast energy
remaining after projection against its three tested nuisance sensitivity
columns:

- H01 seed0: 0.98515
- H01 seed1: 0.98720
- H02 seed0: ~1.00000
- H02 seed1: 1.00000
- H03 seed0: 0.96309
- H03 seed1: 0.91879

Median residual fraction: **0.98617**.

Thus those local nuisance directions explain very little of this particular
source contrast.

This does not prove broad external-model validity, but it argues against the
claim that the response bank lacks source-discriminative directions.

## Observation 3 — the old failure is action-local

Active-Deconfounding V1 selected two-action pairs.

For all six cases:
- held-out minimum source separation at the selected pair = 0;
- selected pair predicted no hits for the true representative in every
  held-out world;
- a false source several metres away could match the same no-hit response.

However, the frozen report explicitly records that **other non-selected
candidate actions predict nonzero true-source responses in five of six
cases**.

Therefore the old result supports:
- failure of the selected finite-budget two-action representation;

but it does not establish:
- absence of source identity in the full feasible-action response manifold.

## Why this specifically motivates CSL

The contrastive hypothesis is not that transport nuisance is small.

It is:

> response variation caused by transport can be learned as a within-source
> manifold, while source-changing directions remain discriminative.

The two observations above are necessary evidence for that possibility:

1. most source leaves have nonzero source contrast;
2. tested nuisance sensitivity directions leave most selected source contrast
   intact.

The two-action no-hit collapse then motivates testing the **whole frozen
action-response signature** before designing another active action rule.

## Decision

**Stage-0 premise = PASS.**

Authorize only the frozen raw-bank Stage-1 implemented in:

- `research/contrastive_surrogate/screen.py`
- `research/contrastive_surrogate/run_six.py`

Do not authorize:
- neural InfoNCE training;
- actual-observation fusion;
- ROS changes;
- closed-loop experiments;

until the pre-registered Stage-1 gate passes.
