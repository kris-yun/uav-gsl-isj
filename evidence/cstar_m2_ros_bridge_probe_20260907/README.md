# Real ROS/DDS M2 bridge probe — 2026-09-07

The connected VM ran `tools/cstar_m2_ros_bridge_probe.py` in an isolated
`ROS_DOMAIN_ID=72`, `ROS_LOCALHOST_ONLY=1` domain using the installed real ROS
message types (`PoseWithCovarianceStamped`, `GasSensor`, `Anemometer`). Three
stamped frames were published in scrambled topic order. The bridge joined the
zero bootstrap and two positive frames by stamp, armed a physical-prior route
law before each positive frame, and completed the horizon without a pending
prediction.

Result: **ROS_M2_BRIDGE_WIRING_PASS_NOT_CLOSED_LOOP**

```json
{"joined_frames": 3, "predictions": 2, "observations": 2}
```

This proves ROS/DDS callback wiring, stamp joining, prediction-before-
observation, and the physical-prior provider crossing the online boundary. It
does not run a simulator, a controller, a House, or a localization comparison;
therefore it is not an M2 predictive/closed-loop pass.

Captured identities:

- `cstar_m2_ros_bridge.py` SHA-256:
  `ac70ffd8a1949c3262b18eae891a36ce9eb4228a075873fa8c6df48c326cd3ad`
- `cstar_m2_ros_bridge_probe.py` SHA-256:
  `d944a18e1f0b9f0cb14d508e862d51b2f4291fde62c4c2555b349735c3d08453`
- `physical_prior.py` SHA-256:
  `1d3f26db40ddd7d07b8f46c571301200b2b7a5e5cb69175879f866d04c08306b`
