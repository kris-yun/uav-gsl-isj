# CTT final three-module method rederivation

Date: 2026-08-30  
Status: **METHOD FROZEN FOR PREMISE TESTING / LARGE MATERIALIZATION PAUSED / CLOSED LOOP NOT AUTHORIZED**

## 0. Decision

The accumulated evidence does not yet establish a complete method or a
localization improvement claim. It does establish a defensible scientific
architecture containing one narrow main innovation and two necessary support
components:

1. **M1 — native interventional concentration-response operator.** For each
   candidate source, construct a legal native physical response family under a
   truth-blind, aligned nuisance design.
2. **M2 — persistent coherent source–transport filter.** Maintain one joint
   source–whole-run-nuisance state across completed robot stops and source
   updates. This is the sole main-innovation claim.
3. **M3 — sensor-aware reachability/detection emission.** Convert candidate
   physical concentration tapes to the same measured event process as the
   robot, separating reachability from imperfect detection.

The integrated method is called **Causal Transport Tomography (CTT)**. Its
paper-level claim is deliberately narrow:

> CTT performs candidate-interventional source inference while retaining the
> same native stochastic transport realization across sequential mobile-robot
> observations, then marginalizes transport only after accumulating the
> sequence through a calibrated sensor-aware detection model.

The network is not one of the three scientific modules. Existing neural plume
surrogates create high collision risk, while both project neural Gates are
NO-GO. A future network may only approximate M1 as a parity-qualified
engineering accelerator. Its current status is
**REJECT_COLLISION_AND_NO_EVIDENCE**.

The shortest next action is the inexpensive G0 artifact/recurrence audit. Full
grid generation, new neural training, C++ takeover and 300 s closed-loop runs
remain paused.

## 1. What the current 43.60% result proves

The preregistered H01 fixed-trajectory shadow reported:

- PMFS mean formal error: 5.0013027 m;
- CTRE mean formal error: 2.8206468 m;
- relative improvement: 43.6018%;
- improved pairs: 10/10;
- registered catastrophes: 0.

This is a strong development signal, not a method result, because:

1. the shadow computes geometry prior times a cumulative CTRE score; it is not
   yet an exact same-window replacement of the PMFS observation operator;
2. CTRE raw true-carrier rank improves in only 4/10 final cases and posterior
   true-carrier rank in only 2/10; seed 9 changes from native rank 25 to CTRE
   posterior rank 208;
3. the official error is a top-5% spatial expectation. Broad or tied mass near
   the source may improve that coordinate statistic while the true carrier
   loses probability. Repeated identical errors make tie and row-order
   sensitivity a concrete concern;
4. the experiment is H01, fixed trajectory, and has no planner feedback.

The present conclusion is therefore:

$$
\text{promising basin-level correction}
\ne
\text{validated source-identification method}.
$$

## 2. Failure-to-mechanism audit

| Historical route | Observed failure | Scientific lesson retained | Boundary |
|---|---|---|---|
| RMFE fixed-amplitude family | H02 true-near candidate needed amplitude about 3.99 while a wrong candidate needed about 1.08 | strength, placement, transport and sensor gain are run-persistent nuisance variables | no fixed or truth-tuned amplitude |
| RMFE carrier-to-grid consumer | parser/geometry repair did not restore source ordering | carrier-to-cell projection must conserve mass | no claim from a repaired consumer alone |
| SCTT | ordered version was worse than shuffled | chronology is meaningful only when attached to a candidate-conditioned physical state | no PCA or generic ordered encoder as temporal novelty |
| residual TCN V1–V7 | some temporal sensitivity but unstable source/nuisance ordering | source-conditioned physics, not response sensitivity alone, is required | do not claim that missing training support was proved; the observed failure is representation/nuisance instability |
| V4–V7 protections | protection could preserve but not create ordering | posterior safety is downstream of a valid likelihood | do not generalize ORR-specific double use to every V4–V7 variant |
| ORR/V3 | 18/30 improved, pooled about 4.02%, H01 degraded | use completed physical stops, native concentration and single consumption | no occupancy-to-ppm, pseudo-replicated blocks or posterior reset |
| V4 identifiability Gate | only 7/150 accepted; at most 6/30 runs could change | a Gate cannot create information | no relaxed threshold or all-abstain success |
| V5/V6 | passive 0/30; absolute adequacy 0 | active sensing cannot rescue a false response family | forward/observation premise first |
| 33-feature wind MLP | conditional worse than static; shuffle not harmful | a learned input must be a physical parent | no summary/local-wind hazard likelihood |
| local-wind spatial CNN | fresh contexts 10–13: conditional worse than static; wind shuffle slightly better | sparse online wind is many-to-one with global corridor/recirculation structure | no deeper network for an unidentifiable input |
| exact first-passage phase | FULL 0.13841 versus SURVIVAL 0.13825; p=0.154; two contexts reversed | robust information is reachability/detection, not exact phase | arrival phase is an ablation |
| nearest airflow donor | oracle 0.13825; dev-nearest 0.47935; fresh LOCO 0.37941 | full transport family contains information not recoverable from sparse local wind | no hidden context ID or oracle donor |
| CTRE shadow | 43.60% formal improvement but inconsistent carrier rank | possible basin gain plus unresolved prior/tie/metric effects | no closed-loop claim yet |

