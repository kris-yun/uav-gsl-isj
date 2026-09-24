# CESS Mainline Freeze v1 — 2026-09-25

Status: **MAIN-INNOVATION CANDIDATE — D1A AUTHORIZED AFTER CODE AUDIT**

## Stable empirical basis

R0 independently passed on 18 sources ×16 realizations.

The most reproducible stochastic object is encounter/support structure, not a
full ppm path density.

At the same time, multiple prior routes showed that stochastic realizations can
reorder exact 0.30 m source cells while retaining a geographically local source
basin.

The resulting scientific question is:

> At what spatial source scale does turbulent encounter evidence carry maximal
> reproducible source information, and can that scale emerge from data instead
> of being imposed as an error tolerance?

## Mother theory

Primary family:
**causal emergence / effective information / information-theoretic
coarse-graining**.

Key anchors:

- Zhang et al., *Dynamical reversibility and a new theory of causal emergence
  based on SVD*, npj Complexity, 2025,
  DOI 10.1038/s44260-025-00028-0.
- Liu et al., *Singular-value-decomposition-based causal emergence for Gaussian
  iterative systems*, Physical Review E, 2025,
  DOI 10.1103/mfct-sxn5.
- Yang et al., *Finding emergence in data by maximizing effective information*,
  National Science Review 12(1), 2025 volume,
  DOI 10.1093/nsr/nwae279.

The useful mother principle is that noisy/redundant microscopic causal channels
can admit a macro representation with higher intervention-defined effective
information / information-transmission effectiveness.

## GSL second-order adaptation

Micro causal state:
0.30 m candidate source cell S.

Effect:
binary turbulent encounter/support history H over frozen observations.

Macro source state:
a spatially connected coarse-graining M=g(S).

Macro intervention:

p(h|do(M=m)) =
  (1/|S_m|) sum_{s in S_m} p(h|do(S=s)).

No macro likelihood receives extra training samples.

The scale is selected by held-out **raw interventional EI lower bound**, not by
manual radius, endpoint error tolerance, PMFS smoothing, or normalized
classification accuracy.

## Corrected D0

Primary-thread audit found an intervention-weighting bug in the older D0/D1
implementation: macro held-out samples were averaged micro-uniformly despite a
uniform-macro intervention claim.

After correction, the exploratory 18-source signal remains:

- micro average raw EI: 1.306475 nats;
- M=12 spatial macro average raw EI: 2.006061 nats;
- corrected gain: +0.699586 nats;
- M=12 spatial percentile versus 250 size-matched random partitions: 0.996.

Thus the positive signal survives the strongest identified confound.

## Why D1A, not the old 630x8 D1

The old D1 is superseded and must not be executed.

D1A uses:

- 168 dense contiguous equal-area source microstates;
- >=143 requirement satisfied;
- 16 fully fresh realizations/source;
- 8/8 symmetric train-validation;
- correct macro intervention weighting;
- realization bootstrap;
- random grouping control;
- no scientific HOLD/rescue.

This is a cheaper and statistically stronger first falsification than 630x8.

## Track A status

Temporal encounter history is a real auxiliary signal, but not the current main
claim.

2025 Physical Review Fluids already studies realistic turbulent encounter
statistics and correlations in Bayesian olfactory search. The present 10-time
operator also cannot support continuous-time renewal/inter-whiff/first-passage
claims without a new observation protocol.

Track A remains a possible auxiliary discrete event-history likelihood if CESS
survives.

## Novelty boundary

Do not claim novelty for:

- coarse PMFS grids;
- multiresolution maps;
- map smoothing;
- binary encounter probability;
- ordinary clustering;
- standard mutual information;
- NIS/NIS+;
- causal emergence as a general theory.

Candidate paper-level novelty, if D1A and later cross-environment gates survive:

> intervention-defined discovery of an information-optimal **source inference
> scale** under turbulent plume stochasticity, using emergent source
> macrostates as the latent state of a PMFS-style probability map.

## Current decision

`CESS_D0_CORRECTED_ADVANCE_D1A`

Only D1A is authorized.

No closed loop, auxiliary-module build, cross-House claim, or final paper claim
is authorized yet.
