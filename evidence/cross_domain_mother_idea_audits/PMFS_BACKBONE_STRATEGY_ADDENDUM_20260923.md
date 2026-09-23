# Addendum — classical PMFS backbone, radical evidence replacement

Date: 2026-09-23

The project architecture is now explicitly treated like a classical tracking backbone with replaceable scientific modules.

## Frozen backbone

Keep, unless later ablation disproves their value:
- PMFS spatial source-probability map;
- occupancy/grid geometry;
- PMFS source-conditioned forward simulator;
- quadtree candidate generation/refinement;
- Native PMFS as the baseline implementation.

## Replaceable scientific core

The current Native source score is a product of confidence-blended independent cell agreements:

[
S(s)=\prod_i \mathrm{lerp}\left(1,1-\gamma|p_i^{obs}-p_i^{sim}(s)|,c_i\right).
]

This is the primary location for a radical cross-domain replacement.

The paper need not claim a completely new GSL architecture. It may claim that a classical PMFS probability-map backbone is retained while the evidence semantics, map update, and active sensing modules are replaced by scientifically motivated mechanisms.

## Expert-panel triage

### Candidate main mother theory: non-equilibrium biological error correction

Conceptual source:
- immune kinetic proofreading / nonequilibrium discrimination;
- repeated evidence must survive multiple confirmation stages rather than being multiplied once;
- naturally distinguishes weak persistent evidence from transient false matches.

Recent anchors:
- PNAS 2025, *Parallel reactions on a single T cell receptor offer a robust kinetic proofreading mechanism*, DOI 10.1073/pnas.2514057122.
- SIAM J. Appl. Math. 2025, stochastic Hopfield–Ninio kinetic proofreading.
- Physical Review Research 2025, comparison of kinetic proofreading and kinetic segregation.

This is currently the highest-priority immediately testable mother idea because old/new runs contain full causal sensor traces and candidate static forward maps.

### Candidate auxiliary: robust perfect adaptation / fold-change sensing

Conceptual source:
biological sensing systems suppress absolute background level and respond to relative changes.

Recent anchors:
- Nature Communications 2025, *Toward single-cell control: noise-robust perfect adaptation in biomolecular systems*, DOI 10.1038/s41467-025-67736-y.
- Physical Review E 2026, *Perfect adaptation in eukaryotic gradient sensing using cooperative allosteric binding*, DOI 10.1103/z9xd-xbw5.

Role:
make candidate evidence less sensitive to global plume-strength / transport-gain changes.

This cannot be the main innovation alone because it normalizes evidence rather than creating source identity.

### Candidate auxiliary: population/homeostatic probability-map dynamics

Potential sources:
- replicator-mutator / biological bet-hedging;
- divisive normalization / homeostatic stabilization;
- mass-conserving reaction-diffusion.

Role:
prevent premature collapse, retain multiple source hypotheses, and spatially regularize the probability map.

These are explicitly auxiliary-only until a source-identifying main evidence operator exists.

### Second main-track mother theory: transfer operators

Wait for standalone candidate replay parity across multiple runs.

If source identity exists in the source-conditioned transport dynamics beyond the averaged hitMap, Perron–Frobenius/transfer-operator evidence may replace the Native static cell product while retaining the PMFS map.

## Routes not to recycle

Do not reopen without genuinely new data/theory:
- HCMC cross-scale static conformance;
- HCCE causal-emergence macrostate coupling;
- HCDG static diffusion geometry;
- direct Mori–Zwanzig history proxy from static candidate hitMaps;
- simple large-deviation/SCGF path fingerprint that did not separate from hit-rate-preserving surrogates;
- simple Koopman/delay fingerprint that lacked strong cross-transport identity;
- time-irreversibility proxy as currently formulated.

The purpose of this ledger is to prevent repeated tuning of failed families under new names.

## Immediate kill test before any method name

For biological proofreading transfer:

1. candidate evidence is evaluated over pre-frozen causal sensor blocks;
2. compare Native one-shot product with multistage evidence survival;
3. require source-near candidates to survive more consistently across old and independent plume realizations;
4. require cross-transport source identity on CStar to outperform the trivial hit-rate baseline, not merely match it;
5. time/block-order destruction must reduce the signal;
6. constant/low-excitation cases must return low activation/abstention, never undefined;
7. geometry-only and candidate-permutation controls must fail.

Only after these pass may the mechanism receive a project method name.
