# User execution clarification before formal campaign

Received 2026-09-27 before any scored 96 x 4 campaign.

- Use the existing ROS2 + GADEN replay + VGR motion/action backend.
- Label results `VGR interactive closed-loop development campaign`, never
  Gazebo physics closed loop. Do not switch to Gazebo/Nav2 in this campaign.
- Every arm must invoke the original PMFS planner with its own sourceProbability
  and varianceOfHitProb; VGR executes the resulting goal before the next
  spatiotemporal GADEN observation. Paths may differ.
- First export all nine candidates absent from Native initialization: ID,
  grid/xy, reason and overlap with the frozen twelve truth sources.
- If all twelve truths are retained, all four arms use the same fixed Native
  legal support (615), with learned posterior renormalization after masking.
- If any truth is excluded, HOLD/STOP the formal campaign and return its ID and
  reason. Do not drop the truth or compare learned624 against Native615.
- H01/H02 training supports must follow the identical Native fixed legality
  rule, rather than all geometrically enumerated source centers.
- Existing full model-bank generation continues; it is support infrastructure.
- Before formal scoring, test two different posterior/variance inputs through
  the actual planner and verify different goals are executed by VGR. This is a
  software check only.

## Conditional stop actually triggered

The Native initialized mask excludes frozen truth `pmfs_24_13` (index 622;
x=6.5, y=2.187, z=0.20 m). Eleven of twelve truths are retained. The actual
mask was reproduced exactly by VGR fine-grid serialization, Native 3x3 occupancy
reduction and unmodified Native reachability pruning. Thus the formal campaign
is HOLD under the user's condition. No truth case is removed; no support or
Native legality code is changed. Six-candidate functional weights remain
excluded from scored use. The old automatic GPU launcher was stopped while
waiting, before it could train against unbound geometric-only supports.

Detailed evidence is in software_audit/actual_support_audit_v2/.