Ideas rejected from the scientific method are generic residual
TCN/Transformer corrections, local-wind-to-hazard networks, precise arrival
phase as the main mechanism, independent best-member redraw at each stop,
occupancy interpreted as ppm, repeated blocks treated as independent stops,
posterior reset/temperature/blend/Top-K rescue, truth-conditioned nuisance
selection and active probing used to hide a failed likelihood.

Reliable positive evidence is limited to:

| Evidence | Result | Supports | Does not support |
|---|---:|---|---|
| fresh native source ordering | mean normalized rank 0.13825; median 20/210; Top-10 26.67%; Top-5 15.42% over 1,680 cases | M1 contains source information in H01 | external-House performance or calibrated likelihood |
| persistent-sensor parity | frozen bank serialization parity | reproducible physical-to-measured chain | calibrated event probability |
| coherent-versus-stopwise | 0.13288 versus 0.14841; 574/430/676; one-sided p=3.09e-6; no fresh-context reversal | shared transport identity helps H01 ordering | chronological-order increment, cross-House performance or Bayesian calibration |
| H01 shadow | 10/10 and 43.60% | strong fixed-trajectory development potential | exact replacement, planner feedback or confirmation |
| full-grid smoke | 626 cells × 1,500 samples in 2.758 s for one source/member | materialization is technically feasible | scientific authorization to spend the full cost |

## 3. Unified probability model

### 3.1 Variables and causal chain

Let:

- \(E=(G,B,W)\) denote source-independent environment information: geometry,
  boundaries/ventilation and global airflow;
- \(X_b\) denote poses and sample times at completed physical stop \(b\);
- \(S\) denote the persistent source carrier;
- \(U\) denote a legal 3-D placement within that carrier;
- \(Q\) denote source strength;
- \(K\) denote a stochastic native transport realization;
- \(\Psi\) denote source-independent persistent sensor/noise parameters;
- \(J=(U,Q,K,\Psi)\) denote a whole-run nuisance atom;
- \(C_n\), \(R_n\), and \(Y_n\) denote native concentration, persistent sensor
  state and measured gas at causal sample \(n\);
- \(D_b\) denote the stop observation used for inference, primarily
  reachability/detection, with arrival phase retained only as a diagnostic.

The controlled chain is:

$$
E,do(S=s),J,X_{1:n}
\rightarrow C_{1:n}
\rightarrow R_{1:n}
\rightarrow Y_{1:n}
\rightarrow D_{1:b}
\rightarrow p(S,J\mid D_{1:b})
\rightarrow p(S\mid D_{1:b})
\rightarrow \text{planner}.
$$

The native response and sensor process are:

$$
C_{1:n}=F_E(do(S=s),U,Q,K,X_{1:n}),\qquad
R_n=f_\Psi(R_{n-1},C_n),\qquad
Y_n\sim p_\Psi(\cdot\mid R_n).
$$

The real robot's measured \(Y_n\) is authoritative and is not passed through
the sensor model again. Only candidate physical tapes \(C_{1:n}\) are filtered
through \(f_\Psi\) before comparison with measured data.

Each native transport member must define one coherent four-dimensional world
\(C_{s,k}(x,t)\) across every queried cell and time. Independently regenerating
a member at each cell would destroy M2's scientific object.

### 3.2 Source-dependent but truth-blind nuisance design

Because legal placement \(U\) depends on candidate carrier \(i\), the nuisance
prior is not a candidate-independent \(\pi(j)\). It is:

$$
\pi_i(j\mid E)=
p(U_j\mid S=i,G)\,
p(Q_j)\,
p(K_j\mid E)\,
p(\Psi_j).
$$

