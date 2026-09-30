# R2C signature-path discovery decision

Decision: **OCB_R2_R2C_SIGNATURE_PATH_NO_GO**

The frozen RBF signature-kernel dependence residual did not reproduce or amplify the R2 source signal. All results are discovery-only and use the same 64 binary tensors. No generator, PMFS forward, continuous-channel scorer, neural model, confirmation, House03, R3, planner or closed loop was run.

| Scope | Frozen R2 Energy factor | R2C signature factor |
|---|---:|---:|
| All | 53/64 | 35/64 |
| House01 | 26/32 | 18/32 |
| House02 | 27/32 | 17/32 |

Paired **7 rescues / 25 harms**; one-sided discordant binomial p = `0.9997324736323208`.
Positive source-context group means: **9/16**; positive contexts: **7/8**. Exact context sign-flip p = `0.0078125`. Both House medians and all LOCO medians are positive, but these do not rescue the failed target, group and omission criteria.

## Context and source-group results

| Context | House | Wind | Gas | ES / 8 | SIG / 8 | Mean Delta_SIG |
|---|---|---|---:|---:|---:|---:|
| X00 | House01 | 1,3-2,4_fast | 13 | 5 | 4 | 0.004155521 |
| X01 | House01 | 1,3-2,4_slow | 13 | 7 | 6 | 0.008318648 |
| X02 | House01 | 2,4-1_fast | 10 | 8 | 4 | 0.033568816 |
| X03 | House01 | 2,4-1_slow | 10 | 6 | 4 | -0.004049502 |
| X04 | House02 | 3,5-1_fast | 10 | 5 | 4 | 0.032068739 |
| X05 | House02 | 3,5-1_slow | 10 | 7 | 4 | 0.040908519 |
| X06 | House02 | 4,5-3_fast | 13 | 7 | 5 | 0.028896852 |
| X07 | House02 | 4,5-3_slow | 13 | 8 | 4 | 0.017334520 |

| Context | Source | ES / 4 | SIG / 4 | Mean Delta_SIG |
|---|---|---:|---:|---:|
| X00 | House01_configured_1 | 2 | 4 | 0.120922850 |
| X00 | House01_configured_2 | 3 | 0 | -0.112611807 |
| X01 | House01_configured_1 | 4 | 3 | 0.020948002 |
| X01 | House01_configured_2 | 3 | 3 | -0.004310706 |
| X02 | House01_configured_1 | 4 | 0 | -0.072246739 |
| X02 | House01_configured_2 | 4 | 4 | 0.139384371 |
| X03 | House01_configured_1 | 4 | 1 | -0.046662513 |
| X03 | House01_configured_2 | 2 | 3 | 0.038563509 |
| X04 | House02_configured_1 | 3 | 4 | 0.108739582 |
| X04 | House02_configured_2 | 2 | 0 | -0.044602104 |
| X05 | House02_configured_1 | 3 | 4 | 0.276807181 |
| X05 | House02_configured_2 | 4 | 0 | -0.194990143 |
| X06 | House02_configured_1 | 3 | 2 | 0.010505099 |
| X06 | House02_configured_2 | 4 | 3 | 0.047288606 |
| X07 | House02_configured_1 | 4 | 0 | -0.118919342 |
| X07 | House02_configured_2 | 4 | 4 | 0.153588382 |

## All frozen amplification conditions

| Condition | Passed |
|---|---|
| House01_ge26 | False |
| House02_ge27 | False |
| Q_convergence | False |
| all_LOCO_positive | True |
| all_omission_house_pooled_medians_positive | False |
| context_contribution_le40 | True |
| contexts_all8 | False |
| deterministic_repeat | True |
| groups_ge15 | False |
| paired_rescue_harm | False |
| signflip_le05 | True |
| target_positive_ge58 | False |

## Q numerical convergence

B=2048 -> 4096 sign agreement: **63/64**, meeting >=63. Maximum absolute Delta change: **0.0332992212**, exceeding the frozen 10%-of-median threshold **0.0092826729**. Median absolute primary Delta: `0.09282672925419955`. **The convergence gate fails.** The 4096 result is not substituted, and no larger B or new seed is used to rescue it.

## Alternative-reference omission robustness

| Omit | SIG / 64 | H01 median | H02 median | Pooled median |
|---:|---:|---:|---:|---:|
| 1 | 33 | -0.012610435 | -0.011562494 | -0.012610435 |
| 2 | 34 | -0.002689688 | 0.040441013 | 0.006655747 |
| 3 | 34 | -0.008687358 | 0.051879180 | 0.024704466 |
| 4 | 38 | 0.034156939 | 0.010581312 | 0.033013309 |

## Truncated signature anatomy

| Level | Scope | Strict positive / targets | Mean Delta |
|---|---|---:|---:|
| LEVEL1 | ALL | 29/64 | -1.87350135e-16 |
| LEVEL1 | House01 | 13/32 | -2.08166817e-16 |
| LEVEL1 | House02 | 16/32 | -1.66533454e-16 |
| LE2 | ALL | 33/64 | 0.0020003858 |
| LE2 | House01 | 16/32 | 1.92901235e-05 |
| LE2 | House02 | 17/32 | 0.00398148148 |
| LE3 | ALL | 35/64 | 0.00314931548 |
| LE3 | House01 | 17/32 | 0.000242300621 |
| LE3 | House02 | 18/32 | 0.00605633034 |

These are explicit linear-coordinate Chen signatures, not truncations of the primary RBF feature-space signature. The <=2 and <=3 summaries do not support promotion. Level1 depends only on the endpoint; Q preserves that law. Its nonzero residual is exactly the finite-K difference between the RAW U self term and the empirical-product Q self expectation: `D_level1 = sum_i ||endpoint_i - mean_endpoint||^2 / [K(K-1)]`. This identity was independently verified for all candidate/omission anatomy rows, maximum error `1.3955850364233413e-15`. 10/64 primary deltas are numerical ties within 1e-10; exported strict signs are retained, and rounding-scale signs are not treated as information. Thus the level1 count cannot establish temporal coupling.

## Implementation, repeat and interpretation

Scorer freeze commit: **be1b6930** (pushed before R2C scoring). Protocol source: **7967491d57af26875ce07ed6aac093c28879410c**. Public sigkernel reference commit: **40a583155ea8d2194af0e90dddab37e2659cfcfd**. RBF follows public exp(-squared_distance/sigma), sigma=1; default corrected PDE, dyadic order1. Synthetic public-library parity, symmetry, PSD and exact-Q Chen enumeration passed before scoring. An independent unmodified public solver then checked 512 original-path kernel pairs, all 1024 exported RAW candidate rows, and 8192 fixed Q kernel pairs; maximum RAW discrepancy `6.794564910705958e-14`, Q discrepancy `1.7763568394002505e-15`. Two complete 2048/4096 scoring and aggregation passes are byte-identical.

The public Torch parity backend emits a pre-existing NumPy ABI bridge warning. It uses list-to-Tensor and Tensor-to-list exclusively; all public comparisons completed successfully. The production scorer uses NumPy/Numba, no global package replacement or ROS changes.

This NO-GO is for the specified binary RBF signature residual and its promotion gate. It does not prove every rough-path model fails, that the R0/R1/R2 mechanism is absent, or that pairwise models are universally inadequate. The failed numerical-convergence condition further limits broad scientific interpretation. A fair proper kernel score is not a source likelihood or calibrated posterior; nothing is inserted into PMFS. **STOP. No automatic continuous-axis experiment or network follows.**
