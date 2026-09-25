# CODEX TASK — JTD-E1D HOLD Diagnosis

Branch: `research/jtd-cross-environment-v0`

Authoritative charter:
`research/jtd_cross_environment_v0/JTD_E1D_HOLD_DIAGNOSIS_CHARTER_20260925.md`

Upstream E1 final commit:
`3412acc5692cd4f5026dfdb5ee157bb37e65c980`.

Hard scope:
- 0 new plume;
- only E1 open references + 36 E1 fresh targets;
- no H01 DEV/House03;
- no dense G1A;
- do not alter E1 decision or thresholds;
- no neural model or feature search.

Perform exactly:
1. frozen adjacent-pair FULL vs SHUFFLED log-odds audit;
2. Gaussian score-term decomposition for wrong-partner targets;
3. four K=3 leave-one-reference-out source-specific OAS refits;
4. JTD-G0-style BLOCK-PRODUCT diagnostic control;
5. classify floor/tie vs materially negative units using raw magnitudes; report raw values rather than inventing a replacement E1 threshold;
6. issue one of the three descriptive E1D diagnosis labels.

Deliver:
- `JTD_E1D_RESULT.json`;
- target pair-margin CSV;
- environment×pair summary CSV;
- Gaussian component CSV;
- K3 jackknife stability CSV/JSON;
- FULL/BLOCK_PRODUCT/SHUFFLED comparison CSV;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- branch/final commit;
- review package path/bytes/SHA256.

Stop after E1D.