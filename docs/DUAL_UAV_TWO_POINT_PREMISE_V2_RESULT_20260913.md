# Dual-UAV same-frame two-point premise result

Date: 2026-09-13

Branch: `codex/dual-uav-two-point-premise-20260913`

Pre-gas freeze SHA: `8ff978951fbbab18b6c5c4451315a6fee18252ba`

## Evidence integrity

The experiment reused the 12 audited House02 raw caches. It did not run the filament simulator or create a GADEN dataset. Two receiver coordinates were queried from the same frame at each of 750 route times for every source-wind pair. The resulting 12 traces contain 9,000 synchronized rows and 18,000 position queries over frames 0 through 299.

The independent trace audit reproduces all coordinates and both persistent FOPDT channels exactly:

```text
trace count                         = 12/12
row count                           = 9000/9000
same-frame/timing errors            = 0
maximum route-coordinate error      = 0
maximum independently replayed FOPDT error = 0
TRACE_INTEGRITY_AUDIT               = PASS
```

## Per-wind source observability

The preregistered primary representation is `SIGNED_INCREMENT = z_plus-z_minus`. All centered four-source matrices have numerical rank 3, but the weakest source direction is far below the required `sigma3/sigma1 >= 0.05` gate.

| Wind | Signed rank | Signed sigma3/sigma1 | Ordinary D2 sigma3/sigma1 | Signed minimum pair distance | Gate |
|---|---:|---:|---:|---:|---|
| W_fast | 3 | 0.001345 | 0.001359 | 1.1073 | FAIL |
| W_slow | 3 | 0.000683 | 0.000683 | 0.4894 | FAIL |
| W_altfast | 3 | 0.001384 | 0.001419 | 0.8823 | FAIL |

The failure is not caused by an empty dataset. `S_truth` has about 470 exposed samples in every wind and `S_k10` has 171 to 291. The source response is strongly imbalanced: `S_k01` has only 7 to 8 exposed samples and `S_k22` has 0 to 20. The two-point difference therefore has a nominal third dimension, but that dimension carries only about one thousandth of the dominant source contrast and does not meet the physical observability premise.

## Internal held-wind identity

Prototypes use only `W_fast` and `W_slow`; `W_altfast` is evaluated without tuning.

| Representation | Rank-1 sources | Minimum margin |
|---|---:|---:|
| S1 plus | 1/4 | -23.7078 |
| S1 minus | 2/4 | -0.00755 |
| Ordinary D2 | 1/4 | -19.9690 |
| Signed increment | 2/4 | -2.24885 |
| Squared structure | 2/4 | -1.41283 |

The signed increment does not satisfy the required 4/4 held-wind source identity.

## Destructive controls and ordinary D2

Position-label swap reduces signed-increment identity to 1/4 and collapsed baseline reduces it to 1/4. The preregistered 5 s time mismatch increases the result from 2/4 to 3/4 and improves the minimum margin from -2.24885 to -0.91744. Thus the synchronized spatial pairing is not consistently load-bearing.

Signed increment improves held-wind rank count over ordinary D2 (2/4 versus 1/4), but both fail. It also has a slightly lower worst-wind structural ratio than ordinary D2 (`0.0006832433` versus `0.0006832438`). The strict same-data ordinary-D2 advantage gate is therefore false.

## Scientific decision

```text
TWO_POINT_APERTURE_SOURCE_OBSERVABILITY = NO_GO
HELD_WIND_SOURCE_IDENTITY = FAIL_2_OF_4
NEGATIVE_CONTROLS = FAIL_TIME_MISMATCH_IMPROVES
ORDINARY_D2_COMPARATOR = NO_STABLE_SIGNED_ADVANTAGE
FINAL_VERDICT = B. STRUCTURAL_COMPLEMENTARITY_ONLY_NO_SOURCE_IDENTITY
```

This result rejects the current fixed 2 m, map-constrained House02 route as support for the main two-point algorithmic innovation. It does not show that two receivers are useless: the hardware adds measurements, and signed differencing changes some held-wind decisions. It shows that the proposed turbulent two-point operator does not yield strong, wind-stable source identity on this preregistered test. No causal localization or stochastic out-of-distribution claim is authorized.
