# TPT / Reactive-Path Novelty Collision Screen V3

Date: 2026-09-14
Status: targeted novelty screen, not exhaustive bibliometric proof

## Decision

Do **not** claim novelty for any of the following:

- `committor = source-to-sensor hit probability`;
- `first-passage / detection probability from candidate source`;
- `Transition Path Theory for generic source/origin inversion`;
- `Bayesian source inference + TPT`;
- `plume reachability` without path-ensemble information.

Those concepts already have direct or near-direct precedents.

## Direct collisions

### 1. Robotic OSL already uses source-conditioned filament arrival probability

Xu et al., *A Bumblebee-Inspired Spatial Memory Navigation Framework for Robotic Odor Source Localization*, Biomimetics 2026, 11(5), 350, DOI 10.3390/biomimetics11050350.

Their POMDP observation model explicitly interprets a miss as no filaments released from candidate source `C_i` reaching the current robot location over the time window, and assigns source-conditioned detection / missed-detection probabilities.

Therefore a scalar `q_s = P(candidate-source material reaches sensor)` is **not** sufficient novelty.

### 2. TPT is already used for origin inversion in a large-scale transport problem

Miron et al., *Tracing the origin of tropical North Atlantic Sargassum blooms to West Africa*, PNAS Nexus 2026, 5(4):pgag085, DOI 10.1093/pnasnexus/pgag085.

The work combines a time-inhomogeneous Markov chain, Bayesian inversion and nonautonomous TPT to infer the origin of a transported material field, and analyzes transition currents from candidate origin regions to the observed bloom region.

Therefore `TPT for source/origin inversion` is not a defensible broad novelty claim.

### 3. TPT transport conduits already exist in environmental transport

Olascoaga & Beron-Vera, *Exploring the use of Transition Path Theory in building an oil spill prediction scheme*, Frontiers in Marine Science 2023, DOI 10.3389/fmars.2022.1041005.

This applies TPT to stochastic transport trajectories and identifies dominant communication conduits from spill source to protected target region.

Therefore `reactive transport corridor` by itself is not novel outside GSL.

## Mother-theory references supporting the scientific object

- Breebaart et al., *Understanding Mechanisms of Molecular Rare Events from Start to Finish*, Phys. Rev. Lett. 136, 168001 (2026), DOI 10.1103/lk32-njx7. The committor is treated as the ideal reaction coordinate and full transition-path ensembles are sampled.
- Chen et al., *Following the Committor Flow: A Data-Driven Discovery of Transition Pathways*, J. Chem. Theory Comput. 22(3):1258–1265 (2026), DOI 10.1021/acs.jctc.6c00007. The committor is used to identify dominant transition channels.
- Megías et al., *Iterative variational learning of committor-consistent transition pathways using artificial neural networks*, Nature Computational Science 5:592–602 (2025), DOI 10.1038/s43588-025-00828-3.

These papers support the **mother theory**, not the novelty of our GSL application.

## Narrow novelty candidate that remains worth falsifying

Working concept:

**Source-Conditioned Transition-Path Fingerprint**  
**源条件过渡路径指纹**

The candidate novelty is not the scalar probability of reaching a sensor. It is the hypothesis that, conditioned on successful finite-time transport into the robot-accessible sensing domain, the **geometry of the successful transition-path ensemble** retains source identity that is lost in marginal hit probability or marginal plume occupancy.

Candidate objects:

- first-entry location/time measure into the sensing domain;
- contribution-weighted successful filament paths;
- source-conditioned reactive occupancy;
- direction-aware reactive current / edge-flow field inside robot-accessible sensing space.

The main falsifiable claim is:

> Across transport regimes, a source-conditioned reactive-current fingerprint preserves source identity **strictly better than** scalar hit probability, first-entry statistics, and unconditional/marginal plume occupancy computed from the same stochastic simulations.

If this does not hold, TPT is demoted to a diagnostic language and is **not** a paper innovation.

## Anti-triviality constraints

A reactive-current map can trivially reveal source location if it includes the source neighborhood. Therefore the premise test must:

1. evaluate only robot-accessible free/sensing cells;
2. mask a fixed source-neighborhood radius defined only from grid resolution (pre-registered, same rule for every source);
3. report the unmasked result only as a diagnostic, never for PASS;
4. keep route, horizon, wind split and metric frozen before held-wind evaluation.

## Current collision status

```text
SCALAR_COMMITTOR_NOVELTY = REJECTED
GENERIC_TPT_ORIGIN_INVERSION_NOVELTY = REJECTED
REACTIVE_PATH_GEOMETRY_IN_ROBOTIC_GSL = LOW_DIRECT_COLLISION_IN_TARGETED_SCREEN
NOVELTY_CONFIRMED = FALSE
NEXT_REQUIRED_STEP = OFFLINE_PHYSICAL_PREMISE + FINAL_BIBLIOGRAPHIC_SCREEN_IF_PASS
```
