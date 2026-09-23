# Mother-idea screening cycle 02 — post dynamic-replay unlock

Date: 2026-09-23
Branch: `research/cross-domain-mother-idea-audits-20260923`
Status: **NO METHOD NAMED / ONE NEW MOTHER IDEA ADVANCES TO A CELL-TRANSITION KILL TEST**

## Screening rule

This cycle follows the post-HCMC/HCCE discipline:

1. remote-domain mother theory;
2. necessary phenomenon;
3. current-data eligibility;
4. early kill test;
5. only after a mechanism survives may a localization construction be designed.

Endpoint error is not used as the first promotion criterion.

---

## A. Large-deviation / path-space trajectory statistics

Mother theory:
- stochastic thermodynamics / large-deviation path ensembles;
- recent 2026 work on dynamical partition functions and path observables.

Necessary phenomenon tested:
- same-source gas-encounter trajectory fluctuations should remain more similar across fast/slow transport than wrong-source trajectories after removing the mean encounter rate.

Proxy:
- block path observables from hit/no-hit and switching activity;
- centered scaled cumulant generating-function features;
- cross-transport SA/SB source identity.

Result:
- 10/12 source identity across block sizes 10, 25, 50, 100 samples.

Critical null:
- independently shuffle hit order within every episode while preserving each episode's exact hit rate.
- fraction of 200 null repetitions as good as or better than real:
  - block 10: 43.5%
  - block 25: 14.5%
  - block 50: 12.0%
  - block 100: 9.0%

Verdict:
`NO_GO_MAIN`

Interpretation:
the apparent path-space source identity is not cleanly separated from encounter-rate / low-order marginal information.

---

## B. Koopman / delay-dynamics operator fingerprint

Mother theory:
- operator-level comparison of nonlinear dynamical systems;
- 2025–2026 Koopman work on turbulent flows and changing dynamics.

Necessary phenomenon tested:
- same source under fast/slow transport should share a dynamical fingerprint more strongly than different sources.

Proxy:
- source-blind AR/delay operator coefficients of log gas time series;
- compare fast↔slow source identity.

Result:
- delay order 5: 8/12;
- orders 10 and 20: 7/12.

Temporal-shuffle null:
- for order 5, 16% of nulls reached or exceeded the real 8/12;
- higher orders weaker.

Verdict:
`NO_GO_MAIN`

No stable same-source operator identity was established.

---

## C. Time irreversibility / nonequilibrium probability currents

Mother theory:
- stochastic thermodynamics;
- time-reversal breaking and entropy production.

First proxy:
- antisymmetric gas-state transition currents across multiple lags.

Result:
- real cross-transport source identity: 9/12;
- full temporal shuffle null: 2.5% reached 9/12;
- reversing only target or only template drops to 4/12;
- reversing both restores 9/12.

Thus a genuine common time orientation exists.

Stronger source-conditioned physical test:
- six-state process built from candidate-relative wind alignment × gas hit/no-hit;
- candidate score from entropy-production / probability-current magnitude.

Result:
- best entropy-production variant: 7/12;
- most variants: 5–6/12;
- directed hit-current variants worse.

Verdict:
`NO_GO_MAIN`

Interpretation:
gas trajectories contain time-arrow structure, but the source-conditioned nonequilibrium current is not a stable source-identity mechanism.

---

## D. Nonequilibrium response / fluctuation-response theory

Mother-theory anchor:
- Giorgini, Falasca, Souza, PNAS 2025,
  *Predicting forced responses of probability distributions via the fluctuation–dissipation theorem and generative modeling*,
  DOI `10.1073/pnas.2509578122`.
- 2026 work continues generalized nonequilibrium fluctuation-response theory.

### D1. Paired intervention response law

CStar provides the unusually strong experimental structure needed for an initial mechanism test:
- identical route;
- same source;
- fast and slow transport interventions.

For each House/source:
- input perturbation = local `wind_fast - wind_slow`;
- response = `log1p(gas_fast) - log1p(gas_slow)`;
- source-specific ridge response kernel;
- held-out spatial/temporal route blocks;
- compare own-source kernel against wrong-source kernel.

Results:
- 0 lag: **24/30** held-out source decisions;
- lag 2: 23/30;
- lag 5: 22/30;
- lag 10: 22/30.

Controls at 0 lag:
- source-specific intercept only: 20/30;
- independent wind-permutation null, 100 reps: mean 19.45/30, 0/100 >= 24;
- circular-shift null, 100 random shifts: mean 19.91/30, only 1/100 >= 24.

Conclusion:
a source-specific transport-response law is present in the paired intervention data and depends on the actual wind/response alignment.

### D2. Stronger fluctuation-response requirement

