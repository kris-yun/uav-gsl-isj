# CS-MoM V1 — extended falsification log

Date: 2026-09-22

## A. All exported source-update snapshots

The same frozen B=4 translation-invariant CS-MoM rule was replayed at every source-update context bank.

There are 30 exported snapshots total (5 per R2 case).

Aggregate:

- native mean endpoint error: **4.9180 m**
- CS-MoM mean endpoint error: **3.9589 m**
- reduction: **19.50%**
- CS-MoM non-worse: **20/30 snapshots**

Per run:

- House01 seed0: 2/5 better; mean 5.239 → 5.188 m
- House01 seed1: 3/5 better; mean 4.011 → 3.689 m
- House02 seed0: 4/5 better; mean 2.947 → 2.583 m
- House02 seed1: 3/5 better; mean 2.871 → 2.318 m
- House03 seed0: 5/5 better; mean 7.597 → 3.321 m
- House03 seed1: 3/5 better; mean 6.842 → 6.654 m

This is correlated within-run evidence, not 30 independent trials, but it rejects the explanation that the terminal 29% result is a single-snapshot accident.

## B. Local corruption stress

Source-blind stress:

- divide the free grid into the same physical 4×4 blocks;
- select spatial blocks without source/candidate truth;
- apply the same bounded corruption to all candidates in selected cells:
  measured probability p -> 1-p.

At 10% corrupted blocks over 10 fixed seeds:

Clean-to-corrupted posterior change:

- native mean TV distance: **0.352**
- CS-MoM mean TV distance: **0.248**
- native mean Jensen-Shannon divergence: **0.178**
- CS-MoM mean Jensen-Shannon divergence: **0.092**

Thus the robust posterior distribution is materially more stable under localized spatial corruption.

However, the authoritative top-5 point estimate of the broad/multimodal CS-MoM posterior can still jump between modes under corruption. This again separates evidence robustness from safe point-mode release.

## C. Naive heterogeneous-corruption weighting rejected

NeurIPS 2025 heterogeneous-corruption theory motivates different reliability across samples/blocks.

A direct test used the existing PMFS measured confidence as a source-blind block reliability proxy.

Variants:
- mean block confidence weighted median;
- sum confidence weighted median;
- confidence-mass / sqrt(block-size) weighted median.

All substantially weaken the result and most restore false confidence.

Example, mean-confidence weighting:
- pooled improvement only about **5.7%**
- false-confident collapse: **6/6**

Conclusion:

**PMFS measured confidence is not a valid corruption-rate proxy.**

Do not equate map confidence with forward-model reliability.

## D. Candidate-relative informative-block screen rejected as replacement

A second source-blind construction removed block losses common to all candidates and retained only blocks with nonzero cross-candidate loss dispersion.

Variants based on summed, median, and Huberized relative block loss were tested.

They do not beat CS-MoM:
- sum relative evidence: about +1.7%, with collapse returning;
- median relative evidence: about +12.3%, no collapse;
- Huber relative evidence: about +6.6%, no collapse.

Thus source-identifying sparsity is real, but simply deleting common-mode blocks is not the missing solution.

## E. Pairwise robust tournament diagnostic

Pairwise candidate loss differences across 4×4 blocks are often exactly zero on the majority of blocks.

This proves an important structural fact:

> much of the mapped support is source-nondiscriminative even though it contributes to candidate-wise absolute loss.

A naïve majority-vote / MoM tournament therefore cannot by itself solve mode release: the source-specific differences can live in a minority of blocks.

## F. Current decision

Keep the main evidence-layer candidate:

**correlation-scale robust posterior under structured spatial contamination.**

Reject for now:
- confidence-weighted heterogeneous MoM;
- candidate-relative block masking as the main rule;
- simple pairwise majority tournament.

The unresolved research problem is now narrow:

**how to release a point source from a robust but multimodal / partially identified source distribution without recreating false confidence.**
