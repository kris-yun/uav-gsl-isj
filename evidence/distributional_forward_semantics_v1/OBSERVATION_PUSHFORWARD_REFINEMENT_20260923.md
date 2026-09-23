# Observation-pushforward refinement of distributional forward semantics

Date: 2026-09-23  
Branch: `research/distributional-forward-semantics-v1`

## Why a direct GenCFD transplant is not enough

The main failure diagnosed in Native PMFS is not merely that its forward simulator is deterministic or low-capacity. The actual interface is also mismatched:

1. the source candidate generates a stochastic plume process;
2. the robot samples that process along a path;
3. the physical/virtual gas sensor has dynamics and memory;
4. PMFS converts those samples into a spatial evidence map;
5. Native then compares that constructed evidence map to one time-averaged simulated hitMap cell by cell.

Therefore a generative plume model that outputs realistic plume fields but is still compared to the current PMFS map through the old independent-cell product can reproduce the same semantic failure.

## Proposed second-order innovation

Let

- `s`: source candidate;
- `g`: geometry / occupancy;
- `w`: wind condition;
- `U`: stochastic plume field/process;
- `tau`: robot trajectory and observation schedule;
- `S`: sensor dynamics, including response/decay memory;
- `M`: PMFS evidence-map construction;
- `E_obs`: the actual observable evidence.

The 2026 statistical-fluid viewpoint motivates a conditional measure

`mu_s = Law(U | s, g, w)`.

The GSL-specific innovation is to infer with the **observation push-forward**

`nu_s = (M o S o O_tau)_# mu_s`,

where `O_tau` samples the plume process along the robot trajectory.

Thus each source candidate is not represented by one hitMap. It is represented by a predictive distribution over the exact evidence object that the localization algorithm can observe.

The source probability map remains the outer PMFS scaffold; the forward evidence semantics are replaced.

## What is new relative to the mother idea

GenCFD / function-space diffusion addresses statistical forward computation of chaotic physical fields. It does not solve gas source localization, robot-path observation, sensor-memory convolution, or source-probability-map inversion.

The proposed GSL adaptation adds:

1. source position as a conditioning variable;
2. geometry/wind conditioning appropriate to indoor plume transport;
3. an explicit robot observation operator;
4. sensor dynamics before evidence comparison;
5. push-forward from plume measure to evidence measure;
6. source-candidate inversion using whole-evidence distributional compatibility;
7. retention of a PMFS-style spatial source probability map for online localization.

This is deliberately larger than changing the Native likelihood or replacing Bayes with another scalar scoring rule.

## Why this directly matches already-observed failure mechanisms

### Mean-field collapse

Current PMFS compresses stochastic transport to per-cell mean hit probabilities. The proposed object retains the predictive distribution until after the observation process.

### Cell-independence failure

The current product score discards spatial/temporal dependence. `nu_s` is a joint distribution over the observable evidence object.

### Sensor-memory confound

The H03 time-irreversibility audit showed that the local analog time direction can be dominated by asymmetric sensor relaxation even when true local gas is zero. The sensor operator `S` is therefore part of the forward generative semantics, not an after-the-fact correction.

### Simulator/reality mismatch

A learned or calibrated `mu_s` can ultimately be trained on GADEN/CFD ensembles rather than only Native PMFS filament outputs. The first mechanism tests must nevertheless use exact Native replay so that any gain can be attributed to retaining stochastic evidence rather than to changing every component at once.

## Decisive pre-training gate

Do not train a diffusion model until this test passes.

For accepted hit-bearing H02/H03 runs:

1. use exact standalone Native replay to retain 200-step source-conditioned stochastic fields;
2. project each candidate ensemble through the **frozen actual robot path** up to the source-update time;
3. apply the **frozen asymmetric sensor response** used by the accepted run;
4. construct a predictive ensemble over the same observable trace/evidence summary used for scoring;
5. freeze a source-blind distributional compatibility score;
6. evaluate truth-nearest source-candidate rank;
7. compare against Native and against a mean/marginal-only baseline;
8. destructive null: independently permute candidate cell/time occupancy while preserving every candidate's per-cell marginal hit probability, then pass the null through the same observation/sensor operator;
9. require the source-identity improvement to materially weaken/disappear under this null;
10. repeat on both independent seeds in H02 and H03.

A positive result would demonstrate that the load-bearing information is the source-conditioned stochastic observation distribution, not a geometry shortcut or a different scalar likelihood.

## Current status

**Mother idea:** statistical hydrodynamics / measure-valued forward computation for chaotic flows.  
**GSL second-order innovation:** observation-pushforward measure-valued source inference.  
**Implementation candidate after validation:** conditional diffusion / function-space generative model.  
**Outer scaffold retained:** PMFS-style source probability map and online candidate/action loop.  
**Old internals not retained:** one mean hitMap per source, independent-cell product evidence, and the assumption that sensor/map evidence is directly comparable to a raw simulated field.

Status: **mechanistically well matched; not yet experimentally validated as the main innovation.**
