# JTD-G1A — 168-Source Dense Frozen-Bank Assessment

Date: 2026-09-25

Status: **ZERO-PLUME / FROZEN-ALGORITHM DENSE ASSESSMENT**

## 1. Scientific purpose

Test whether the JTD working model has practical dense-source localization value beyond ordinary block-independent modeling, while directly isolating the contribution of fitted cross-block covariance.

This is NOT a fresh blinded confirmation and does NOT establish the final main innovation.

## 2. Data

Use the complete compatible House02 `3,5-1_slow` dense D1R bank:
- exactly 168 frozen sources;
- exactly 16 independent realizations/source;
- frozen legacy D1R 10x30 observation contract;
- no source filtering after outcomes are seen.

Before any scoring, complete an A0 compatibility audit:
- canonical wind asset identity and hashes;
- source IDs and xyz, including z;
- gas/source release settings;
- time indices 100,150,...,550;
- 30-probe ordering and pooling contract;
- ppm transform/units;
- seed/source/run mapping;
- intersection with the original G0 18-source panel;
- raw-cube and extracted-tensor hashes.

If the bank is incompatible with the G0 observation/model contract, return DATA_CONTRACT_STOP without scientific scoring.

## 3. Evaluation split

Keep the original G0 four-fold scheme exactly:
- each source has 12 reference realizations and 4 held-out evaluation realizations per fold;
- every realization is evaluated exactly once across the four folds;
- transformations are fitted on reference data only.

## 4. Frozen representation

Exactly inherit G0:
- raw ppm / original transform;
- five contiguous two-time blocks;
- StandardScaler fitted per block on pooled reference observations only;
- PCA=2 per block on pooled references only;
- concatenate to 10-D;
- uniform prior over all 168 candidates;
- original jitter/numerical stabilization;
- source-specific OAS covariance.

No temperature scaling.
No probability floor.
No PCA/component search.
No neural model.
No alternate normalization.

## 5. Models/controls evaluated in the SAME run

### FULL
Original G0 source-specific 10-D OAS Gaussian likelihood.

### BLOCK-PRODUCT (BP)
For each source and each 2-D block, fit an independent OAS Gaussian on the same 12 references.
Score a target by summing the five block log likelihoods.
This is the primary ordinary comparator.

### MATCHED-BLOCK-DIAG (MBD)
For each source, start from the already-fitted FULL covariance after the original jitter/stabilization.
Construct:
`Sigma_MBD = blockdiag(Sigma_FULL[block1], ..., Sigma_FULL[block5])`.

Use the exact FULL mean vector.
Do NOT refit OAS.
Do NOT add a second jitter.
MBD is the matched mechanistic ablation: fitted block marginals are inherited from FULL; only cross-block covariance terms are removed.

### DIAG-COV
Retain the original G0 diagnostic unchanged.

### SHUFFLED
Retain the original G0 marginal-preserving destructive diagnostic with 200 null models/fold.
SHUFFLED is NOT the primary deployable comparator.

## 6. Null randomization infrastructure fix

Do not extend the historical arithmetic seed formula.

Every randomization uses a domain-separated SHA256 key containing at least:
`project|JTD_G1A|fold|null_id|source_id|block_id|purpose`.

Map the digest deterministically to the RNG seed/derangement.

Save all derangements or their exact reproducible keys before scoring.

This is an infrastructure correction for 168-source expansion and does not alter the historical G0 result.

## 7. Primary probabilistic endpoint

For every held-out target from source s:

`delta_BP = NLL_BP(s|y) - NLL_FULL(s|y)`.

Positive values favor FULL.

Primary source-panel statistic:

`Delta_BP = mean_over_sources( mean_over_targets_of_source(delta_BP) )`.

Compute a 5,000-resample source-level bootstrap sensitivity interval over the 168 source means.
Label it explicitly as a source-panel sensitivity interval, not a full learning-procedure confidence interval.

## 8. Matched-mechanism endpoint

Define:
`delta_MBD = NLL_MBD(s|y) - NLL_FULL(s|y)`.

Use the same source-mean aggregation and 5,000-resample source-level sensitivity interval.

