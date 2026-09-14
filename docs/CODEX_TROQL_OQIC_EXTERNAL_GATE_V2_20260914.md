# TROQL/OQIC external gate V2 — distributional-dominance freeze

Date: 2026-09-14

## Single mechanism change

V2 changes only the evidence-release statistic. The V1 representation, raw
Orebro3DSEN inputs, source/null pairs, development/confirmation split, and claim
boundary remain fixed.

V1 asked nearly every target block to exceed an extreme pointwise nuisance
quantile. V2 instead tests the property required by transport-replicated
identifiability: in each direction, the distribution of different-source
relative margins must dominate the matched same-source nuisance-margin
distribution.

This is a development revision after the documented V1 development NO-GO. It is
not confirmation evidence. V2 becomes evidential only if its subsequently opened,
untouched confirmation stage passes without changing this file, the policy, or
the scorer.

## Frozen representation

For each experiment:

1. read only concentration columns `C_000` through `C_222` in upstream order;
2. trim the first and last 10% of rows;
3. divide the remainder into 40 contiguous blocks;
4. take the per-channel median in each block;
5. replace the 27-channel vector by centered spatial mid-ranks and L2-normalize;
6. form each experiment prototype from even-numbered blocks;
7. score odd-numbered target blocks using the own-versus-other cosine-distance
   margin.

No PMFS/GADEN project bank, held wind, unseen seed, or new House is read.

## Frozen distributional-dominance certificate

For each direction independently, compare the 20 different-source margins with
the corresponding 20 same-source nuisance margins.

The direction passes only if all conditions hold:

- Mann–Whitney probability-of-superiority (AUC) is at least `0.80`;
- one-sided tie-corrected Mann–Whitney normal-approximation p-value is at most
  `0.01`;
- at least `0.90` of the different-source margins are strictly positive.

The edge resolves only if both directions pass. Otherwise the two candidates
remain in one observation-quotient cell and no candidate-relative evidence is
released.

## Frozen stages

Development:

- nuisance pair: `Exp01` versus `Exp02` (same source coordinate, different source
  size);
- source pair: `Exp02` versus `Exp03` (different source coordinates);
- permitted raw logs: `Exp01`, `Exp02`, `Exp03` only.

Untouched confirmation, opened only after a development PASS:

- nuisance pair: `Exp08` versus `Exp09` (same source coordinate and fan, different
  source size);
- source pair: `Exp06` versus `Exp07` (different source coordinates under DC-fan
  transport);
- permitted raw logs: `Exp06`, `Exp07`, `Exp08`, `Exp09` only.

The scorer must refuse confirmation after a development failure or after any
policy, scorer, representation-kernel, or development-result hash change.

## Decision and claim boundary

- Development failure: `TROQL_OQIC_V2_EXTERNAL_DEVELOPMENT_NO_GO`; confirmation
  remains unopened.
- Confirmation failure: `TROQL_OQIC_V2_EXTERNAL_CONFIRMATION_NO_GO`.
- Confirmation pass: `TROQL_OQIC_MAIN_INNOVATION_PREMISE_PASS`.

A confirmation pass authorizes only this bounded claim:

> On a public real-sensor dataset and two pre-separated source/null experiment
> pairs, the frozen transport-replicated observation-quotient certificate
> distinguished a different-source edge from a same-source nuisance edge in both
> directions on untouched confirmation data.

It does not authorize online PMFS integration, closed-loop localization
improvement, universal source identifiability, or a new-House/unseen-seed claim.
