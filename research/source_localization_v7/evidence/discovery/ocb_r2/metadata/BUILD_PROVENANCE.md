# OCB-R2 isolated generator build provenance

- VM: Ubuntu 22.04, GCC `11.4.0`; ROS 2 Humble overlay from `/opt/ros/humble`.
- Isolated source/build/install: `/home/zyc/ocb_r2_seeded_gaden/{src,build,install}`.
- Parent source commit: `17adaf650a4f11d29aa049cf0661e9f9ea2e636f` (`MAPIRlab/GADEN`).
- Core source commit: `9e93c36ae1af74f6a62c42f1c9d7b813153222ed` (`MAPIRlab/gaden_core`).
- **These source checkouts are dirty.** Exact tracked deviations are frozen in
  `UPSTREAM_PARENT_DIRTY.patch` (SHA256
  `5c2b3c543ffd1ed082efd686ba05491b6aa9acc02bb4b834b3ab47186a9c6f6e`)
  and `UPSTREAM_CORE_DIRTY.patch` (SHA256
  `6a1304d213dd84e70cd6b440e66db3c98e01f78b2c138a849799a117973dd01c`).
  The latter includes the OCB-R2 timeline insertion. Historical HCMC source
  changes predate this qualification; the new diff alone is separately saved
  as `research/ocb_r2/READONLY_TIMELINE.patch` (SHA256
  `e875f61355ced7e17d490d2f28eb82951c28c3372060358e805fa7ebcef067d1`).
- `MathUtils.hpp` SHA256
  `0a30c798bd4c413adc30748e70cb643f32a65c570d08b41ac0df2c5aabb2cfff`;
  `RunningSimulation.cpp` SHA256
  `98b9ab100d7cf220524ecb5c15a150da91016407fe5452a4700201164910f995`.
- Binary: `/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator`, SHA256
  `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`.
- Built in Release mode with a serial colcon executor. An initial isolated
  link lacked `libbsc.so` search path; the retry set `LIBRARY_PATH` and
  `LD_LIBRARY_PATH` to the isolated built libbsc directory and passed the
  matching `-Wl,-rpath-link` linker flag. No source/physics was changed to
  resolve this link issue.
- Existing `/home/zyc/ros2_ws/{src,build,install}` and HCMC binary were not
  modified. The only runtime env changes are explicit `GADEN_RNG_SEED`,
  `OMP_NUM_THREADS=1`, `OMP_DYNAMIC=FALSE`, `OMP_PROC_BIND=TRUE`, and library
  lookup for the isolated build.
- The source diff from the prequalification HCMC copy is solely the
  read-only `RECORD_TIMELINE.tsv` writer. It executes after each scientific
  result record and does not call RNG or change solver state/order.

The pre-plume wind-format failure is retained in
`OCB_R2_PREFLIGHT_WIND_FORMAT_ERROR.log`. The approved old `999` split-double
wind files were layout-converted to native v3 interleaved floats in a new
isolated directory. All 33 inputs and 11 outputs passed independent SHA256
verification. No original wind asset was modified.
