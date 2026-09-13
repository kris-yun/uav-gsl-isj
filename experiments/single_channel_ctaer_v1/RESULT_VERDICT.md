# CTAER H03 seed11 result

## Frozen verdict

`CTAER_H03_NO_GO`

CTAER passed five of six preregistered checks.  It did not satisfy the
top-decile true-source rank, so the formula must not be tuned or integrated
into PMFS on this exposed trace.

## Result

| Arm | True-source rank | Normalized rank | MAP error |
|---|---:|---:|---:|
| Frozen TAORL forward score | 3,089 / 7,258 | 42.5520% | 4.9851 m |
| CTAER forward-minus-reverse | 804 / 7,258 | 11.0652% | 4.9557 m |
| Sign-reversed CTAER control | 6,455 / 7,258 | 88.9348% | 8.4992 m |

The true candidate used the same forward-selected `tau=6.5 s` in both arms.
Its forward ordinal loss was `0.107174`, reverse loss was `0.164895`, and
reverse-minus-forward evidence was positive `0.0577214`.

CTAER therefore improved the true-source rank by 2,285 positions, beat the
sign-reversed control, and slightly improved the TAORL MAP endpoint.  This is a
strong component signal.  It is not a formal mechanism pass because the
registered top-decile boundary was missed by 78 rank positions, and the MAP
candidate remains in the same false region near `(4.3, 0.49)`.

## Scientific interpretation

The result supports the specific diagnosis that forward fit alone retained
substantial reversible/static ambiguity.  Candidate-wise forward/reverse
subtraction removes much of it.  It does not remove the dominant false source
mode, which has even stronger time-arrow contrast than the true candidate.

Consequently:

- do not return to transport-member consensus or backward trajectories; those
  incremental mechanisms already failed their own controls;
- do not relax 10% to 11.1% after reading the answer;
- do not call this cross-dataset, causal-source-localization, or main-innovation
  evidence;
- preserve CTAER as the strongest surviving component hypothesis and diagnose
  whether its false-mode advantage is stable across independent completed
  windows before defining any future mechanism.

## Provenance

- pre-result Git commit and verified remote ref:
  `40d73b5ab7c44ca9b5aa0ae51f030abba551e6fa`;
- formal result: `results/H03_SEED11_CTAER_GATE.json`;
- formal run count: one;
- no new House, seed, source-response bank, neural model, or PMFS run was used.

