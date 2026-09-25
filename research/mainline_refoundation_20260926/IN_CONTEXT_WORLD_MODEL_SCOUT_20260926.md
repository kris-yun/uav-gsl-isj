# Candidate Scout — In-Context Partial-Observation Physical World Model

Date: 2026-09-26

Status: LITERATURE / FEASIBILITY SCOUT ONLY. No experiment authorized yet.

## Why this family is being considered

Repeated project failures share one pattern:
- a representation/operator can fit one fixed environment or local source support;
- the sign/value changes under new wind, source support, probe protocol, or House;
- forward-field accuracy alone does not guarantee inverse source discrimination.

A candidate mainline should therefore adapt the observation operator to the current physical context rather than freeze it in global weights/statistics.

## Recent anchors

1. VICON, TMLR 2026:
Vision In-Context Operator Networks for Multi-Physics Fluid Dynamics Prediction.
Key property: infer/adapt a 2-D fluid operator from a small context without weight updates; public code/checkpoints.

2. LANO, AAAI 2026:
Learning Neural Operators from Partial Observations via Latent Autoregressive Modeling.
Key property: operator learning when observations are sparse/incomplete, using mask-to-predict and a physics-aware latent propagator.

3. LILAD, AAAI 2026:
Learning In-context Lyapunov-stable Adaptive Dynamics Models.
Key property: short trajectory prompts adapt dynamics models under distribution shift; supporting evidence for in-context physical adaptation, not a direct GSL method.

## Required distinction from failed M4

Any successor must NOT repeat:
- optimize full-field L2 and hope inverse ranking improves;
- assume reusable additive wind/source deformation;
- require source superposition;
- train a fixed monolithic field operator and evaluate only forward error.

Potential new object:

`environment-conditioned observation operator`

mapping:
`(map/occupancy, sparse wind context, candidate source, sensor query space-time) -> predictive observation distribution`.

Primary scientific endpoint must be candidate source likelihood/ranking/probability-map quality on held-out environments, not full-field reconstruction.

## Deployment constraint

At runtime the method may use:
- mapped occupancy/geometry;
- onboard/sparse wind observations;
- robot/sensor position and timestamps;
- gas observations from the actual search.

It may NOT require:
- a dense stochastic source bank generated in the target environment;
- known labeled source-output examples from the target environment;
- full simulator wind field unless an onboard estimator is explicitly supplied.

## Admission before coding

Do not authorize an experiment until we can specify how the model adapts to a new environment using only legal deployment context, and why this differs mathematically from M4.

If adaptation secretly requires target-environment labeled plume examples, reject the candidate.