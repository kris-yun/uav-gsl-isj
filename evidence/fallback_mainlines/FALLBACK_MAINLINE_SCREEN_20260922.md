# Fallback mainline cycle — 2025–2026 remote-domain ideas with public code

Date: 2026-09-22  
Branch purpose: **exploratory fallback search only**  
Parent: `research/hcrc-mechanism-scas-20260922` @ `3755cd525a58896904dbaf8b16ee70a31b157771`

## Hard separation from the active HCMC validation

The frozen HCMC V1 independent-plume experiment currently running on the VM must not be tuned, reinterpreted, filtered, or rescued using anything in this branch.

All numbers below are **discovery-set screens** on the old frozen six cases only. Their endpoint is a local Python ceil/stable-tie clone for rapid screening, not the authoritative linked-native C++ tie semantics used by the independent HCMC gate.

If HCMC independent-plume validation passes, these routes remain fallback/mechanism research unless separately validated.  
If HCMC fails, the next route must be frozen before it sees any new validation truth.

---

## 1. Search strategy

Priority was given to 2025–2026 ideas satisfying as many of the following as possible:

1. mother idea originates outside ordinary gas-source-localization engineering;
2. peer-reviewed/top scientific venue or a strong current scientific program;
3. public implementation / GitHub repository;
4. can be expressed without House-specific or truth-dependent tuning;
5. can be destructively falsified on the existing source-conditioned candidate bank;
6. no obvious direct collision with existing GSL/OSL literature.

Candidate routes screened in this cycle:

- diffusion geometry / graph heat flow;
- wavelet scattering spectra;
- Minkowski / excursion-set stochastic geometry;
- local inverse-operator tangent geometry inspired by BiLO;
- diffusion information-flow / entropy-production variants.

Two heavier routes were retained for a future cycle but **not fabricated from insufficient data**:

- causal Koopman source identifiability;
- function-space diffusion posterior inference.

---

# 2. Fallback candidate B — Hypothesis-Conditioned Diffusion Geometry (HCDG)

## Mother idea and public code

2026 **Computing Diffusion Geometry** provides a data-driven calculus/geometry/topology framework on discrete point clouds and graphs by reformulating geometric operations through heat diffusion.

Public implementation:

- paper: *Computing Diffusion Geometry* (2026), arXiv:2602.06006
- GitHub: https://github.com/Iolo-Jones/DiffusionGeometry

The transferred source-inference principle is:

> A source hypothesis should not only reproduce point values. The observed scalar field and the source-conditioned simulated field should dissipate spatial roughness in a compatible way under the same graph heat semigroup.

For each candidate source, define the measured and simulated field on the common observed-support graph and evolve

[
f_t = e^{-tL}f_0,
]

where (L) is a source-blind graph Laplacian. Compare the candidate and observation through the decay trajectory of graph Dirichlet energy

[
E(t)=f_t^	op L f_t.
]

This is different from HCMC's fixed-separation structure-function slopes: the primitive object is **heat-flow dissipation on the environmental graph**.

## Frozen discovery screen

Three principled, predeclared heat-time families were checked:

| heat-time family | mean endpoint error | pooled reduction vs Native | improved cases |
|---|---:|---:|---:|
| fast: 0,.25,.5,1,2,4 | 3.72885 m | 32.87% | 6/6 |
| mid: 0,.5,1,2,4,8 | 4.16176 m | 25.08% | 6/6 |
| slow: 0,1,2,4,8,16 | 3.87632 m | 30.22% | 6/6 |

The result is therefore not unique to one exact heat-time grid.  
**Do not select the fast family as a promoted method from these same six cases.** The current scientific statement is only that the heat-dissipation family carries a reproducible discovery signal.

## Destructive falsification

The mid family was frozen for the first null screen:

### Final-leaf permutation, 150 repetitions

- real HCDG mean: 4.16176 m
- null mean: 4.42949 m
- null 5–95%: 3.36355–5.60981 m
- fraction null as good as real: **0.3467**

