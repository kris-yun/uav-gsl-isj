# 2025–2026 auxiliary-module screen

This screen asks whether ME-ACI V11 should be expanded with two additional online modules before the next multi-seed qualification.  The answer is currently **no**: the existing method is better presented as three coherent contributions, while the following ideas remain future extensions.

## Candidate A — conformalized source region

### External lineage

- Areces, Mohri, Hashimoto & Duchi, **Online Conformal Prediction via Online Optimization**, ICML 2025.  The work develops online conformal prediction with coverage guarantees for adversarial and stochastic data.
- Wang & Ning, **Conformal Prediction in The Loop: A Feedback-Based Uncertainty Model for Trajectory Optimization**, NeurIPS 2025.  The work couples prediction-set risk and realized trajectory feedback while preserving coverage guarantees.

### Why it fits V11 conceptually

V11 releases a generalized/decision posterior whose masses are useful decision weights but are not calibrated belief probabilities.  A set-valued conformal output could therefore provide a separate uncertainty statement without pretending that the normal-rank aggregate is an exact posterior probability.

### Offline screen on current three held-out runs

Final nearest-truth candidate ranks in the released V11 candidate distribution are approximately:

- H01: `192/210 = 91.4%`;
- H02: `22/201 = 10.9%`;
- H03: `91/206 = 44.2%`.

A naive calibration that retained enough top-ranked candidates to include all three current truths would therefore need roughly **91% of the candidate set**, which is not an informative localization region.

A conservative two-fold consensus ranking is better but still coarse: the current offline screen needs on the order of **56% of candidates** to include all three cases.

### Verdict

`NOT_READY_AS_PAPER_AUXILIARY_MODULE`.

The idea is scientifically valid but the present calibration bank is too small and the resulting source set too broad.  Revisit after the larger independent-seed bank exists.

## Candidate B — conformal information-pursuit planner

### External lineage

Chan, Ge, Dobriban, Hassani & Vidal, **Conformal Information Pursuit for Interactively Guiding Large Language Models**, NeurIPS 2025.  The paper replaces unreliable entropy/mutual-information estimates with uncertainty derived from conformal prediction-set size when selecting the next query.

### Why it fits V11 conceptually

The frozen V11 qualification has an explicit planner limitation: `posterior_guidance_weight=0`, and H01/H03 OFF/ON trajectories are identical.  A future GSL analogue could select sensing goals according to expected reduction of a calibrated source-support set rather than raw posterior entropy.

### Why it should not be inserted now

- It changes the treatment from an inference-module study to an inference+planner study.
- The current held-out V11 evidence would no longer qualify the planner mechanism.
- Proper testing requires a separately frozen action-selection contract and new truth-blind seeds.
- Candidate A is not yet calibrated enough to supply the source sets required by Candidate B.

### Verdict

`FUTURE_PLANNER_EXTENSION`, not part of the current V11 paper method.

## Selected paper structure instead

Keep one frozen runtime method and expose its three internal scientific contributions:

1. amplitude-conditioned conditional inverse-transport source abduction;
2. spatiotemporally replicated identifiability before release;
3. fixed-prior reversible cumulative generalized inference.

This structure has cleaner causal attribution, uses existing held-out evidence, and permits direct offline ablations without contaminating the frozen online result.
