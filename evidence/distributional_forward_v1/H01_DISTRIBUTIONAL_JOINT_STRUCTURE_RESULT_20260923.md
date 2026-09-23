# H01 distributional-forward joint-structure kill test

Date: 2026-09-23

Status: **NO_GO_H01_DISTRIBUTIONAL_JOINT_STRUCTURE**

Frozen observation: last 200 sensor samples before source update 195.500 s; threshold 0.1 ppm; observed hits 0/200; 20-sample block counts [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; 14 unique visited cells; 121 terminal candidates.

| score | truth rank |
|---|---:|
| Native PMFS reference | 76.00/121 |
| prior static low-occupancy reference | 20.50/121 |
| mean block-count distance | 56.00/121 |
| **joint block-CRPS (primary)** | **56.00/121** |
| multivariate Energy Score (secondary) | 56.00/121 |

## Joint-destruction null

- repetitions: 500
- null truth-rank median: 56.00
- null truth-rank 5-95%: 56.00-56.00
- fraction null rank as good or better than actual: 1.0000

The null independently circular-shifts each visited-cell occupancy trace. It preserves each candidatexcell 200-step occupancy count and each cell's circular autocorrelation, while destroying cross-cell relative plume phase. Thus the original mean-hitMap information survives the null.

## Predeclared gate

- joint CRPS truth rank better than 20.5/121: **False**
- null as-good-or-better fraction <= 0.05: **False**
- **PASS: False**

H01 does not support a load-bearing source-identity gain from joint plume organization beyond the mean hitMap under this frozen test. Do not tune block size, threshold, phase weighting, or score coefficients to rescue H01.
