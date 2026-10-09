# Failure-first review — 2025–2026 gas source localization (GSL)
Date: 2026-10-08. This is a literature-backed screening memo, not new simulations or an algorithm validated for the user's first paper.

## Actual prior evidence (checkable source and delimitation)

### A. Posterior concentration vs reliable source inference — strongest DIRECT reported failure
van Hove, Aalstad, Pirk (2026), Environmental Data Science, DOI 10.1017/eds.2026.10029, https://www.cambridge.org/core/journals/environmental-data-science/article/actively-inferring-methane-sources-with-drones/B9636E970B3888E7503464A41633719E . Section 4.3.2: collaborative **joint** assimilation gave HIGHER cumulative information gain yet WORSE predictive CRPS, plausibly from noisy near-equifinal measurements and particle degeneracy; sequential assimilation with rejuvenation improved CRPS. Sect 4.2.2: particle rejuvenation may widen posterior on uninformative measurements; high emission at distant source may mimic low nearby emission; upwind low-background samples resolve ambiguity. Sect 4.1.3 notes the nature run samples temporal observations independently. This is genuine experimental failure, but sequential assimilation, tempering, multi-model robust likelihood and source-strength marginalization are already existing repairs. **Novelty candidate only if a NEW transport-conditional mechanism and material repeatable source error is demonstrated beyond those strong baselines.**

### B. Time correlation / absent hit — PRIOR WORK directly addresses mechanism
Heinonen et al. (2025), Phys Rev Fluids 10, 064614, DOI 10.1103/9q6q-nlxc, https://journals.aps.org/prfluids/abstract/10.1103/9q6q-nlxc : direct numerical turbulence; policies with independent encounter models tested under correlated flow, failure of quasioptimal under no mean flow. This is not an untouched gap. Historical TNQC / P0 / R0C1 user STOP records block casual rerun under rebranding. Verdict: **REJECT simple temporal-correlation add-on as FIRST PAPER novelty.**

### C. Time-varying emission — already studied and directly solved in part
Lin, Huang, Zhang (2025), Building and Environment 267 112251, DOI 10.1016/j.buildenv.2024.112251, https://www.sciencedirect.com/science/article/pii/S036013232401093X: Bayesian + unsteady adjoint, release forms constant / periodic / declining, temporal sensor acquisition and source strength–location effects. 2026 Sustainable Cities and Society 139 107186 DOI 10.1016/j.scs.2026.107186 optimizes sensor configuration for varying sources. **REJECT merely adding varying emission or temporal inverse as claimed novelty**.

### D. Terrain-aware source posterior and sensor rank invariance — prior art
Tian et al. (2025), IEEE ICRA, DOI 10.1109/ICRA55743.2025.11128134, https://github.com/CHTiansweet/Topography-aware-Gas-Source-Localization : 2D occupancy map and live wind / gas observations; normal and windchange experiments with known source coordinates. The repo's wind is sampled per plume encounter; further source diversity/altitude must be audited, NOT guessed.
Jin et al. (2026), ICRA / arXiv:2605.13208, https://arxiv.org/abs/2605.13208 : relative concentration ranking to estimate posterior without gas sensor calibration, high-fidelity simulation and real tests. Aug 2026 Jin et al. arXiv:2608.28214 already applies rank features and product-of-experts to multi-robot uncalibrated sensors. **REJECT naive rank-based fusion and generic calibration-free novelty**.

### E. Critical NEW 2026 measured benchmark: Red:Vapor
Hinsen, Wiedemann, Shutin, Lilienthal (2026), Scientific Data 13, 586, DOI 10.1038/s41597-026-06927-8, https://pmc.ncbi.nlm.nih.gov/articles/PMC13065752/ ; data DOI 10.5281/zenodo.18299926 (paper's cited version), concept DOI 10.5281/zenodo.16414472 (GitHub badge); code https://github.com/DLR-KN/red-vapor . 39 experimental runs: 8 dense 3D rasters, 22 fly-through, 9 purging runs. PID-AH2 plus MiCS-5524/6814 real sensor time responses in four industrial model topologies, controlled wind. **Critical limitations for our GSL:** source is ONE fixed tank outlet rotated with turntable, not multiple independently varied source locations. It is not a real lake, cannot establish source-generalization or real lake breeze. Great for measured wind/plume/sensor dynamics and simulation-to-measurement cross-validation; verify actual 3D wind vector vs point sensor records and source coordinate contract from files before calling it a source localization test set. Dataset is measured physical experiment, not synthetic ground-truth wind nature run.

