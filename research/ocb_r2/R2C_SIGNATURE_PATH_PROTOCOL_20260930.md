# OCB-R2 R2C — Rough-Path Signature Kernel Amplification Test

Date: 2026-09-30

Status: **PREREGISTERED DISCOVERY-ONLY TEST / NO NEW DATA**

Parent results:

- R0: stable cross-time source information.
- R1: broad-memory source information beyond adjacent slots.
- R2: candidate-wise broad-memory Energy factor: 53/64 target-level truth>wrong,
  16/16 source-context group means positive, 8/8 contexts positive.
- R2A: matched-window Mori-Zwanzig physical interpretation HOLD.
- R2B: pairwise Variogram dependence score NO-GO (35/64; 4 rescues, 22 harms).

## 0. Scientific inference from R2B

R2B rejects the hypothesis that the useful R2 signal is well captured by
second-order / pairwise temporal discrepancy alone.

The next test therefore targets **ordered higher-order path interactions**.

The mother-theory candidate is:

> **Rough Path Theory / Path Signatures**

A path signature represents a sequential path by its hierarchy of iterated
integrals. A signature kernel evaluates path similarity in the induced
infinite-dimensional feature space and can be used in a strictly proper kernel
scoring rule after suitable path augmentations.

This is an estimator/method-family test. It does not yet establish the final
paper method.

## 1. Inputs

Reuse exactly the frozen 64 R0/R1/R2 discovery tensors:

- 8 matched House-wind-gas contexts;
- 2 sources/context;
- 4 independent realizations/source;
- shape 10 x 30;
- binary representation B = 1[C>0];
- no new extraction.

Require exact SHA parity with R0.

Do not use continuous concentration for scientific scoring in R2C.

No GADEN, PMFS forward, confirmation, H03, R3, neural network, learned source
classifier, or closed loop.

## 2. Path construction

For each 10 x 30 binary tensor B, form a discrete path with 10 chronologically
ordered points.

### Frozen spatial scaling

Use

`Z_t = B_t / sqrt(30)`

so the maximum Euclidean distance between two binary 30-D snapshots is <= 1.
This is dimension normalization, not fitted scaling.

### Frozen time augmentation

Append normalized time

`u_t = t / 9`, t=0,...,9.

Thus each point is

`X_t = [u_t, Z_t]` in R^31.

### Frozen basepoint augmentation

Prepend one zero vector in R^31 before the first observation.

Basepoint + time augmentation are mandatory in the primary path because they
remove translation/time-parametrization ambiguities needed for strict
identifiability of the signature representation.

No lead-lag augmentation in the primary test.

Lead-lag may be reported only as a separately labelled descriptive robustness
calculation and cannot rescue the primary gate.

## 3. Signature kernel

Primary kernel specification is frozen to mirror the 2026 signature-kernel
scoring-rule construction:

- static kernel: RBF;
- sigma = 1;
- dyadic order = 1;
- basepoint augmentation = yes;
- time augmentation = yes;
- input scaling as in Section 2.

Do not search sigma, dyadic order, augmentation, or path length after target
scores are visible.

Implementation may use a public signature-kernel library or an independently
verified equivalent implementation.

Before scientific scoring, verify:

1. symmetry of K(X,Y);
2. non-negative diagonal K(X,X);
3. Gram PSD up to numerical tolerance on a fixed small test set;
4. deterministic repeat;
5. agreement with an independent implementation or library on >=10 fixed path
   pairs within numerical tolerance.

If implementation parity fails: STOP.

## 4. Proper signature-kernel score for the intact candidate law

For a target path y and candidate source s, use the same K=3
leave-one-realization-out reference paths as R2.

Define the fair-U finite-ensemble signature score

`SIG_RAW(s,y) =
  [1/(K(K-1))] sum_{i != j} Ksig(x_i,x_j)
  - [2/K] sum_i Ksig(x_i,y)`

Lower is better.

The omitted target realization is never present in its truth reference bank.

## 5. Marginal-preserving Q-time reference law

For candidate s with K=3 reference realizations, define Q_s as the empirical
product across time blocks:

at each t independently choose one of the K complete 30-D snapshots from the
same candidate source and the same time t.

Thus Q_s preserves every time-specific complete spatial snapshot marginal and
destroys only cross-time realization identity.

### Numerical integration of Q

Do not treat Q draws as independent physical samples.

They are numerical draws from the constructed product law only.

Primary Monte Carlo integration:

- B = 2048 deterministic Q draws for the target-similarity term;
- B = 2048 deterministic independent Q-pairs for the self-similarity term;
- RNG seed derived only from fixed identifiers
  (base seed 2026093201, context, candidate source, target replicate,
   alternative omission);
- no target-value-dependent seed logic.

Define

`SIG_Q(s,y) =
  mean_b Ksig(q_b, q'_b)
  - 2 mean_b Ksig(q_b, y)`

where q_b and q'_b are independent draws from Q_s.

Primary Q numerical-convergence requirement:

repeat with B=4096 on all targets after the primary run and require:

- target-level sign agreement for Delta_SIG on >=63/64 targets;
- maximum absolute change in Delta_SIG <= 10% of the median absolute primary
  Delta_SIG, unless the median is numerically zero, in which case report HOLD
  for numerical instability.

