# OCB-R2 R2B — Dependence-Sensitive Proper-Score Amplification Test

Date: 2026-09-30

Status: **PREREGISTERED DISCOVERY-ONLY TEST / NO NEW DATA**

Parent evidence:

- R0: stable cross-time source information.
- R1: broad-memory source information; lag 1..3 robust.
- R2: candidate-wise broad-memory factor Gate B PASS.
- R2A: matched-window MZ physical interpretation HOLD.

## 0. Scientific question

The current R2 broad-memory factor is real but its numerical margin is small.
One plausible reason is methodological rather than physical:

> R0/R1/R2 use an Energy Score, which is a generic multivariate proper score
> and is known to have limited sensitivity to misspecified dependence/
> correlation structure.

R2B therefore asks:

> Does a dependence-sensitive proper score recover a materially stronger
> candidate-specific temporal-dependence signal on the same frozen data?

This is an **estimator test**, not a new mother theory.

No new House, GADEN, PMFS, confirmation, H03, model training, source classifier,
or hyperparameter search is allowed.

## 1. Frozen inputs

Reuse exactly the 64 discovery tensors from R0/R1/R2:

- 8 contexts;
- 2 sources/context;
- 4 independent realizations/source;
- each tensor 10 x 30;
- primary representation = binary encounter B = 1[C>0].

Require exact SHA parity with R0 input hashes.

The 64 continuous concentration tensors may be inspected only to verify that
the stored files are continuous-valued before binarization; **do not score the
continuous channel in R2B**. That is reserved for a later, separately frozen
stage.

## 2. Why Variogram Score

Use a cross-time Variogram Score because its statistic directly compares
pairwise component differences and is therefore targeted at dependence
structure.

For binary data, choose p=1. Since |0-1|^p = 1 for any p>0, there is no tuning
degree of freedom on the binary representation.

Only cross-time pairs are included. Within-time pairs are excluded because
R2B is intended to measure temporal dependence beyond the already-preserved
30-D snapshot law.

Primary temporal support is frozen to lags L in {1,2,3}, matching the R1
broad-memory region that was independently stable before R2B.

All lag-1..3 pairs receive equal weight.

Full lag-1..9 is descriptive robustness only and cannot rescue the primary
gate.

## 3. Exact marginal-preserving Q reference

For each held-out target y and candidate source s, form the same K=3
leave-one-realization-out reference bank as R2.

For any cross-time component pair

a=(t,q), b=(t+L,r), L in {1,2,3},

define the intact empirical pair expectation:

m_RAW(a,b) = (1/K) sum_i |X_i(a)-X_i(b)|

and the exact marginal-product expectation:

m_Q(a,b) = (1/K^2) sum_i sum_j |X_i(a)-X_j(b)|.

This Q expectation is exact for the empirical product of the two time-specific
snapshot laws:

- each complete 30-D snapshot marginal is preserved;
- cross-time realization identity is destroyed;
- no Monte Carlo surrogate is required;
- no random seed enters the primary score.

This exact-Q construction is a methodological improvement over taking the
median of 1000 shuffled surrogates, but it must be interpreted as the empirical
product reference, not as extra independent data.

## 4. Candidate-specific dependence score

For target y define:

VS_RAW(s,y) = mean_(a,b in cross-time lag1..3 pairs)
              ( |y(a)-y(b)| - m_RAW(a,b) )^2

VS_Q(s,y) = mean_(a,b in same pair set)
            ( |y(a)-y(b)| - m_Q(a,b) )^2

Lower Variogram Score is better.

Define the candidate-specific dependence evidence:

D_VS(s,y) = VS_Q(s,y) - VS_RAW(s,y)

Higher D_VS means the candidate's intact temporal dependence matches the target
better than the same candidate's marginal-preserving Q reference.

For a two-source target define:

Delta_VS(y) = D_VS(truth,y) - D_VS(alternative,y)

Positive Delta_VS means the dependence-sensitive score alone favors the true
source.

## 5. Frozen comparator

The comparator is the already-frozen R2 primary candidate factor:

