# Reproduce this bounded control

This package is an Eq6-only reconstruction and a fixed-tree stored-history sensitivity study, not a complete ROS distribution or full paper replication. Read 本轮结论_zh.md first.

On Linux with g++ and Python+NumPy, compile `g++ -std=c++17 -O2 cpp/check.cpp -o eq6_check`; then run `./eq6_check --unit` and, for each fixture directory, `./eq6_check fixtures/A2_update_0 /tmp/A2_update_0_scores.csv` (the output filename must be new). The C++ runner reads only stored maps. Grid check: `g++ -std=c++17 -O2 cpp/grid_probe.cpp -o grid_probe && ./grid_probe`.

`python verify.py` checks all delivered file hashes. The saved Windows/VM paths in original provenance are historical identities, not required network resources. `prepare.py` is the original frozen-data preparation procedure and requires original local evidence; it is not an offline portable entrypoint. The guest runner is the original execution logger, not a portable ROS launcher.

The C++ formula fragments and original score body are derived from the pinned Sep18 source; minimal containers do not reproduce ROS/grid orchestration. The stored prediction maps and history are explicitly the 2026 corrected-wind diagnostic, with coefficient0.3 and adaptive tree frozen. Changing Eq6 may change adaptive refinement/actions; those are not simulated here. No importance sampling or new closed-loop gain is tested.
