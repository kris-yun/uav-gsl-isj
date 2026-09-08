# PMFS failure-first implementation checkpoint

Status: SUPERSEDED_BY_REAL_CLOSED_LOOP_NO_GO. See
`PMFS_CER_M12_CLOSED_LOOP_20260908.md` for the completed House123 seed12 result.
No M1/M2 efficacy or causal-identifiability claim is supported by that result.

## Implemented change

The development M1 keeps a normalized joint posterior:

`p_t(s,k) proportional to p_(t-1)(s,k) p(y_t | s,k,h_(t-1),a_t)`.

Marginalize k only after updating the joint state. In the executable wrapper k currently indexes fixed source-release rates, NOT learned transport regimes. Persistent k avoids an unintended model that redraws source strength independently at every observation. A synthetic switching-component counterexample matches exact batch marginalization; this does not establish the cause of previous House failures.

Predictions precede observations. Frames are immutable snapshots; timestamps cannot be scored twice; new wind enters the following prediction; residual state persists across update boundaries. Missing observations are neutral in the estimator and valid zero measurements remain evidence. The physical wrapper requires complete actual frames and does not impute missing sensor history. A candidate-independent context denominator is omitted because it cancels in normalized source odds.

No source truth or House identifier enters the estimator. Ordinary sequential Bayes and a causal temporal interface are not by themselves a new identifiable causal method. The Gaussian observation law and static release-rate assumption need real-data adequacy checks.

## Environment changes and verification

- Legacy launch sends GMRF to scenario/occupancy.yaml; qualified geometry names navigation_slice.yaml. The new opt-in launch guard checks exact map path/bytes, image, occupancy identity, height, seed/cadence, free-space start, helper and realization binding.
- Legacy reproduction defaults remain unchanged. New runs must supply cstar_environment_preflight, cstar_geometry_manifest, cstar_house and gmrf_map_yaml_file. Old unguarded launches are not qualified new runs.
- The independent live verifier had a hard-coded a16ffa3 commit. It now requires --expected-code-commit from an external run manifest, rejects malformed values and records its own hash.
- Local/VM: 7 joint-update regressions pass. VM: 22 environment tests pass. Three corrected map bindings accepted, three legacy map paths rejected.
- Fresh H01/H02/H03 stationary ROS probes each produced eight positive-stamp frames. Independent raw-file wind comparison passed, maximum absolute error 7.180059963252106e-09. Stored controlled-frame verification covered 8640 frames with zero numeric discrepancy.
- Probes load neither GMRF nor PMFS: no live planner/GMRF geometry or navigation claim.

## Not completed

1. New wrapper is not connected to PMFS sourceProbability. It has not controlled a flight.
2. Native-forward-law M1-only comparator is not implemented. The wrapper uses the physical M2 prior; calling it a clean M1-only arm would be incorrect.
3. Provider replays the whole prefix for every candidate/rate/request. Full-grid deployment needs equivalent incremental state and measured runtime, not a blind expensive launch.
4. Default VM gsl_actionserver_node is a broken symlink to /home/zyc/ros2_ws/build/gsl_server/gsl_actionserver_node. Older executables exist but have not been substituted as a current-source binary.
5. House123 seed12 240-second native/M1/M1+M2 runs have NOT started. Final error and distance AUC are unavailable.

Next milestone: current-source PMFS binary, stamp/geometry-bound posterior consumer, matched native-forward ablation and online-cost tests. Then live GMRF/planner geometry and House123 seed12 development screening. Do not expand a failed screen to multiseed or call exposed seed12 independent confirmation.

## Evidence and provenance

Evidence: evidence/cstar_joint_development_20260908, evidence/cstar_joint_environment_20260908, evidence/cstar_joint_live_20260908.

VM used an isolated copy of the prior tmpfs environment with explicit overlays, NOT a complete newly built HEAD archive. Declared reference commit: 484cac2828faf095372d352c3128c5a2e366bf34. Actual tested estimator/launch/verifier bytes are hashed in IMPLEMENTATION_STATUS.json and match local files. Environment code/inputs are bound in PREFLIGHT.json. Old evidence and protected banks were not overwritten or rebuilt. System disk remains nearly full; evidence from the new tmpfs copy was retrieved locally.
