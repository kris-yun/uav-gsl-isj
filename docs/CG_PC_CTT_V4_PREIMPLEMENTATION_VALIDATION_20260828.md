# CG-PC-CTT V4 pre-implementation validation freeze

Date: 2026-08-28
Status: PRE-IMPLEMENTATION VALIDATION COMPLETE; development evidence only

## Decision

The paper-level method remains a three-module causal-spatiotemporal framework:

1. **M1 Spatiotemporal Transport Representation**
2. **M2 Cross-Context Invariant Causal Source Residual**
3. **M3 Observation-Resolved Minimum Causal Assimilation**

V3-ORR remains NOT-GO and is not reused as a posterior replacement architecture.

## A. Real multi-context invariance evidence

Using only archived OFF context-bank forward exports from the completed 60-arm package, the intersection across all 50 OFF source-update contexts in each House is:

| House | contexts | common sources | common cells | stable modes lambda>1 | source / interaction energy | raw unseen-seed Top1 | stable-space unseen-seed Top1 | raw Top5 | stable Top5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| House01 | 50 | 74 | 126 | 20 | 109.55 | 33.65% | 34.19% | 43.51% | 43.78% |
| House02 | 50 | 64 | 140 | 32 | 94.30 | 58.13% | 61.41% | 69.06% | 71.72% |
| House03 | 50 | 85 | 136 | 25 | 122.16 | 39.88% | 41.06% | 47.41% | 48.00% |

Split is fixed by seed: train 0..5, validation 6..7, test 8..9. No localization error is used in fitting.

Independent candidate-identity shuffle destruction on the training contexts collapses unseen-seed Top1 to approximately 1.3--1.5%, near chance. Hence the stable source effect is not a candidate-index artifact.

### Interpretation boundary

The global generalized eigenspace is **offline qualification evidence**, not an online sparse-observation classifier. Random sparse-support tests show no consistent stable-space advantage for 1--32 cells. V4 therefore must not project an unobserved full field and pretend it was observed. Online source evidence is evaluated only at actual physical stops.

## B. Physical-stop unit validated from the 60-arm archive

The archived simulator traces and launch parameters show:

- `measurement_block_samples=10`
- `measurement_settle_samples=0`
- `maxUpdatesPerStop=8`

A physical stop therefore yields eight completed block measurements, each block being an average of ten sensor samples. The eight blocks share the same source/member forward prediction at that position and are not eight independent spatial dimensions.

V4 uses one physical stop as one spatial inferential unit. The stop outcome is the eight-block hit fraction `r_j`; the eight blocks have total source-likelihood weight one.

## C. H02 response-bank replay qualification

The recovered House02 V12 bank has 201 geometry-only source carriers x 8 keyed transport members x 1053 cells, T=200, method seed 20260818 and transport substream 6077111455669390931.

Before using it for V4 development replay, it was checked against the archived H02 V3-ORR audits. Across all 37 H02 ON source updates:

- event count matched 37/37;
- RELEASE/ABSTAIN matched 37/37;
- nuisance rank matched 37/37;
- resolution-cell count matched about 81.1% exactly;
- resolved-edge count differed by only about 1.38 edges on average out of 657 local edges.

It is therefore a high-fidelity **development replay surrogate**, but is not claimed to be the original V3 `rawProbabilities` tensor.

## D. H02 truth-blind M2 safety replay on pure Classic paths

The strict physical-stop LOSO rule is:

1. calibration members 0..3 define observation-resolved physical source components;
2. scoring members 4..7 retain member identity across all training stops;
3. leaving out each physical stop, all training subsets must select one common macro component B;
4. on a held-out stop, B may not lose to a rival component;
5. B must beat the source-independent context mixture on that held-out stop;
6. at least two held-out physical stops must be source-informative;
7. deleting any one scoring member may not reverse the accepted component.

On the 50 H02 OFF source-update windows (10 seeds x 5 updates):

- 48 ABSTAIN;
- 2 ACCEPT;
- the two ACCEPTs are seed0/update2 and seed9/update4;
- both accepted components contain the truth-near carrier (truth used only after replay for evaluation);
- previously dangerous seed1/2/3/7 windows abstain.

This is development/post-hoc evidence only. It is a safety/falsification result, not a confirmatory performance claim.

### Important limitation from off-policy V3 trajectories

The same rule can still find stable-but-wrong components on some trajectories already deformed by V3. Therefore **cross-stop stability is not equal to universal model correctness**. This limitation is explicit. V4 prevents the V3 deconfidence trajectory through M3 minimum-change assimilation; it does not claim that one forward family can detect every shared systematic model error.

## E. Temporal-view result

CTT traces preserve both first-arrival/incidence and 200-step occupancy/hit-frequency structure. These views are not identical, but first-arrival and other simple temporal summaries do not reliably resolve source pairs that hit frequency already ties. Consequently:

- temporal transport structure stays in M1 and in ablations;
- first-arrival is **not** a hard M2 release vote in V4.

This avoids adding a decorative 'temporal' module unsupported by the data.

## F. M3 state mathematics stress test

M3 is a minimum-change reconciliation, not posterior replacement.

Given a native PMFS posterior `q_N`, a validated macro region B, and stable branch mass `alpha` on B:

- if `beta = q_N(B) >= alpha`, output is exactly `q_N`;
- if `beta < alpha`, use the KL/I-projection that raises only B's mass to alpha and preserves native conditional proportions inside B and its complement.

10,000 randomized probability-state tests gave:

- maximum mass-constraint error: `4.44e-16`;
- maximum conditional-ratio error: `2.22e-16`;
- exact-native error when the constraint is inactive: `0`;
- candidate permutation error: numerical roundoff only (~1e-16).

Sequential synthetic tests also verify that a later genuinely opposite stable likelihood can reverse an earlier macro correction; history is therefore not frozen incorrectly.

## G. Final design corrections before C++

1. The global cross-context stable eigenspace is **offline evidence/diagnostic only**; it must not be applied to unobserved feature cells online.
2. Online M2 uses source-vs-context residual likelihood at actual physical stops and observation-resolved source components.
3. Scoring transport-member identity is coherent across stops: marginalize members only after accumulating the stop-set likelihood within each member.
4. `eps_T = 0.5/(T+1)`; with T=200 the numerical value happens to be 0.5/201. Candidate count is unrelated.
5. V4 never treats eight repeated blocks at one stop as eight spatial observations.
6. V4 never normal-rank transforms absolute source evidence.
7. ABSTAIN returns native PMFS exactly.
8. ACCEPT is a minimum macro-region correction; it never clears and replaces the full native posterior from a geometry prior.
9. Seeds 0..9 are permanently development-only. Fresh confirmation must use unseen seeds.

## Authorization

The mathematical design is sufficiently constrained for a C++ implementation + infrastructure smoke + **one fixed development closed-loop batch** on the already-revealed seeds 0..9.

This is not yet authorization to call seeds 0..9 confirmatory. If the fixed V4 development batch meets the frozen endpoint, freeze binary/source/launch hashes and then run fresh confirmatory seeds 10..19.

`CODEX_IMPLEMENTATION_AUTHORIZED = YES`