A stronger GFDT-like proxy was then tested:
- estimate susceptibility from spontaneous slow-state wind/gas fluctuations only;
- block-demean to suppress route-scale trends;
- use that susceptibility to predict the held-out fast–slow response.

Results:
- 0 lag: 4/6 source cases;
- lags 2,5,10: 3/6;
- circularly shifted fluctuation kernels also obtain 2–4/6.

Verdict:
`PAIRED_RESPONSE_PHENOMENON_POSITIVE / FLUCTUATION_RESPONSE_TRANSFER_NOT_ESTABLISHED`

Do not promote response theory as the main innovation from the 24/30 paired-regression result alone.
The deployable stronger premise—recovering the response law from spontaneous fluctuations without seeing the paired intervention—has not been established.

---

## E. Coarse dynamic-operator information test on verified H01 Native replay

New data:
- H01_R2026092201 standalone replay;
- 152 candidates × 200 internal steps;
- static Native support and score exact parity;
- full replay final hitMap bitwise parity against the compiled PMFS kernel.

Question:
does internal temporal dynamics contain source-location information beyond the final static candidate hitMap?

Coarse dynamic representation:
- source-relative filament centroid;
- covariance trace / anisotropy / cross covariance;
- hit-cell fraction;
- per-candidate temporal standardization;
- fitted one-step linear transition fingerprint.

Across all 152 candidates (11,476 candidate pairs):
- dynamic-fingerprint distance vs source-point distance: Spearman **0.0255**;
- static hitMap distance vs source-point distance: **0.1235**;
- dynamic vs static distance: **0.0566**;
- partial dynamic/source correlation controlling static: **0.0187**.

Temporal-order destruction:
- 20 within-candidate temporal shuffles;
- null mean dynamic/source correlation: **0.0210**;
- null mean partial correlation: **0.0199**;
- multiple shuffled nulls exceed the real operator correlation.

Verdict:
`COARSE_DYNAMIC_OPERATOR_REPRESENTATION_NO_GO`

This does **not** reject Perron–Frobenius / transfer-operator theory because the verified replay package contains full cell transitions that were not used in this coarse summary test.

---

# F. Next mother idea: Transition Path Theory / committor / reactive current

Why this idea is scientifically different:

TPT does not require:
- exact plume realization matching;
- a stable static descriptor;
- globally similar transfer operators.

Instead it asks a more source-specific question:

> starting from a candidate source's stochastic transport process, what is the probability/current of reaching an observed gas-support region before reaching a competing sink/no-evidence region?

The central object is the **committor** / reactive current, which is explicitly designed for stochastic paths and rare transitions.

Recent external anchors:
- 2026 *Reactive Flux Matching: Mechanism Discovery and Adaptive Sampling of Rare Events*, arXiv:2606.06295.
- 2026 JCP *A continuous-space analytical framework for committor functions from molecular dynamics*, DOI `10.1063/5.0337005`.
- 2025 JCTC *Nonparametric Determination of the Committor in Multimolecular Systems*, DOI `10.1021/acs.jctc.5c01427`.

Mature open-source implementation reference:
- `deeptime-ml/deeptime` (Markov state models / coherent sets / Koopman and transition-path tooling), active through 2026.

Targeted scite collision search found:
- 0 hits for GSL/OSL + committor / transition-path theory / reactive flux;
- 0 hits for chemical/odor plume + transition-path theory / committor.
This is a targeted screen, not an exhaustive novelty proof.

## F1. Data eligibility

The verified H01 replay package already contains exactly the primitive required:
- source-conditioned filament positions;
- aligned cell-to-cell transitions;
- unique occupied-cell events;
- Native source sampling and wind contract.

Unlike the earlier HCMC/HCCE ideas, this is not a statistic invented after temporal aggregation; it acts on the pre-aggregation transport paths.

## F2. Necessary kill test — before localization

Do not build a posterior.

For each final candidate source:
1. estimate its empirical cell transition matrix from the verified internal particle transitions;
2. define target set B using **source-blind measured evidence only**, e.g. cells with positive measured hit evidence under a predeclared rule;
3. define competing set A from no-evidence / exit states by a predeclared rule;
4. solve forward committor q(i) = probability of reaching B before A;
5. compute candidate reactive flux from its injection neighborhood into B.

Required phenomena:
- truth-near candidates should have higher reactive reachability / flux than spatially remote candidates;
- result must outperform static hitMap/native score at direct truth-candidate rank, not just endpoint centroid;
- random transition rewiring preserving per-cell in/out degree must destroy the signal;
- time/order destruction preserving final occupancy must destroy or strongly degrade it;
- simple first-hit / final hit-rate controls must not fully explain it.

If this H01 pre-screen fails, reject TPT transfer immediately.

If H01 passes:
- replay the other 11 development cases with the frozen replay contract;
- only then test cross-realization source identity and CStar source×transport intervention.

No method name is authorized yet.