This directly tests whether fitted cross-block covariance contributes beyond FULL's own fitted block marginals.

## 9. Legacy destructive-null continuity

Report:
- FULL mean NLL;
- median over the 200 aggregate SHUFFLED mean NLLs;
- mean target-wise FULL-vs-median-null delta;
- 20% trimmed target-wise delta;
- positive-source count.

Do not treat target-wise median-null as one deployable posterior.
Do not use the old p-value wording as an exact permutation-test probability.

## 10. Dense spatial utility endpoints

Using the 168 source xy coordinates and each model's normalized posterior, report:
- truth rank;
- top-1 / top-3 / top-5;
- mean multiclass Brier score;
- posterior probability mass within 0.5 m of truth;
- posterior probability mass within 1.0 m of truth;
- posterior expected source distance;
- MAP source Euclidean error;
- nearest-neighbor confusion rate;
- true-vs-nearest-neighbor log-odds margin.

Nearest neighbor is frozen geometrically from source coordinates before scoring.

## 11. Breadth and tail diagnostics

For FULL-vs-BP and FULL-vs-MBD report:
- source-level mean delta distribution;
- fraction of sources with positive mean delta;
- fold-level means;
- 10% and 20% two-sided trimmed target means;
- mean after removing the largest positive 1% of target deltas;
- mean after removing the largest positive 5% of target deltas;
- leave-one-source-out aggregate influence (descriptive only);
- largest positive and negative target deltas;
- original G0-18 subset vs the other dense sources separately.

Do not remove observations from the primary endpoint.

## 12. Gaussian failure diagnostics integrated from E1D

For every target where FULL MAP is wrong and the predicted MAP is the geometric nearest neighbor, export:
- true and predicted source IDs;
- FULL/BP/MBD posterior probabilities;
- FULL true-vs-neighbor log-odds;
- Mahalanobis quadratic contributions;
- log-determinant contributions;
- OAS shrinkage coefficients and covariance condition numbers.

This is diagnostic only and cannot change the GO/STOP threshold.

## 13. Frozen decision gates

### G1 — practical proper-score gain over ordinary model
`Delta_BP > 0` and the source-level 95% sensitivity interval lower bound > 0.

### G2 — matched cross-block contribution
`Delta_MBD > 0` and the source-level 95% sensitivity interval lower bound > 0.

### G3 — breadth
At least 60% of the 168 sources have positive source-mean delta_BP, and at least 60% have positive source-mean delta_MBD.

### G4 — heavy-tail robustness
For delta_BP, both the 20% trimmed mean and the mean remaining after removal of the largest positive 5% target deltas must be >0.

### G5 — legacy JTD continuity
FULL mean NLL must be lower than the median aggregate SHUFFLED mean NLL.

### G6 — no major spatial/probabilistic utility conflict
At least one of the following must improve for FULL vs BP:
- mean Brier score;
- mean posterior mass within 1.0 m;
- mean posterior expected source distance.

And none of those three may worsen by more than 5% relative to BP.

Exact-cell top-1 is reported but is not a gate because dense adjacent candidates can exchange MAP cells while preserving local probability mass.

## 14. Decision

GO:
`JTD_G1A_GO_DENSE_PROBABILISTIC_UTILITY_AND_CROSSBLOCK_CONTRIBUTION`
only if G1-G6 all pass.

HOLD:
`JTD_G1A_HOLD_SCORE_UTILITY_TRADEOFF`
if G1-G5 pass but G6 fails.

STOP:
`JTD_G1A_STOP_DENSE_UTILITY_OR_MECHANISM_NOT_CONFIRMED`
for failure of any of G1-G5.

DATA STOP:
`JTD_G1A_DATA_CONTRACT_STOP`
if the A0 compatibility audit fails.

## 15. Consequence

GO authorizes one equal-depth cross-environment confirmation design; no new representation work before that.

HOLD requires interpretation of the proper-score vs spatial-utility tradeoff; do not upgrade to main innovation.

STOP freezes JTD as a discovery/limited-setting finding and ends this mainline without model rescue.

House01 DEV and House03 remain sealed throughout.