### Candidate simulated-field spatial shuffle, 30 repetitions

- null mean: 4.84862 m
- null 5–95%: 3.90852–5.73641 m
- fraction null as good as real: **0.1667**

## Decision

**PROMISING FALLBACK / NOT PROMOTED.**

Reasons to retain:
- 25–33% discovery reduction;
- 6/6 across three principled heat-time families;
- strong and recent external mother idea;
- official public code;
- graph/heat-flow formulation naturally respects obstacles and irregular supports.

Reasons it is not yet a main-line peer of HCRC:
- null separation is much weaker than HCMC;
- a substantial fraction of leaf permutations can match the real mid-family result;
- no independent plume validation;
- no source-position-transfer validation;
- generic "diffusion state/manifold learning" has already appeared in 2026 odor-source-localization literature, so novelty must be narrowly stated as **source-hypothesis-conditioned heat-semigroup conformance**, not "use manifold learning for odor diffusion".

Required next falsification if HCMC fails:
1. freeze one source-blind heat-time construction without choosing by truth;
2. rerun null controls at higher repetition count;
3. graph-rewiring / spectrum-preserving null;
4. independent-plume validation;
5. source-position-transfer 300-s localization.

---

# 3. Diffusion information flow — screened, weaker than HCDG

A more thermodynamic-looking variant normalized fields into positive graph distributions and compared heat-flow trajectories of:

- Shannon entropy / KL to uniform;
- graph Fisher energy;
- KL dissipation / entropy-production proxy.

Discovery results:

| representation | mean endpoint error | pooled reduction | improved |
|---|---:|---:|---:|
| entropy curve | 4.66268 m | 16.06% | 5/6 |
| KL curve | 4.66268 m | 16.06% | 5/6 |
| Fisher curve | 4.51921 m | 18.65% | 5/6 |
| KL dissipation | 4.91422 m | 11.54% | 5/6 |
| equal information consensus | 5.17155 m | 6.90% | 4/6 |

**Decision: NO-GO as a main innovation.**  
The heat-semigroup idea survives, but the extra entropy-production dressing does not add evidence and should not be used merely because it sounds more fundamental.

---

# 4. Wavelet scattering spectra — screened and demoted

Mother idea: stable multiscale non-Gaussian texture statistics from wavelet scattering, widely used in complex physical fields.

Reference implementation considered:
https://github.com/SihaoCheng/scattering_transform

A fixed Morlet first/second-order scattering-like conformance score was applied without training.

Discovery:
- mean error: **4.58440 m**
- pooled reduction: **17.47%**
- improved: **5/6**
- House03 seed0 worsened materially.

**Decision: NO-GO main line.**  
Keep only as adjacent literature / possible feature-level ablation.

---

# 5. Minkowski / excursion-set stochastic geometry — rejected

Mother idea: characterize random fields using threshold excursion-set morphology such as area, interface/perimeter and Euler/connectivity statistics.

Recent code anchor considered:
https://github.com/sfzwarts/RockMicro_Minkowskis

A threshold-normalized morphology curve was compared candidate-wise.

Discovery:
- mean error: **5.14182 m**
- pooled reduction: **7.44%**
- improved: **3/6**

**Decision: NO-GO.**

The morphology is too lossy for the present source-hypothesis problem.

---

# 6. BiLO-inspired local operator geometry — rejected as main line

2026 JCP:
**BiLO: Bilevel Local Operator Learning for PDE Inverse Problems**

- DOI: 10.1016/j.jcp.2026.114679
- code: https://github.com/Rayzhangzirui/BILO

Instead of training a neural operator, a lightweight non-neural screen tested the underlying idea: near each candidate source, estimate the local tangent map from source-coordinate changes to simulated plume-field changes, and score how much of the measured residual lies outside that local source-to-field tangent space.

Results:

| local neighbors K | mean error | pooled reduction | improved |
|---|---:|---:|---:|
| 6 | 5.23602 m | 5.74% | 3/6 |
| 8 | 4.76116 m | 14.29% | 4/6 |
| 12 | 4.67685 m | 15.81% | 5/6 |

