# GSL 2025–2026 failure-first literature screening — additional round

Date: 2026-10-08
Evidence class: targeted publisher paper/abstract/preprint review, NOT experimental proof in House or FSR, NOT a completed ResearchStudio automated skill run.
Main endpoint remains **industrial GSL source coordinates and a 2D probability map**. Emission-rate quantification, environmental mapping, plume RMSE, monitoring site design, and wind reconstruction are adjacent objectives, not interchangeable results.

## High-impact newly verified prior art

| Reference | What the paper really established | Task | How it changes our innovation screening |
| --- | --- | --- | --- |
| Vänskä, Weidmann & Ursin, *Inverse Problems* (2025), DOI 10.1088/1361-6420/adfb29, https://iopscience.iop.org/article/10.1088/1361-6420/adfb29 | Nonstationary **3D source/concentration Bayesian state estimation**, in simulation and real controlled methane release; reports 8.9 m average localization bias on experimental set in paper concluding results. Authors flag *inhomogeneous winds and complex topography* as future extension. | gas source maps / location + intensity with **multi-open-path laser**, not UAV point samples. | **Reject novelty = 3D inverse source mapping + Bayesian posterior + memory.** Genuine research gap only in applicability under complex terrain and UAV point-sampling; neither guarantees new algorithm. |
| Wang et al., *Urban Climate* (2026), DOI 10.1016/j.uclim.2026.102990, https://www.sciencedirect.com/science/article/pii/S221209552600221X | Tested industrial park CFD–RSM–LP 3D source-receptor inversion, reported >50% improvement over 2D and source–sensor angular structure. | **Emission intensity estimation**, NOT necessarily source-coordinate GSL. | **Reject novelty = 3D transport, 3D source–receptor mapping, wind-angle-aware sensor choice.** Cannot transfer its 50% gain to our source coordinates. |
| Gu et al., *Annals of Nuclear Energy* (2026 online; Nov issue), DOI 10.1016/j.anucene.2026.112500, https://www.sciencedirect.com/science/article/pii/S0306454926003889 | Physical wind-tunnel Gaussian-hill tracer data and monitoring placement/height criterion; existing 2D tunnel scope and explicitly recommends 3D+field validation. | aerosol source-term initialization and monitor siting. | **Reject novelty = multiheight hill monitoring / terrain vertical influence.** 3D lake-geometry controlled GSL remains an untested application-specific research question. |
| Kim et al. (2026-08 preprint), arXiv 2608.16221, https://arxiv.org/abs/2608.16221 | Physical dependency-guided **sequential** wind → concentration → source posterior estimation, sparse mobile robot samples, real-robot online feasibility; article is **preprint**, peer-reviewed venue unverified. | indoor gas source **position posterior**. | **HIGH novelty collision with our previous wind+plume+source 3-stage neural idea.** Cannot nominate it unchanged as novelty. |
| Zhao et al., *JGR Atmospheres* (2026), DOI 10.1029/2025JD045952, https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JD045952 | UAV plume-meander produces conventional inverse Gaussian / mass-balance **emission-rate** MAPE 27–46%; flight-speed/plume-centroid-speed ratio important; sparse-to-average-plume U-Net already improves rate errors 30→22% in LES and 38→29% in controlled release. | **Emission rate**, NOT source location error. | Actual measured and simulated failure, but **reject naive plume-averaging network / turbulence-invariant representation** as new. Transfer to source-position confusion untested and potentially contrary to M0. |
| Mohammadloo et al., *Atmospheric Measurement Techniques* (2025), DOI 10.5194/amt-18-1301-2025, https://amt.copernicus.org/articles/18/1301/2025/ | In 1001 historical drone flights and analytic error assessment, coarse vertical/horizontal sampling can entirely miss plume and cause emission-quantification errors up to ~100%. | **Rate measurement**, NOT source location. | Strong evidence of *measurement coverage bottleneck*, but sampling-grid fixes and flight-density controls are existing approaches; not a primary method innovation by themselves. |
| DeYoung & Evans, *Weather and Forecasting* (2026), DOI 10.1175/WAF-D-25-0197.1, https://repository.library.noaa.gov/view/noaa/73320 | 55 radiosondes / 4 Lake Michigan missions, operational HRRR struggles with sharp thermal gradients immediately above lake and at MABL cap. | real lake **meteorology**, NO known gas source. | Confirms lakeshore multiheight thermal structure is a legitimate physical measurement problem; does NOT establish FSR CFD lake-breeze truth or source localization harm. |
| Goodell, Anderson & Leang, *Robotics and Autonomous Systems* (2026), DOI 10.1016/j.robot.2026.105431, https://www.sciencedirect.com/science/article/pii/S0921889026001041 | Find-and-consume infotaxis for unknown-number multiple live methane sources. | multiple source GSL. | **Reject 'multiple sources of unknown number' as headline novelty.** |
| UGAS, IEEE SmartIoT (2026), DOI 10.1109/SmartIoT70864.2026.00009, https://ieeexplore.ieee.org/abstract/document/11677853 | Uncertainty-guided hybrid static+mobile gas localization and continuous-time irregular samples. | source position, hybrid sensor network (small room). | **Reject generic uncertainty-driven active supplementation as main novelty.** |

