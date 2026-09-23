# Native PMFS recovery runner checkpoint

**Status:** isolated source staged and Release binary built. R0 runtime parity has not yet been claimed.

The source staging script verifies all 19 official PMFS implementation files against the local ZIP's per-file SHA256 manifest before copying them into a **new** `gsl_server` package. It starts from a copy of the VM's ROS package so existing VGR/ROS interfaces remain available, replaces the entire PMFS directory, and changes only the following in the isolated package:

- `USE_GADEN ON`, `USE_GUI OFF`, and only Common + PMFS targets enabled in CMake;
- an unconditional SCIM reference removed from the copied action-server dispatcher because that experimental target is excluded;
- fail-closed `/wind_value` query checks and passive query, source-update, measurement-event, measured-map and candidate-geometry CSV exports in official PMFS source.

No original `/home/zyc/ros2_ws/src/GSL` file, frozen runner, R2 archive, or previous run root was edited. The main Native launch contains only VGR simulation, the isolated PMFS action server, and the benchmark runner. It does not launch GMRF or pass PFDI/TNQC/TADM/P2 controls. The PMFS branch itself throws if `useWindGroundTruth` is false or if `/wind_value` is unavailable, fails, has the wrong shape, or returns nonfinite values. The runner validates service type and source-blind response before launch. At each completed source update, the verifier compares every free-cell internal wind vector to the last preceding service response and records component and angular error plus wind magnitude distribution.

VM staging root: `/home/zyc/native_pmfs_recovery_v1`. Build command is in `reference/build_native_pmfs_recovery_20260923.sh`; the initial successful build was Release, serial, with `USE_GADEN=1` present in the compile command. The output binary SHA256 was `f9fb6c915fe36fd3ec85146bed0c04a0a826c86cc9f9b4dfa8f3d9098e05e5fc`. Isolated PMFS source SHA256 values at that build:

| File | SHA256 |
| --- | --- |
| `PMFSLib.cpp` | `1c15c5a1f876fbca35f560f502344599deaedfb2de749d4fdecdadaf4a945949` |
| `PMFS.cpp` | `32392bc2e18dacfd7502c648f74f499bd6d42c924ace6eda831a2c60f08aee3a` |
| `internal/Simulations.cpp` | `be015c6cdd049e30be3d0c40743f1123d910ecef6cdcc43f5aadbfefe0d6937b` |
| `gsl_server.cpp` | `ca857607460db0de81f3f254be38935b1335f99814e297b4be2e37644855396d` |
| `CMakeLists.txt` | `b8526621b07edc2b7e4e9f882c80f6bbed1f871dd0187fcc50883bee756e6fdd` |

The recorded source hash and binary are a build checkpoint, not runtime proof of the wind branch. R0 must still show the explicit `NATIVE_RECOVERY_WIND_PATH=GADEN_GROUND_TRUTH` marker, positive service query count, zero fallback/failure, and numerical parity. The runner keeps the 300 s simulation budget for all normal cases; R0 is labeled as a smoke test and stops only after the first PMFS source update has completed. All runs use unique new directories under the recovery root.