In addition, a 2026 IROS paper is already accepted under the title **A physics-informed neural operator for gas source localization in turbulent environments**.

**Decision: NO-GO main line.**

The effect is weak/K-sensitive, while generic neural-operator-for-GSL novelty is already directly occupied.

---

# 7. Future fallback C — Causal Koopman source identifiability

2025 *Communications Physics*:
**Deep Koopman operators for causal discovery**

- public package: https://github.com/juannat7/kausal
- DOI: 10.1038/s42005-025-02426-1

The attractive transferred principle is not "use a Koopman neural network". It is:

> Embed nonlinear plume dynamics in an approximately linear evolution space and ask which source hypothesis supplies the missing causal state needed to predict the measured dynamics.

A paper-level GSL form would compare, for each source hypothesis, joint-vs-marginal Koopman predictive skill / causal contribution under robot motion and wind forcing.

### Why it was not screened on the current frozen archive

The current final-leaf candidate bank gives rich **spatial** candidate support but does not provide a sufficiently long, candidate-conditioned counterfactual time series along the full trajectory for each source hypothesis. Five PMFS source updates are not an honest substitute for a causal dynamics dataset.

Therefore no fake "Koopman result" is reported.

### Data required

For every source candidate and trajectory step, export:
- predicted hit/concentration statistic;
- wind-conditioned state;
- robot pose/action;
- measured sensor response;
- stable candidate identity across time.

Then freeze a low-rank Koopman causal score before reading truth.

**Status: HIGH-SCIENCE LONG-SHOT / DATA NOT YET ELIGIBLE.**

---

# 8. Future fallback D — Function-space diffusion posterior

2026 *Nature Communications*:
**FunDiff: Diffusion Models over Function Spaces for Physics-Informed Generative Modeling**

- GitHub: https://github.com/sifanexisted/fundiff
- DOI: 10.1038/s41467-026-72292-0

FunDiff explicitly contains fluid/turbulence/mass-transfer examples and models distributions of continuous functions rather than individual grid vectors.

Potential GSL transfer:

> Learn a source/wind-conditioned **distribution over physically plausible plume functions**, then perform source inference by posterior compatibility with the measured partial field instead of comparing against one deterministic plume realization.

This directly attacks the central stochastic-realization mismatch that motivated HCMC, but by learning the full conditional distribution rather than an invariant statistic.

### Why it is not yet screened

The six frozen episodes are nowhere near enough to train or validate a function-space generative model without severe leakage. It requires a deliberately generated bank of many independent GADEN realizations, partitioned by source position and wind before model design.

**Status: HIGH-COST PLAN-D / genuinely distinct from HCRC, not currently testable honestly.**

Also keep the novelty claim distinct from deterministic neural/PINO gas-source-localization work.

---

# 9. Current fallback hierarchy

This branch does **not** change the active HCMC gate.

Current research hierarchy after this cycle:

1. **HCRC/HCMC** — primary, currently under true independent-plume validation.
2. **HCDG — Hypothesis-Conditioned Diffusion Geometry** — strongest new immediately-testable fallback; 25–33%, 6/6 across heat-time families, but null separation still insufficient.
3. **Causal Koopman source identifiability** — scientifically orthogonal and code-backed; requires new candidate-temporal counterfactual export.
4. **Function-space diffusion posterior (FunDiff transfer)** — most ambitious orthogonal fallback; requires a large new multi-realization training/validation bank.
5. Wavelet scattering — demoted.
6. Local operator geometry / BiLO transfer — rejected as main route.
7. Minkowski morphology — rejected.

## Important methodological rule

If HCMC independent validation fails, **do not select HCDG's best heat-time family using the same failed validation truth**. HCDG must enter its own frozen validation protocol.

Likewise, no future Koopman/FunDiff route may use the current independent HCMC holdout as training data and then call it independent evidence.

