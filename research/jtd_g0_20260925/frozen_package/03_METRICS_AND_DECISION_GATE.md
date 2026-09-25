# 03 — METRICS AND DECISION GATE

## 1. Primary metric

For heldout target q with true source y:

`NLL_q = -log p(y | z_q)`

Aggregate equally over all heldout tasks.

Do not weight by number of raw observation points.

## 2. Null distribution

For each of 200 SHUFFLED replicates m compute:

- overall mean NLL
- fold-wise mean NLL
- source-wise mean NLL
- median truth rank
- top-1
- top-3

Define:

`NULL_MEDIAN_NLL = median_m(mean_NLL_m)`

`REL_NLL_GAIN = (NULL_MEDIAN_NLL - FULL_MEAN_NLL) / NULL_MEDIAN_NLL`

Empirical one-sided p:

`p_emp = (1 + count_m(mean_NLL_m <= FULL_MEAN_NLL)) / 201`

Lower NLL is better.

## 3. Paired target effect

For every heldout task q:

`delta_q = median_m(NLL_shuffled[m,q]) - NLL_full[q]`

Positive = FULL better.

Report:

- overall mean/median delta
- per-source mean delta
- per-fold mean delta
- hierarchical bootstrap 95% CI

Hierarchical bootstrap:

1. resample sources with replacement;
2. within selected source resample its heldout realizations with replacement;
3. 5000 bootstrap draws;
4. do not resample 300 raw entries as independent.

## 4. Influence

Leave one source out at a time.

Recompute overall paired mean delta.

Record whether sign stays positive for all 18 exclusions.

Do not delete influential sources.

## 5. Ranking metrics

For each heldout task:

- truth rank (1 = best)
- top-1
- top-3
- posterior(true)

If source coordinates exist:

- MAP source-center Euclidean error

Ranking metrics are secondary but protect against a probability-score "improvement" that destroys source ordering.

## 6. Frozen internal discovery thresholds

These are internal GO/HOLD/STOP thresholds for allocating more research effort, not universal scientific laws.

### GO

Label:

`JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL`

Require ALL:

1. input contract PASS;
2. `REL_NLL_GAIN >= 0.05`;
3. `p_emp <= 0.01`;
4. hierarchical bootstrap 95% CI lower bound for paired mean ΔNLL > 0;
5. all 4 folds have positive mean ΔNLL;
6. at least 12/18 sources have positive source-wise mean ΔNLL;
7. leave-one-source-out ΔNLL sign remains positive for all 18 exclusions;
8. FULL median truth rank is not worse than median SHUFFLED truth rank;
9. FULL top-3 success is not lower than null median by > 0.02 absolute.

GO is **discovery signal only**. It does not authorize a paper claim.

### HOLD

Label:

`JTD_G0_HOLD_WEAK_OR_UNSTABLE_SIGNAL`

Use when:

- overall effect is positive and `p_emp <= 0.05`,
- but one or more GO stability/practical-effect conditions fail,
- OR 0.02 <= REL_NLL_GAIN < 0.05 with consistent direction.

HOLD means no dense expansion until human review.

### STOP

Label:

`JTD_G0_STOP_NO_INCREMENTAL_TEMPORAL_SIGNAL`

Use if any:

- `REL_NLL_GAIN <= 0`;
- `p_emp > 0.05`;
- bootstrap CI includes 0 and practical gain < 0.02;
- effect sign is negative in >=2 folds;
- fewer than 9/18 sources have positive ΔNLL;
- FULL ranking materially worsens (top-3 drops >0.02 and median rank worse);
- effect sign flips after removing one source and no broad source support is present.

Do not rescue with alternative hyperparameters.

### INPUT STOP

`JTD_G0_STOP_INPUT_CONTRACT_INVALID`

for provenance/shape/independence failure.

## 7. Interpretation

GO statement may say only:

"On the frozen 18-source R0 discovery panel, preserving cross-block realization dependence improves held-out source probability evidence relative to a marginal-preserving shuffled null under the frozen working model."

It may NOT say "temporal dynamics solve source localization" or "joint path likelihood is validated".
