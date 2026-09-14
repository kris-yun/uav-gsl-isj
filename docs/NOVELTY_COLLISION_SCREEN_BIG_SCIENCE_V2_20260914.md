# Novelty Collision Screen — Big-Science Theory V2

Date: 2026-09-14
Branch: `project/research-master-20260914`

## Scope and warning

This is a targeted collision screen, not an exhaustive bibliometric proof of novelty. The screen used 58 directed web-search queries spanning robotic gas/odor source localization, active sensing, optimal experimental design, adjoint/domain-of-dependence methods, Lagrangian transport, coherent structures, transition-path theory, committors, transfer operators, plume-boundary search, multi-robot localization and sensor response. The collision labels below mean: how directly an existing body of work already occupies the proposed scientific idea in or adjacent to robotic GSL.

## Collision matrix

| Candidate idea | Direct GSL/OSL collision | Representative prior art | Decision |
|---|---|---|---|
| Sensor response-delay compensation / transient response | VERY HIGH | Mobile-robot olfaction literature has exploited transient sensor response for decades; reviews explicitly discuss slow chemical sensors as a standard issue | ENGINEERING CONSTRAINT ONLY; not a main innovation |
| Entropy / information-gain / OED / active sensing | VERY HIGH | Infotaxis (Nature 2007); model-based GSL work explicitly frames exploration as optimal sensor placement / OED; JFR 2025 active sensing and multi-robot mapping | REJECT AS NOVELTY |
| Plume-boundary seeking / casting / zigzag / edge tracking | VERY HIGH | Classical moth-inspired methods; mobile OSL reviews; Measurement 2026 Zigzag-Spiral uses plume-boundary discovery explicitly | REJECT AS MAIN NOVELTY |
| Multi-robot fusion / formation / PoE / more sensors | VERY HIGH | Cooperative model-based GSL, flocking robots, formation-based OSL, active multi-robot sensing | REJECT AS NOVELTY |
| Adjoint / sensor domain of dependence | DIRECT COLLISION | You, Wang & Zhu, AIAA SciTech 2026, `Scalar Source Localization Using Multi-Sensor Domains of Dependence in Turbulent Channel Flow`; broader building-source adjoint inversion literature | USE ONLY AS DIAGNOSTIC/THEORY SUPPORT; cannot be main novelty |
| Generic persistent excitation / observability-first route design | HIGH ADJACENT COLLISION | GSL exploration has long been related to observer design, optimal sensor placement and OED; our own frozen 12-route test also failed physically | REJECT IN CURRENT FORM |
| Fixed simultaneous two-point gradient / difference | HIGH | Bilateral sensor / odor compass / formation-based OSL; direct dual-view difference was also NO-GO in our House02 premise | REJECT |
| Lagrangian coherent structures (LCS/FTLE) for transport topology | MEDIUM | Not a mainstream robotic-GSL family in current reviews, but LCS already appears in urban contaminant source inversion and in 2025 odour-plume mixing/source-separation physics | KEEP AS SUPPORTING PHYSICS / ROUTE PRIOR ONLY; novelty claim must be much narrower |
| Transfer-operator / coherent-set source reachability | LOW-MEDIUM in robotic GSL search | No clear direct robotic-GSL hit in this screen, but strongly adjacent to Lagrangian transport/coherent-set literature | SECONDARY THEORY CANDIDATE |
| Transition Path Theory (TPT) / committor-based source-to-sensor reachability | LOW DIRECT COLLISION in robotic GSL search | No direct robotic gas/odor-source localization use found in this 58-query screen; mother theory is active in statistical/chemical physics, e.g. PRL 2026 `Understanding Mechanisms of Molecular Rare Events from Start to Finish`, Nature Computational Science 2025 committor-consistent pathways | PRIMARY BIG-SCIENCE CANDIDATE FOR FALSIFICATION |

## Important direct collisions

### 1. OED / active sensing is already occupied in GSL

Wiedemann, Shutin & Lilienthal explicitly connect GSL exploration to optimal sensor placement and optimal experimental design. Later active-sensing work uses entropy / information-theoretic objectives for single and multi-robot source localization and mapping. Therefore the claim `we optimize where to measure` is not novel.

### 2. Adjoint / domain of dependence is directly occupied

AIAA SciTech 2026 already uses forward-adjoint duality and multi-sensor domains of dependence for turbulent scalar source localization. Therefore `sensor domain of dependence for gas-source localization` cannot be claimed as our main innovation.

### 3. Plume-boundary ideas are saturated

Boundary acquisition, crosswind casting and plume re-acquisition have decades of history. A 2026 Measurement paper uses plume-boundary discovery explicitly in a Zigzag-Spiral GSL strategy. The Nature 2026 Drosophila plume-edge result can at most motivate physics; it cannot make plume-edge seeking novel in robotic GSL.

### 4. LCS is physically attractive but not cleanly novel by itself

