# PRO6 NEXT TASK — Multiview Plume Identifiability Route

Date: 2026-09-25

Primary-thread update:
- strong CESS/FSEI mainline is STOPPED;
- successor/occupation world-model route is also STOPPED as the mainline after D1R D0;
- no new GADEN runs and no final targets are authorized.

New D1R positive signal:

Treat independent plume realizations from the same source as repeated stochastic views.
Shared latent content = source identity/location.
View-specific nuisance = turbulent plume realization.

Linear evidence:
- log(1+ppm) shrinkage LDA, train8/test8 with train-only temperature calibration:
  top-1 about 41.5-43.2%, top-3 about 67.6-70.2%, median rank 2,
  mean true-source log score about -2.81 to -2.95 bits;
- binary encounter shrinkage LDA also improves ranking over independent Bernoulli;
- checkerboard 84-source holdout: source means are predicted only by ordinary spatial interpolation,
  while a pooled Ledoit-Wolf nuisance covariance is learned only from the other 84 sources;
- full covariance whitening improves unseen-source top-1 from about 8-11% to 16-22%,
  top-3 from about 32-36% to 56-59%, and median rank from 5-6 to 3;
- however source-held-out proper log score is not yet better than the Euclidean interpolated-mean model.

Candidate mother-theory family:
- multi-view identifiable representation learning;
- content-style identifiability/disentanglement;
- invariant shared-content representations under view-specific nuisance;
- multi-view causal representation learning as supporting theory.

Priority 2025 anchors already found:
- Kori, Toni, Glocker, ICML 2025, Identifiable Object Representations under Spatial Ambiguities;
- Shrestha & Fu, ICLR 2025, Content-Style Learning from Unaligned Domains: Identifiability under Unknown Latent Dimensions;
- Wu et al., ICLR 2025, Unsupervised Disentanglement of Content and Style via Variance-Invariance Constraints.

Your task:
1. Deep prior-art audit: GSL/olfaction/chemical source localization using contrastive, multi-view, invariant, disentangled, content-style or nuisance-invariant representations.
2. Decide whether independent plume realizations satisfy any identifiable multi-view/content-style assumptions, and where the analogy breaks.
3. Derive a GSL-specific second-order model:
   observation = f(source-content, realization-nuisance, wind/map context),
   with explicit assumptions and a PMFS-compatible calibrated posterior.
4. Explain how to avoid a trivial supervised-classifier relabeling. The main contribution must be more than shrinkage LDA or supervised contrastive learning.
5. Propose one existing-D1R offline D0/D1 gate only. No new simulations.
6. Mandatory baselines:
   - calibrated shrinkage LDA on log-ppm;
   - pooled covariance whitening;
   - independent zero-hurdle / Bernoulli models;
   - ordinary supervised classifier;
   - supervised contrastive learning;
   - source-coordinate regression / prototype interpolation.
7. The candidate must improve both fresh-realization proper score and source-held-out transfer, not only rank.
8. Explicit sim-to-real argument: training may use simulation multi-view data, but online real flight must not require repeated releases per source.
9. STOP if identifiability assumptions are invalid for plume realizations, or if the candidate reduces to ordinary contrastive/domain-invariant representation learning without a GSL-specific scientific object.

Deliver only:
- MULTIVIEW_IDENTIFIABILITY_THEORY_AUDIT.md
- GSL_PRIOR_ART_AND_NOVELTY.md
- GSL_SECOND_ORDER_FORMULATION.md
- D1R_OFFLINE_FALSIFICATION.md
- SIM_TO_REAL_ARGUMENT.md
- one-page GO/HOLD/STOP recommendation.

Do not run simulations.
Do not revive FSEI or successor/occupation as the mainline.
Do not choose a winner from target results.