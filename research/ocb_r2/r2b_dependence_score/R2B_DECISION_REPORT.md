# OCB-R2 R2B decision report

Decision: **OCB_R2_R2B_DEPENDENCE_SCORE_NO_GO**

The frozen exact-Q lag1–3 binary Variogram dependence factor does not amplify the prior R2 factor. No new simulation, continuous scoring, learned SC-MPDR model, confirmation, House03, R3 or closed loop was run.

| Scope | Frozen R2 Energy factor | R2B Variogram factor |
|---|---:|---:|
| All targets | 53/64 (82.8125%) | 35/64 (54.6875%) |
| House01 | 26/32 | 19/32 |
| House02 | 27/32 | 16/32 |

Rescues: **4**; harms: **22**. Exact one-sided discordant-target binomial p: `0.9999560117721558`. The protocol treats target pairing as an operational score comparison; physical source/context grouping remains the mechanism stability unit.

Positive group means: **7/16**; positive context means: **5/8**. Exact 8-context sign-flip p: `0.64453125`. House01 group median: `2.2862368541367792e-05`; House02: `-0.0010851051668952904`. Seven of eight leave-one-context-out medians are negative.

## Eight contexts

| Context | House | Wind | Gas | ES correct / 8 | VS correct / 8 | Mean Delta_VS |
|---|---|---|---:|---:|---:|---:|
| X00 | House01 | 1,3-2,4_fast | 13 | 5 | 5 | -0.00035237 |
| X01 | House01 | 1,3-2,4_slow | 13 | 7 | 4 | 0.00007716 |
| X02 | House01 | 2,4-1_fast | 10 | 8 | 5 | 0.00100823 |
| X03 | House01 | 2,4-1_slow | 10 | 6 | 5 | 0.00019547 |
| X04 | House02 | 3,5-1_fast | 10 | 5 | 5 | 0.00001543 |
| X05 | House02 | 3,5-1_slow | 10 | 7 | 6 | 0.00101337 |
| X06 | House02 | 4,5-3_fast | 13 | 7 | 3 | -0.00126286 |
| X07 | House02 | 4,5-3_slow | 13 | 8 | 2 | -0.00156636 |

## Sixteen source-context groups

| Context | Source | ES correct / 4 | VS correct / 4 | Mean Delta_VS |
|---|---|---:|---:|---:|
| X00 | House01_configured_1 | 2 | 3 | 0.00062300 |
| X00 | House01_configured_2 | 3 | 2 | -0.00132773 |
| X01 | House01_configured_1 | 4 | 3 | 0.00073160 |
| X01 | House01_configured_2 | 3 | 1 | -0.00057727 |
| X02 | House01_configured_1 | 4 | 4 | 0.00321616 |
| X02 | House01_configured_2 | 4 | 1 | -0.00119970 |
| X03 | House01_configured_1 | 4 | 4 | 0.00118484 |
| X03 | House01_configured_2 | 2 | 1 | -0.00079390 |
| X04 | House02_configured_1 | 3 | 1 | -0.00080304 |
| X04 | House02_configured_2 | 2 | 4 | 0.00083390 |
| X05 | House02_configured_1 | 3 | 2 | -0.00136717 |
| X05 | House02_configured_2 | 4 | 4 | 0.00339392 |
| X06 | House02_configured_1 | 3 | 1 | -0.00311043 |
| X06 | House02_configured_2 | 4 | 2 | 0.00058471 |
| X07 | House02_configured_1 | 4 | 1 | -0.00159922 |
| X07 | House02_configured_2 | 4 | 1 | -0.00153349 |

## Omission and arithmetic verification

The four synchronized alternative-reference omissions produce 35/64, 36/64, 31/64 and 36/64. Their House02 and pooled group medians are all negative. No diagnostic lag or stratum is allowed to rescue this result.

Two full scoring/aggregation passes are byte-identical. An independent integer-arithmetic implementation checked all 512 candidate scores under the 256 target/alternative-omission combinations, all 16 group means and both exact tests. Maximum Delta discrepancy: `1.1275702593849246e-16`; **zero sign or tie mismatches**. The exact empirical product is also checked against all K² cross-realization pairs in the scorer.

## Interpretation and stop

This NO-GO applies to the preregistered Variogram factor and the Energy-insensitivity amplification hypothesis. It does not replace the frozen R0/R1/R2 results or establish that all temporal dependence estimators fail. SC-MPDR remains an untrained algorithm candidate. Any continuous-channel or learned ratio test requires its own later authorization and freeze.

Protocol source commit: `8281f5d4dccd485c411c2529d430fa51119d2df7`. Scorer freeze commit: `0384fff2`. Nine scientific amplification conditions fail; deterministic repeat passes. STOP after evidence packaging.
