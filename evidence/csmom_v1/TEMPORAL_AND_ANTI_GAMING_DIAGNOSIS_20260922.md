# CS-MoM V1 — temporal and anti-metric-gaming diagnosis

Date: 2026-09-22  
Status: **MAIN MECHANISM REMAINS POSITIVE; RELEASE/IDENTIFIABILITY LAYER UNRESOLVED**

## 1. Temporal replay

CS-MoM was replayed at every exported source-update snapshot, not only the terminal bank.

The blocking H01 seed0 case is not uniformly negative.

H01 seed0:

| t (s) | native error (m) | CS-MoM error (m) |
|---:|---:|---:|
| 65.6 | 3.81 | 4.00 |
| 118.8 | 5.85 | 4.62 |
| 172.0 | 5.54 | 3.16 |
| 222.6 | 5.47 | 6.95 |
| 275.8 | 5.53 | 7.21 |

The robust inference is strongly beneficial at 118–172 s and flips after the 172→222.6 s update.

Therefore the terminal failure is not evidence that the robust statistic never carries source information.

## 2. Low-signal abstention does not explain the failure

The H01 seed0 flip is not caused by a late period without gas.

Recent-window measured-gas hit fraction (>0.1 ppm):

- through 172 s interval: about 27%
- 172→222.6 s interval: about 75%
- 222.6→275.8 s interval: about 90%

A simple “low gas support” guard is therefore rejected.

## 3. Pure-MoM failure morphology

At the failing late H01 seed0 updates, some wrong candidates have:

- very small median block risk;
- very large full-support mean loss;
- a minority of blocks with extremely large losses.

This is exactly the regime in which a 50%-breakdown median can regard rare but severe contradictions as contamination.

However, this morphology alone is not a valid guard: successful House02/House03 cases can show equal or larger mean/median tail ratios.

## 4. Standard Huber M-estimator control

A fixed classical Huber block-location estimator was tested:

- Huber kappa = 1.345;
- robust scale = 1.4826 × MAD;
- same 4×4 correlation-scale blocks;
- same 16 block origins;
- median aggregation across origins.

Result:

- pooled error = about 3.882 m;
- pooled reduction = about **30.12%**;
- 5/6 non-worse;
- 0/6 false-confident collapse.

H01 seed0 remains bad at about 7.18 m.

Thus the counterexample is not fixed by merely replacing block MoM with a smoother robust M-estimator.

## 5. Offset-consensus gate rejected

Several source-blind block-origin consistency diagnostics were tested:

- modal top-candidate vote fraction;
- fraction of offset-top candidates within one block width of the modal candidate;
- spatial spread of offset-top candidate centers;
- median top-two offset score gap;
- number of unique offset-top candidates.

H01 seed0 is not uniquely separable from the successful cases by these diagnostics.

No threshold was tuned or promoted.

## 6. Anti-metric-gaming diagnostics

CS-MoM is not only flattening the posterior to improve the authoritative top-5% metric.

Across the six final R2 banks:

### MAP error

- native mean: **5.526 m**
- CS-MoM mean: **4.321 m**

### Full-posterior expected source distance

- native mean: **5.559 m**
- CS-MoM mean: **5.185 m**

### Nearest-to-truth candidate rank

- native mean rank: **132.5**
- CS-MoM mean rank: **52.5**

### Posterior mass near truth

Mean mass within 1 m:

- native: effectively zero
- CS-MoM: **4.03%**

Mean mass within 2 m:

- native: effectively zero
- CS-MoM: **15.02%**

Even in H01 seed0, whose endpoint worsens:

- nearest-truth candidate rank improves from **110 to 33**;
- mass within 1 m becomes **3.92%**;
- mass within 2 m becomes **9.34%**.

Therefore the robust evidence layer genuinely restores source-supported probability that the native multiplicative likelihood had effectively annihilated.

The remaining failure is primarily a **mode/release ordering problem**, not absence of true-source recovery.

## 7. Current scientific interpretation

The evidence now separates two problems:

1. **Evidence pathology:** correlated/misspecified PMFS cells are multiplied as if they were independent witnesses, producing false-confident annihilation of true-source support.
2. **Decision/release pathology:** after robustification restores broader true-source support, a wrong competing mode can still outrank it in some cases.

The first problem currently has strong positive evidence for correlation-scale robust inference.

The second problem must not be patched using case truth.

A second-stage identifiability/release mechanism is admissible only if it is:
- source-blind;
- fixed before endpoint evaluation;
- justified by a separate modern theory line;
- shown to improve or abstain on the temporal sequence without sacrificing the five positive terminal cases.

## 8. Decision

**Do not demote the robust-statistics mother idea.**

**Do not authorize closed loop.**

Next work should search for a principled mode-release / partial-identification mechanism rather than further tuning MoM/Huber constants.
