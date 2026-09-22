# HCMC V1 — cross-asset mechanism diagnostic

Date: 2026-09-22
Status: **SUPPORTIVE BUT NOT UNIVERSAL / IDENTIFIABILITY LIMIT FOUND**

## Purpose

Test the already-frozen HCMC choices on a different controlled VGR asset:

- H01/H02/H03
- SA/SB
- fast/slow
- 12 episodes
- 240 s
- identical within-House trajectory geometry

No HCMC power or scale was changed:

- p = 1,2,3,4
- scales = 1,2,4,8 cells
- 0.3 m grid

For each episode, its spatial gas field was compared with the opposite-wind SA and SB fields using unweighted multi-order structure-function slope mismatch on common spatial support.

This is a mechanism diagnostic, not the authoritative R2 300-s localization endpoint.

## Result

Cross-wind source identity:

- overall: **10/12 = 83.33%**
- H01: **4/4**
- H02: **2/4**
- H03: **4/4**

Failures:

- H02_SA_fast
- H02_SA_slow

## Why the H02-SA failure matters

The two H02-SA traces are effectively a scalar-excitation failure:

| episode | nonzero samples / 1200 | samples > 0.01 ppm | samples > 0.1 ppm | max ppm |
|---|---:|---:|---:|---:|
| H02_SA_fast | 93 | 0 | 0 | 0.00916 |
| H02_SA_slow | 697 | 0 | 0 | 0.00317 |
| H02_SB_fast | 443 | 203 | 121 | 18.857 |
| H02_SB_slow | 442 | 129 | 108 | 14.729 |

Therefore the failed SA condition contains essentially no resolvable plume amplitude at ordinary gas-hit scales. A cross-scale exponent spectrum cannot be treated as identifiable when the scalar field itself is near numerical/background scale.

## Claim boundary

This diagnostic rejects the strongest possible claim:

> HCMC is invariant across arbitrary transport/wind regimes.

That claim is not supported.

A narrower and physically defensible statement remains:

> When source-conditioned measured/simulated support contains sufficient spatial scalar variation, multiscaling-law conformity can provide source-specific evidence that is substantially different from pointwise plume matching.

The R2 result is candidate-conditioned within each source-hypothesis simulation and remains the authoritative Stage-1 discovery result.

## Consequence for future method design

Do **not** tune a ppm threshold from this diagnostic.

Instead, any future online HCMC release rule should be based on a truth-blind identifiability condition such as:

- sufficient non-degenerate structure-function support over the frozen scales;
- split-support reproducibility of the estimated multiscaling vector;
- or a confidence bound on the slope-spectrum estimate.

That condition is an auxiliary design problem and must be validated independently.

## Decision

- HCMC remains the current primary main-innovation candidate.
- Universal cross-wind multiscaling invariance is **not** claimed.
- Low-excitation HCMC inference must abstain rather than manufacture source evidence.
