# CTT Supplemental Collision Closure — 2026-08-31

## Scope and frozen interpretation

This supplement closes the mechanism-level literature audit requested after the
2026-08-30 scoop check. It does **not** change any experimental verdict. All
existing neural, wind-sufficiency and first-passage NO-GO records remain valid;
no full-grid bank, runtime integration or closed-loop run is authorized.

The candidate CTT scientific object is the run-level joint state

$$
w_b(S,A,K),\qquad A=(H,U,Q,\tau_0,\Psi),
$$

where the same native stochastic transport realization \(K\), aligned nuisance
\(A\), and persistent sensor state explain all completed mobile-robot stops and
source updates. Candidate tapes are generated under \(do(S=s)\), passed through
the sensor process, consumed once by the source channel, and only then
marginalized to \(p(S\mid D_{1:b})\).

## 1. Closest GSL / atmospheric-source-inversion mechanisms

| Work | Mathematical object | Information flow | Demonstrated capability | Collision with CTT | Defensible CTT delta |
|---|---|---|---|---|---|
| Ristic, Gunatilaka, Gailis & Skvortsov, *Bayesian likelihood-free localisation of a biochemical source using multiple dispersion models*, **Signal Processing 108 (2015), 13–24**, [arXiv:1405.6460](https://arxiv.org/abs/1405.6460) | Joint latent \((m,\theta_m)\): one candidate dispersion-model identity \(m\) and that model's source/dispersion parameters explain the complete measurement vector \(z=[\zeta_1,\ldots,\zeta_S]^T\). | Draw \(m\sim p(m)\), draw \(\theta_m\sim p(\theta_m\mid m)\), simulate a complete \(z^*\), compare \(z^*\) with \(z\) in ABC, infer \(p(m,\theta_m\mid z)\), then Bayesian-model-average the source posterior. | Likelihood-free source localization over several dispersion models on two experimental data sets. | **Strongest direct collision; HIGH risk.** It already enforces one model identity over a collection of measurements and jointly marginalizes model and source uncertainty. Therefore “one coherent model explains all observations” is not novel. | CTT must claim only the finer stochastic object and online use: a **native realization identity \(K\) within one high-fidelity transport family**, not merely a structural model label, persists across sequential mobile stops and PMFS source updates together with causal sensor memory; the primary comparator redraws only \(K\), and the resulting source likelihood replaces rather than multiplies onto the native PMFS source channel exactly once. |
| Hutchinson, Liu & Chen, *Source term estimation of a hazardous airborne release using an unmanned aerial vehicle*, **Journal of Field Robotics 36 (2019), 797–817**, [DOI 10.1002/rob.21844](https://doi.org/10.1002/rob.21844) | A low-dimensional source-term state including three-dimensional release location, emission rate, and dispersion-relevant variables under two analytical advection–diffusion models. | UAV concentration observations and meteorological data enter an analytical dispersion likelihood; sequential Monte Carlo recursively estimates the source-term posterior. | Outdoor, fully automated UAV source-term estimation under different flight paths and wind speeds. | **Strong sequential-inference neighbor; HIGH risk for broad claims.** It already performs mobile sequential Bayesian source/nuisance estimation with physical dispersion models. The publisher-accessible record does not establish a retained high-dimensional native stochastic plume-realization identity. | CTT's residual delta is not “Bayesian source inversion on a robot”; it is the discrete native-response realization \(K\) and persistent sensor state carried across stops, tested against a same-\(A\) transport-redraw ablation, and integrated as single-consumption source-channel replacement in PMFS. |
| Kim, Kim, Lee & Oh, *Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*, **arXiv preprint (2026), submitted to IEEE Transactions on Robotics**, [arXiv:2608.16221](https://arxiv.org/abs/2608.16221) | Learned posterior fields: wind \(w\), concentration \(c\), and source \(s\); separate probabilistic networks model the physical dependency \(w\rightarrow c\rightarrow s\). | Sparse gas/wind/map observations \(\rightarrow p(w\mid\cdot)\rightarrow p(c\mid w,\cdot)\rightarrow p(s\mid w,c,o)\); Monte Carlo marginalizes intermediate field samples; the source posterior drives an active planner. | Simulation and active-GSL evaluation plus embedded-GPU real-robot feasibility. | **Broad framing and neural-flow collision; HIGH risk.** “Physical dependency-guided sequential inference,” neural intermediate physical fields, source posterior and active planning are occupied. | CTT must not claim a generic causal/physical neural sequence. Its narrower object is the exact candidate intervention bank and run-persistent native \(K\) identity with explicit sensor-state likelihood and PMFS source-channel replacement. A neural response operator is therefore not retained as a scientific module. |

### Mechanism verdict

Ristic is the closest paper to M2's coherence wording. The collision closes the
broad claim but does not yet collapse the exact CTT object. A structural
dispersion-model index \(m\) over a fixed measurement vector is not identical to
a stochastic native plume realization \(K\) queried causally at a mobile
trajectory while a physical sensor state recurs across source updates. This is
still a **single-axis, fragile delta**, so M2 remains a provisional main
candidate with **HIGH** collision risk, not a frozen novelty claim.

The one-sentence delta is:

> Unlike Ristic et al. (2015), which draws one structural dispersion-model label and its low-dimensional parameters to simulate and accept an entire measurement vector, CTT retains one native stochastic transport-realization identity \(K\) and persistent sensor state across completed mobile-robot stops and PMFS updates, isolates that identity with a transport-only redraw comparator, and replaces the native PMFS source-evidence channel once, aiming to prevent mutually incompatible plume realizations from reversing online source ordering.

## 2. Six-domain 2024–2026 transfer coverage ledger

These papers are theory sources, not novelty evidence. KEEP means a principle
survives a gas-specific rederivation and falsification Gate. REJECT means the
tempting transfer is mismatched, already occupied in GSL, unidentifiable from
deployable inputs, or only an engineering accelerator.

| ID | Remote field and formal source | Original object / principle | Candidate transfer to CTT | What is explicitly not transferred | Decision and reason |
|---|---|---|---|---|---|
| A | **Systems biology** — Sha et al., *Reconstructing growth and dynamic trajectories from single-cell transcriptomics data*, **Nature Machine Intelligence 6 (2024), 25–39**, [DOI 10.1038/s42256-023-00763-w](https://doi.org/10.1038/s42256-023-00763-w) (TIGON) | Dynamic unbalanced optimal transport connects unpaired time snapshots while jointly representing state transition velocity and population growth; a WFR continuity equation prevents treating snapshots as unrelated samples. | **KEEP** only the principle that temporally separated observations must be coupled by one explicit generative transport law rather than independently matched. This supports the M2 requirement that all stops belong to one run-level realization. | Cell identity, gene-regulatory-network causality, WFR geometry, neural ODE architecture, and mass-growth semantics are not imported. CTT uses a discrete native GADEN realization and sensor recursion, not cellular optimal transport. | **KEEP_AS_REMOTE_SUPPORT.** Useful for the “unpaired snapshots require a dynamics-constrained bridge” rationale; too far from GSL to establish novelty and not a direct algorithm transplant. |
| B | **Medical dynamic / sparse CT** — Dillon et al., *Real-time spatiotemporal optimization during imaging*, **Communications Engineering 4 (2025), 61**, [DOI 10.1038/s44172-025-00391-9](https://doi.org/10.1038/s44172-025-00391-9) | Acquisition is controlled so sparse projections have a planned spatiotemporal structure that the 4D reconstruction can jointly exploit; per-phase independent reconstruction wastes cross-phase information. | **KEEP** the design rule that measurement-time structure and downstream inference must be co-designed, and that repeated blocks must not be treated as exchangeable pseudo-replicates. This motivates physical-stop keys and future-predictive/order controls. | X-ray projection physics, respiratory periodicity, deformation-vector fields, image-space reconstruction, dose optimization and active acquisition hardware are not transferred. | **KEEP_AS_REMOTE_SUPPORT, REJECT_AS_MODULE.** It supports the ledger/order contract but does not provide the source–transport likelihood or a standalone CTT innovation. |
| C | **Astronomy** — McAlpine et al., *The Manticore Project I: a digital twin of our cosmic neighbourhood from Bayesian field-level analysis*, **MNRAS 540 (2025), 716–745**, [DOI 10.1093/mnras/staf767](https://doi.org/10.1093/mnras/staf767) | A full latent initial density field is inferred under a nonlinear physical forward model and represented by posterior realizations that remain globally coherent under evolution. | **KEEP** joint marginalization over coherent latent physical realizations rather than pointwise mixing incompatible local explanations. This is the cleanest remote analogy for \(w_b(S,A,K)\). | Cosmological priors, galaxy-bias model, Poisson catalogue likelihood, N-body solver and astronomical image/field semantics are not transferred. | **KEEP_AS_REMOTE_SUPPORT.** Strong conceptual support for M2; no GSL capability or novelty entitlement follows from it. |
| D | **Ecology / imperfect detection** — Priyadarshani et al., *A unified framework for time-to-detection occupancy and abundance models*, **Methods in Ecology and Evolution 15 (2024), 555–568**, [DOI 10.1111/2041-210X.14296](https://doi.org/10.1111/2041-210X.14296); Goldstein et al., *Guidelines for estimating occupancy from autocorrelated camera trap detections*, **Methods in Ecology and Evolution (2024)**, [DOI 10.1111/2041-210X.14359](https://doi.org/10.1111/2041-210X.14359) | Separate latent occurrence/abundance from imperfect time-to-detection; account for censoring and temporal autocorrelation instead of treating repeated detections as independent. | **KEEP** separation of plume reachability from sensor detection, right-censoring of never-detected stops, and a persistent sensor/noise process. This supports M3. | Species occupancy, abundance links, ecological covariates and independent-visit assumptions are not transferred. | **KEEP_AS_REMOTE_SUPPORT; REJECT_AS_STANDALONE_NOVELTY.** Detection likelihoods and hidden-state plume models already exist in GSL, so this can only justify M3's correctness. |
| E | **Earth-system / environmental transport inversion** — Vänskä, Weidmann & Ursin, *Greenhouse gas emission mapping and quantification based on 3D transport modeling and Bayesian state estimation*, **Inverse Problems 41 (2025), 095001**, [DOI 10.1088/1361-6420/adfb29](https://doi.org/10.1088/1361-6420/adfb29); established ensemble anchor: Lucas et al., *Bayesian inverse modeling of the atmospheric transport and emissions of a controlled tracer release from a nuclear power plant*, **Atmospheric Chemistry and Physics 17 (2017), 13521–13543**, [DOI 10.5194/acp-17-13521-2017](https://doi.org/10.5194/acp-17-13521-2017) | Vänskä et al. recursively estimate a spatiotemporally evolving 3-D concentration field and gas-source distribution under a convection–diffusion state-space model; ensemble inversion also treats transport configurations as uncertain physical inputs jointly with source parameters. | **KEEP** truth-blind nuisance marginalization, recursive physics-constrained state estimation, posterior weight over transport members, and the requirement that one run is explained by a globally compatible physical state. | Open-path tomography geometry, linear-Gaussian Kalman smoother, continental WRF/FLEXPART categories, emissions inventory and stationary sensor semantics are not transferred. | **KEEP_AS_CLOSE_THEORY_SOURCE WITH HIGH COLLISION WARNING.** The 2025 work removes any broad novelty claim for recursive source–transport state estimation; only CTT's native-realization identity, mobile-stop sensor recurrence, transport-only comparator and PMFS replacement delta remains. |
| F | **CFD / operator learning** — Azizzadenesheli et al., *Neural operators for accelerating scientific simulations and design*, **Nature Reviews Physics 6 (2024), 320–328**, [DOI 10.1038/s42254-024-00712-5](https://doi.org/10.1038/s42254-024-00712-5) | Learn mappings between function spaces to amortize expensive PDE simulation, with physics constraints and out-of-distribution qualification. | At most compress a validated candidate-conditioned forward operator and demand pointwise concentration, likelihood, posterior and planner parity. | A learned inverse source classifier, source labels, posterior features, route-specific memorization, hidden wind identity, or replacement of the sensor likelihood are forbidden. | **REJECT_COLLISION AS SCIENCE MODULE; OPTIONAL ENGINEERING ONLY.** Neural plume and physics-guided source surrogates already exist in GSL, and current CTT neural routes are NO-GO. |

### A–F coverage conclusion

- M1 receives provenance/intervention discipline from controlled physical
  experimentation and Earth-system forward inversion, but candidate-source
  simulation is already established in PMFS; it stays supporting only.
- M2 receives independent intellectual support from TIGON's dynamics-constrained
  linkage, Manticore's coherent field-level posterior, dynamic CT's structured
  temporal acquisition, and Earth-system ensemble inversion. None grants a
  novelty claim; Ristic and Hutchinson make the GSL collision risk **HIGH**.
- M3 is well motivated by ecological imperfect-detection/event-history theory,
  but that same maturity is why it cannot be the main novelty.
- Operator learning is excluded from the scientific three-module claim. It can
  return only after exact M1+M2+M3 is positive and only as a parity-proven
  accelerator.

## 3. Four-state innovation decision ledger

Only scientific innovation candidates appear here. Event-ledger bookkeeping,
exact source-channel replacement, launch plumbing and optional accelerators are
method invariants or engineering items and are outside this four-state table.

| Candidate | Collision finding | Evidence maturity | Allowed state |
|---|---|---|---|
| M1 native candidate intervention response | Same candidate-forward object is already present in PMFS and source inversion. | Required support; not independently novel. | **KEEP_AS_SUPPORTING_COMPONENT** |
| M2 persistent native source–transport realization | Ristic 2015 and Hutchinson 2019 occupy broad joint/sequential source–dispersion inference; exact native \(K\)-persistence plus sensor recurrence and PMFS replacement was not found in the checked sources. | Coherence premise only under a surrogate score; calibrated Bayesian and closed-loop evidence absent. | **KEEP_AS_MAIN_INNOVATION** *(provisional; collision risk HIGH)* |
| M3 sensor-aware reachability/detection emission | Imperfect-detection and hidden-state objects are mature in ecology and GSL. | Necessary sensor contract; current deterministic score not calibrated. | **KEEP_AS_SUPPORTING_COMPONENT** |
| Sparse-wind hidden-field reconstruction | Deployable local wind was empirically many-to-one with global transport topology. | Input-identifiability premise failed. | **REJECT_NO_EVIDENCE** |
| Neural native-response scientific module | Jin 2023, Ruiz 2024 and Kim 2026 occupy neural/physics-guided plume or source inference; all current CTT neural M1 attempts remain NO-GO. | No scientific evidence and direct object/framing collision. | **REJECT_COLLISION** |

## 4. Authorization boundary

This closure changes **wording and collision risk only**. It does not turn the
H01 coherence premise into a calibrated posterior, does not restore any neural
module, and does not authorize full-grid generation, C++ runtime integration or
closed-loop testing. Advancement still requires the preregistered low-cost
future-predictive/order/sensor-calibration Gates in the main method document.
