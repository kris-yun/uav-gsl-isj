# Failure-informed mainline cycle after HCMC independent NO-GO

Date: 2026-09-22
Base commit: 878bcbd1082d00f1554286920d9fde88cc84c5ea
Status: **SCREENING-PROTOCOL RESET + TWO NEW MAINLINE CANDIDATES FALSIFIED**

## 1. Lesson from HCMC independent failure

HCMC V1 produced a very large old-discovery effect but failed on true independent plume realizations, including one valid case where the frozen representation became undefined.

Therefore no future main-line candidate may be promoted from the old six-case discovery archive alone.

The promotion process is changed from:

> old six discovery -> freeze -> one expensive independent holdout

to:

> heterogeneous development corpus -> distribution-shift stress -> freeze -> brand-new holdout

The HCMC independent six are now unblinded and must be treated as **development data**, never as a holdout again.

## 2. Required development corpus before the next main-line promotion

D0 old discovery:
- House01/02/03 x seed0/1 R2 archive.

D1 failed HCMC independent-plume corpus:
- six TRUE_INDEPENDENT_PLUME_VALIDATION runs from commit 878bcbd...
- these must be imported with their full source-update context banks; current GitHub evidence only contains summary matrices, not the raw candidate support needed to screen new methods.

D2 intervention/source-position stress:
- existing H01/H02/H03 x SA/SB x fast/slow controlled asset.

D3 synthetic source-blind stress:
- constant/near-constant measured fields;
- amplitude rescaling/offset;
- monotone compression;
- support thinning;
- candidate spatial destruction;
- geometry-only controls.

Only a method positive across D0-D3 may be frozen for a **newly generated** D4 holdout.

## 3. Candidate A — Anti-Causal Invariant Abstraction transfer

Mother idea:
NeurIPS 2025, *Measure-Theoretic Anti-Causal Representation Learning* (ACIA).
The source is a cause and the sensed plume is an effect, so gas-source localization is naturally anti-causal inference under environment interventions (wind, stochastic plume realization, trajectory).
Code: https://github.com/ArmanBehnam/ACIA

A lightweight non-neural transfer was tested before investing in model training.

Low-level per-update representation:
- empirical distribution of robust-normalized measured/simulated hit probability;
- empirical distribution of cardinal local increments;
- fixed quantile-Wasserstein discrepancy for both channels.

High-level environment abstraction:
- five PMFS source updates treated as source-blind environments;
- candidate risk = worst per-update equal-weight discrepancy;
- candidate density = average percentile rank;
- no truth-dependent parameter.

Old six-case result:
- Native mean: 5.5551 m
- anti-causal invariant proxy mean: 3.6885 m
- pooled reduction: 33.60%
- improved: 5/6

However the robustness evidence is not strong enough:
- final-leaf permutation 300: null mean 4.5205 m; **9.0%** of nulls as good as/better than real;
- update/environment permutation 100: null mean 4.4067 m; **19.0%** as good as/better than real;
- cross-seed candidate-score Spearman:
  - H01 0.441
  - H02 0.280
  - H03 0.844

Decision:
**NO-GO AS MAIN LINE.**
Do not repeat the HCMC mistake of promoting a good discovery mean with weak shift-mechanism evidence.

## 4. Candidate B — IDG-style invariant causal subgraph

Mother idea:
NeurIPS 2025, *Quantifying Distributional Invariance in Causal Subgraph for IRM-Free Graph Generalization*.
Code: https://github.com/anders1123/IDG

Transfer tested:
- build the observed spatial grid graph;
- each cardinal edge is a candidate local evidence element;
- estimate candidate ranking on that edge separately in the five source-update environments;
- weight an edge by the positive part of its cross-environment candidate-ranking stability;
- infer the source from the worst-environment weighted edge mismatch.

Old six-case result:
- mean endpoint: 4.9944 m
- pooled reduction: 10.09%
- improved: 3/6

Decision:
**NO-GO.**

This is exactly the kind of candidate that would previously have been kept because the aggregate number is positive; under the new failure-informed standard it is discarded immediately.

## 5. Candidate C — Partial identification / breakdown-frontier transfer

Mother idea:
NeurIPS 2025, *Data Fusion for Partial Identification of Causal Effects*.
Code: https://github.com/harsh-parikh/Partial-Identification-Data-Fusion

Why it matters:
A stochastic forward simulator can be misspecified even when the source is correct. Instead of forcing a point posterior, infer a **set of source hypotheses** compatible with a bounded simulator/environment violation and ask how much assumption relaxation is required before the conclusion changes.

A lightweight source-set screen used the same environment-robust discrepancy from Candidate A only to test whether partial identification would remain useful.

Result:
- exact best candidate covers the true-source leaf in 0/6;
- at relative sensitivity 0.1%, true-source coverage reaches 5/6 but the plausible set contains on average about 59.8 final leaves;
- 6/6 coverage requires roughly 5% sensitivity and an average plausible set of about 76.5 leaves.

Decision:
**NO-GO AS THE MAIN LOCALIZER in its current form.**
Retain only as a possible safety/abstention layer. It is scientifically useful because a low-information realization should return a broad identified set rather than an undefined or false-confident point estimate.

## 6. Candidate pre-audits

### Equivariance-by-Contrast / source translation symmetry
NeurIPS 2025 EbC has strong public code, but exact source-translation symmetry is physically false in indoor maps because walls/doors change the forward transport operator under translation. Do not spend an experiment pretending this group action is a valid plume symmetry. It can be reconsidered only with geometry-conditioned group actions.

### Causal world model / Koopman
High-level idea remains attractive and genuinely orthogonal, but the current repository does not contain step-resolution candidate-conditioned counterfactual plume predictions. Five source-update snapshots are not enough for an honest world-model/causal-dynamics test. Mark DATA-INELIGIBLE, not positive.

## 7. New hard promotion contract

A future main-line candidate must satisfy all of the following before a new holdout is generated:

1. mathematically defined under constant and near-constant observation fields;
2. old R2 discovery improvement >= 10% with >=4/6 non-worse;
3. positive on the six now-unblinded independent plume cases after they are moved into the development corpus;
4. source-position/intervention stress does not collapse;
5. destructive null separation: <=5% null as good/better for at least the principal structure-destroying control;
6. no geometry-only baseline explains the gain;
7. source-blind parameter freeze;
8. no result-driven case/scale/update selection.

Only then generate a fresh stochastic-plume holdout.

## 8. Immediate next action

The single most important next data action is not another model run. It is to package the six accepted independent-plume source-update context banks from:
  /home/zyc/hcmc_v1_native_runs_20260922
into a compact development archive.

Needed per case:
- context_bank/source_update_0001..0005/
  - candidate_manifest.csv
  - candidate_support_alignment.csv
  - measured_hit_probability.csv
  - source_posterior.csv
- context_bank/source_update_timing.csv
- native terminal/evaluation metadata
- realization ID + content hash
- no failed attempts

Once imported, every new idea will be screened jointly on old six + new six before it can be called a main-line candidate.

This is the concrete process change intended to prevent another HCMC-style discovery-only false positive.
