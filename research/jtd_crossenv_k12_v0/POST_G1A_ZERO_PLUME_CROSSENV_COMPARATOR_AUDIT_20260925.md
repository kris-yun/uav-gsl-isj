# Post-G1A Zero-Plume Cross-Environment Comparator Audit

Date: 2026-09-25

Status: **DESIGN DIAGNOSTIC ONLY — DOES NOT CHANGE E1 HOLD**

## Purpose

After G1A established FULL > BLOCK-PRODUCT and FULL > MATCHED-BLOCK-DIAG on the 168-source dense H02 W0 bank, re-evaluate those same clean comparators on the already-open E1 data before spending new simulation budget.

Data:
- three E1 OPEN environments;
- 6 sources/environment;
- 4 frozen references/source;
- 2 already-acquired fresh targets/source;
- 0 new plume;
- no sealed data.

Representation and model fitting were reproduced exactly as E1, with the G1A definitions of BP and MBD.

## Mean truth-source NLL differences

`delta_BP = NLL_BP - NLL_FULL`
`delta_MBD = NLL_MBD - NLL_FULL`

| Environment | FULL mean NLL | BP mean NLL | MBD mean NLL | delta_BP | delta_MBD | positive source units BP | positive source units MBD |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01 / 1,3-2,4_fast | 5.070 | 11.770 | 11.070 | +6.700 | +6.000 | 4/6 | 5/6 |
| H02 / 3,5-1_slow | 1.760 | 5.724 | 3.863 | +3.964 | +2.103 | 1/6 | 2/6 |
| H02 / 4,5-3_slow | 114.075 | 118.501 | 111.529 | +4.426 | -2.546 | 3/6 | 3/6 |

Pooled target means:
- delta_BP ≈ +5.030;
- delta_MBD ≈ +1.852.

## Interpretation

At K=4, FULL already beats the ordinary BLOCK-PRODUCT comparator in mean truth-source NLL in all three OPEN environments.

However the matched cross-block contribution is not environment-stable at K=4: H02 `4,5-3_slow` has negative mean delta_MBD.

This result is exploratory and cannot change the frozen E1 HOLD because BP/MBD were introduced after E1.

It motivates the pre-agreed next step after dense G1A GO:

> equal-depth K=12 cross-environment confirmation with genuinely new targets, testing both FULL > BP and FULL > MBD.

No theory/model expansion is authorized before that confirmation.