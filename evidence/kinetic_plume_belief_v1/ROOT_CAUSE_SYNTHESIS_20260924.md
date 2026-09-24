# Root-cause synthesis after M4-v3 failure

Date: 2026-09-24
Branch: `research/kinetic-plume-belief-v1`
Status: diagnostic synthesis; no ADVANCE claim.

## Central diagnosis

The repeated failures are consistent with a state-closure problem, not a missing scalar feature.

For a horizontal observation plane, the resolved concentration obeys schematically

[
\partial_t C + \nabla_{xy}\cdot J_{xy}
= S - \partial_z J_z.
]

The frozen M4-v3 state stores only one scalar per cell, (C(x,y)), and approximates resolved flux mostly by present local wind acting on that scalar.

But the exact coarse flux depends on unresolved quantities such as:
- sub-cell directional mass distribution;
- concentration-velocity covariance (u'c');
- filament age/dispersion state;
- constraint-active obstacle interactions;
- vertical concentration/flux structure.

Therefore (C(x,y)) alone need not be a closed Markov state even when the local wind field is known.

## Evidence pattern

1. M4-v3 learns a real wind-driven bulk response, but full wind-intervention geometry remains wrong.
2. A causal memory auxiliary improves field MSE but adds only about +0.032 wind-delta cosine and does not cross the frozen 0.5 gate.
3. Oracle replacement within wall<=1 pooled cell (about 24.4% of free space-time) can cross 0.5 in all four comparisons.
4. Oracle replacement in top-25% strain regions can also cross 0.5.
5. Top-25% |Wz| and |dWz| regions can cross 0.5.
6. These masks are not a complete explanation: wall-only and vertical-only supports overlap only partly and most error energy remains outside their union. They are sensitivity proxies for unresolved transport, not sufficient hand-written mechanisms.
7. M4's 0.2 m cell-centre characteristic representation detects zero obstacle-contact source cells in the source-blind contact audit.
8. Restoring 0.1 m continuous sub-cell position reveals nonzero near-wall contacts; with the pre-existing 0.01 m stochastic displacement scale the mean near-wall single-step contact fraction is about 4.86%, while far-wall contacts are negligible.
9. A deterministic wall-slide rule has negligible impact on the frozen M4 response.
10. A simple local vertical-exchange rule can reduce average field MSE but worsens the wind-intervention response, consistent with the fact that vertical exchange depends on vertical concentration structure, not only local Wz.

## Consequence

Do not add more scalar-memory, scalar-residual, wall-slide, or Wz-gating patches to M4-v3.

The next necessary-phenomenon test is whether retaining a low-dimensional **kinetic / directional population state** improves intervention geometry.

This is motivated by 2025 kinetic data-driven turbulence work that learns local collision operators in a discretized Boltzmann state rather than closing turbulence directly in macroscopic variables. The literature anchor does not make D2Q9 itself novel.

## D2Q9 screen interpretation

The D2Q9 physical control is only a representation test.

- If it remains numerically stable, learns nonzero directional persistence, and improves the held-out wind-delta geometry, the kinetic-state hypothesis survives.
- If the learned collision relaxes nearly instantaneously and geometry does not improve, first directional moments are insufficient.
- If D2Q9 fails after a valid stable run, do not rescue it by arbitrary larger velocity sets on House02. Escalation to particle/age states requires an independent necessary-phenomenon justification.

The previous first-moment central-difference run is INVALID as scientific evidence because its loss was NaN from epoch 1. It records a numerical-scheme failure, not a kinetic-state NO-GO.

## Mandatory anti-overclaim ablation if D2Q9 is positive

A positive D2Q9 result is not sufficient to attribute gain to kinetic memory.

Force the trained model to `omega=1`, so directional populations instantaneously
relax to the wind-conditioned equilibrium every step. This preserves the same
positive conservative lattice transport/bounce-back discretization but removes
persistent directional state.

Interpretation:
- full kinetic improves and omega=1 loses the gain -> directional hidden state is supported;
- full and omega=1 are equivalent -> the gain is a numerical finite-volume/streaming improvement, not a kinetic-state innovation;
- neither improves -> first directional moments are insufficient.