Candidate alignment is imposed by a source-independent quantile/quadrature rule:
the same predeclared placement quantile, strength node, transport seed and
sensor node index is used for every carrier; only the legal coordinate obtained
from the carrier support changes. No true source, observed error or posterior
may influence this mapping or its weights.

The environment context \(W\) must either be genuinely available at runtime
from source-independent metadata/measurement, or be marginalized under a
source-independent prior. Reading the simulator's hidden true airflow identity
is an oracle and fails the method.

### 3.3 Sensor-aware stop emission

For candidate carrier \(i\), nuisance atom \(j\), and completed stop \(b\):

$$
g_b(i,j)=
p(D_b\mid D_{<b},do(S=i),J=j,X_{\le b},E).
$$

M3 separates physical reachability \(Z_b\) from measured detection \(D_b\):

$$
p(D_b\mid i,j)
=
\sum_{z\in\{0,1\}}
p_\Psi(D_b\mid Z_b=z)\,
p(Z_b=z\mid C_{i,j,1:b},X_{\le b}).
$$

For a binary detection with predicted probability \(r_{b,i,j}\):

$$
g_b(i,j)=r_{b,i,j}^{D_b}(1-r_{b,i,j})^{1-D_b}.
$$

The current deterministic-bit Jeffreys score 0.25/0.75 is only a frozen
surrogate proper score. It is not a calibrated physical likelihood. M3 must be
calibrated with source-independent sensor/noise and placement/transport
replicates or be reported honestly as a predictive score.

### 3.4 Coherent sequential update

Map the authoritative PMFS cell prior to carriers:

$$
q_0^C(i)=\sum_{c\in i}q_0^{cell}(c),\qquad
\rho_0(c\mid i)=\frac{q_0^{cell}(c)}{q_0^C(i)}.
$$

The within-carrier distribution \(\rho_0\) is frozen once. After carrier
inference:

$$
q_t^{cell}(c)=q_t^C(i(c))\,\rho_0(c\mid i(c)).
$$

This projection conserves mass. Any zero-support carrier remains unreachable
unless the preregistered baseline itself supplies positive support; inventing
support after seeing truth is forbidden and is audited before testing.

Initialize and globally normalize over all \((i,j)\):

$$
w_0(i,j)=q_0^C(i)\pi_i(j\mid E).
$$

Let \(\Delta_t\) contain only newly completed, unconsumed physical stops at
source update \(t\). Then:

$$
w_t(i,j)\propto
w_{t-1}(i,j)
\prod_{b\in\Delta_t}g_b(i,j),\qquad
q_t^C(i)=\sum_jw_t(i,j).
$$

The batch identity is:

$$
w_t(i,j)\propto
q_0^C(i)\pi_i(j\mid E)
\prod_{b\in\cup_{r\le t}\Delta_r}g_b(i,j).
$$

Online and batch results must match numerically at every update. The valid
coherence-ablated comparator is:

$$
q_{\mathrm{ind}}(i)\propto
q_0^C(i)
\prod_b\sum_j\pi_i(j\mid E)g_b(i,j),
$$

which intentionally permits a different nuisance explanation at each stop.

## 4. PMFS integration, single consumption and planner closure

CTT replaces the native source-observation channel exactly once:

1. retain authoritative PMFS mapping, motion, stop scheduling and planner;
2. retain actual sensor preprocessing exactly once;
3. shadow native source inference only for logging;
4. prevent the native source likelihood from also writing the ON posterior;
5. write \(q_t^{cell}\) once and let the audited planner consume it.

The ratio expression

$$
q_{\mathrm{CTT}}\propto
q_{\mathrm{PMFS}}\exp(L_{\mathrm{CTT}}-L_{\mathrm{PMFS}})
$$

is permitted only after it is proved as a numerical identity on identical
positive support. The current PMFS implementation does not expose a verified
incremental \(L_{\mathrm{PMFS}}\); pre-native replacement is safer.

The assimilation ledger primary key is:

$$
(\text{run UUID},\text{physical stop ID},
\text{sample start},\text{sample end}).
$$

It also records observation hash, method and update ID. Semantics are:

- same primary key and same hash: exact no-op;
- same primary key and different hash: fail closed;
- different physical stops with identical all-zero tapes: both are valid and
  both are consumed once.

Sensor recurrence at every 0.2 s sample is physical state evolution, not
another Bayesian consumption.

Replacement is incomplete until every planner belief consumer is audited.
In particular, sourceProbability, varianceOfHitProb, entropy/information
terms, candidate map summaries and target-selection inputs must all be either:

- derived consistently from CTT weights; or
- proved unused by the planner.

