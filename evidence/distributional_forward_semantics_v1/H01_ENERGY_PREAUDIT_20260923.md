# Distributional forward semantics — H01 energy-score preaudit

Date: 2026-09-23

Status: **NO_GO_OR_INCONCLUSIVE_DISTRIBUTIONAL_DEPENDENCE_H01**

## Question

Does the full stochastic joint plume field carry source evidence that is lost when PMFS compresses each candidate to per-cell mean hit probabilities?

The test uses the frozen 200-step standalone candidate replay. No neural model is trained. The actual candidate ensemble is compared with an independence null that preserves every per-cell occupancy probability exactly in expectation while deleting cross-cell dependence.

## Truth-nearest candidate ranks

| score | truth rank | good-score Spearman vs -truth distance |
|---|---:|---:|
| native_score | 76.00/121 | 0.1576 |
| marginal_occupancy_mass | 20.50/121 | 0.2663 |
| meanfield_l2_to_all_miss | 20.50/121 | 0.2706 |
| distributional_energy_actual_joint | 20.50/121 | 0.2762 |
| distributional_energy_independent_marginals_null | 27.50/121 | 0.2498 |

## Destructive null

- preserves candidate-specific per-cell hit probabilities q_i (the information represented by the PMFS mean hitMap);
- removes cross-cell dependence/co-occurrence by replacing the joint field with the product of Bernoulli marginals;
- Monte Carlo samples per candidate: 5000; seed: 20260923.

## Gate

- actual_energy_beats_native_truth_rank: **True**
- actual_energy_beats_meanfield_truth_rank: **False**
- actual_energy_beats_independent_marginals_truth_rank: **True**
- actual_truth_energy_better_than_null_by_3mcse: **False**
- pass: **False**

A PASS means the load-bearing object is the stochastic multivariate plume distribution rather than the mean field alone, justifying replay on hit-bearing H02/H03 and only then a learned conditional generative model. A failure means diffusion/flow-matching should not be pursued merely because it is newer.