Other frozen prior work: Tian et al., 2025 IEEE ICRA topography-aware GSL, DOI 10.1109/ICRA55743.2025.11128134; van Hove et al., 2026 *Environmental Data Science* DOI 10.1017/eds.2026.10029; Piro et al. 2025 many-wrong-model Bayesian inverse; Heinonen et al. 2025 turbulent correlations; Red:Vapor 2026 Scientific Data DOI 10.1038/s41597-026-06927-8. Reuse existing earlier collision audits; do not pretend fresh novelty.

## Round 2 candidates, qualified strictly for source coordinate output

### Candidate A: Transport-aware source-coordinate discrimination in thermally forced lakeshore with only sparse UAV point sensors
**Evidence:** Published 2025 3D Bayesian tomography already reconstructs 3D concentration/source but calls out inhomogeneous wind and complex terrain. 2026 industrial 3D CFD study demonstrates importance for intensity, and 2026 lake meteorology validates physically sharp gradients. **Inference**: FSR may support challenging GSL observations in which those effects translate into source-coordinate posterior ambiguities.
**Prior-art threat:** 2007/2008 building-resolving urban Bayesian inversion already handles complicated terrain; 2025 ICRA uses terrain and wind; 2026 Kim wind-concentration-source sequential physical dependencies, 2025 Vänskä joint 3D source posterior. Thus 'add 3D wind+Bayes' is definitely NOT novel.
**Own evidence:** M0_STOP correct 8/8 across wind arms with saturated two-source posteriors; R0C1 2/4 vertical tests STOP; FSR no qualified paired thermal GSL data. **Decision: CONDITIONAL SCIENTIFIC PROBLEM, not accepted innovative algorithm.**
**Only fair gate after FSR qualification:** multi-legal-source source-heldout under matched routes and thermal forcing; baseline PMFS + multiheight simple interpolation + 3D physical forward likelihood + source-strength nuisance and existing sequential conditional/3D Bayesian approach. Require material source-rank/MAP error change across sources and seeds, not only plume distortion; ensure 3D deployable method has measurements and no oracle wind leakage.

### Candidate B: Moving-UAV temporal scanning alias versus source coordinate
**Evidence:** Zhao JGR (2026) shows rate error and relative UAV speed role; Mohammadloo AMT (2025) shows severe miss risk under coarse flight spacing. These are **rate** endpoints. Under finite flight speed and shifting plume, asynchronous samples combined as if a snapshot could hypothetically shift source posterior.
**Threat:** 2026 Zhao already uses plume reconstruction, 2025 UAV path control, 2025 turbulence-correlated Bayesian inference, user P0 0/21 transfer STOP. **Decision: HOLD lower priority**. No assertion of GSL coordinate failure. First would need same-route time-resolved measured/qualified plume and source-coordinate ablation, then show simple timestamp alignment and interpolation don't solve.

### Candidate C: Multiheight wind sensing / angular sensor planning on hills
**Evidence:** Gu 2026 wind tunnel and Wang 2026 angular 3D industrial comparisons.
**Decision: REJECT main innovation** as already studied in closely adjacent problems; can be FSR experimental factors and second paper baselines.

### Candidate D: More drones for intermittent / multiple source search / rank-calibration
**Evidence:** Goodell 2026 unknown multiple sources; UGAS 2026 uncertainty-guided; van Hove 2026 high-no-information flights; Jin 2026 calibration-free rank and multi-robot PoE.
**Decision: REJECT main innovation** as generic claim; reserve narrower multi-UAV plume coverage+source verification objective for research content 2.

### Candidate E: Physical dataset benchmarking: paired shoreline thermal CFD → source posterior
**Evidence:** 2026 lake met observations, physical wind tunnels, real-terrain FSR R8 geometry. Only existing FSR geometry and local S2 full checkMesh, no qualified plume bank yet.
**Decision: GO for **dataset-building science** independently of ANY proposed algorithm; still not a novel inverse method by itself.

## Decision discipline and what NOT to claim
- As of 2026-10-08: ZERO new first-paper mechanism with demonstrated repeated GSL positive signal.
- Do not interpret source **emission intensity** percentage errors as source **position** errors.
- Do not conflate a weather model's lake-boundary temperature gradients with a gas-source localization experiment.
- Prior P0, R0C1, M0 null results remain active STOP, unless genuinely new externally validated problem source and data are different.
- Avoid overfitting source-grid cardinality or selected thermal cases to force baseline failure. Grid truth-support and candidate difficulty must be preregistered.
- Avoid claiming author explicitly identified failure where we merely hypothesize from limited scope of their paper.
- Publishing a paper in SCI Q2 cannot be guaranteed by crossing research domains or packing three modules.

## Next action (not a new experiment authorization)
For Codex, prepare **3 exact source-coordinate novelty collision sheets**, mapping our tentative idea against 2025 Vänskä 3D Bayesian source posterior, 2025 Tian 2D topography-aware GSL, 2026 Kim physically conditioned source posterior, 2026 Wang 3D industrial source *rate* and 2026 Gu multi-height terrain monitor siting.
For each sheet use `paper_search` + `scoop_check`: full-text claim evidence, method outputs, needs of real input sensors, actual new technical operator (not just geometry), naive baseline, measurable prediction, falsifying counterexample, compute budget and branch STOP. If nearest work already fulfills claim, **NO GO without simulation**.

Only after full FSR physics and gas-source data qualification do a small preregistered offline source-coordinate signal test; do not resurrect M0, P0 or R0C1 by renaming the mechanism.