A mixed system using CTT sourceProbability and native varianceOfHitProb is not
the frozen method. A neutral-bypass OFF parity test must also show that
bypassing the native posterior write does not suppress unrelated PMFS state
updates or change the OFF trajectory.

## 5. The three serial scientific modules

### 5.1 M1 — native interventional concentration-response operator

**Failure addressed:** 2-D/proxy response families confound source, transport,
strength, placement and sensor effects.

**Definition:**

$$
\mathcal O_E:
(do(S=i),U,Q,K,X_{1:n})
\mapsto C_{i,U,Q,K}(X_{1:n}).
$$

M1 uses legal 3-D placement, frozen source strength, native transport and
truth-blind environment support. Sensor parameters are not part of the
concentration operator; they enter M3.

**Required provenance:** \(G,B,W\) must come from deployable,
source-independent information or be marginalized. Observation nuisance keys
are disjoint from predictive keys, but the true source must remain in candidate
support.

**Status:** **KEEP_AS_SUPPORTING_COMPONENT.** Candidate-source simulation is
already used by PMFS and related GSL work. M1 is necessary physical support,
not the novelty.

### 5.2 M2 — persistent coherent source–transport filter

**Failure addressed:** independently marginalizing nuisance at each stop allows
mutually incompatible plume realizations to explain one robot run.

**Definition:** retain \(w_t(S,J)\) by the recursion in Section 3.4. The same
transport, placement, strength and sensor state explains every completed stop
and source update. The contribution is latent physical persistence, not a
generic sequence encoder.

The present H01 result proves only:

> **coherence premise PASS under a frozen surrogate score.**

It does not yet prove a calibrated Bayesian posterior. The product likelihood
is exchangeable over correctly paired stops; therefore current evidence proves
cross-stop coherent latent structure, not an independent benefit from
chronological order. A future-predictive and raw-tape order Gate is required.

**Status:** **KEEP_AS_MAIN_INNOVATION**, collision risk **MEDIUM**. Atmospheric
source inversion already retains global source/meteorological parameters. The
defensible delta is narrower: a native stochastic plume-response member and
persistent sensor state are retained jointly with source across mobile-robot
stops and PMFS updates, with single-consumption source-channel replacement.

### 5.3 M3 — sensor-aware reachability/detection emission

**Failure addressed:** exact first-passage phase reverses across fresh airflow
contexts, while ever/never reachability remains stable; deterministic simulator
hits are not measured sensor probabilities.

**Definition:** pass each M1 concentration tape through the same persistent
sensor/noise family as the robot and form the calibrated emission in Section
3.3. Physical reachability, false negative, false positive and sensor memory
are separated. Exact arrival time is retained as an ablation.

**Independent role:** M3 changes the mapping from physical concentration to
evidence. It does not reconstruct transport, choose a source or provide
temporal coherence. It therefore acts at a different point from M1 and M2.

**Status:** **KEEP_AS_SUPPORTING_COMPONENT.** Detection/non-detection and
occupancy models are established in GSL and ecology; the gas-specific
sensor-persistent coupling is necessary but not claimed as standalone novelty.
The current 0.25/0.75 surrogate means this module is not yet validated.

### 5.4 Neural operator — optional accelerator outside the science modules

An admissible future accelerator is:

$$
N_\theta(G,B,W,do(S=i),U,Q,K,x,t)
\rightarrow \log(1+C_{i,U,Q,K}(x,t)).
$$

It does not read \(\Psi\), PMFS posterior, source truth, error, rank or planner
choice. The exact M3 sensor model remains downstream.

It may be reconsidered only if:

1. the runtime global physical inputs are actually available and pass an
   input-identifiability Gate;
2. exact M1+M2+M3 is already scientifically positive;
3. held-out carriers, free cells, airflow contexts and members pass pointwise
   concentration, likelihood, posterior and planner parity;
4. closed-loop error is non-inferior and runtime/storage improves materially.

Current status: **REJECT_COLLISION_AND_NO_EVIDENCE**. Route-bank reconstruction
alone cannot authorize arbitrary planner-divergent queries.

## 6. Cross-domain Mechanism Transfer

The transfer rule is:

$$
\text{observed failure}
\rightarrow\text{remote principle}
\rightarrow\text{gas-specific rederivation}
\rightarrow\text{falsification}.
$$

