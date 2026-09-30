# OCB-R2 R2A matched-window memory audit

**Decision: `OCB_R2_R2A_MZ_MATCHED_WINDOW_HOLD`.** The H3–H1 effect remained positive in the pooled and both House group medians, but it missed the frozen group-count and exact sign-flip gates. The R2 Gate B candidate-wise broad-memory path factor remains frozen and was not retested here.

## Input and common-support contract

R0/R1/R2 input and deterministic-repeat hashes passed parity. The analysis reused only the 64 frozen binary `10×30` H01/H02 discovery tensors. Each held-out target used the other three realizations of its truth source. H1, H2 and H3 all predicted the identical seven future slots `3..9` from identical anchors `t=2..8`; only the available history length changed. No target was extracted again.

Two complete scoring passes produced byte-identical results in all seven scientific output files. Independent finalization checked all **448** anchor rows against 64 target means, 64 target values against 16 groups, 16 groups against eight contexts, the House medians, and the 256-configuration exact sign-flip reference.

## Frozen primary gate

| Condition | Result | Required |
|---|---:|---:|
| House01 median source×context `D_MZ_COMMON` | +0.002282 | >0 |
| House02 median source×context `D_MZ_COMMON` | +0.000397 | >0 |
| Pooled median | +0.001389 | >0 for HOLD rather than NO_SIGNAL |
| Positive source×context groups | **10/16** | ≥12/16 |
| Positive context means | 6/8 | ≥6/8 |
| Leave-one-context-out pooled medians | all positive | all positive |
| One-sided exact 8-context sign-flip | **0.06640625** | ≤0.05 |

The two failed conditions fix the `HOLD` label. Relative to the original R2 Gate A, which used different eligible prediction times for H1 and H3, the matched-window House medians decreased from +0.006426/+0.003682 to +0.002282/+0.000397. This is a descriptive comparison of the frozen calculations, not a new rescue test.

## Descriptive anatomy

On the common prediction support, pooled group medians of predictive gain were H1 **0.015873**, H2 **0.017758**, and H3 **0.018155**. This monotonic pooled pattern did not rescue the primary gate. The per-anchor mean H3–H1 effect was negative at anchors 2 and 8; context means were negative for House02 `3,5-1_fast` and `4,5-3_fast`. The slow stratum was more consistently positive than the fast stratum. These observations are diagnostics only; they were not used to adjust windows, weights or thresholds.

## Scientific boundary

R2A removes the different-prediction-time confound from the nearest-history physics diagnostic. It does **not** establish stable cross-context evidence that H3 improves next-snapshot prediction over H1, so Mori–Zwanzig or projection-induced non-Markovian closure should not be promoted as the central physical claim on this gate. It also does not negate the separately established R0/R1 cross-time dependence or R2 Gate B candidate-wise path evidence. No prospective multi-source panel, confirmation, House03, learned model or closed loop was run.

Target, group, context, anchor and two-pass evidence are under `evidence/ocb_r2/r2a_matched_memory/`.