## User's ground truth and non-negotiable negative evidence
- M0_STOP 40/40: plume/sensor changes but no material source posterior Brier damage; max 8.85e-8 vs frozen 0.10; two-candidate source posteriors nearly saturated. No rescue.
- R0C1 vertical support 2/4 STOP, P0 source-plume dynamics transfer 0/21 STOP, previous TNQC and AOD no GO.
- FSR (Fengshuling) real shore/terrain and water-land physical geometry, but CFD/thermally forced wind/GADEN candidate-source bank not yet scientifically qualified; R9.3 full mesh/Budget HOLD, check latest engineering reports before new steps. No claim lake-breeze reversal or real thermal observations.

## Strict screener: 4 candidate gaps
| Gap | Actual recent evidence | Novelty-collision risk | First-paper stage | Immediate no-new-sim test |
| --- | --- | --- | --- | --- |
| Posterior concentration worse under noisy collaborative observation | 2026 van Hove Section 4.3.2 measured CRPS deterioration | Sequential MCMC rejuvenation / tempering / covariance-intersection already known | HOLD as **testable failure**, no new method GO | Audit House S2X raw observation alignment and source posterior scoring, compare naive independent vs simple sequential/correlation-aware baselines under source/seed-heldout |
| Time-correlated intermittent hit and no-hit information | 2025 Heinonen correlated DNS experiments | Existing turbulent Bayesian corrections, previous TNQC no signal | STOP as same novelty | Only literature/prior art, don't run simulator |
| Time-varying source intensity | 2025 Lin and 2026 SCS explicit STE methods | Existing time-varying Bayesian adjoint / sensor design | REJECT headline novelty | Don't build FSR release-rate suite just to claim novelty |
| Sensor response lag confounds rank-based source evidence | Red:Vapor PID/MOX physical response; 2026 Jin rank-based GSL | Inverse filtering / deconvolution / rank robustness longstanding; may be third-paper sensor problem | HOLD as **independent external validation opportunity**, not first-paper candidate | Red:Vapor metadata & small-file audit, align PID/MOX time traces at same controlled fly-through, measure rank reversals/lag, source fixed caveat |

## Candidate 2026 theoretical transfers only after direct positive signal
- ICML 2026 task-sufficient world models NOT selected; P0 transfer failed, so do not reuse.
- ICML 2026 Stable Localized Conformal Prediction via Transduction, https://proceedings.mlr.press/v306/min26d.html : finite calibration-set prediction-set stability, not source coordinate improvement. Cannot claim top GSL novelty simply wrapping an existing posterior with conformal sets.
- ICML 2026 Testing for Distribution Shifts with Conditional Conformal Test Martingales, https://proceedings.mlr.press/v306/shaer26a.html : immutable reference under shift, no inference of gas source or 3D transport. Could inspire later qualification/online drift monitor only after evidence of source-posterior failure.
- 2026 UAI adaptive conformal with diffusion priors, https://proceedings.mlr.press/v337/jiang26a.html : adaptation under shift, no source-GSL evidence; heavy model not justified.

## Immediate bounded Codex task — auditing, no gas simulations / no method tuning
1. Retrieve Red:Vapor Zenodo record metadata & checksum and full methodology; independently verify run IDs, one fixed source, 3D spatial grid versus time series, PID/MOS time response, wind records, license and whether fixed time-paired sensor channels exist. Download small metadata first. Only download full dataset if capacity and license checked; no auto run.
2. Reproduce exactly the paper's stated evidence in a **paper-to-gap table** (source quote, figure/table number, what was actually measured, authors' attempted repairs, nearest 2025-26 solutions, what could falsify the claim in OUR endpoint source coordinate/map).
3. Query the available H01/H02 S2X bank hashes, timestamps, route and source grid for an *offline* posterior reliability comparison. If exact compatible repeated observation records / heldout source regimes are unavailable, mark NOT QUALIFIED. Do not invent records or switch to M0.
4. Only if the new measured Red:Vapor dataset permits a fair paired same-route PID-versus-MOS test, run **sensor-dynamics** screening; this is not a GSL score without multiple legal true source positions.
5. Preserve no new simulation, no CFD modification, no expansion of FSR scope, and no first-paper algorithm claim.

## Reviewer-style verdict
**NO new main innovation qualified today.** Strongest direct failure is posterior overconfidence under joint assimilation, but current prior art addresses major parts. New Red:Vapor physical dataset is the most actionable newly found **independent evidence source**. Avoid 'we are the first 3D industrial dataset' or 'more plume changes means stronger GSL'.