| Observed failure | Remote field and exact source | Original principle | Gas-specific adaptation | Decision |
|---|---|---|---|---|
| candidate physics must encode a controlled source cause | causal physical intervention: *Causal chambers as a real-world physical testbed for AI methodology*, Nature Machine Intelligence (2025); interventional representation identification, NeurIPS (2024) | interventions define mechanisms and identifiability conditions | native \(do(S=i)\) response under legal aligned nuisance support and reserved observation worlds | M1 support; not novel by itself |
| per-stop redraw destroys one-run plume consistency | atmospheric transport inversion: Lucas et al., *Bayesian inverse modeling of the atmospheric transport and emissions of a controlled tracer release from a nuclear power plant*, *Atmospheric Chemistry and Physics* (2017), DOI 10.5194/acp-17-13521-2017; coherent latent-field reconstruction: McAlpine et al., *The Manticore Project I: a digital twin of our cosmic neighbourhood from Bayesian field-level analysis*, MNRAS (2025), DOI 10.1093/mnras/staf767 | repeated observations share one latent physical realization and its uncertainty is marginalized jointly | persistent native GADEN member, placement, strength and sensor state in \(w_t(S,J)\) | M2 main candidate |
| exact phase is unstable but reachability survives | imperfect-detection/occupancy models: Priyadarshani et al., *A unified framework for time-to-detection occupancy and abundance models*, *Methods in Ecology and Evolution* (2024), DOI 10.1111/2041-210X.14296; Goldstein et al., *Guidelines for estimating occupancy from autocorrelated camera trap detections*, *Methods in Ecology and Evolution* (2024), DOI 10.1111/2041-210X.14359 | separate latent presence/reachability from imperfect observation and avoid autocorrelated pseudo-replication | M1 plume reachability plus persistent gas-sensor false-positive/false-negative emission | M3 support |
| sparse online wind does not identify global corridor topology | sparse-field reconstruction and physics-consistent projection, *Communications Physics* (2025), article s42005-025-02329-1 | learned reconstruction requires identifiable inputs and explicit physical constraints | first test conditional information in deployable inputs; reject learning if many-to-one | rejected under current input |
| native field bank is expensive | neural operators in *Nature Reviews Physics* (2024), ICLR (2026), and *Nature Communications* (2025–2026) | approximate a physical operator and qualify out of distribution | only compress M1 after exact concentration-to-posterior parity | optional engineering accelerator |

What is deliberately not transferred: gene/cell identity, ecological species
semantics, astronomical image priors, a learned inverse source label, or an
oracle global airflow identity. The secondary innovation is the rederived
source–transport–sensor chain, not the imported name.

## 7. GSL Collision Audit

The closest authoritative baseline is Ojeda, Monroy and
Gonzalez-Jimenez, *Robotic Gas Source Localization with Probabilistic Mapping
and Online Dispersion Simulation*, IEEE Transactions on Robotics 40 (2024),
DOI 10.1109/TRO.2024.3426368. It already simulates candidate sources,
constructs probabilistic hit maps and performs Bayesian localization.
Detection/non-detection likelihoods and information-driven plume search are
also established. Learned plume/source-conditioned dispersion surrogates
already appear in ICRA 2023 and ISOEN 2024.

Therefore candidate simulation, hit/miss evidence and neural plume surrogacy
cannot be claimed independently new.

### CTT_CROSS_DOMAIN_INNOVATION_COLLISION_MATRIX_20260830

