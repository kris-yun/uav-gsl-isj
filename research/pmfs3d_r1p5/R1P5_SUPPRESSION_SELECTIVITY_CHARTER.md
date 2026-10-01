# PMFS3D-R1P5 — suppression/selectivity audit

Date: 2026-10-01
State: **FROZEN OFFLINE MECHANISM AUDIT / NO NEW FORWARD RUNS**

Parent branch: `research/pmfs3d-r1-oracle-ranking-20261001`
Parent head: `dea9bd946e9df9156b75b79fcdf6edac59ac4aa1`
Parent decision: `PMFS3D_R1_HOLD_RANK_NONINFERIORITY`

## 1. Why this audit exists

R1 gave positive Oracle-3D minus Oracle-2D truth-vs-best-wrong margin changes in all four historical cases, but the truth rank worsened in two cases. The independent R1 audit additionally established that the Oracle-2D and Oracle-3D truth log scores are exactly equal in all four cases.

Therefore R1 did **not** show that 3-D transport creates stronger positive evidence at the true source. Its margin gain came entirely from score changes among wrong hypotheses. At the same time, the number of wrong leaves tied with the truth increased in all four cases.

The only scientifically useful next question is therefore:

> Does the 3-D operator produce broad, source-selective and cross-seed-stable suppression of false hypotheses, or did R1 merely suppress the current strongest wrong competitor while leaving the global ranking structure fragile?

This audit answers that question from the already-saved R1 candidate score tables. It does not add a new scorer.

## 2. Frozen data

Use only the already completed R1 outputs:

`PMFS3D_R1_SCIENTIFIC_20261001/repeat1/<case>/{oracle2d,oracle3d}/candidate_log_scores.csv`

and the frozen R1 result JSON.

Exactly these cases:
- House01_seed0_off_off
- House01_seed1_off_off
- House02_seed0_off_off
- House02_seed1_off_off

No H03, no confirmation set, no new plume realization.

## 3. Candidate-level quantities

For candidate hypothesis (j):

- (S_{2,j}): Oracle-2D log score
- (S_{3,j}): Oracle-3D log score
- (T): truth-owning leaf
- (delta_j=S_{3,j}-S_{2,j})
- (delta_T=S_{3,T}-S_{2,T})

Define the pairwise truth-advantage gain

[
A_j=(S_{3,T}-S_{3,j})-(S_{2,T}-S_{2,j})
    =delta_T-delta_j.
]

Interpretation:
- (A_j>0): 3-D improves truth relative to wrong candidate (j)
- (A_j=0): no pairwise change
- (A_j<0): 3-D harms truth relative to (j)

This is diagnostic decomposition only. It must not be turned into a new probability-map score in R1P5.

## 4. Required per-case diagnostics

For every case, report:

1. exact reproduction of R1 Oracle-2D/Oracle-3D truth ranks and delta margin;
2. finite candidate-pair coverage;
3. (delta_T);
4. among all wrong candidates: fraction (A_j>0), (A_j=0), (A_j<0), and median (A_j);
5. among **2-D-ahead wrongs** ((S_{2,j}>S_{2,T})): the same positive fraction and median (A_j);
6. repaired crossings: wrong in front of truth in 2-D but not in 3-D;
7. harmful crossings: not in front of truth in 2-D but in front in 3-D;
8. truth-tie additions/removals;
9. the best-wrong candidate in each arm, only as a descriptive check.

The already-known 4/4 best-wrong margin improvement is **not a gate**.

## 5. Cross-seed structural stability

Within House01 and House02 separately, intersect candidate IDs between seed0 and seed1, exclude both truth leaves, and compute tie-aware Spearman correlation between the vectors (delta_j).

This asks whether the 3-D-vs-2-D suppression pattern is a property of the transport/geometry operator rather than an accident of one terminal observation map.

Require at least 50 common finite wrong candidates for a house-level correlation to be valid.

## 6. Frozen mechanism gate

### Integrity gate

All must hold:
- score candidate sets match between Oracle-2D and Oracle-3D;
- stored R1 truth ranks reproduce exactly;
- stored R1 delta margins reproduce to <=1e-9;
- finite paired-score coverage >=0.95 in every case;
- (|delta_T|<=1e-12) in every case.

Failure -> `PMFS3D_R1P5_INVALID_STOP`.

### Broad-selectivity gate

A case is selective only if, among its 2-D-ahead wrong candidates:
- at least one such candidate exists;
- fraction with (A_j>0) >= 0.60;
- median (A_j>0).

Broad selectivity requires >=3/4 selective cases.

### Cross-seed-stability gate

Both houses must have:
- >=50 common finite wrong candidates;
- Spearman((delta_{seed0},delta_{seed1})) >= 0.50.

### Decision

- integrity fails:
  `PMFS3D_R1P5_INVALID_STOP`
- broad selectivity passes AND both-house stability passes:
  `PMFS3D_R1P5_SELECTIVE_FALSE_SUPPRESSION`
- otherwise, if >=2 selective cases OR at least one valid house has Spearman >=0.30:
  `PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY`
- otherwise:
  `PMFS3D_R1P5_FRAGILE_TOP_COMPETITOR_SUPPRESSION_STOP`

No outcome is a main-innovation PASS.

## 7. Strict stop boundary

R1P5 performs only saved-score analysis.

Forbidden:
- new GADEN;
- new Oracle forward;
- changed 3-D collision/noise/hit semantics;
- fusion weights;
- score calibration;
- threshold tuning after result;
- H03 or confirmation data;
- network training;
- ROS/300 s closed loop.

After writing the decision and evidence: **STOP**.

Only `PMFS3D_R1P5_SELECTIVE_FALSE_SUPPRESSION` authorizes designing a *separate* counterexample-guided hypothesis-elimination experiment. A HOLD authorizes theory review only, not closed loop.
