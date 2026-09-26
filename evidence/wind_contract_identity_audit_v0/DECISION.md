# Wind contract identity audit decision

`HOLD_Z_OR_TIME_SEMANTICS_UNRESOLVED`

- Existing wind states: 11 CSV and 11 binary files.
- Primary match z: 0.30 m, proven by historical trace and launch.
- Candidate-forward z: 0 m, proven by recovery launch and PMFS runtime log.
- Forward server always queries CSV state 0, independently of time.
- Same-numbered wind values agree at all 44 audited sensor-height state/site pairs.
- The frozen single-state matching list is diagnostic, not a proven coherent sequence.
- Ten-reading mixed-state averaging reproduces the event values closely, but
  historical ROS receipt windows cannot be uniquely assigned from existing logs.

This is an event/time assignment HOLD, not unknown height. All frozen matcher
outputs are retained; no new decision threshold or time assumption was added.
See ADAPTER_CONTRACT.md for source lines, limitations and complete reasoning.

No simulator or localization calculation was run. Stop after packaging.
