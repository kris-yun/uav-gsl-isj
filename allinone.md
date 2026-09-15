# CTT network role and physics-likelihood upgrade: 2024–2026 literature search

Date: 2026-08-30  
Scope: physics-conditioned surrogate models, causal/multi-environment representations, first-passage or detection models, and source-identification under sparse observations.

## Search record

- Queries: `physics-conditioned surrogate partial observations transport`; `causal representation multi-environment intervention diversity`; `discrete-time survival first-passage neural hazard`.
- Years: 2024–2026.
- Raw API hits: arXiv 24, OpenAlex 24, Semantic Scholar 8, Crossref 24, DBLP 0, OpenReview 0; 80 records before semantic filtering and deduplication.
- Machine-readable raw results: `_staging/CTT_NETWORK_UPGRADE_PAPER_SEARCH_20260830.json`.
- Search limitations that must be retained with the evidence: the bundled CLI documented `--json`, but the installed script rejected that option; the programmatic fallback succeeded. Semantic Scholar returned HTTP 429 for two of the three queries, so its coverage is incomplete. Crossref results were especially noisy and were filtered by title and abstract relevance.
- Venue status is stated explicitly below. A 2026 arXiv preprint is not treated as an accepted top-venue paper.

## Filtered papers

### Physics reconstruction and assimilation

1. **Patel et al., “Turbulence model augmented physics-informed neural networks for mean-flow reconstruction,” Physical Review Fluids, 2024.** Combines sparse point measurements with RANS and a turbulence closure; reports improved reconstruction in separated/high-gradient regions. Direct lesson: a network can reconstruct a missing global flow only when the physical constraints and the reconstruction target are explicit. It does not justify a local-wind-to-source-hazard shortcut. DOI: https://doi.org/10.1103/PhysRevFluids.9.034605. OpenAlex citations at search time: 93.
2. **“An airflow velocity field reconstruction method with sparse or incomplete data using physics-informed neural network,” Journal of Building Engineering, 2024.** Reconstructs a full airflow field from sparse/incomplete velocity measurements under physics constraints. Lesson: if a neural module remains, its falsifiable target should be the global flow field, not source likelihood. https://www.sciencedirect.com/science/article/pii/S235271022400799X.

## Online handoff and observability-gated active localization search (2026-09-15)

Search query: `gas source localization informative path planning observability coverage active sensing sequential Bayesian handoff`  
Years: 2016–2026.  
Raw API result counts: OpenAlex 8, Crossref 8, arXiv 0 (HTTP 429), Semantic Scholar 0 (HTTP 429), DBLP 0 (SSL error), OpenReview 0. The unfiltered programmatic result is `paper_search_online_handoff.json`; the installed CLI rejected its documented `--json` option, so the programmatic API fallback was used.

### All retained papers

