# OCB-R1 historical simulator recovery R1

## Frozen boundary

The pinned 1803-record ROS2 binary is `CURRENT_1803_BINARY_NOT_ELIGIBLE_FOR_OCB_R1_REFERENCE`. This audit did not use nearest-time alignment, interpolation or save-cadence changes to release OCB-R1.

## Existing executable search

`EXECUTABLE_CANDIDATES.tsv` inventories eight actual ELF `filament_simulator` files under `/home/zyc`, including build and install copies in the HCMC, PF-DEI reference/current and RMFE directories. It records realpath, size, mtime, SHA256, ELF Build ID, linked libraries, source root, source HEAD and fingerprint classification. The explicitly named Native/PMFS and `ros2_ws` locations contain no additional executable of this name. Six candidates have recoverable ROS2 source with the binary32 strict-interval writer, so they are `MISMATCH`. Two RMFE ELF files have no recoverable corresponding source and remain `UNKNOWN`, never `MATCH`. All eight link ROS2 `librclcpp`, rather than supplying a demonstrated build of the archived ROS1 source. **No eligible existing executable was found.** Date or file name was not used to promote one.

The frozen reference in `HISTORICAL_SOURCE_FINGERPRINT.tsv` is GADEN ROS1 commit `2b5d1218d25cf8af6a789e99cd57ab0db07bce8e`, the source candidate whose floor-bin writer yields 2000 records and whose wind-state replay matches all 25 inspected 2022 result headers. The fingerprint includes the clock, writer, wind/release/transport order, termination, both RNG mechanisms and the exact House02 ROS1 launch parameters. The original 2022 executable itself remains unlocated, so source-to-original-binary provenance is still conditional.

## Isolated rebuild assessment

Only after finding no `MATCH`, the exact archived `gaden_filament_simulator` package was copied via `git archive` into `/home/zyc/ocb_r1_historical_gaden_rebuild/source`. Its `.cpp` and header SHA256 agree with the frozen source object (`be0ec969...` and `266dfe48...`); the repository source and ROS2 `ros2_ws/build/install` were untouched. Before configuring, root had 2,603,962,368 bytes available, so this small source/CMake attempt preserved more than 1 GiB. Compiler: GCC 11.4.0; CMake 3.22.1; installed ROS: Humble only. The old CMake file requests C++11, OpenMP, Boost iostreams and ROS1 `catkin/roscpp` with visualization, standard, navigation and PCL packages. `cmake -S ... -B ...` failed at `find_package(catkin)` because `catkinConfig.cmake` is absent. Full log and toolchain record are included. **No executable was built and no existing environment was rebuilt.** Installing or adapting ROS1 would be a new infrastructure change, outside this frozen recovery attempt.

## Seed and replay gate

`RNG_SEED_PROVENANCE.md` establishes that the archived simulator does not accept a plume seed in the inspected launch: `main()` calls `srand(time(NULL))` and the OpenMP transport path separately initializes thread-local Boost `mt19937` from `time(0)`. Neither seed/state is serialized in the historical plume files. Thus the signed instruction to replay the **same historical seed** cannot presently be met. The one allowed historical simulation was therefore not started. `HISTORICAL_REPLAY_PARITY.tsv` correctly records `NOT_RUN` rather than fabricating a 2000-record/wind/concentration result.

## Decision

`HISTORICAL_SIMULATOR_RECOVERY_FAIL` under the signed same-seed parity contract: no matching executable, no feasible local ROS1 configure, and `seed_provenance=FAIL`. This does **not** imply the old scientific data are invalid; it says the proposed same-generator, same-realization recovery has not been established. `OCB_R1_RUN_HOLD` remains. No new seeds or GADEN runs were generated.
