# Online numerical core VM verification

This is a real-VM compile/run of the existing ROS-independent online core,
not a closed-loop model result.

- `core_test.out`: `CTPI_ONLINE_CORE_V2_SELFTEST=PASS`; mass conservation,
  non-negative transport, wall isolation, advection, time convergence,
  prediction-before-observation ordering, 0.2 s sensor cadence and FOPDT
  prehistory checks.
- `clock_test.out`: `DUAL_CLOCK_UNIT_ONLY_PASS`; distinguishes native 0.5 s
  field integration from 0.2 s sensor time and rejects future wind, field gaps,
  altered durations and partial mutation after rejection.

VM compiler: `g++ -std=c++20 -O2`; no ROS node or bank was launched.

Executable SHA256:

`core_test` a71c31a18abea51f80e994b159288e82ca9f3cf7e6e13c8cf974d83006cbcbdf

`clock_test` 7e326d5e3063ebc095b1a8fbbf6125ea7c737bcb46b4c2241b3325bca1f1febf

Header SHA256:

`CTPIOnlineCoreV2.hpp` a1ef8c3876c4de24fc6f89bad9e94031387d24f37f36140b9f53aa32862d2718

`CTPIDualClockV2.hpp` c55900bd982cead4d7e5b4e331abe987d9c986b4073e79e0a2b7f9c056ebcede

These tests establish numerical/clock invariants only. They do not establish
that M2 improves source localization, that the physical prior is calibrated,
or that ROS observations are consumed by a deployed CPO implementation.
