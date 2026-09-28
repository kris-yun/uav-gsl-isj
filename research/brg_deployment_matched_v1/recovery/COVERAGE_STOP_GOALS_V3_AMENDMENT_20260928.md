# BRG V1 training coverage: stop-and-sample implementation amendment

The original V2 file route was chosen using only the Native legal map and
fixed start. Its first VGR software pilot ran for 300 s but failed the
predefined ten-publication integrity check. The VGR open-loop profile kept
moving while PMFS accumulated ten readings at one recorded measurement pose.
All 25 pilot blocks had fewer than ten VGR publications within 0.02 m of the
PMFS block pose. No pilot feature, score, or label enters training or model
selection. The full invalid raw run is preserved at
`C:\Users\50176\Desktop\vm数据\BRG_V1_INVALID_COVERAGE_PILOT_20260928\INVALID_COVERAGE_OPEN_LOOP_PILOT_013.tar.zst`,
SHA256 `fd86348bbf9c9f7965ed3b0b8cb4e2f82704ed3a303411b2c632a319a0b1c911`.

The V3 implementation keeps the same V2 legal-map path as a geometric input.
Before another coverage run, it freezes twelve distinct source-blind goals
per OPEN environment: every seventh 3.4 s segment endpoint of that path.
When PMFS next asks VGR to navigate, an opt-in training-only VGR branch
substitutes the next frozen goal and uses the **normal** collision-checked
NavigateToPose action. VGR stops at the goal; PMFS then acquires its original
ten-reading windows. The opt-in branch records requested and actual goals.

`COVERAGE_STOP_GOALS_FREEZE_V3.json` binds every exact goal, its parent route
SHA, the deterministic selection rule, and the invalid pilot archive. It was
written before the V3 pilot. No source truth, gas concentration, score, or
House03 asset participated in goal selection. Native, learned-arm, and final
evaluation motion paths use the unmodified default branch. The three
networks, features, labels, optimizer, source split, candidate banks, plume
assets, and 300 s budget are unchanged.

The V3 pilot on frozen training case 013 then completed its 300 s VGR run,
executed four frozen stop goals, recorded 25 measurement events, and passed
the ten-publication encoder check. Replaying all 25 events through the online
V1 encoder reproduced offline observations and candidate cues with maximum
absolute difference zero. This is only software/input-contract qualification;
the pilot's source estimate is not used as a scientific result or route
selection criterion. The verified pilot archive is counted as one of the 48
planned coverage episodes.