B=4096 is convergence audit only and cannot be selected as the better result.

## 6. Candidate-specific higher-order path-dependence evidence

Define

`D_SIG(s,y) = SIG_Q(s,y) - SIG_RAW(s,y)`

Higher D_SIG means the candidate's intact ordered path law matches the target
better than the same candidate's time-factorized, snapshot-preserving law.

For the two-source discovery target:

`Delta_SIG(y) = D_SIG(truth,y) - D_SIG(alternative,y)`

Positive Delta_SIG means the rough-path dependence residual favors the true
source.

Also report the intact direct source margin:

`G_SIG_RAW(y) = SIG_RAW(alternative,y) - SIG_RAW(truth,y)`

but G_SIG_RAW is descriptive because it contains both marginal and dependence
information.

## 7. Frozen comparator

Comparator:

R2 primary `Delta_ES = Delta_BM`

with frozen facts:

- 53/64 target-level positive;
- H01 26/32;
- H02 27/32;
- 16/16 group means positive;
- 8/8 context means positive.

Verify exact parity against the frozen R2 export.

## 8. Primary amplification gate

Decision:

`OCB_R2_R2C_SIGNATURE_PATH_AMPLIFIES`

only if all hold for Delta_SIG:

1. >=58/64 target-level Delta_SIG > 0;
2. H01 target correctness >=26/32;
3. H02 target correctness >=27/32;
4. >=15/16 source-context group means > 0;
5. 8/8 context means > 0;
6. every leave-one-context-out pooled median > 0;
7. exact one-sided 8-context sign-flip <= 0.05;
8. four synchronized alternative-reference omission views keep positive H01,
   H02 and pooled group medians;
9. versus Delta_ES: rescues > harms and exact one-sided discordant-target
   binomial <= 0.05;
10. no one context contributes >40% of total absolute context effect;
11. Q Monte Carlo convergence gate passes;
12. deterministic full repeat is byte-identical apart from explicitly allowed
    floating-point formatting, and scientific numeric arrays are equal within
    the frozen tolerance.

## 9. Other labels

### `OCB_R2_R2C_SIGNATURE_PATH_STABLE_NOT_AMPLIFIED`

Use if signature residual remains stable:

- H01/H02 medians > 0;
- >=12/16 groups positive;
- >=6/8 contexts positive;
- sign-flip <=0.05;

but the amplification gate fails.

### `OCB_R2_R2C_SIGNATURE_PATH_NO_GO`

Use if stable source-discriminative path residual is not reproduced.

## 10. Mechanism anatomy required regardless of label

Because R2B pairwise Variogram failed, export a source-blind anatomy of which
signature levels carry discrimination.

Do **not** tune the primary result with this anatomy.

Using an explicit truncated signature implementation only for diagnostics,
report candidate residuals for:

- level 1 only;
- levels <=2;
- levels <=3.

The primary decision remains the full signature-kernel score.

If level 1 fails but <=2/<=3 recover the effect, that supports a genuinely
higher-order ordered-interaction interpretation.

If level 1 alone explains nearly all discrimination, do not claim higher-order
rough-path structure.

## 11. Literature / novelty boundary

Do not claim:

- invention of path signatures;
- invention of signature kernels;
- first temporal GSL;
- first use of higher-order sequence features in robotics.

Allowed working claim, if R2C passes:

> a source-conditioned, marginal-preserving path intervention exposes
> source-specific ordered dependence, and rough-path signature scoring converts
> that dependence into a candidate-source inference term.

Targeted prior-art search as of 2026-09-30 did not identify direct gas-source
localization work using path signatures/signature-kernel scoring. This is not a
formal novelty proof.

## 12. Stop boundary

After one R2C label:

- STOP;
- do not use continuous concentration automatically;
- do not train Random CDE / R-RDE / Transformer models;
- do not generate new data;
- do not run R3;
- do not open confirmation/H03;
- do not integrate into PMFS closed loop.

Human review decides whether the path-signature family is promoted to the
main algorithm candidate.

## 13. Required outputs

- `research/ocb_r2/r2c_signature_path/R2C_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/r2c_signature_path/R2C_INPUT_PARITY.json`
- `evidence/ocb_r2/r2c_signature_path/R2C_IMPLEMENTATION_PARITY.json`
- `evidence/ocb_r2/r2c_signature_path/R2C_TARGETS.tsv`
- `evidence/ocb_r2/r2c_signature_path/R2C_GROUPS.tsv`
- `evidence/ocb_r2/r2c_signature_path/R2C_CONTEXTS.tsv`
- `evidence/ocb_r2/r2c_signature_path/R2C_OMISSION.tsv`
- `evidence/ocb_r2/r2c_signature_path/R2C_RESCUE_HARM.tsv`
- `evidence/ocb_r2/r2c_signature_path/R2C_SIGNATURE_LEVEL_ANATOMY.tsv`
- `evidence/ocb_r2/r2c_signature_path/R2C_Q_CONVERGENCE.json`
- `evidence/ocb_r2/r2c_signature_path/R2C_REPEAT.json`
- `research/ocb_r2/r2c_signature_path/R2C_DECISION_REPORT.md`
