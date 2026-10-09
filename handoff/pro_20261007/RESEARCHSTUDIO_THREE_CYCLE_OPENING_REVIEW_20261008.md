# ResearchStudio-inspired 3-cycle novelty audit for FSR thesis proposal
Date: 2026-10-08
Status: proposal revision, NOT algorithm validated.
Methodology: read Microsoft's ResearchStudio-Idea SKILL.md (Idea-Spark, Paper-Search, Scoop-Check) via GitHub connection; **manually** execute three bounded literature → gap → method → four-axis prior-art → falsification cycles. The actual ResearchStudio run.py, isolated LLM calls and receipt validators were not run (local GitHub network unreachable). Never describe this as an automated IdeaSpark pass.

## Ground truth and rejected mechanisms
- M0 40/40 qualified, source-posterior damage max ~8.85e-8 vs frozen 0.10 gate; M0_STOP. Strong plume response ≠ source localization damage.
- P0 dynamics 0/21 transfer; R0C1 2/4 vertical confirmation; W0C boundary HOLD; FSR R9.3 full mesh/RAM HOLD. Do not resurrect by merely increasing model size or changing criteria.
- FSR: real shore + DEM and water/land masks, controlled thermal forcing; not observed lake breezes; no qualified FSR wind/GADEN/posterior yet.

## Research cycle 1 — identifiability-aware probability update
Claim: attenuate posterior updates when source candidates are observationally similar.
Closest work: Ojeda et al. T-RO 2024 probabilistic source localization DOI:10.1109/TRO.2024.3426368; Piro et al. 2025 multi-wrong-model Bayesian blending DOI:10.1080/14685248.2025.2492711; van Hove et al. 2026 active Bayes source + intensity inference DOI:10.1017/eds.2026.10029.
Collision: classic posterior calibration, source-strength marginalization and selective abstention are already standard. Decision: REJECT as **selected novel main method**, retain identifiability diagnosis as evaluation.

## Research cycle 2 — ICML 2026 task-sufficient / flow-equivariant 3D world model
Prior theory: Feng et al., ICML 2026 PMLR 306:30616-30641, https://proceedings.mlr.press/v306/feng26aa.html; Lillemark et al., ICML 2026 PMLR 306:73968-74002, https://proceedings.mlr.press/v306/lillemark26a.html.
These works test structured task-sufficient states in control and dynamic video; neither establishes transfer to source localization. Prior P0 failure and high training budget make a world model inappropriate as preselected solution. Decision: HOLD as remote theoretical reserve.

## Research cycle 3 — lakeshore transport-observation layer mismatch
Source grounding: Welch et al., Atmosphere 2024 lake-breeze-front flow DOI:10.3390/atmos15070809; Tian et al., ICRA 2025 topography-aware GSL DOI:10.1109/ICRA55743.2025.11128134; van Hove et al. 2026 single scenario/no temporal correlations limitations.
Hypothesis: near-shore thermal/terrain forcing creates vertical transport strata inconsistent with sparse UAV sampling strata, such that otherwise legal source candidates become hard to distinguish.
**Not demonstrated in FSR**. Required chain: qualified physical vertical difference → material source-posterior/rank harm across independent sources/winds/seeds → insufficient existing baselines (PMFS, source-strength marginalization, simple multiple-height wind interpolation, calibration and BMA) → THEN develop task-specific transport-consistency inference. M0_STOP prevents assuming forward differences imply posterior harm.
Decision: CONDITIONAL HOLD as a precise falsifiable first-paper scientific problem, NOT original method GO.

## Multi-UAV and closed-loop prior art
- SniffySquad, ACM TOSN 2026, DOI:10.1145/3786599, already studies patchiness-aware sensing and collaborative role adaptation. Dynamic multi-robot scheduling alone is not new.
- Jin et al., ICRA 2026, arXiv:2605.13208, already derives calibration-free source position probabilities from concentration ranks.
- The second paper should target **continuous valid-time coverage of plume front/edges PLUS source-region confirmation**, measured under equal platforms and flight budget. The third paper should stage sensor dynamics/time misalignment/flight safety system validation and avoid claiming generic calibration is novel.

## User and supervisor contracts reflected
- First-paper GSL output: source coordinates + 2D posterior + ranking/confidence; plume pathway, shape, density, center/front/edges are evaluated auxiliary outputs, forecast only if separately validated.
- Three papers: (1) main source inversion problem, (2) lighter multi-UAV changing-plume monitoring, (3) sensor/calibrated closed-loop/conditional safe field flight.
- Lakeshore industrial source is hypothetical; gas is not restricted to VOC. FSR geometry is real; meteo forcing is controlled.
- Four concept-only images preserved, 46 references and no mathematical equations in Word. Official school table template not uploaded publicly.

Decision on originality: not established. The revised proposal is defensible as an honest falsifiable study plan, not a validated SCI-Q2 method.

Local Word deliverable and full audit record remain in private ChatGPT session; this public handoff intentionally includes no school forms, personal details, third-party PDF copies or generated concept art.