Delta_ES = R2 Delta_BM

using the same 64 targets and the same primary alternative omission.

Do not recompute or retune Delta_ES except to verify exact parity with the R2
export.

Current frozen R2 reference facts:

- 53/64 target-level Delta_ES > 0;
- 16/16 source x context group means > 0;
- 8/8 context means > 0;
- House01 and House02 group medians > 0.

## 6. Primary amplification gate

R2B receives label

`OCB_R2_R2B_DEPENDENCE_SCORE_AMPLIFIES`

only if all conditions hold for Delta_VS:

1. target-level truth-vs-wrong accuracy is at least 58/64;
2. House01 target accuracy is not lower than its frozen Delta_ES accuracy;
3. House02 target accuracy is not lower than its frozen Delta_ES accuracy;
4. at least 15/16 source-context group means are positive;
5. all 8 context means are positive;
6. every leave-one-context-out pooled median is positive;
7. exact one-sided 8-context sign-flip reference <= 0.05;
8. synchronized four-view alternative-reference omission robustness keeps
   positive H01, H02 and pooled group medians;
9. paired target-level comparison against Delta_ES has rescues > harms and
   exact one-sided binomial probability <= 0.05 on the discordant targets;
10. deterministic repeat is byte-identical.

The 58/64 threshold is deliberately substantial: the existing 53/64 signal
must gain at least five net correct targets before this score is called an
amplification.

## 7. Other outcomes

### `OCB_R2_R2B_DEPENDENCE_SCORE_STABLE_NOT_AMPLIFIED`

Use if the new score remains stably source-discriminative
(H01/H02 medians positive, >=12/16 groups positive, >=6/8 contexts positive,
sign-flip <=0.05) but does not pass the amplification gate.

Meaning:

the mechanism survives a dependence-targeted score, but the small practical
effect is not mainly caused by Energy Score insensitivity.

### `OCB_R2_R2B_DEPENDENCE_SCORE_NO_GO`

Use if the dependence-targeted score is not stably source-discriminative.

Meaning:

do not promote Variogram scoring; retain the R2 mechanism evidence only.

## 8. Descriptive diagnostics

Report but do not use for rescue:

- lag1, lag2, lag3 contributions separately;
- full lag1..9 result;
- fast/slow;
- gas10/gas13;
- source identity;
- bottom quartile of M-FULL margin;
- target-level rescue/harm table versus Delta_ES;
- correlation between Delta_VS and Delta_ES.

No post-hoc lag selection is allowed.

## 9. Interpretation

If R2B amplifies, the candidate method becomes:

> **Source-Conditioned Dynamic Synergy Evidence**
> estimated by an **Exact Marginal-Preserving Dependence-Sensitive Score**.

This is not merely "use temporal information".
The method isolates the source evidence that is lost under a
time-factorized, snapshot-preserving reference.

If R2B does not amplify, the next stage may test whether binary encounter
compression is the bottleneck by restoring continuous concentration, but that
must be separately preregistered after review.

## 10. Stop boundary

After assigning one R2B label:

- STOP;
- do not test continuous concentration automatically;
- do not train density-ratio classifiers;
- do not generate new data;
- do not run R3;
- do not open confirmation/H03;
- do not run closed loop.

## 11. Required outputs

- `research/ocb_r2/r2b_dependence_score/R2B_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/r2b_dependence_score/R2B_INPUT_PARITY.json`
- `evidence/ocb_r2/r2b_dependence_score/R2B_TARGETS.tsv`
- `evidence/ocb_r2/r2b_dependence_score/R2B_GROUPS.tsv`
- `evidence/ocb_r2/r2b_dependence_score/R2B_CONTEXTS.tsv`
- `evidence/ocb_r2/r2b_dependence_score/R2B_OMISSION.tsv`
- `evidence/ocb_r2/r2b_dependence_score/R2B_RESCUE_HARM.tsv`
- `evidence/ocb_r2/r2b_dependence_score/R2B_REPEAT.json`
- `research/ocb_r2/r2b_dependence_score/R2B_DECISION_REPORT.md`
