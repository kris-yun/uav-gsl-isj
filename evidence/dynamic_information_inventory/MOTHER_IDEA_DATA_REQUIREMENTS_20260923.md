# Mother-idea × information requirements (testability only)

This matrix selects no method and authorizes no new scientific experiment.

| Scientific premise | Required information | Present state | Read-only export sufficient? |
|---|---|---|---|
| Mori–Zwanzig / memory | Source-conditioned ordered state or observable history, plus aligned observations across updates | Native computes 200 internal ordered steps but discards their sequence; only one source update per accepted run | Forward summaries recover model memory diagnostics. One bank/update cannot establish empirical across-update memory or closed-loop benefit. |
| Fluctuation–response | Known time-varying perturbation paired with response under controlled initial state | Candidate uses a fixed 2D wind grid; GADEN time-varying wind is simulator oracle | No. Summary export alone creates no intervention or causal perturbation; future wind forbidden online. |
| Perron–Frobenius / transfer operator | Time-resolved mass/transport transition on a defined state space | Native has 2D filament positions, but no physical mass or concentration; dataset has 3D filament snapshots | Partial: sparse occupancy/filament summaries can test a *model-particle* transition offline, not physical mass transport. |
| Lagrangian coherent structures / FTLE | Time-resolved spatial velocity field and trajectory integration | GADEN 3D snapshots exist offline; Native has fixed estimated 2D grid | No for Native causal online test. Offline oracle-only diagnostic possible, explicitly not deployable evidence. |
| Large-deviation / trajectory ensemble | Many independently keyed source-conditioned stochastic trajectories with tails | One Native realization per candidate in accepted bank; P2 replica machinery exists but disabled | Summary export of one run is insufficient. Additional source-blind replicas require a separate, frozen computation contract. |
| Intervention equivariance | Paired source-fixed transport interventions with identical source and controlled transport change | No accepted paired intervention bank | No. Shadow capture cannot create pairs; future truth cannot be substituted. |

Only model-internal hypothesis dynamics are eligible for a causal read-only export. Simulator oracle fields may inform offline diagnosis but cannot be spliced into an online algorithm. The 200-step temporal summary is a **data capability**, not evidence that any mother idea works.
