# PE-WHRM route freeze

Date: 2026-09-14

## Main innovation

**Permutation-Equivariant Whole-History Ratio Maps (PE-WHRM)** replaces the
PMFS probability-map update kernel while preserving its normalized source-map
interface. It is a simulation-based, neural-ratio estimator over the ordered
history

`H_t = {(pose, time, wind/context, mask, gas)}`.

Within each environment/acquisition stratum, positive pairs are sampled from
the joint distribution `(source cell, H_t)` and negative pairs by source-label
permutation, i.e. the product of marginals. A shared scorer over the physical
source coordinate and the whole history is permutation-equivariant by
construction. At the population optimum its logit is

`log p(H_t | source, context) - log p(H_t | context)`.

Prior-weighted normalization therefore emits the same `pi_t(source)` object
that the downstream PMFS planner consumes. Consecutive-prefix logit
differences provide auditable true-source versus fixed-wrong-source evidence
before any legacy posterior accumulation.

This is an SBI/NRE import, not a causal provider, posterior repair, PINN, or
field-reconstruction module. Causal routes were already audited and did not
establish a main innovation; they remain negative controls, not the next arm.

## Frozen experiment order

1. Read-only contract check: source labels, complete ordered prefixes,
   acquisition-policy/environment strata, positive support for prior-allowed
   source cells, and no future-record leakage.
2. Mechanism smoke: train/evaluate on a tiny synthetic joint-vs-permuted
   history set; verify ratio-moment, exact source-list permutation equivariance,
   and destructive time-position/source-pair permutations.
3. Development shadow replay on existing VGR/GADEN-labelled trajectories only.
   Compare PE-WHRM, calibrated direct `q0`, unchanged PMFS, and a field-only
   probabilistic map. Report fixed-rival signed increments, cumulative margin,
   rank, and map calibration. Do not consume held-out confirmation banks.
4. Only if the shadow gate passes, pre-register a held-out episode split and
   decide whether a fresh House1--3 seed is permitted. House4 is deferred until
   algorithmic and in-domain gates pass because it changes geometry and method
   simultaneously.

## Falsification gate

The route is a NO-GO if the intact PE-WHRM arm is not better than direct `q0`
on fixed-rival cumulative evidence, if the ratio-moment or exact equivariance
checks fail, or if destructive permutations do not remove the claimed gain.
No planner or closed-loop claim is opened by a map-only pass.

## Evidence pointers

- IdeaSpark candidate: `ideaspark_run/pmfs-probability-map-kernel-replacement/phase2_coherence/refined_candidate.json`
- Coherence and numeric trace: `ideaspark_run/pmfs-probability-map-kernel-replacement/phase2_coherence/`
- Collision audit: `ideaspark_run/pmfs-probability-map-kernel-replacement/phase3_collision/collision_hits.json`
- Independent critique: `ideaspark_run/pmfs-probability-map-kernel-replacement/phase3_critique/phase3_critique_output.json`
- Synthetic contract smoke (PASS; not a localization result): `experiments/pe_whrm_smoke.py` and `experiments/pe_whrm_smoke_result.json`
