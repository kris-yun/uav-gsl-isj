# M4-v2 C0.5 frozen House02 comparison result

Date: 2026-09-23  
Status: **LOCAL FIELD SIGNAL; NO QUALIFYING SOURCE-RANK OR G3 PASS**

## Provenance and integrity

The eight House02 GADEN `concentration.npy` files were checked against the
committed SHA-256 values in `c0_5_real_gaden_bank/spatial_summary.json`; all
eight match. Each has ten 83×119 snapshots. The two plume seeds in each
source×wind cell remain distinct in the earlier raw and spatial audits.

The frozen split was S1-W1, S2-W1, S1-W2 for training and S2-W2 A/B for
held-out evaluation. Four v2 checkpoints were committed in `efa3f14` before
the S2-W2 target was read. Trainable parameters were 2,857 monolithic and
3,136 operator (9.77% more than monolithic). Training seeds were 1729 and
2718. An initial operator training run was preserved separately: one seed's
source injection was killed by ReLU before any target inspection. The only
pre-holdout repair used the magnitude of the source projection; see
`C0_5_LOCAL_COMPARISON_V2_PRE_HOLDOUT_REPAIR_20260923.md`. No model setting
was changed after held-out evaluation.

## Held-out field error

Free-space mean squared error of `log1p(concentration)` after a fixed 2×
spatial reduction (lower is better):

| Training seed | Plume seed | Monolithic | Operator |
|---|---|---:|---:|
| 1729 | A | 0.442162 | 0.135064 |
| 1729 | B | 0.431375 | 0.113821 |
| 2718 | A | 0.310335 | 0.141936 |
| 2718 | B | 0.297871 | 0.120340 |

The operator wins all four paired comparisons. These are correlated snapshots
from one House, two source positions, and two wind configurations; the table
does not establish transfer to an unknown House. The model input used a
single canonical wind slice, while GADEN used a time-varying wind sequence.

## Source identity and transport controls

A second frozen script selected 30 sparse probe cells using only the obstacle
mask. The two-candidate S1/S2 source comparison ranked true S2 first for
**both** models, both training seeds, and both plume seeds (4/4 per model).
There is therefore no truth-rank improvement in this diagnostic; rank 1/2 is
already the floor for the monolithic control. The source swap to S1 raises
error in every operator run, but also does so for the monolithic control.

For the operator, changing only W2 to W1 at S2 changed probe error by
`+0.000353`, `+0.000112`, `+0.000051`, and `-0.000027` across the four runs.
One of four changes has the wrong sign, and all are small relative to the
S2-W2 errors (0.0575–0.0756). Thus this check does not demonstrate a
wind-sensitive reusable transport mechanism. The exact scores and 30 probe
coordinates are in `m4_c05_local_compare_20260923_frozen_v2/sparse_rank_diagnostic.json`.

This sparse network is **not** a Native PMFS-compatible candidate replay or
UAV trajectory. Source-label and wind-label shuffle retraining was stopped
after the rank tie and weak wind-swap result, following the frozen gate. No
claim about their outcome is made.

## Decision

`C0.5 LOCAL FIELD SIGNAL`: supported on House02 S2-W2 A/B.  
`C0.5 MECHANISM ADVANCE`: **not met**; the diagnostic did not improve truth
rank over monolithic or show a reliable transport-swap effect.  
`M4-v2 G3 UNKNOWN-HOUSE`: **HOLD**; the required held-out House spatial field,
two independent target seeds, unseen wind-family target, and sensor-shift bank
are absent.  
`M4-v2 MAIN INNOVATION`: **not established**. No ROS/PMFS live loop or 300 s
closed-loop experiment was run.