| # | Paper | Year | Venue | Citations at search time | Link |
|---|---|---:|---|---:|---|
| 1 | A Mobile Sensing Approach for Regional Surveillance of Fugitive Methane Emissions in Oil and Gas Production | 2016 | Environmental Science & Technology | 92 | [DOI](https://doi.org/10.1021/acs.est.5b05059) |
| 2 | Coordinated Bayesian-Based Bioinspired Plume Source Term Estimation and Source Seeking for Mobile Robots | 2019 | IEEE Transactions on Robotics | 79 | [DOI](https://doi.org/10.1109/tro.2019.2912520) |
| 3 | Model-based gas source localization strategy for a cooperative multi-robot system | 2019 | Robotics and Autonomous Systems | 49 | [DOI](https://doi.org/10.1016/j.robot.2019.03.014) |
| 4 | Information-Driven Gas Source Localization Exploiting Gas and Wind Local Measurements for Autonomous Mobile Robots | 2021 | IEEE Robotics and Automation Letters | 47 | [DOI](https://doi.org/10.1109/lra.2021.3057290) |
| 5 | Decentralized Multi-agent information-theoretic control for target estimation and localization: finding gas leaks | 2020 | The International Journal of Robotics Research | 41 | [DOI](https://doi.org/10.1177/0278364920957090) |
| 6 | An Algorithm for Odor Source Localization based on Source Term Estimation | 2019 | ICRA | 28 | [DOI](https://doi.org/10.1109/icra.2019.8793784) |
| 7 | C-OPT: Coverage-Aware Trajectory Optimization Under Uncertainty | 2016 | IEEE Robotics and Automation Letters | 29 | [DOI](https://doi.org/10.1109/lra.2016.2530302) |
| 8 | Underwater chemical plume tracing based on partially observable Markov decision process | 2019 | International Journal of Advanced Robotic Systems | 28 | [DOI](https://doi.org/10.1177/1729881419831874) |
| 9 | Sequential Bayesian Optimization for Adaptive Informative Path Planning with Multimodal Sensing | 2023 | ICRA | 16 | [DOI](https://doi.org/10.1109/icra48891.2023.10160859) |
| 10 | Informative Path Planning for Acoustic Source Localization With Environmental Uncertainties | 2020 | Global Oceans | 1 | [DOI](https://doi.org/10.1109/ieeeconf38699.2020.9389262) |
| 11 | Cumulative Informative Path Planning for Efficient Gas Source Localization with Mobile Robots | 2025 | IROS | 1 | [DOI](https://doi.org/10.1109/iros60139.2025.11246224) |
| 12 | GOSSIPP: Graph and Observability-Based Signal Synchronized Informative Path Planning for Active Localization of Benthic Fauna | 2026 | IEEE Robotics and Automation Letters | 0 | [DOI](https://doi.org/10.1109/lra.2026.3719196) |
| 13 | Sequential Sensor Placement using Bayesian Compressed Sensing for Source Localization | 2021 | EUSIPCO | 1 | [DOI](https://doi.org/10.23919/eusipco47968.2020.9287709) |
| 14 | Informative Path Planning for Active Field Mapping under Localization Uncertainty | 2020 | ICRA | 25 | [DOI](https://doi.org/10.1109/icra40945.2020.9197034) |
| 15 | Adaptive Informative Path Planning Using Deep Reinforcement Learning for UAV-based Active Sensing | 2022 | ICRA | 68 | [DOI](https://doi.org/10.1109/icra46639.2022.9812025) |
| 16 | Hierarchical Informative Path Planning for Active Sensing and Field Reconstruction | 2024 | Symposium on Control Engineering and Robotics | 0 | [DOI](https://doi.org/10.1145/3679409.3679463) |

### Summary

The relevant neighborhood is not one single gas-localization paper. It is the intersection of four established lines: recursive Bayesian source estimation, information-driven informative path planning, coverage-aware exploration under uncertainty, and POMDP-style exploration/exploitation switching. The closest direct precedent is the 2019 odor-source paper, which explicitly couples source-term estimation with POMDP navigation; the closest coverage precedent is C-OPT; the closest modern active-sensing precedent is sequential Bayesian informative path planning.

The specific mechanism tested here is therefore best described as an observability-gated handoff: a source-blind coverage phase supplies a positive detection event, then a Bayesian information-action controller performs local exploitation. The literature supports each parent idea separately; the new claim is the measurable handoff rule and its post-hit path reduction in gas-source localization. This search does not establish that the combination is globally novel; a dedicated prior-art collision audit is still required.

#### Main themes

1. Recursive Bayesian source/term estimation: papers 1–4, 6.
2. Information-theoretic active path planning: papers 4–5, 9–11, 14–16.
3. Coverage and observability under uncertainty: papers 7, 12, 14.
4. Sequential/POMDP exploration–exploitation switching: papers 6, 8–9.

#### Top cited papers in this result set

| Rank | Paper | Year | Citations |
|---:|---|---:|---:|
| 1 | A Mobile Sensing Approach for Regional Surveillance of Fugitive Methane Emissions | 2016 | 92 |
| 2 | Coordinated Bayesian-Based Bioinspired Plume Source Term Estimation and Source Seeking | 2019 | 79 |
| 3 | Adaptive Informative Path Planning Using Deep Reinforcement Learning for UAV-based Active Sensing | 2022 | 68 |
| 4 | Model-based gas source localization strategy for a cooperative multi-robot system | 2019 | 49 |
| 5 | Information-Driven Gas Source Localization Exploiting Gas and Wind Local Measurements | 2021 | 47 |

#### Reading path

1. Read paper 1 for recursive Bayesian source estimation plus information-driven gas sensing.
2. Read paper 6 for explicit POMDP exploration/exploitation in odor localization.
3. Read paper 7 for coverage-aware planning under sensing uncertainty.
4. Read paper 9 for sequential Bayesian adaptive informative path planning.
5. Read paper 11 for the most recent gas-localization-specific cumulative path-planning comparison.
3. **“RecFNO: resolution-invariant flow and heat field reconstruction from sparse observations via FNO,” International Journal of Thermal Sciences, 2024.** A neural-operator route for sparse-to-field reconstruction. Useful only as an optional accelerator/reconstructor with an out-of-distribution field gate. https://www.sciencedirect.com/science/article/pii/S1290072923004805.
4. **“Physics-consistent machine learning with output projection onto physical manifolds,” Communications Physics, 2025.** Enforces physical consistency at the output rather than hoping a learned representation discovers it. Lesson: any learned flow completion should be projected or checked against governing constraints. https://www.nature.com/articles/s42005-025-02329-1.
5. **“Data assimilation with physics-informed neural network surrogates constructed against prediction uncertainty,” Journal of Computational Physics, 2025.** Couples a physics-informed surrogate to uncertainty-aware data assimilation. Lesson: a surrogate should expose uncertainty and be evaluated on the physical state it reconstructs before being allowed to influence localization. https://www.sciencedirect.com/science/article/pii/S0021999125008691.
6. **“Dual-branch neural operator for enhanced out-of-distribution generalization,” Engineering Analysis with Boundary Elements, 2025.** Relevant to cross-regime operator generalization, but it does not remove the need for a held-out flow-field and downstream ordering gate. https://www.sciencedirect.com/science/article/pii/S0955799724005551.

### Causal and multi-environment identification

7. **Yao et al., “Unifying Causal Representation Learning with the Invariance Principle,” ICLR 2025.** Shows that invariance-based representations need not identify causal variables. Direct lesson: the previous stable-channel or wind-conditioned representation cannot be called causal merely because it is invariant or predictive. https://proceedings.iclr.cc/paper_files/paper/2025/hash/85381f4549b5ddf1d48e2e287d7d3d15-Abstract-Conference.html.
8. **“Sample Complexity of Interventional Causal Representation Learning,” NeurIPS 2024.** Formalizes the role and amount of interventional information needed for causal representation identification. Direct lesson: the defensible causal object in this project is the controlled simulator intervention `do(source=s)`, not a label attached to a passive neural embedding. https://proceedings.neurips.cc/paper_files/paper/2024/hash/458fa8ee331566383d8e74bdb647f829-Abstract-Conference.html.
9. **“Learning Mixtures of Unknown Causal Interventions,” NeurIPS 2024.** Relevant to coherent marginalization over latent interventions/regimes. It supports keeping a global nuisance realization coherent rather than selecting a different best member at every stop. https://proceedings.neurips.cc/paper_files/paper/2024/file/1dcee1cd6890ab7fcdf173ec10526da9-Paper-Conference.pdf.
10. **“Causal Representation Learning from Multiple Distributions: A General Setting,” ICML 2024.** Treats multiple environments/distributions as identification information. Direct lesson: wind contexts are environments and must be separated into development and held-out regimes; they cannot be mixed and called generalization. https://openreview.net/pdf?id=Pte6iiXvpf.
11. **Song et al., “Causal Temporal Representation Learning with Nonstationary Sparse Transition,” NeurIPS 2024.** Gives identifiability conditions for nonstationary temporal transitions. Direct lesson: temporal order helps only under stated transition assumptions and a successful order-sensitive falsification; our fresh-context audit did not pass that falsification for precise first-passage timing. https://proceedings.neurips.cc/paper_files/paper/2024/hash/8cef4e4bcb85f7d4a1005a9db018d6b6-Abstract-Conference.html.
12. **“Causal chambers as a real-world physical testbed for AI methodology,” Nature Machine Intelligence, 2025.** Emphasizes controlled interventions and out-of-distribution tests in physical systems. This matches the proposed use of source placement as a controlled physical intervention and new airflow contexts as the OOD test. https://www.nature.com/articles/s42256-024-00964-x.

### Detection, occupancy, and time-to-event evidence

13. **Pautrel et al., “Analysing biodiversity observation data collected in continuous time: Should we use discrete- or continuous-time occupancy models?”, Methods in Ecology and Evolution, 2024.** Separates latent ecological occurrence from the observation process and compares detection/non-detection with continuous-time event models. This is the closest far-domain analogy for separating plume reachability from imperfect sensor detection. https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.14314.
14. **“Spatio-temporal Occupancy Models with INLA,” Methods in Ecology and Evolution, 2024.** Provides a mature framework for latent spatial occurrence plus imperfect detection over time. The transferable idea is the factorization, not the specific INLA implementation. https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.14422.
15. **“A digital twin for real-time biodiversity forecasting with citizen science data,” Nature Ecology & Evolution, 2025.** Factors movement/spatial state from observation and detection in a real-time digital twin. This supports treating the GADEN transport bank as a physics digital twin and the persistent gas sensor as a separate observation operator. https://www.nature.com/articles/s41559-025-02966-3.
16. **Yanagisawa, “Proper Scoring Rules for Survival Analysis,” ICML 2023.** Outside the requested 2024–2026 window but foundational for evaluating censored time-to-event predictions with proper scores. It supports the audit metric, not a claim that precise first-passage timing generalized here. https://proceedings.mlr.press/v202/yanagisawa23a/yanagisawa23a.pdf.

### Recent preprints retained only as leads

17. **Shen, “When Do Surrogate Updates Improve Decisions? A Local Theory of Trajectory-Wise Transfer,” arXiv:2608.01130, 2026.** Highly relevant to the observed mismatch between neural hazard loss and source-ranking utility, but unreviewed as of the search date. It is a motivation for an explicit downstream ordering gate, not primary theoretical authority. http://arxiv.org/abs/2608.01130v1.
18. **“Deep Learning Surrogate for Fast CIR Prediction in Reactive Molecular Diffusion Advection Channels,” arXiv:2512.18071, 2025.** Relevant transport-surrogate lead, but not evidence that the current H01 local-wind representation is sufficient. http://arxiv.org/abs/2512.18071v1.

## 1. Overview

The literature does not support another direct `local wind patch -> source first-passage hazard` network. It supports two separate layers: a physics-defined latent transport/reachability model and an explicit detection model; a neural module, if used at all, reconstructs or compresses the physical field under constraints and must pass its own OOD physical-state gate.

## 2. Trends

1. Physics-informed learning is moving from generic regularization toward explicit data assimilation, uncertainty handling, and physical output constraints.
2. Causal representation work increasingly states identifiability assumptions and warns that invariance alone is not causality.
3. Far-domain observation sciences distinguish a latent process from imperfect detection instead of treating a detection time as the latent state itself.
4. Cross-environment evaluation is becoming part of the method contract, not an afterthought.

## 3. Key themes

- **Intervene on the source, marginalize transport:** use `do(S=s)` in the native forward model and preserve one transport member coherently across stops.
- **Reachability before timing:** the fresh H01 evidence says ever/never detection carries nearly all robust ordering; within-stop first-passage timing is not a stable main mechanism.
- **Observation operator is separate:** native concentration, persistent sensor state, thresholding, and missed detection must not be collapsed into an occupancy proxy.
- **Neural role is conditional:** a network may reconstruct a global flow/transport state or accelerate an exact operator, but it must not define the scientific likelihood until it reproduces held-out physical fields and candidate ordering.

## 4. Keywords frequency

Qualitative frequency after semantic filtering: `physics-informed/physics-consistent` (high), `data assimilation/reconstruction` (high), `causal representation/intervention` (high), `multi-environment/OOD` (medium-high), `occupancy/detection` (medium), `first-passage/survival` (medium), `source localization` (low). The gap is scientifically useful: the proposed reachability-detection likelihood is a cross-domain synthesis rather than a copied gas-localization module.

## 5. Most cited by accepted paper

Within the retrieved set, the most cited directly relevant accepted paper was Patel et al., Physical Review Fluids 2024 (OpenAlex citation count 93 at search time), followed by several 2024 physics-surrogate/data-assimilation papers. Citation counts are snapshot metadata and not quality gates.

## 6. Most cited by first author

The retrieved APIs do not provide reliable author-level citation totals. No author-level ranking is reported rather than fabricating one.

## 7. Recommendations

1. Retire the direct hazard CNN as a scientific module; preserve its NO-GO.
2. Promote a **causal transport reachability-detection likelihood** as the main innovation: native GADEN intervention, coherent transport nuisance, persistent sensor/detection operator, and sequential Bayesian evidence.
3. Use a likelihood-ratio correction against the exact PMFS window likelihood so the module replaces a misspecified observation operator instead of double-counting the same measurements or resetting the prior.
4. Keep temporal information as coherent evidence across distinct physical stops and sensor state; treat precise first-passage phase as a logged ablation unless a brand-new airflow test proves incremental value.
5. Allow a neural module only as a source-independent physics-field reconstructor or exact-operator compressor. Require OOD field error, physical residual, and downstream candidate-ordering parity before runtime use.
6. Run a cheap, frozen historical shadow Gate before any 300-second closed loop; then development seeds and truly unseen confirmatory seeds must remain separate.
