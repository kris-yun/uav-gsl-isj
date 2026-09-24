# D3 Independent Review and Post-Failure Scientific Diagnosis

Date: 2026-09-24  
Reviewed branch: `research/realization-invariant-source-signature-v0`  
Reviewed result commit: `622e870aa92500c1784b9dbb6f6356a7233177be`

Frozen decision: **D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE**

## 1. Package integrity

Reviewed archives:

- `MZ_D3_S1_W2_REVIEW_20260924.tar.gz`
  - bytes: 141610
  - SHA256: `42efdb3251497225075f689cddd15bf9685d08a385d47ebb42c6e2c4a6c190e0`
- `BIGREEN_GATE1A_REVIEW_20260924.tar.gz`
  - bytes: 1281180
  - SHA256: `9f2c4e93c3833b00dd82d3f53a21e2286f23afdf3e5087328fc094cada1ba2be`

All files listed in both internal SHA256 manifests independently verified.

The D3 package records:

- branch `research/realization-invariant-source-signature-v0`;
- HEAD `622e870aa92500c1784b9dbb6f6356a7233177be`;
- clean worktree.

The D3 `source_bank.tsv` and `gate1a_contract.json` are byte-identical to the Gate-1A package.

## 2. Wind / target contract

Both new targets are House02 / W2 / `3,5-1_slow`.

Truth:

- `pmfs_10_17`;
- `(-2.242730141, -2.200880051, 0.20)`.

Seeds:

- S1_W2_A = 2026092301;
- S1_W2_B = 2026092302.

The frozen GADEN binary, occupancy, W2 iteration-1 and extractor hashes match the D3 contract.

No infrastructure-only patch was reported.

## 3. Independent rank recomputation

The committed JSON ranks were not trusted.

Ranks were independently recomputed from:

- both raw D3 target concentration cubes;
- the original Gate-1A 630-source C/D prediction bank;
- the frozen pooled observation operator;
- the frozen D0 projection;
- the frozen temporal covariance construction;
- the frozen target-blind memory horizon rule.

Recomputed memory horizon: **7**.

Exact reproduced ranks:

| target | raw | D0 static | diagonal | D2 finite memory |
|---|---:|---:|---:|---:|
| S1_W2_A | **1** | 9 | 6 | 5 |
| S1_W2_B | **1** | 1 | 1 | 1 |

Therefore:

- both D2 ranks <=3: false;
- D2 rank sum 6 <= raw rank sum 2: false;
- D2 sum 6 <= D0 sum 10: true;
- D2 sum 6 < diagonal sum 7: true.

The frozen decision is correctly:

`D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`

## 4. Reporting defect

The original JSON contains a `pass_rule` display object with four literal `true` values.

This is a reporting-only bug in `score_d3_second_source.py`: those fields are not the executable predicate used to produce `decision`.

The original result must remain unchanged for auditability. The integrity note is authoritative for interpreting this defect.

## 5. Why the mechanism failed on S1

The failure is not merely “memory horizon 7 was wrong”.

For S1, raw exact-forward already identifies the truth at rank 1 in **both** independent target realizations.

Target A/B same-source variability is small:

- raw cosine: ~0.99759;
- raw relative L2 difference: ~0.08117.

The true-source C/D prediction pair is similarly stable:

- raw cosine: ~0.99690;
- relative difference with respect to their mean: ~0.0790.

Thus absolute concentration amplitude is not primarily a nuisance for S1; it is a useful source-discriminating statistic.

The per-time mass-fraction projection removes that information:

- S1_A raw rank: 1 -> D0 rank: 9;
- finite memory only partially recovers it: 9 -> 5.

By contrast, the original S2 target pair is much more realization-sensitive:

- raw A/B cosine: ~0.97741;
- raw relative L2: ~0.21181.

This is why the same normalization appeared useful for S2.

## 6. 630-source heteroscedasticity audit

Across all 630 source hypotheses, independent C/D plume-realization variability is highly source-dependent.

Relative C/D discrepancy distribution:

- minimum: ~0.015;
- 25th percentile: ~0.093;
- median: ~0.153;
- 75th percentile: ~0.244;
- 90th percentile: ~0.345;
- maximum: ~0.575.

Mean source mass and realization variability are substantially related:

- Spearman correlation(relative variability, mean mass): ~**-0.503**.

Specific frozen sources:

- S1 prediction relative variability: ~0.079, low-variability regime;
- S2 prediction relative variability: ~0.180, substantially more stochastic regime.

Therefore stochastic plume uncertainty is **source/location-conditioned and heteroscedastic**.

## 7. Scientific conclusion

The D0–D2 construction made an implicit global assumption:

> absolute plume mass can be treated as a realization nuisance and removed before source inference.

D3 falsifies that assumption.

A globally invariant representation cannot be the main solution because the same observable component can be:

- nuisance-dominated for one source region (S2);
- source-discriminative for another source region (S1).

The stronger scientific problem is now:

> infer source identity under a source-conditioned stochastic path distribution whose amplitude uncertainty, morphology uncertainty and temporal memory vary with source location.

This requires comparing **path ensembles**, not globally deleting one observable component.

## 8. Frozen action

Do not rescue the current MZ mainline by:

- changing the normalization;
- mixing raw and normalized scores after seeing D3;
- changing the horizon;
- source-dependent hand weights;
- re-tuning D3 thresholds.

The route remains stopped.

The reusable findings are:

1. exact transport contains strong local source information;
2. plume realization noise is temporally correlated;
3. the strength of that noise is source-conditioned / heteroscedastic;
4. global realization invariance destroys useful information in low-noise source regimes.

These facts should become hard constraints for the next main-innovation search.
