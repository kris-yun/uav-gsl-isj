# PMFS-backbone-preserving main-innovation strategy

Date: 2026-09-23
Branch: `research/cross-domain-mother-idea-audits-20260923`

Status: **ARCHITECTURE DECISION ONLY — NO NEW METHOD NAMED OR PROMOTED**

## 1. Clarified design philosophy

The project does not need to replace PMFS as a whole.

PMFS can remain the classical backbone in the same way a classical tracker can remain the backbone while new modules replace evidence association, state discrimination, and update logic.

Keep:
- the occupancy/grid representation;
- the measured hit-probability map;
- the source-probability map as the final spatial belief carrier;
- the PMFS candidate forward simulator;
- quadtree candidate generation/refinement unless later evidence shows it is the limiting factor;
- standard PMFS navigation as the initial closed-loop baseline.

The main innovation may radically replace **how candidate evidence is constructed and how probability-map mass is updated**.

## 2. What Native PMFS actually does

From the frozen PMFS implementation:

[
S(s)=prod_i e_i(s)
]

with the per-cell term

[
e_i(s)=operatorname{lerp}left(
1,,
1-|p_i^{obs}-p_i^{sim}(s)|,gamma,,
c_i
ight),
]

where:
- (p_i^{obs}) is the measured hit probability;
- (p_i^{sim}(s)) is the source-conditioned simulated hit probability;
- (c_i) is confidence;
- (gamma) is sourceDiscriminationPower.

This candidate score is then written to every cell represented by the candidate leaf and normalized to form the source-probability map.

Thus the classical PMFS backbone contains a particularly replaceable component:

> **independent static per-cell agreement multiplied over the map.**

The failures already observed suggest that this evidence operator, rather than the probability-map representation itself, is the scientifically interesting place to innovate.

## 3. Failure requirements for any replacement evidence operator

A replacement must improve at least one of these experimentally demonstrated weaknesses:

1. stochastic plume realization changes can destroy a static structural score;
2. transport interventions can preserve source identity while changing plume statistics;
3. low-information/constant fields must not make the method undefined;
4. one or a few mismatching regions must not cause uncontrolled multiplicative collapse;
5. endpoint centroid improvement must correspond to true candidate/source identity;
6. absence of a hit is not automatically strong evidence against a source in an intermittent plume.

## 4. Expert-panel conclusion: distinguish MAIN evidence ideas from AUXILIARY map dynamics

### Main-innovation class
A mother idea qualifies as main only if it creates **new source information semantics**.

### Auxiliary class
An idea that merely smooths, stabilizes, diffuses, or preserves diversity in the source map cannot be the main innovation by itself because it cannot create source identity that is absent from the candidate evidence.

This distinction eliminates several tempting but insufficient routes.

## 5. Mother-idea candidate A — biological adaptive discrimination

External scientific principles:
- kinetic proofreading / nonequilibrium error correction in immune recognition;
- robust perfect adaptation / fold-change sensing in cell signaling and chemotaxis.

Recent anchors:
- PNAS 2025: *Parallel reactions on a single T cell receptor offer a robust kinetic proofreading mechanism*, DOI `10.1073/pnas.2514057122`.
- Nature Communications 2025: *Toward single-cell control: noise-robust perfect adaptation in biomolecular systems*, DOI `10.1038/s41467-025-67736-y`.
- Physical Review E 2026: *Perfect adaptation in eukaryotic gradient sensing using cooperative allosteric binding*, DOI `10.1103/z9xd-xbw5`.

Why this is a plausible transfer:
biological sensing systems discriminate weak true signals from large fluctuating backgrounds by:
- adapting to background intensity;
- responding to relative/fold changes;
- requiring repeated or multi-stage confirmation before committing.

That directly addresses intermittent plume evidence and the fragility of a simple product of independent cell matches.

### Necessary phenomenon before any localization construction
Using only causal information already available in the accepted runs:

1. a candidate near the true source must survive repeated evidence blocks/checkpoints more consistently than wrong candidates;
2. the advantage must survive old-vs-independent stochastic plume shift;
3. source identity under fast/slow transport must exceed trivial hit-rate matching;
4. destroying temporal/checkpoint order must materially reduce discrimination;
5. low-information episodes must yield low activation/abstention rather than undefined or false-confident output.

Fail any of these => discard the transfer.

### Possible later construction if the necessary phenomenon passes
Only after the kill test:
- PMFS map remains the belief carrier;
- current per-cell product is replaced by an adaptive/proofreading evidence operator;
- candidate evidence accumulates through stages rather than multiplying all cells once.

No method name is assigned yet.

## 6. Mother-idea candidate B — transfer/operator transport dynamics

External scientific principles:
- Perron-Frobenius / transfer operators;
- coherent-set and density-evolution dynamics.

Recent anchors:
- 2026 *Dynamical compartments in stirred tank reactors and Markov state modeling for mixing quantification: a transfer operator approach*.
- 2026 *Perron-Frobenius Operator Matching for Generative Modeling*.

Why it remains attractive:
the verified standalone PMFS replay now exposes the 200 × 0.2 s source-conditioned transport process that Native PMFS averages into one static hitMap.

This route would replace static map matching with transport-dynamics evidence while still writing the final result into the classical PMFS probability map.

### Necessary phenomenon
Do not build a localization score until:
- source-conditioned transition/transport dynamics contain candidate/source identity beyond the final time-average hitMap;
- that extra identity survives independent plume realizations;
- it survives source × transport intervention;
- a simple static baseline cannot explain it.

This route waits for multi-run deterministic replay data.

## 7. Ideas demoted to auxiliary modules

### Replicator-mutator / biological bet-hedging
Useful for:
- preserving multiple hypotheses;
- avoiding premature posterior collapse;
- spatial exploration/exploitation.

Not main:
it redistributes existing source evidence but does not create new source identity.

### Divisive normalization / homeostatic plasticity
Useful for:
- preventing one global amplitude regime from dominating;
- stabilizing map updates under gain changes.

Not main:
normalization alone cannot identify the source.

### Reaction-diffusion / morphogen-like pattern dynamics
Useful for:
- spatial regularization;
- local excitation / long-range inhibition;
- consolidating fragmented probability maps.

Not main:
it shapes the probability field after evidence has already been produced.

## 8. Proposed eventual three-module paper architecture

If the biological-adaptive-discrimination evidence passes:

1. **Main module:** new source-evidence semantics inspired by biological adaptive discrimination/proofreading.
2. **Auxiliary module 1:** robust map stabilization/diversity mechanism, chosen only after ablation (e.g. homeostatic normalization or replicator-mutator flow).
3. **Auxiliary module 2:** active measurement/planning mechanism aligned with the new evidence operator.

If the transfer-operator route instead passes:
1. **Main module:** source-conditioned transport-dynamics evidence.
2. **Auxiliary module 1:** uncertainty/degeneracy gate.
3. **Auxiliary module 2:** active sensing that targets transport-state discrimination.

In both cases PMFS remains the recognizable classical probability-map backbone.

## 9. Immediate next experiment order

A. Test biological adaptive discrimination first because the required causal sensor trace + static candidate bank already exist in old/new accepted data.

B. Do not tune on endpoint error. First test:
- true-candidate block survival;
- old/new consistency;
- time-order destruction;
- amplitude/fold-change perturbation;
- CStar source × transport identity;
- comparison against hit-rate and Native per-cell product.

C. In parallel, Codex expands standalone replay. Transfer-operator audit begins only after replay parity exists for multiple runs.

Only a route that passes its necessary-mechanism gates may receive a method name and a fresh holdout.
