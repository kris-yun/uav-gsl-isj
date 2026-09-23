# Novelty audit v1 — Anytime-valid / e-process gas-source localization

Date: 2026-09-23  
Branch: \`research/anytime-valid-source-eprocess-v1\`

## Searches performed

Targeted literature/web searches included combinations of:

- e-process + robot + localization;
- e-value + robot + localization;
- confidence sequence + robot + localization;
- e-process + source localization;
- anytime-valid + source localization;
- confidence sequence + active sensing;
- e-process + active sensing;
- safe testing + sequential design + localization;
- gas/odor source localization + sequential hypothesis testing / stopping / confidence.

No direct robotic GSL paper was found in this screening that maintains candidate-source e-processes or a time-uniform spatial source confidence set.

This is a negative search result, not proof of absence.

## Closest GSL stopping practice found

### Source-term-estimation GSL
Representative STE work stops when posterior entropy falls below a predetermined threshold or at a fixed iteration/timeout budget.

### Recent mobile GSL
Recent particle/Bayesian approaches likewise use posterior concentration/entropy or iteration limits.

### PMFS
Official PMFS stops when spatial variance of the source-probability map is below \`convergence_thr\`.

These are uncertainty/convergence criteria, not anytime-valid error certificates.

## Classical collision

Controlled sensing / active multihypothesis testing already jointly optimizes:
- sensing actions;
- likelihood evidence;
- stopping;
- decisions.

Therefore M2 cannot claim active sequential testing as novel.

## Modern e-process collisions / parents

### Safe Testing, JRSS-B 2024
Provides the modern e-value/e-process framework including composite hypotheses and nuisance handling.

### Adaptive anytime-valid inference, 2025–2026
Recent work develops e-process/confidence-sequence validity under adaptive experiments.

### Robotics 2026 near-neighbor
Chen & Weng, *Sim-to-Real Betting on the E-Process*, arXiv:2606.24038, applies simulator-assisted e-process/confidence-sequence ideas to robot performance testing.

It does not appear to perform:
- spatial source-hypothesis inversion;
- candidate-wise source elimination;
- active source-search action selection;
- safe source declaration.

## Current defensible research question

Not:

> Can e-processes be used in robotics?

But:

> Can a mobile gas-source localizer maintain an anytime-valid spatial source confidence set and stop with a spatial error certificate while its own measurements are adaptively selected from the same evolving evidence?

## Required final novelty check before publication

Search at least:
- GSL/OSL;
- active sensing;
- active diagnosis/fault isolation;
- adaptive experiment design;
- sequential spatial search;
- robotics safety certification;
- source detection/localization in radiation/acoustic/chemical domains.

If an existing work already inverts per-location e-processes into a spatial confidence set under adaptive sensor motion, M2 must be narrowed or killed.
