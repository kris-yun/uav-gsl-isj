# FSR skill + dataset comparative advantage + cross-field novelty audit
Date: 2026-10-08. Evidence-constrained research memo, NOT validated main innovation.

## Scientifically defensible assessment
FSR is a real-terrain, controlled-forcing *planned* lakeshore benchmark for UAV gas source localization of hypothetical industrial sources. 3D CFD, GADEN, source-ground-truth datasets and terrain-aware GSL already exist elsewhere. No claim of unique first-ever dataset is justified yet.
The prospective added capability is matched, auditable **same-topography** source × neutral/thermal water-land forcing × gas realization × fixed source-blind UAV sampling, accompanied by complete 3D wind, plume and 2D source-posterior truth support. Those wind/plume/posterior assets are NOT yet validated or complete.
R8 terrain lineage achieved; R9.3 local S2 quality pass/S4 four determinant failures, 250k vs 1.47–1.63M full-mesh design conflict. Check more recent local CFD/MPI changes before asserting latest engineering status. M0_STOP 40/40 qualified: forward plume changed, source posterior did not (max abs Brier delta 8.85e-8 vs frozen 0.10), 2-source discrimination saturated. The M0 hypothesis remains STOP.

## Skill shortlist, verified actual SKILL.md
1. Microsoft ResearchStudio Scoop-Check https://github.com/microsoft/ResearchStudio/blob/main/ResearchStudio-Idea/skills/scoop_check/SKILL.md : novelty collision across problem/mechanism/insight/domain.
2. K-Dense Hypothesis Generation https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/hypothesis-generation/SKILL.md : register hypotheses, rivals, predicted outcomes and negative controls.
3. K-Dense Experimental Design https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/experimental-design/SKILL.md : real source × wind × realization blocking, control confounders, avoid pseudoreplication.
4. K-Dense Scientific Critical Thinking https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-critical-thinking/SKILL.md : claim-evidence quality gates.
5. K-Dense GeoPandas https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/geopandas/SKILL.md : coordinate/shoreline validity, not a CFD mesh solver.
6. K-Dense DataLad https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/datalad/SKILL.md : optional data lineage after assessing Git-annex complexity, disk resources and existing hash manifests.
7. K-Dense Uncertainty and Units https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/uncertainty-and-units/SKILL.md : field/pressure/wind/gas units and uncertainty propagation.
ResearchStudio IdeaSpark https://github.com/microsoft/ResearchStudio/blob/main/ResearchStudio-Idea/skills/idea_spark/SKILL.md is a heavyweight multistage run, not equivalent to borrowing its rules. Local install and complete runs not claimed.

## What closest prior work already covers
- GADEN 3D CFD-plume simulator: https://github.com/MAPIRlab/gaden
- 2025 ICRA Tian et al. topography-aware GSL with 2D occupancy, local wind, sensor observations, source coordinate labels and public dataset/code: DOI 10.1109/ICRA55743.2025.11128134 ; https://github.com/CHTiansweet/Topography-aware-Gas-Source-Localization
- 2026 van Hove et al. drone methane nature run calibrated to Svalbard real data, source location AND intensity, active paths, temporal-independent synthesis and single source: DOI 10.1017/eds.2026.10029 . FSR simulated meteorology cannot claim greater field fidelity.
- 2024 Welch et al. FastEddy lake-breeze-front CFD and physical observational comparisons: DOI 10.3390/atmos15070809 . Not a labeled mobile GSL benchmark.
- 2025 Heinonen et al. Phys Rev Fluids turbulent encounter temporal dependence: DOI 10.1103/9q6q-nlxc . Temporal dependence alone is not an untouched research gap.

## Conditional flagship scientific question, NOT preselected algorithm
Test whether real-terrain thermally driven **transport-layer versus UAV-observation-layer mismatch** makes physically distinct source candidates observationally confusable under sparse 2D winds and source-blind routes, AND whether qualified 3D transport information actually improves 2D source posterior/error/rank. No proof exists in FSR yet. The M0 null explicitly cautions that plume change does NOT guarantee localization damage.
Stage A: independently qualify full local physical CFD mesh, solver and source-labeled GADEN outputs; distinguish controlled water/land temperature forcing from observed lake breeze; no fabricated inversion data.
Stage B: freeze nontrivial, truth-containing candidate grid; multiple legal source positions, multiple forcing cases, independent gas realizations, same route, source-strength nuisance, matched temporal samples. Avoid two-source posterior saturation.
Stage C: fair native PMFS vs 2D physical inverse vs upper-bound 3D oracle; test repeated source localization *damage*, not only plume metrics; report per-source rank, MAP/metres, posterior score and calibration; no oracle leakage into proposed deployable method.
Stage D: compare plain multi-height wind interpolation, simple 3D physical likelihood, emission-rate marginalization, memory-aware likelihood and BMA. If an ordinary baseline solves the issue, reject new-method novelty.

## Potential cross-field mother theories (not transplanted success)
- 2026 ICML Feng et al. Learning Task-Sufficient World Models https://proceedings.mlr.press/v306/feng26aa.html : only keep source-discriminating 3D latent state, not dense plume; their experiments are robotics/control, not GSL. Historical P0 0/21 transfer cautions.
- 2026 ICML Lillemark et al. Flow Equivariant World Models https://proceedings.mlr.press/v306/lillemark26a.html : align memory with dynamics under partial observation, proven for dynamic visual environments, not thermally forced gas transport. Simple advection and time memory are old; require concrete new source-posterior operation and ablation.
- A robust/source-set abstention path is methodologically plausible but collides with standard robust Bayesian and selective prediction. Not leading novelty unless a nontrivial transport-conditioned mechanism is shown.

## Next Codex task: FSR_GAP_CAPABILITY_QUALIFICATION_R0 only
(1) Audit actual latest FSR local outputs and hashes, including post-R9.3 CFD engineering (do not erase passed short gates or mislabel short runs as full physics).
(2) Native capability matrix for shoreline/DEM, U/T/flux 3D winds, gas concentration/filaments, source truth, synchronized fixed UAV routes, sample rate, candidate grid, licences and storage.
(3) Literature full-text comparison for the exact 4 peer cases above; honest missing data fields, not universal claims.
(4) Freeze a source×forcing×realization diagnostic contract that tests whether source posterior is harmed under 2D and rescued by 3D upper bound. If FSR native fields unqualified, STOP at design, no GSL runs.
(5) At most three 1-page idea cards. Each: 4-axis Scoop-Check, genuine new mechanism, rival ordinary explanation, naive baseline, resource budget, falsification and STOP rule.
Retain main paper GSL coordinate and 2D posterior outputs; M0 permanently STOP; no premature world-model training or first-paper algorithm claim.