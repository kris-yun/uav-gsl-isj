# Literature gap matrix — focused interim sweep

This is an interim targeted sweep to guide the next falsifiable experiment. It is **not** a systematic-review claim.

| Work | Scene / platform | Wind representation | Geometry | Main objective | Source posterior/localization? | Why it does not already close our candidate gap |
|---|---|---|---|---|---|---|
| Ojeda et al., IEEE TRO 2024, DOI 10.1109/TRO.2024.3426368 | mobile robot, realistic indoor obstacles | point wind + online dispersion simulation | indoor map / obstacles | probabilistic GSL | Yes | strong GSL baseline, but does not formulate task-oriented reconstruction of lakeshore 3D transport uncertainty |
| Tian et al., ICRA 2025, DOI 10.1109/ICRA55743.2025.11128134 | wheeled robot, dynamic wind + obstacles | observed local wind | 2D occupancy/topography | learned source likelihood | Yes | already uses topography; candidate novelty must be 3D transport/source-likelihood sensitivity rather than merely adding maps |
| Hutchinson et al., JFR 2019, DOI 10.1002/rob.21844 | UAV outdoor release | meteorology + analytical dispersion | simplified atmospheric model | Bayesian source-term estimation | Yes | mature inverse baseline; useful backbone/benchmark but not lakeshore task-oriented 3D wind inference |
| Bayesian + probability adjoint, STOTEN 2024, DOI 10.1016/j.scitotenv.2023.169802 | field-trial source estimation | dynamic wind | atmospheric dispersion | source-term inversion | Yes | emphasizes inversion/adjoint under dynamic wind, not sparse lakeshore 3D wind reconstruction tied to GSL utility |
| Time-varying source Bayesian adjoint, Building & Environment 2025, DOI 10.1016/j.buildenv.2024.112251 | building dispersion | unsteady flow | building | time-varying source term | Yes | shows source–sensor relation matters strongly; not UAV lakeshore sparse-met → transport → posterior chain |
| Wang et al., CJChE 2019, DOI 10.1016/j.cjche.2019.02.029 | obstructed chemical-spill domain | reconstructed fine wind field from CFD/local sensors | complex man-made geometry | wind reconstruction for spill consequence | No direct GSL posterior | crucial prior art: forbids claiming novelty for “wind reconstruction for gas dispersion” alone |
| Gao et al., CACAIE 2024, DOI 10.1111/mice.13147 | urban | sparse sensors → high-res wind | urban obstacles | wind RMSE / physical consistency | No | shows sparse physics-informed reconstruction is mature |
| GenDA, ICML 2026, PMLR 306 | complex urban, sparse fixed and trajectory sensors | generative data assimilation | held-out geometry / wind | wind RRMSE / SSIM | No | powerful candidate wind prior, but downstream task is not source inversion |
| Physics-informed sensor placement for street-canyon wind reconstruction, SCS 2026, DOI 10.1016/j.scs.2026.107561 | street canyon | sparse sensors | canyon | wind reconstruction + sensor placement | No | sensor placement itself is occupied; our second paper must not simply repeat this |
| Rooftop sparse wind reconstruction, Building & Environment 2026, DOI 10.1016/j.buildenv.2026.114480 | rooftop/UAM | sparse sensors | rooftop | wind-field accuracy / deployment | No | reinforces that sparse wind reconstruction alone is crowded |
| Allouche et al., JGR Atmospheres 2025, DOI 10.1029/2023JD040708 | land–sea breeze LES | 3D unsteady circulation | thermal patches/coast | physical regimes | No | provides physical basis for controlled shoreline forcing; not GSL |
| Wagner et al., JAS 2022, DOI 10.1175/JAS-D-20-0297.1 | Lake Michigan shoreline | profilers/lidar | shoreline boundary layer | lake-breeze vertical structure | No | validates vertical/low-level structure; not source inversion |
| Yang et al., ACP 2026, DOI 10.5194/acp-26-7867-2026 | Lake Chaohu + Hefei | WRF-Chem | lake/urban | lake effect on pollutant transport | No | supports lake–background-wind / convergence / mixing mechanisms; not unknown-source GSL |

## Gap that survives this targeted sweep

The defensible gap is **not**:
- 3D wind reconstruction;
- physics-informed wind reconstruction;
- wind reconstruction for pollutant dispersion;
- topography-aware GSL;
- Bayesian source inversion.

The candidate gap is the missing **task coupling**:

> how sparse, uncertain 3D transport information should be represented/assimilated when the final objective is source posterior quality, and whether wind errors that are equal under global flow metrics are unequal under source-inversion metrics.

## Literature statements to avoid

Do not write:
- “No one has considered wind in GSL.”
- “No one has reconstructed wind fields for gas dispersion.”
- “No one has included topography in GSL.”
- “Lake breeze has not been studied.”

Use:
- “Existing lines are mature but largely separated; the proposed question concerns the coupling between transport-field error structure and source-inversion utility.”

## Papers that Pro should read in full first

1. Ojeda et al., TRO 2024 — PMFS.
2. Tian et al., ICRA 2025 — topography-aware learned GSL.
3. Hutchinson et al., JFR 2019 — UAV Bayesian source term estimation.
4. Wang et al., CJChE 2019 — wind reconstruction for chemical spill dispersion.
5. Gao et al., CACAIE 2024 — sparse physics-informed wind reconstruction.
6. GenDA, ICML 2026 — modern geometry-aware sparse wind data assimilation.
7. Allouche et al., JGR 2025 — unsteady shoreline thermal/synoptic flow interaction.
8. Yang et al., ACP 2026 — lake-driven pollutant transport regimes.
