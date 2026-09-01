# CPIR factorial offline audit — blocked before outcome read

Date: 2026-09-01

## Frozen verdict

`CPIR_FACTORIAL_OFFLINE_INVALID_FULLGRID_COVERAGE_NO_CLOSED_LOOP`

The requested H01/H02/H03 × seeds0–9 factorial did not reach posterior or
task-metric evaluation. The already-generated full-grid banks pass their
contract, file-integrity, House, member-count, time-count, and source-update
schedule checks, but they do not cover every trajectory sample required by
M2's persistent sensor state.

Under the user's downstream-increment rule, M2 cannot be retained as a main
module from this input. The frozen module marker is:

`M2_PERSISTENT_SENSOR_MAIN_MODULE_NO_GO`

M1 and M3 are not assigned performance verdicts from this run because the
common five-arm factorial input is invalid. No VM Release parity, H01 seed1
closed-loop smoke, or formal 9-condition closed loop was started.

## Code state

- authoritative reset point: `57cd4e41bb02f5e3e85b3d3a7986c9e4ff72632d`;
- factorial runtime/evaluator/preregistration commit:
  `b3eab73e844bc4963f5a15223255e0a603265648`;
- fail-closed motion-coverage interface audit commit:
  `0141bb8844a04225796ff1b0c0cc767ab8693e03`.

The new runtime factor is only `cpir_m1_m3 = raw + stop-resolved`. Bank-free
selftests prove the intended matrix:

| Arm | Sensor event | Score |
|---|---|---|
| F00 | raw | count-only |
| F01 | raw | stop-resolved |
| F10 | persistent | count-only |
| F11 | persistent | stop-resolved |

The four bank-free tests passed on the VM before coverage inspection:

- `CPIR_FACTORIAL_MODE_SELFTEST=PASS`;
- `CPIR_FACTORIAL_OFFLINE_SELFTEST=PASS`;
- `CPIR_THREE_MODULE_BANK_FREE_CONTRACT_SELFTEST=PASS`;
- `CPIR_FORMAL_RUNNER_STATIC_SELFTEST=PASS`.

## Frozen-bank preflight

All three independent integrity reports remain PASS. Bank-summary SHA-256:

| House | bank summary SHA-256 |
|---|---|
| H01 | `8bab8c2e5c39d091137beef5d2efe69eb2131be09c75efb1347f18411a776888` |
| H02 | `f00daf24c70771d95f945de098fed29e17cc72a763b000bdd281038383bd2845` |
| H03 | `736444246178d89432cfde5bc2f12699e7ec9d5600f2e11fa385e609fbfa68ab` |

The five common source-update schedules are valid for all 30 tapes. Coverage
fails only in motion, but M2 explicitly carries sensor state through motion,
so this is load-bearing rather than ignorable:

| House | missing motion samples | missing stop samples |
|---|---:|---:|
| H01 | 34 | 0 |
| H02 | 42 | 0 |
| H03 | 70 | 0 |
| Total | 146 | 0 |

Twenty-seven of 30 tapes contain at least one missing motion sample. H03's
first gap occurs before its first source update, so carrying the previous
state only after the gap does not avoid contamination.

Coverage report SHA-256:
`550fc3ab3ad3381a79ecd3e085fde0f2a19b03fd156774064d9bcbcaf2dc857e`.

## Why no fill or bank substitution is legal

An independent audit read the corresponding exact historical-route physical
values for every missing motion position across every source and predictive
member. They are not zero:

| House | values checked | exact nonzero | maximum / ppm |
|---|---:|---:|---:|
| H01 | 57,120 | 38,822 | 54.2854080 |
| H02 | 67,536 | 43,002 | 103.7621384 |
| H03 | 115,360 | 17,999 | 37.9774284 |

Therefore zero fill or skipping would change M2's frozen recurrence. The
audit then tested whether the historical-route bank could be an exact
sidecar. It could not: after scanning H01's 1,680 source/member shards, the
first overlapping counterexample was:

```text
carrier=quadtree_0_0_2_2, member=0, seed=0, sample=371
full-grid=0.0 ppm
historical-route=0.00298071070574224 ppm
```

This is expected when a cell-centre lookup bank and an exact continuous-pose
route query are not the same observation operator. Mixing them would change
M1 and invalidate the factorial.

- missing-value audit SHA-256:
  `58f09de047e189f5b089b055c4dc85e2a0def5738026554c49f32c6b3a8a1d8e`;
- overlap audit log SHA-256:
  `7d6a3f2bbc1f10b11ef1a752806e0c697541277fb963e4f366f521b6dd5a1731`.

## Scientific boundary

No A0 posterior, source truth, localization error, AUC, threshold time, or
module outcome was read. No GADEN run, neural training, parameter tuning,
zero fill, interpolation, nearest-cell substitution, or route-bank rescue was
performed.

The shortest valid continuation is to create and independently verify a bank
whose lookup support covers every sample consumed by M2's persistent state,
then rerun the unchanged preregistered factorial. Until that exists, parity
and closed loop remain unauthorized.
