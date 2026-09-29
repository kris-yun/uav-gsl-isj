# Historical replay parity gate: not entered

The signed recovery task permits one GADEN simulation only after an executable with the historical source fingerprint has been found or rebuilt, and only with the same historical plume RNG state. Neither prerequisite was met. The eight retained ELF candidates include no established `MATCH`; six point to a different ROS2 float-clock strict-interval source and two have no recoverable corresponding source. The isolated historical-source CMake configure halted at absent ROS1 `catkin`; it did not compile an executable. The historical source seeds C `rand` and per-thread Boost RNGs from wall time, and the old result files do not serialize those seeds.

Accordingly **no simulation was launched**. `HISTORICAL_REPLAY_PARITY.tsv` records all planned record groups as `NOT_RUN`; `exact_hash_match`, numerical differences and 25-record wind parity are **not measured**, rather than being assigned invented zeros. Previous read-only checks of 25 historical file headers remain valid evidence for the archived *source candidate* but are not a replay result.

`CURRENT_1803_BINARY_NOT_ELIGIBLE_FOR_OCB_R1_REFERENCE` and `OCB_R1_RUN_HOLD` remain in force. No new plume seed, 96-run benchmark, nearest-time substitution, interpolation, or change to the existing ROS2 workspace occurred.
