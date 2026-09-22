# Mother-idea audit cycle after deterministic candidate replay

Date: 2026-09-23
Status: **NO MAIN INNOVATION PROMOTED YET**

## New data capability

Standalone replay of H01_R2026092201 now reproduces the Native PMFS candidate forward model exactly for all 152 evaluated candidates and recovers ordered 200 x 0.2 s source-conditioned internal dynamics without perturbing the ROS closed loop.

This changes only data eligibility. It does not itself validate any transport-dynamics mother theory.

Transfer-operator / Perron-Frobenius ideas are now technically testable **for this one realization**, but cannot be promoted or meaningfully cross-realization-tested until the same frozen replay contract is extended to additional accepted realizations.

## Audit A — path-space / large-deviation proxy

Necessary phenomenon tested on the controlled CStar SA/SB x fast/slow episodes:

- build block-level fluctuation / SCGF fingerprints from encounter trajectories after removing the mean;
- classify source identity across the opposite transport intervention.

Observed:
- 10/12 source identity over block sizes 10, 25, 50, 100.

However a destructive surrogate that preserves every episode's hit rate while shuffling time order frequently matches the real result:
- block 10: 43.5% of 200 nulls >= real;
- block 25: 14.5%;
- block 50: 12.0%;
- block 100: 9.0%.

Verdict:
**NO-GO as a large-deviation/path-space mother mechanism.**
The apparent signal is not sufficiently separated from low-order encounter-rate structure.

## Audit B — Koopman / delay-dynamics fingerprint

A lightweight delay-linear dynamics fingerprint was compared across fast/slow source interventions.

Best:
- 8/12 source identity for AR/Koopman-style order 5;
- marginal-preserving full temporal shuffles matched/exceeded it in 16% of null repetitions;
- higher orders were weaker (7/12; ~28% null exceedance).

Verdict:
**NO-GO.**
No strong evidence that same-source episodes preserve a transport-invariant Koopman fingerprint.

## Audit C — nonequilibrium time irreversibility / entropy-production structure

Antisymmetric state-transition fluxes (forward minus reverse transition counts) initially gave:
- about 9/12 for a canonical 4-state multi-lag representation;
- full-shuffle null >= real in 2.5%.

But mechanism-specific ablation fails:
- symmetric transition features, which contain no time-arrow information, give 10/12;
- complete transition features also give 10/12;
- across 3/4/5 state families, symmetric/full features are usually as good as or better than the antisymmetric irreversible part.

Verdict:
**NO-GO as an irreversibility / entropy-production mother mechanism.**
Temporal state-transition organization exists, but the time-arrow component is not load-bearing.

## Audit D — measured transition-operator proxy

Because full transition features yielded 10/12, a row-normalized conditional transition matrix was tested to remove raw state occupancy as much as possible.

Result:
- canonical conditional-transition source identity = 10/12;
- after completely shuffling each gas sequence in time while preserving its marginal values, **300/300 null repetitions remain 10/12**.

Verdict:
**INVALID AS TRANSFER-OPERATOR EVIDENCE.**
The measured scalar transition proxy is completely explained by episode marginals / encounter rate.

This does not reject the actual PMFS particle/cell transfer operator recovered by standalone replay; it only rejects using the CStar scalar gas transition matrix as evidence for it.

## Audit E — nonequilibrium fluctuation-response proxy

Mother-theory anchor:
Giorgini, Falasca, Souza, PNAS 2025, "Predicting forced responses of probability distributions via the fluctuation-dissipation theorem and generative modeling", DOI 10.1073/pnas.2509578122.

Necessary phenomenon proxy:
- use source-blind local wind u, v, |u| and measured gas;
- construct lagged cross-response fingerprints;
- test fast<->slow source identity;
- compare with circular time shifts that preserve wind and gas marginal/autocorrelation structure while destroying wind-gas alignment.

Positive observation:
- log-gas response fingerprint = 11/12;
- robust over lag horizons;
- 200 circular-shift nulls reach 11/12 in only ~0.5-1.5%;
- gas-only temporal structure = 8/12;
- wind-only = 0/12;
- SA and SB wind traces are bitwise/numerically identical within each House/transport episode, so source identity does not leak through different winds.

Critical kill test:
- raw-gas **zero-lag only** already yields 11/12;
- positive-lag causal response gives 11/12;
- negative-lag / anti-causal response still gives 10/12.

Verdict:
**DO NOT PROMOTE FLUCTUATION-RESPONSE.**
There is strong source-specific wind-gas coupling, but directional response dynamics add only a marginal increment beyond instantaneous co-variation. The evidence is more consistent with source-specific wind-gas spatial coupling along the identical route than with a fluctuation-response law.

## Current transfer-operator status

The most scientifically aligned remaining mother-theory family is still:

**Perron-Frobenius / transfer-operator transport dynamics**

Recent cross-domain anchor:
Anna Klunker et al., Industrial & Engineering Chemistry Research 2026,
"Dynamical Compartments in Stirred Tank Reactors and Markov State Modeling for Mixing Quantification: A Transfer Operator Approach",
DOI 10.1021/acs.iecr.6c01170.

Public authors' code:
https://github.com/akluenker/Compartment-paper

The paper constructs transition matrices directly from trajectory data and uses transfer-operator / coherent-set analysis of mixing dynamics.

Why it remains eligible:
- PMFS candidate replay now exposes the exact analogous primitive: source-conditioned filament/cell trajectories and transitions;
- unlike the rejected CStar scalar-transition proxy, the replay trajectories are actual model-particle transport under a candidate source and estimated wind.

Why it is **not yet a candidate main innovation**:
- only one realization has exact replay dynamics;
- no cross-realization source identity has been tested;
- no source-position / transport intervention test exists on replayed candidate dynamics.

## Required next data gate

Extend the exact standalone replay, unchanged, to the remaining accepted independent-plume runs.

Before any source-localization construction, test only:

1. candidate-level transfer-operator representation derived from per-step cell transitions;
2. same-house cross-realization score/operator reproducibility;
3. truth-nearest candidate rank and source-distance association;
4. operator-destruction nulls:
   - time-order destruction;
   - source-location permutation among candidate transition operators;
   - transition-row permutation preserving marginal occupancy;
5. geometry-only controls.

If the transfer operator cannot carry source-specific information across independent plume realizations, reject it before any localization posterior is built.

## Current conclusion

No main innovation has been found yet.

The cycle has nevertheless removed four attractive false leads before method naming:
- large-deviation path statistics;
- Koopman/delay fingerprints;
- time irreversibility;
- fluctuation-response.

The transfer-operator route remains the next legitimate mother-theory audit only because the new deterministic replay now exposes the physical object that theory actually acts on.
