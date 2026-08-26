# NACC V14 — Native-Anchored Replicated Causal Semi-Modular Inference

Status: **DEVELOPMENT CANDIDATE / OFFLINE GATE COMPLETE**

Base source: `664b2f9f3ec728d7677ab080629c076ef018f335` (RCEC V13 frozen source).

## Why V14 exists

RCEC V13 showed that causal inverse-transport evidence contains useful signal, but the H02 prospective stress test also exposed a structural ownership error: a misspecified causal transport model was allowed to replace the native PMFS source state. In four revealed H02 seeds, true-nearest candidates were systematically disfavoured by the causal transport model. Geometry/CFD diagnostics further showed that replacing Euclidean source-sensor geometry by simple obstacle/geodesic/streamline surrogates does not reliably restore the correct ordering.

The correction therefore targets **evidence ownership**, not another transport heuristic.

## Imported theory: modular and semi-modular inference under misspecification

The design is motivated by modern modular Bayesian inference:

- Liu & Goudie, JRSS-B 2025, *A general framework for cutting feedback within modularized Bayesian inference*: a suspect/misspecified module should not be allowed to contaminate a more reliable module; cut distributions formalize this information-flow restriction and have a KL projection interpretation.
- Frazier & Nott, JASA 2025, *Posterior Risk of Modular and Semi-Modular Bayesian Inference*: complete cutting trades bias against variance; semi-modular/posterior-shrinkage constructions allow controlled partial influence and can improve posterior risk.

NACC adapts this principle to robotic GSL. PMFS and causal inverse transport are **not treated as independent likelihoods**. PMFS owns the source-state posterior; the causal module supplies only a bounded structural correction.

## Modules

### Trusted module N — native PMFS

Let `p_N,t(x)` be the normalized native PMFS source posterior after the ordinary PMFS source update and before any causal injection.

### Suspect auxiliary module C — replicated causal inverse transport

The frozen ACIT machinery still computes the even/odd conditional-on-hit-count inverse-transport ranks. Define

`r_t(s) = min(z_even,t(s), z_odd,t(s))`.

This is a replicated lower envelope. It is a generalized structural score, not a Bayesian likelihood product and does not require independence between parity views.

## NACC update

Map the candidate score `r_t(s)` to the cells owned by that candidate and solve

`q_t = argmax_q [ E_q[r_t] - KL(q || p_N,t) ]`.

The unique Gibbs solution is

`q_t(x) = p_N,t(x) exp(r_t(x)) / Z_t`.

This is the complete V14 source-state update. There is:

- no House/seed-specific parameter;
- no truth or final-error gate;
- no learned weight or temperature;
- no native-rank replacement posterior;
- no temporal median memory.

The temporal median is intentionally removed. ACIT already scores the cumulative retained event history at each identifiable update, so successive score snapshots are nested, not independent repeated observations. A second all-history median can introduce inertia without creating new evidence.

## Deterministic influence bound

For two supported cells/candidates `i,j`,

`log[(q_i/q_j)/(p_N,i/p_N,j)] = r_i-r_j`.

Therefore, if `Delta_r = max(r)-min(r)`, the suspect causal module can change native pairwise odds by at most `exp(Delta_r)`. With finite normal-rank scores this is a deterministic bounded-influence property. A sufficiently decisive native ordering cannot be arbitrarily overturned by a misspecified causal module.

This directly addresses the H02 V13 failure mode, where replacing the native posterior with a rank-generated posterior flattened a very concentrated PMFS state and created large localization regressions.

## Offline development gate

Operator tested:

`q = normalize(p_native * exp(min(z_even,z_odd)))`.

### Revealed H02 prospective stress trajectories

Three previously frozen H02 runs were re-used only as now-revealed development data. Native shadow grids were available, so this is an exact same-trajectory grid-level replay of the source-state operator.

- pairs: 3
- wins vs the contemporaneous native shadow: 3/3
- pooled improvement: +0.2467%
- worst pair improvement: +0.1367%
- catastrophic regression: 0

The effect is deliberately small: the point of this gate is that the misspecified auxiliary module no longer destroys a concentrated native source state.

### Fifteen previously revealed V11 trajectories

The same operator was applied to the final native shadow on 15 development-visible trajectories using the existing even/odd causal ranks.

- pairs: 15
- wins: 10/15
- pooled change: -0.0131% (essentially neutral)
- worst pair: -1.5709%
- catastrophic regression: 0

This set shows strong tail-risk reduction but does **not** establish a meaningful average localization gain in fixed-trajectory replay. V14 therefore remains a candidate requiring true closed-loop testing; the offline gate establishes safety/plausibility, not efficacy.

## Scientific interpretation

NACC V14 should be described as **semi-modular causal inference under transport-model misspecification**:

1. native PMFS is the trusted physical source-state module;
2. replicated ACIT is a potentially misspecified causal-transport auxiliary module;
3. KL anchoring permits bounded causal correction without transferring ownership of the source posterior.

Do not call the result an exact Bayesian posterior. It is a KL-regularized generalized decision posterior / semi-modular source state.

## Next gate

Materialize the operator in the same binary with an explicit V14 arm, verify exact native anchoring and odds identity, then use revealed mechanism seeds before selecting any fresh confirmatory seed. No formula change is allowed after the V14 source/binary freeze.
