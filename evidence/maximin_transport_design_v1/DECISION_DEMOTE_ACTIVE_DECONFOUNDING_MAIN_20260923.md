# DECISION — Demote Active Source–Transport Deconfounding as Main Thesis

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`

## Decision

\`NO-GO AS MAIN SCIENTIFIC THESIS\`

Keep:
- transport-confounding diagnostics;
- V4 nuisance-orthogonal score;
- V5 transport-orthogonal sequential criterion;
- SATI as possible auxiliary/ablation.

Do **not** present the broad theme "active source localization under transport nuisance" as the paper-level novel mother idea.

## Direct 2025 collision

Shen, Dong & Huan, *Variational sequential optimal experimental design using reinforcement learning*, CMAME 444 (2025) 118068, includes a convection–diffusion source-inversion experiment with sequential/mobile experimental design.

Public code: \`wgshen/vsOED\`.

In \`experiments/conv_diff.py\`:

- \`n_design = 2\`: 2-D sensor/design location;
- physical state is the current sensor location;
- \`xp_f\` moves the physical state to the new design;
- source-coordinate parameters are PoIs:
  - uni-model: \`n_pois=[4]\`;
  - multi-model: \`n_pois=[2,4,6]\`;
- nuisance parameters include two wind variables:
  - \`n_nuisps=[2]\` when source strength/width are fixed;
  - \`n_nuisps=[4]\` when source strength/width are also nuisance.

In \`vsOED/models.py::CONV_DIFF.rvs()\`, every simulated parameter set appends:

\`\`\`python
wind_speed = torch.rand(n_sample, 1) * 20
wind_angle = torch.rand(n_sample, 1) * math.pi * 2
wind = torch.cat([wind_speed, wind_angle], dim=-1)
params = torch.cat([params, wind], dim=1)
\`\`\`

Thus 2025 prior art already contains the broad structure:

> sequential mobile source-location experimental design with wind/transport uncertainty treated as nuisance.

The paper/framework also explicitly supports nuisance parameters and model discrimination.

## Consequence

The following claims are not defensible as the main novelty:

- first active source-vs-transport deconfounding;
- first sequential source localization with wind nuisance;
- first mobile source-identification design marginalizing transport nuisance;
- first source/model discrimination under convection–diffusion uncertainty.

## What remains potentially useful

Our PMFS-specific transport-tangent construction is still technically distinct:

- PMFS discrete candidate probability maps;
- stochastic filament simulator;
- local candidate-map sensitivity to a shared transport perturbation;
- projection of candidate disagreement onto the orthogonal complement of the transport tangent;
- exact zero-nuisance reduction to native PMFS \`varianceOfHitProb\`.

This could become:
- an auxiliary robustness module;
- a diagnostic explaining model-based information failure;
- a computationally cheap alternative to full nuisance-posterior sequential OED.

But that is an algorithmic distinction, not the high-level mother idea requested for the paper.

## Evidence retained

The corrected Native R1 transport-only A↔B comparison remains scientifically useful:
- source hypotheses materially reorder when only forward wind changes;
- this motivates robustness diagnostics;
- it does not establish novelty.

## Next action

Restart main-innovation search.

Hard filter for the next mother idea:

1. 2025–2026 remote-field top venue / major scientific trend;
2. not already instantiated in source-location / convection–diffusion OED;
3. changes the inferential object or scientific assumption, not merely acquisition reward;
4. maps to PMFS probability-map shell without heavy training;
5. can be falsified offline on recovered Native artifacts before closed-loop implementation.
