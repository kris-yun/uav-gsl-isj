# RR-MVSI Novelty Boundary V1

Date: 2026-09-25

## Recent far-domain anchors

- Kori, Toni & Glocker, ICML 2025: multi-view probabilistic invariant-content representations with theoretical identifiability under spatial ambiguities.
- Shrestha & Fu, ICLR 2025: content-style identifiability from unaligned domains under unknown latent dimensions.
- Wu et al., ICLR 2025: variance-versus-invariance content/style disentanglement with OOD/few-shot transfer.

These establish the mother-theory level. None of these papers makes CCA, content/style or invariance itself novel for this project.

## Important adjacent olfaction prior art

Generic representation disentanglement and contrastive learning are already entering gas/olfactory sensing:

- 2026 Sensors and Actuators B work uses device-aware feature disentanglement for cross-device gas recognition;
- 2026 visuo-olfactory representation work uses contrastive alignment and odor invariance for odor retrieval/localization;
- modern GSL already uses physics-guided neural networks and deep probabilistic source inference.

Therefore the project must NOT claim novelty for:
- disentanglement;
- invariant gas features;
- contrastive odor representations;
- multi-view learning;
- neural source classification.

## Candidate defensible novelty bundle

If D1 survives, novelty must be the integrated GSL mechanism:

1. repeated independently seeded turbulent plume realizations are treated as stochastic views of one source;
2. cross-view moments/content losses explicitly isolate source-shared structure from realization nuisance while allowing source-dependent heteroscedasticity;
3. the representation is required to transfer to source classes excluded from representation training;
4. a source-context encoder predicts content for candidate cells without plume releases from those cells;
5. inference from one online observation yields a calibrated probability over the original PMFS source grid;
6. evaluation includes same-source fresh realization, unseen-source transfer, cross-wind/cross-House and ultimately single-release real flight.

## Kill conditions

Downgrade or STOP if:
- supervised contrastive learning with the same labels/data budget matches the candidate;
- ordinary PCA/LDA/whitening explains the full proper-score gain;
- source-context transfer fails without source-specific plume prototypes;
- cross-view residual independence is badly violated;
- nonlinear identifiability assumptions cannot be justified;
- real deployment requires repeated releases of every candidate source in the new environment.