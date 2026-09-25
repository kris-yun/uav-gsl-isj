# JTD Route Decision After Pro Review + E1 HOLD

Date: 2026-09-25

## Frozen upstream status

- JTD-G0: `JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL` remains valid as an 18-source discovery result.
- JTD-B0: `JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE` remains valid for the pooled-covariance bridge actually tested.
- JTD-B1: `JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED`, K_min=4, retained as a sampling-depth result but not used as a new mainline prerequisite.
- JTD-E1: `JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL`; average cross-environment effect is positive, but source-level breadth gate failed.
- E4A/E4B/IPTO/LSC/WCIG remain stopped as mainlines.

## Independent Pro review corrections accepted

1. FULL-vs-SHUFFLED does not isolate only fitted cross-block dependence because refitting OAS changes shrinkage and fitted block marginals.
2. BLOCK-PRODUCT is a mandatory ordinary comparator, not a secondary curiosity.
3. A matched block-diagonal control must be constructed from the already-fitted FULL covariance by zeroing only cross-block entries; no OAS refit.
4. SHUFFLED remains a destructive diagnostic, not the primary deployable-model comparator.
5. Dense assessment is historical frozen-bank evaluation, not a fresh blinded confirmation.
6. The old shuffle seed formula must not be extended to 168 sources; use full-tuple domain-separated hashing.

## Change to previous primary-thread plan

The standalone E1D diagnosis is superseded and must NOT be executed as a separate serial gate.

Its useful diagnostics are integrated into dense G1A:
- frozen nearest-neighbor pair margins;
- Gaussian score decomposition for overconfident wrong-neighbor cases;
- BLOCK-PRODUCT comparison.

## Sole next experiment

`JTD-G1A`: one zero-plume, full-168-source dense frozen-bank assessment.

It must simultaneously answer:
1. Does FULL remain useful when candidate density increases dramatically?
2. Does FULL beat the ordinary BLOCK-PRODUCT model on proper probabilistic scoring?
3. Does FULL beat MATCHED-BLOCK-DIAG, which shares the fitted block marginals and differs only by cross-block covariance?
4. Are any gains broad across sources and robust to heavy-tail targets?
5. Does FULL preserve or improve spatial localization probability around the true source and nearest-neighbor discrimination?

## Consequence

Only a dense G1A GO authorizes deeper cross-environment confirmation work.

A dense STOP freezes JTD as an interesting 18-source / limited-environment statistical finding but not a main-innovation route.

House01 DEV and House03 remain sealed throughout G1A.