| Candidate innovation | Failure addressed | Remote field | Exact source paper / year / venue | Original principle | Transferred / not transferred | Gas-specific derivation | Closest GSL paper | Object / information-flow / capability difference | Risk | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| native candidate intervention response | proxy physics and nuisance confounding | causal physical experiments; transport inversion | *Causal chambers*, 2025, Nature Machine Intelligence; Lucas et al., 2017, ACP | controlled physical cause and uncertainty-aware forward family | transfer intervention/provenance; not causal-effect estimation from simulator alone | legal native 3-D source × strength × transport field family | PMFS, TRO 2024 | same candidate-forward object; higher-fidelity support but no new information flow | HIGH | **KEEP_AS_SUPPORTING_COMPONENT** |
| persistent coherent source–transport state | per-stop nuisance redraw | atmospheric/astronomical latent-field inference | Lucas et al., *Bayesian inverse modeling of the atmospheric transport and emissions of a controlled tracer release from a nuclear power plant*, 2017, ACP; McAlpine et al., *The Manticore Project I: a digital twin of our cosmic neighbourhood from Bayesian field-level analysis*, 2025, MNRAS | one latent realization jointly explains repeated observations | transfer persistent latent/marginalization; not astronomical image model | \(w_t(S,J)\) keeps one native plume member across mobile stops and PMFS updates | PMFS 2024; Bayesian UAV source-term estimation, JFR 2019 | related source/nuisance inference exists, but this search found no GSL paper with the exact native response-member identity retained across stops plus PMFS channel replacement | MEDIUM | **KEEP_AS_MAIN_INNOVATION** |
| reachability/detection emission | unstable exact phase and imperfect gas sensor | ecology occupancy/detection; survival/event history | Priyadarshani et al., *A unified framework for time-to-detection occupancy and abundance models*, 2024, MEE; Goldstein et al., *Guidelines for estimating occupancy from autocorrelated camera trap detections*, 2024, MEE | latent presence and imperfect detection are distinct, and repeated detections may be autocorrelated | transfer decomposition; not species/INLA model | native plume reachability through persistent gas sensor at completed stops | Farrell et al., *Plume Mapping via Hidden Markov Methods*, IEEE TSMC-B 2003; Infotaxis, Nature 2007; PMFS 2024 | same detection object exists; sensor-state coupling supports M2 but is not standalone novelty | HIGH | **KEEP_AS_SUPPORTING_COMPONENT** |
| exact replacement and event ledger | double consumption and posterior reset | sequential Bayes/data assimilation | standard filtering literature | each datum updates one state once | transfer accounting; no new likelihood | pre-native source-channel bypass, physical-stop key, online=batch audit | PMFS cumulative update | integration correctness rather than new scientific object | HIGH overlap / low standalone novelty | method contract only |
| sparse-wind hidden-field neural reconstruction | local wind many-to-one with global topology | sparse flow reconstruction | recent CFD/physics-consistent reconstruction work, 2024–2026 | infer hidden field only when inputs contain it | transfer identifiability test; not assumption that a deeper net creates information | no model admitted under present \(W_{online}\) | GSL wind mapping and PMFS | current input fails premise | N/A | **REJECT_NO_EVIDENCE** |
| neural native-response surrogate | physical bank cost | neural operators | ICLR 2026; Nature Communications 2025–2026 | approximate forward PDE operator | transfer operator parity; not inverse source classifier | candidate-conditioned M1 compression, exact M3 downstream | Jin et al., ICRA 2023, DOI 10.1109/ICRA48891.2023.10160816; Prieto Ruiz et al., ISOEN 2024, DOI 10.1109/ISOEN61239.2024.10556061; Kim et al., arXiv:2608.16221 | implementation restrictions differ, but the neural plume-surrogate object already exists | COLLISION as science module | **REJECT_COLLISION**; possible engineering accelerator |

The strongest defensible novelty verdict is **Level 3 — Medium Overlap**.
M1 and M3 overlap strongly with prior GSL objects. M2 shares Bayesian
source/nuisance inference with atmospheric and GSL literature but differs in
the retained native stochastic response-member identity, mobile sequential
stops, persistent sensor state and exact PMFS channel replacement.

The one-sentence delta is:

> Unlike PMFS, which constructs candidate hit evidence without retaining one
> native stochastic plume realization as a joint latent state across the whole
> robot run, CTT maintains and marginalizes a persistent source–transport–
> sensor atom across completed stops, aiming to prevent mutually incompatible
> per-stop plume explanations from reversing source evidence.

This is a search-bounded conclusion, not a claim that no such method exists
anywhere. During the 2026-08-30 search, Semantic Scholar returned rate-limit
errors, OpenAlex timed out on one query, DBLP's proxy failed, and the Windows
CLI encountered a Unicode display error after retaining the raw JSON. Key
papers above were checked through DOI/publisher or official venue pages.

## 8. Independent low-cost falsification Gates

### G0 — metric, prior, tie and recurrence audit

Freeze before execution and use existing H01 data:

1. authoritative \(q_0\)-only formal error;
2. source-label permutation that keeps candidate coordinates and \(q_0\) fixed
   while permuting likelihood rows relative to source identity;
3. observation-to-stop pairing permutation; a pure multiplication-order
   permutation is not a valid destruction control;
4. raw-tape chronological destruction only by rerunning the persistent sensor
   pipeline, when the raw tape is available;
5. legal cell-row permutations and a tie-aware boundary sensitivity analysis,
   while retaining the original PMFS formal metric as authoritative;
6. true-cell rank/mass, carrier rank/mass, raw score, and posterior mass within
   0.5/1/2 m;
7. online joint recursion versus batch parity at all five source updates.

Stop with **CTT_SHADOW_METRIC_OR_RECURRENCE_NO_GO** if the 43.60% signal
survives source-label/pairing destruction, changes materially under legal row
ordering, or online=batch parity fails.

