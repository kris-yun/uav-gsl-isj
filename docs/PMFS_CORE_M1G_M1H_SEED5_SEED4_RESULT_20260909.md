# CORE-M1 cross-House closed-loop result (2026-09-09)

## Frozen evaluation

All runs used the same aligned House123 environment certificate and geometry
manifest, native wind helper, map slices, `stepsSourceUpdate=1`, warmup
exclusion, 3 native transport replicas, and exact 0--240 s V3 ZOH evaluation.
The replay/sensor seed was fixed at 12; algorithm seeds 4 and 5 therefore are
not independent plume realizations.

## Results

| variant | screen | same-world joint gate | mean final improvement | mean AUC improvement |
|---|---|---:|---:|---:|
| M1G geometric log pool | H01 seed5 | PASS | +4.258 m | +298.367 m s |
| M1G geometric log pool | H02/H03 seed5 | NO_GO (0/2) | −2.299 m | −187.051 m s |
| M1H mean-log − 0.5 variance | H01 seed4 | PASS | +5.707 m | +359.819 m s |
| M1H mean-log − 0.5 variance | House123 seed4 | **NO_GO (1/3)** | +1.570 m | +82.531 m s |

M1H improved H02's endpoint error (+1.010 m) but worsened its AUC
(−44.549 m s), and worsened both metrics in H03 (−2.008 m, −67.676 m s).
The geometric M1G and robust M1H failures are therefore preserved as honest
counterevidence; neither supports a cross-House closed-loop claim.

## Scientific conclusion

The causal event-time residual is implemented and auditable, and it can yield
real closed-loop gains in individual environments. However, after testing the
transport-invariant geometric pool and a fixed disagreement-robust entropic
pool, the preregistered cross-House utility gate still fails. It is not
scientifically valid to claim that M1 is broadly effective or that the causal
main innovation is validated across House123. The next defensible step is
mechanism analysis or a new preregistered hypothesis; further post-hoc tuning
of this family is stopped.

## Theory boundary

The design is motivated by 2026 work on partial invariance, interventional
fidelity, auxiliary-controlled causal representation, and mechanism-level
identifiability (see `PMFS_CORE_M1H_ROBUST_POOL_DESIGN_20260909.md`). Those
papers support the separation of causal signal from transport nuisance; they
do not replace the failed gas-specific closed-loop gate.
