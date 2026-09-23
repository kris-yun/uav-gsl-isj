# H01 ACI continuous-channel zero gate

Date: 2026-09-23

Status: **NO_GO_H01_ACI_CONTINUOUS_CHANNEL_ZERO_GATE**

Frozen continuous stream through source update 195.500 s:
- path samples: 977
- unique path cells: 66
- measured hits (> 0.1 ppm): 15, unique hit cells 15, moving-hit samples 15
- physical true-gas hits: 9, unique hit cells 9, moving-hit samples 9
- terminal candidates: 121

| source-blind score | truth rank |
|---|---:|
| Native PMFS reference | 76.00/121 |
| frozen static low-occupancy reference | 20.50/121 |
| **measured positive-hit support (primary)** | **22.00/121** |
| true-gas positive-hit support (physical diagnostic) | 16.00/121 |
| measured full-path Brier (secondary) | 17.00/121 |
| true full-path Brier (secondary) | 3.00/121 |
| measured hit-minus-miss contrast (secondary) | 21.00/121 |
| true hit-minus-miss contrast (secondary) | 16.00/121 |

## Circular-shift destructive null

- repetitions: 500
- null truth-rank median: 64.00
- null truth-rank 5-95%: 63.50-78.50
- fraction null as good or better than actual: 0.0060

The null circularly shifts the complete measured binary hit sequence against the unchanged robot path. Hit count, temporal clustering, sensor-memory pattern, path, dwell pattern, and all candidate mean hitMaps are preserved; only the location of effects along the path is destroyed.

## Predeclared gate

- measured hit-support truth rank < 20.5: **False**
- physical true-hit support truth rank < 20.5: **True**
- null as-good-or-better fraction <= 0.05: **True**
- **PASS: False**

The continuous pre-update effect locations do not pass the source-identity prerequisite for ACI on H01. Do not implement or tune an ACI smoother to rescue this case; move to a different mother mechanism.