LCS/FTLE is a strong big-science theory for finite-time transport barriers and conduits. However:
- urban contaminant source inversion has used Lagrangian coherent structures;
- 2025 PLOS ONE odour-plume work explicitly computes LCS to analyze odour mixing/source-separation structure;
- modern fluid-mechanics work continues to use LCS for turbulent transport.

Thus `use LCS for gas-source localization` is too broad a novelty claim. LCS may still be a physical diagnostic or route prior inside a more original module.

## Revised scientific bottleneck

The latest House02 evidence is stronger than a sensor-delay or route-ranking problem. In `W_slow`, some source interventions are physically unexposed for all 12 precommitted routes and the four-source response matrix collapses to rank 2. Therefore the upstream question is:

> For a candidate source under uncertain turbulent transport, what is the finite-horizon probability that emitted tracer mass reaches a robot-accessible sensing set before escaping, dispersing below detectability, or the mission horizon expires?

This is a finite-time stochastic transport/reachability question, not primarily a Bayesian-posterior question.

## Primary big-science theory candidate: Transition Path Theory / committor

### Mother theory

Transition Path Theory (TPT) studies reactive trajectories connecting two sets in a stochastic dynamical system. Its central object is the committor:

`q(x,t) = P(reach B before A or horizon | X_t = x)`.

The committor is the canonical probability that a trajectory launched from a state will successfully complete a transition. It is widely used in chemical physics, molecular dynamics, rare-event theory and climate-transition analysis.

Recent mother-theory examples:
- PRL 2026, `Understanding Mechanisms of Molecular Rare Events from Start to Finish` — committor as the ideal reaction coordinate for rare-event pathways.
- Nature Computational Science 2025, `Iterative variational learning of committor-consistent transition pathways using artificial neural networks` — committor-consistent pathway discovery across dynamical regimes.
- JCTC 2026, `Following the Committor Flow: A Data-Driven Discovery of Transition Pathways`.

### GSL reinterpretation

Model a gas filament / tracer parcel from candidate source `s` as a stochastic Lagrangian process:

`dX_t = u(X_t,t) dt + stochastic dispersion`.

Define:
- `B_R` = the space-time sensing tube reachable by the robot/formation under deployment constraints;
- `A` = escape / absorption / mission-failure set;
- `T` = mission horizon.

Then define the source-to-sensor finite-horizon committor:

`q_s(R,T) = P_s( tau_{B_R} < min(tau_A, T) )`.

Interpretation:
- `q_s ~ 0`: this source is physically unobservable for this sensing design; no likelihood repair should be allowed to create confident source evidence.
- `q_s > 0`: the source has a physically supported transport path into the sensing domain.

The associated TPT reactive current can identify the dominant transport channels carrying source material into the sensing region.

### Potential second innovation module

Working name only:

**Transition-Path Reachability Sensing** / **过渡路径可达性感知**

Possible mechanism:
1. compute/estimate finite-horizon source-to-sensor committors for candidate-source groups under transport uncertainty;
2. identify source-discriminative reactive-current corridors, not simply high-concentration or high-entropy locations;
3. choose sensing motion to intersect corridors where candidate committors / reactive currents differ;
4. only allow Bayesian source evidence where source-to-sensor reachability is physically supported.

This is not yet authorized as a method. It must first pass an offline premise test with existing GADEN particle/filament histories.

## Why this is qualitatively different from previous failed lines

It does not ask:
- `what posterior weight should this gas sample get?`
- `where is expected entropy reduction largest?`
- `where is concentration largest?`
- `which fixed route maximizes a singular-value score?`

It asks a physically prior question:

> Which candidate sources have a dynamically possible transition path into the robot's finite-time sensing domain, and through which transport channels?

That directly addresses the observed zero-exposure failure.

## Required falsification before promotion

Before any closed loop or PMFS integration, use existing raw plume/filament assets to test:

1. Does estimated `q_s(R,T)` correctly separate the currently zero-exposure sources from exposed sources across `W_fast`, `W_slow`, and `W_altfast`?
2. Do high-reactive-current corridors actually predict where later gas exposure occurs, without using future gas at runtime?
3. Does a committor/current-based route chosen on design winds increase held-wind source support compared with the same-information OED / entropy / map-only baselines?
4. Does the advantage survive route and source permutations?

If not, reject TPT/committor as a GSL main innovation.

## Current recommendation

- Remove sensor-delay compensation from the innovation map.
- Keep domain-of-dependence / adjoint only as a diagnostic reference because of direct 2026 collision.
- Keep LCS only as supporting transport physics unless a much narrower non-colliding mechanism is established.
- Promote **TPT / committor-based finite-horizon source-to-sensor reachability** to the next big-science candidate for strict offline falsification.
- Do not train a neural committor model first. Start with the existing finite filament/particle bank and empirical hitting probabilities; add learning only if the physical premise passes.