### G1 — M1 source ordering and environment provenance

- prove full candidate prior support before truth is read;
- observation nuisance keys are disjoint from predictive keys;
- use reserved source/placement/transport worlds;
- compare true-source ordering with a candidate-label permutation null;
- audit H01/H02/H03 separately;
- prove \(W\) is deployable source-independent context or marginalize it;
- require non-null ordering and no House reversal.

Current status: H01 premise PASS; external-House and provenance Gates pending.

### G2 — M3 sensor/reachability emission

- preserve actual measured gas as authoritative;
- process candidate concentration through the same persistent sensor;
- use source-independent sensor/noise calibration replicates;
- report calibration, proper score, false-positive/false-negative behavior and
  absolute source-independent adequacy;
- compare reachability/detection with exact-phase and sensorless ablations.

Current status: sensor implementation parity PASS; calibrated likelihood
pending. The 0.25/0.75 score is not enough.

### G3 — M2 coherence and future-predictive increment

On identical M1/M3 emissions, compare:

- coherent whole-run \(w_t(S,J)\);
- valid independent-per-stop nuisance marginalization;
- member-identity permutation;
- future-stop prediction from previous stops;
- observation-to-stop pairing destruction;
- raw chronological destruction through the sensor model when feasible.

Report proper score, true-source rank/mass and formal error at actual update
boundaries. Require a preregistered directional paired test and no House
reversal. Current H01 result is only a coherence premise PASS under a surrogate
score.

### G4 — optional neural acceleration Gate

G4 is not needed to validate the scientific CTT method. It may be attempted
only after exact M1+M2+M3 is positive. Thresholds must be calibrated on
simulator-only development data and signed before held-out evaluation. Required
held-out axes are carriers, free-cell spatial queries, airflow contexts,
transport members and Houses.

It must pass:

- native physical concentration parity;
- reachability/likelihood parity;
- posterior total-variation/KL and candidate ordering parity;
- planner target parity;
- closed-loop non-inferiority;
- a preregistered material query-speed or storage benefit.

Failure permanently removes the network without changing scientific CTT.

### G5 — replacement, ledger and planner-consumer safety

- neutral-bypass OFF parity;
- exact source-channel single consumption;
- primary-key ledger invariants;
- online=batch posterior parity;
- carrier-to-cell mass conservation;
- sourceProbability and every planner belief input, including
  varianceOfHitProb, derived consistently or proved unused;
- finite posterior and no hidden truth/airflow oracle.

The current H01 shadow does not pass G5.

## 9. Hierarchical ablation contract

The three modules form a serial generative model; a blind \(2^3\) factorial is
not mathematically valid.

| Arm | Definition | Question | Status |
|---|---|---|---|
| PMFS | authoritative main_v8 | baseline | valid |
| M1 diagnostic | native candidate concentration family, no event likelihood | does physical response contain source ordering? | diagnostic only |
| M2 only | no candidate response or emission | none | structural N/A |
| M3 only | sensor model without candidate concentration | none | structural N/A |
| M1+M3 | native response plus calibrated sensor emission, nuisance marginalized independently per stop | does higher-fidelity physical/sensor evidence help without coherence? | valid coherence ablation |
| M1+M2 | coherent update using the frozen surrogate score | does persistent nuisance have a premise signal before calibration? | diagnostic, not deployable likelihood |
| M2+M3 | no source-conditioned physical family | none | structural N/A |
| M1+M2+M3 | exact native response, calibrated sensor emission and coherent whole-run filter | full scientific method | valid after G0–G3/G5 |

Additional controls:

- M1 source-label, placement-quantile and transport-member permutations;
- M2 independent-per-stop, member-identity and pairing destruction;
- M3 sensorless, detection-null and exact-phase comparisons;
- PMFS OFF and neutral-bypass parity;
- exact versus neural acceleration is a separate engineering comparison, not a
  fourth scientific contribution.

## 10. Fastest execution path

### Phase 0 — preserve current state

- Full-grid materialization remains paused.
- Partial context 14 contains 24/1,680 complete atomic worlds, zero temporary
  files and about 159 MB; no generator is active.
- Preserve these files read-only and reuse them only if their hashes match the
  final contract.

### Phase 1 — G0, estimated 5–20 minutes

Use existing H01 10-seed shadow artifacts. No GADEN, neural training, ROS or new
result-driven threshold is needed.

### Phase 2 — G1/G2/G3 with existing banks

