# H03 existing-route paired-position premise

Date: 2026-09-13

## Verdict

```text
PHYSICAL_CONTRAST_CAPACITY=PASS
FAILED_H03_SA_FULL_SUPPORT_IDENTIFICATION=FAIL
NO_GO_CURRENT_PAIRED_OPERATOR_INSUFFICIENT_FULL_SUPPORT_SEPARATION
```

This is an evaluator-only existing-data screen.  It does not alter PMFS, select
an online action or run a new House/seed.  Geometry motifs are enumerated before
gas and source labels are read.

## What passed

The source-blind H03 route contains four equal-time `A-B-B-A` motifs satisfying
the frozen map/sensor constraints: 0.1 m position bins, at least 0.3 m A-to-B
separation, and 3.6--12 s cycle duration.  The contrast is

```text
z = (y_A1 + y_A2 - y_B1 - y_B2) / 2.
```

Its weights remove a shared constant, and equal timing removes a shared linear
time drift.  On the real crossed `SA/SB x fast/slow` physical histories:

- all four source differences have the same sign in fast and slow transport;
- all four source main effects exceed their source-by-transport interaction;
- the H01+H02-selected held-out provider predicts the observed sign for every
  motif after its 15 s wind window and 3 s sensor constant are evaluated at the
  actual 0.2 s history cadence.

The cadence correction is material.  The manifest's `raw_dt_s=0.1` describes
the simulator snapshots; stored histories are decimated to 0.2 s.  The screen
derives 0.2 s from timestamps, uses 75 samples for a 15 s causal wind window,
and uses sensor update coefficient `0.06449301497`.

## What failed

The complete source-independent H03 support has 820 candidates.  With one
nonnegative cycle-shared amplitude profiled as a nuisance, the failed true SA
source ranks are:

| transport | paired contrast rank | same 16 raw samples rank | best candidate |
|---|---:|---:|---|
| fast | 177/820 | 213/820 | `(1.1, 1.887)` |
| slow | 20/820 | 284/820 | `(0.8, 1.887)` |

The historical strongest false region near `(8.15,-1.413)` is demoted to ranks
309 and 204, so the contrast removes that particular failure.  It does not
separate the truth from all other sources.  The alternative SB source produces
zero contrast in these cycles, leaving a full `1--820` tie; this is not source
identification.

## Root cause and bounded redesign

All four geometry-admissible cycles point in almost the same spatial direction:

```text
singular values = [1.999108, 0.059727]
condition number = 33.47083
second-direction energy fraction = 0.0008918
```

They supply a near one-dimensional source constraint, explaining a long alias
band even though the historical false mode is excluded.  Adding weights or a
posterior temperature cannot create the missing spatial direction.

The next premise is therefore one fixed rank-2 physical action: three
map-feasible paired cycles oriented approximately 60 degrees apart.  It is
constructed only from the shared route geometry and free-space map.  Its
pre-experiment route and gate are frozen separately in
`evidence/m1r_h03_rank2_paired_probe_20260913/`.

## Traceability

- Raw result: `GATE.json`
- Reproducer: `tools/screen_h03_paired_position_premise.py`
- Inputs and SHA-256 values are embedded in `GATE.json`.
