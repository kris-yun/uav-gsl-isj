# Hodge / Helmholtz Plume Decomposition V1 — cheap screen

Date: 2026-09-22
Status: **NO-GO AS MAIN INNOVATION**

## Hypothesis

Construct a transport vector field
`q = rank(gas) * unit_wind`
on the visited spatial grid and test whether source identity is primarily carried by the divergence / potential-like component, while curl-like circulation acts as turbulent nuisance.

This would motivate a Hodge/Helmholtz decomposition as the paper-level mother idea.

## Proxy

Controlled 240-s VGR asset:
H01/H02/H03 × SA/SB × fast/slow.

On interior visited grid cells:
- divergence = d(q_x)/dx + d(q_y)/dy;
- scalar curl = d(q_y)/dx - d(q_x)/dy;
- compare each episode with opposite-wind SA/SB templates using centered cosine.

Gas amplitude is replaced by empirical rank and wind speed by unit direction to suppress simple scale cues.

## Result

At 240 s:
- divergence: **8/12 = 66.7%**
- curl: **6/12 = 50%**
- flow-aligned gas-gradient control: **6/12 = 50%**

Divergence does outperform curl slightly, but is far below the already-established affine-quotient 12/12 source-identity signal.

The result is also unstable over time:
- 160 s divergence 6/12
- 176 s 9/12
- 200 s 7/12
- 220 s 8/12
- 240 s 8/12

Disjoint checkerboard support at 240 s does not rescue the mechanism: valid subsets are around 50% conditional accuracy.

## Decision

The necessary premise is not supported strongly enough.

Do not implement a full graph-Poisson Hodge projection or promote a gradient/curl decomposition as the new main innovation.

The data do not justify the claim that source information lives mainly in the potential component while turbulent circulation is nuisance.