Verify exact source/route/member/sensor/hash provenance before reading external
outcomes. Freeze formulas first. Reuse existing H01/H02/H03 physical banks
where support matches; do not regenerate GADEN merely to fill a convenient
table.

### Phase 3 — exact fixed-trajectory integration and G5

Implement exact M1+M2+M3 in an isolated binary only after premise Gates pass.
Verify source-channel replacement, ledger semantics, planner consumers and
online=batch parity at every source update.

### Phase 4 — one revealed tiny closed-loop runtime check

After G0–G3 and G5:

- one already revealed H01 seed;
- contemporaneous PMFS OFF and exact CTT ON;
- full 300 s;
- no tuning from localization error;
- runtime/ledger/planner closure are hard checks; error is only a development
  diagnostic.

At the smoke benchmark, one H01 full bank is about 77 minutes and 6.3 GB before
compression. This cost is incurred only after premise authorization.

### Phase 5 — frozen 30-pair development

Run H01/H02/H03 × seeds 0–9, paired OFF/ON for 300 s. Freeze source truth,
observation world, initial pose, planner RNG, candidate nuisance and binary.
Observation nuisance keys remain disjoint from predictive keys. Do not inspect
or modify the batch midway.

Development GO requires:

- 30/30 valid pairs;
- pooled official-error improvement at least 10%;
- at least 20/30 pairwise wins;
- nonnegative median improvement;
- no House pooled degradation greater than 5%;
- zero new catastrophes.

A performance catastrophe is preregistered as both
\(e_{ON}>e_{OFF}+1\,m\) and \(e_{ON}>1.5e_{OFF}\).
A false-confident catastrophe is posterior internal variance below
\(1\,m^2\) while final Euclidean error exceeds \(2\,m\).
Report a paired bootstrap confidence interval; development is not the paper's
confirmatory claim.

### Phase 6 — confirmation

Freeze source, binary, launch, exact bank generation, sensor calibration,
metrics and all thresholds. Use previously unseen seeds 10–19 or a genuinely
unseen airflow/environment split. The paper-level 10% claim must come from this
stage.

### Optional Phase 7 — engineering acceleration

Only after exact CTT succeeds, one frozen shared neural operator may attempt G4.
It cannot rescue or define the scientific method.

## 11. Asset inventory

Reusable now:

- 16,800-world H01 wind-conditioned route bank and manifests;
- fresh contexts 10–13 source-ordering cases;
- coherent-versus-stopwise 1,680-case evidence;
- H01 seeds 0–9 schedules and shadow artifacts;
- persistent-sensor parity tools and native RNG-controlled generator;
- H01/H02/H03 PF-DEI banks with provable support/provenance;
- full-grid smoke and 24 complete context-14 worlds.

Generate only after Gates:

- missing arbitrary-position worlds required by a planner-divergent runtime;
- cross-House banks not already supported by verified artifacts;
- new paired closed-loop observations;
- genuinely unseen confirmatory airflow/environment data.

Never tune from outcomes:

- source/transport keys, nuisance ranges or sensor emission;
- thresholds, planner, metric, architecture or checkpoint rule;
- source truth or real-environment labels for network fine-tuning.

## 12. Final scientific verdict

Current status:

| Item | Verdict |
|---|---|
| M1 native interventional source information | H01 PREMISE PASS / EXTERNAL AND PROVENANCE PENDING |
| M2 persistent coherent source–transport state | H01 COHERENCE PREMISE PASS UNDER SURROGATE / EXTERNAL PENDING |
| M3 calibrated sensor-aware detection emission | IMPLEMENTATION PARITY PASS / CALIBRATION NOT PASSED |
| neural scientific module | REJECT_COLLISION_AND_NO_EVIDENCE |
| exact PMFS channel replacement and ledger | NOT IMPLEMENTED / G5 NOT PASSED |
| H01 shadow formal improvement | STRONG DEVELOPMENT SIGNAL |
| H01 exact-carrier consistency | FAILING / UNRESOLVED |
| closed-loop authorization | NO |
| confirmed improvement of at least 10% | NOT ESTABLISHED |

The method is therefore scientifically coherent but not empirically complete.
Its main innovation is still the spatiotemporal/causal object the project
wanted: candidate source interventions are evaluated through one persistent
transport realization across sequential observations. The third module is a
sensor/detection model, not a fashionable network.

The next permitted action is G0. If G0 fails, the 43.60% shadow is rejected as
a metric/prior/recurrence artifact. If G0 passes, G1–G3 and G5 determine
whether exact CTT earns one tiny closed-loop run. No neural work or full-grid
materialization is authorized before that point.
