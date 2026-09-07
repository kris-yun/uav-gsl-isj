# C++/Python physical-prior parity — 2026-09-07

This is a bounded algebraic parity fixture, not a House-data result. Both
implementations start from a three-cell free 1-D grid with `dx=1`, diffusion
`0.1`, uniform wind `(0.5, 0)`, and the V2 finite-volume update duration
`0.2 s`. The first step injects source rate `1.0`; the second has zero source
rate. The C++ side is `tools/selftest_ctpi_python_parity.cpp` compiled on the
connected VM against `CTPIOnlineCoreV2.hpp`; the Python side calls the same
declared update law with `duration=0.2`.

Observed outputs are byte-normalized below (trailing whitespace is ignored):

```text
C++:    0.20000000000000001 0 0
C++:    0.17600000000000002 0.024 0
Python: 0.20000000000000001 0 0
Python: 0.17600000000000002 0.024 0
```

Result: **ALGEBRAIC_PARITY_PASS**. The fixture does not prove parity for
nonuniform wind fields, walls, long horizons, sensor FOPDT history, or ROS
runtime bindings. Those remain required before the physical prior can be used
as a qualified House-data baseline.

The same VM build also exercised the C++ `Fopdt(tau=1.2, dead=0.4)` against
the Python `_Fopdt` implementation for five successive `dt=0.2` inputs
`[1, 2, 0, 4, 5]`; `fopdt_cpp.out` and `fopdt_python.out` match exactly at
the printed precision. Result: **FOPDT_PARITY_PASS**.

Identities at capture:

- `CTPIOnlineCoreV2.hpp` SHA-256:
  `a1ef8c3876c4de24fc6f89bad9e94031387d24f37f36140b9f53aa32862d2718`
- `physical_prior.py` SHA-256:
  `eca38b755c247372a0bd7b5df40faa4eb3bc534b55a872831f15c2b30f7fa663`
- VM compile command: `g++ -std=c++20 -O2 -Wall -Wextra`
