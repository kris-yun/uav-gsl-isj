# Stamped online ingress V2

Status: `ROS_INGRESS_PROBE_PASS_NOT_CLOSED_LOOP`.

- New input adapter: `closed_loop/ctpi/ctpi_v2_ingress.py`.
- Pure ordering test: `tools/selftest_ctpi_v2_ingress.py`; seven tests pass on Windows and VM Python. Includes all six within-frame callback orders across 1,201 synthetic stamped frames, exact coordinate pairing under cross-topic skew, identical t=0 repetition, missing first sample, duplicate/gap, malformed values, changed t=0, unreceived horizon tail and bounded pending queue. This is message plumbing, not a gas/source world or a 240 s task run.
- Real ROS2 Humble/DDS test: `tools/ctpi_v2_ingress_ros_probe.py`, invoked with `tools/run_ctpi_v2_ingress_ros_probe.sh`, passes in localhost-only domain 187. Four stamped test frames (0, 0.2, 0.4, 0.6 s); t=0 readiness before positive samples; published order wind/gas/pose; validates exact aligned output and completion marker.
- Original VM `/home/zyc/ros2_ws/install/olfaction_msgs` points to missing build artifacts. The first probe could not import message types; no experiment was launched. `tools/build_ctpi_v2_ingress_messages.sh` rebuilt ONLY `olfaction_msgs` against `/opt/ros/humble` into `/home/zyc/CTPI_ONLINE_CORE_V2_20260905/message_install`. Build: one package completed successfully. No global ROS install or legacy algorithm edits.

`ROS_INGRESS_PROBE.json` and `frames.jsonl` are copied from the actual probe output, not hand-authored PASS flags.

## Pause-aware revision R2 (current code)

Further VM inspection found that planner pauses republish identical positive-stamp messages, not just t=0 messages. The first adapter would reject a valid pause. The corrected adapter ignores an identical repeat of the latest message on each topic (counts it in the audit, adds no evidence); conflicting same-stamp values, older replay and gaps still fail closed. Eight CPU tests now pass on Windows and VM. The real ROS probe was rerun with all three topics repeated at t=0.2: four unique frames, exactly three ignored repeats, terminal marker present. See `ROS_INGRESS_PROBE_R2.json` and `frames_R2.jsonl`; original R1 outputs remain untouched.

R2 SHA-256, independently matched between local and VM:

```text
88770ff52fe34a63da03466e7ce346d154a8291cd53228d8bfa498e9fe72ba23  closed_loop/ctpi/ctpi_v2_ingress.py
11cb472e34baacae6aaee20a077e7a856820329e78ec8a319b9bda0d42da3867  frames_R2.jsonl
```

## Not proven by this test

No real VGR simulator, source estimator, full wind field, transport model or controller was connected. `/ctpi_v2_ingress_ready` proves only aligned initial **input** availability; a future launcher must also wait for estimator/geometry/wind-model readiness. This node does NOT call `/start_simulation`. Same-stamp gas, pose and local wind are recorded, but same-stamp wind must not be fed backwards into predictions for earlier intervals. No covariance, field freshness or causal identifiability claim is inherited from this test.

Candidate transport still needs unknown pre-existing plume state and ventilation treatment. M1 causal contribution is still under mechanism review. No new House run was started; no multiseed batch is authorized.

VGR-specific bootstrap warning: on raw/GADEN backends, the t=0 local wind message is an initialized zero cache before the first advancing frame query. It is NOT measured zero wind. The t=0 frame records supplied initial state for alignment only, never source likelihood evidence or a calibrated wind snapshot. Input readiness alone must not start a predictor assuming a known zero wind field.
