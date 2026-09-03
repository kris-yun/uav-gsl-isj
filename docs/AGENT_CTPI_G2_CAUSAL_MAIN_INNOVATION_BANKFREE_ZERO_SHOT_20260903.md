# CTPI G2 addendum — causal main innovation + bank-free zero-shot deployment

This document **extends and strengthens** `docs/AGENT_CTPI_G2_DISTANT_SCIENCE_2026_THREE_MODULE_REDESIGN_20260903.md`. Read both. If wording conflicts, this addendum controls the G2 scientific identity and deployment target.

## 1. Paper-level main innovation is causal, not optional

The G2 paper-level innovation must remain a **causal representation / causal world-model paradigm for robotic gas-source localization**. Do not demote causality to one candidate feature among many.

The working scientific thesis is:

> Gas-source localization should not directly map observations to a source coordinate or rely on scene-specific lookup banks. It should explicitly represent the causal chain
>
> `source -> transport -> local encounter -> sensor response -> observation -> posterior -> intervention/action -> new observation`,
>
> separate source identity from transport/sensor nuisance, predict intervention-conditioned future observations, and choose actions by their expected causal resolution of source uncertainty.

Existing evidence is enough to justify keeping this causal direction as the main line, but not enough to claim the full causal three-module closed loop is already proven:

- M1 CREL has confirmed downstream evidence.
- M2 TSDC has fresh confirmatory predictive evidence.
- The complete three-module closed-loop gain is still under validation and must not be overclaimed before true closed-loop results.

Therefore G2 must be a **second-generation causal architecture**, not a replacement of causality with an unrelated fashionable method.

## 2. Three modules must be three parts of one causal model

The preferred G2 factorization is:

### M1 — Causal Source Representation / Inverse Causal Evidence
Infer the latent source state while separating nuisance variables.

Desired latent factorization should explicitly consider variables such as

- `S`: source state / source region;
- `Z`: transport realization / flow-regime nuisance;
- `A` or equivalent: source-strength / amplitude nuisance;
- `M`: sensor-memory state;
- `O_1:t`: executed observations;
- `R_1:t`: executed robot route/history.

M1 should approximate a causal source posterior such as

`p(S | do(R_1:t), O_1:t)`

or an equivalent identifiable representation, rather than treating transport amplitude, sensor memory, and source identity as one undifferentiated score.

This module must directly attack the RMFE fixed-amplitude failure and nuisance-confounding failures.

### M2 — Causal Transport–Observation World Model
Predict the future observation distribution under an **intervention on the next robot action**:

`p(O_{t+1:t+H} | S, do(a), geometry, local wind/context, M_t)`.

This is where distant-field ideas such as committors, rare-event dynamics, coarse-grained memory, latent transport modes, neural/operator surrogates, Koopman-like latent dynamics, or stochastic transport operators may enter.

M2 is not allowed to re-assimilate the current observation into the source posterior as a second M1. Its job is future counterfactual prediction under candidate actions.

### M3 — Causal Experimental Design / Intervention Planning
Use M1 posterior and M2's intervention-conditioned predictive law to choose the next physically feasible action.

A generic objective may be information-theoretic, decision-theoretic, or information-geometric, but it must evaluate **what observation distribution would change under `do(a)`**, not merely move toward the current posterior maximum.

The planner must consume M2 in the actual runtime causal chain. No decorative planner module and no post-hoc arbitrary planner-weight tuning.

## 3. Bank-free deployment is a hard G2 requirement

The current predictive bank is useful for controlled development and falsification, but it is **not acceptable as the final deployment identity** of G2.

### Final deployment target
On an unfamiliar environment, the robot should not need to first generate a scene-specific predictive bank before it can localize a gas source.

The desired deployment contract is:

- no per-scene GADEN precomputation;
- no precomputed `source x transport-member x action` bank for the new site;
- no per-site retraining or calibration after seeing source truth;
- no requirement that the new House/environment appeared during training;
- no source-location truth, future gas, or future wind leakage;
- the robot may directly use information physically available at deployment time.

### Information allowed at deployment
A new environment may provide or be sensed online:

- occupancy map / geometry, including a map produced online by SLAM;
- current and recent local wind measurements or an online wind estimate;
- current and past gas measurements;
- robot pose and executed trajectory;
- sensor internal state / causal memory state;
- physically feasible candidate actions;
- a source search domain or region prior that does not contain hidden source truth.

The robot should then directly begin closed-loop localization.

### Preferred bank-free M2 abstraction
Replace the site-specific lookup bank by a geometry- and context-conditioned stochastic transport operator / causal world model of the form

`F_theta : (geometry, wind/context, source hypothesis, action/route, sensor state) -> distribution of future encounter/observation`.

Examples of acceptable outputs include

- future hit/encounter probability;
- finite-horizon committor;
- distribution over concentration / detection events;
- latent transport-mode distribution;
- calibrated stochastic trajectory or observation law.

The scientific identity is the **causal transport–observation operator**, not a particular neural architecture.

The operator may be trained offline once across many heterogeneous environments. Deployment to a new environment must be amortized/zero-shot or use only causal online state estimation; it must not require a new simulator campaign for that site.

## 4. Direct-flight target: what 'arrive and fly' means

The desired final workflow for a previously unseen environment is:

1. obtain or build geometry/occupancy online;
2. start measuring local wind and gas;
3. initialize a source-region prior without source truth;
4. M1 updates causal source belief from executed observations;
5. M2 predicts future observations for candidate actions using the learned bank-free causal operator;
6. M3 selects the next action;
7. robot moves and obtains fresh real observations;
8. repeat until localization terminates.

There must be no hidden stage of 'pause deployment, run GADEN for this scene, generate 8/32/64 predictive members per source, then fly'.

Initial mapping/SLAM is not considered a predictive bank. Reading geometry and live wind is normal deployment sensing.

## 5. Bank-free generalization must be tested explicitly

A G2 candidate cannot be declared successful only because it reproduces the current House banks.

Required evaluation hierarchy:

### Stage 1 — bank-distillation diagnostic
Use existing H01/H02/H03 banks as teacher/evaluation assets only. Test whether the learned causal transport operator can reproduce source-conditioned future-observation structure without memorizing source IDs or House IDs.

### Stage 2 — leave-one-House-out zero-shot
Train/develop without one House, then deploy on that held-out House with **no bank from the held-out House used at runtime**.

The held-out House may supply only geometry and online observations that a real robot would have.

### Stage 3 — geometry / flow perturbation generalization
Evaluate on altered geometry, wind regime, source strength and transport realization not used during fitting. Explicitly test nuisance invariance and source contrast.

### Stage 4 — true bank-free closed loop
Run the full M1+M2+M3 system where the planner never queries the old predictive bank. Compare against classic PMFS and, separately, against the bank-assisted G2 diagnostic version.

Required comparison should include at least:

- classic PMFS;
- causal G2 with legacy predictive bank (diagnostic upper/reference condition if scientifically useful);
- causal G2 bank-free operator;
- destructive controls.

Bank-free success requires that the bank-free full system retains the preregistered task advantage without scene-specific precomputation.

## 6. The >=10% goal applies to the deployable causal system

The performance target is not merely for a bank-assisted laboratory version.

The final claim sought is:

> A causal three-module system that can operate in an unseen environment without generating a site-specific predictive bank achieves at least 10% relative improvement over classic/native PMFS on the preregistered primary continuous task metric, with all three modules load-bearing and no systematic cross-environment reversal.

If the bank-assisted version exceeds 10% but the bank-free version collapses, the deployment problem is not solved and G2 is not complete.

If the bank-free system cannot reach the target, report the exact remaining gap instead of weakening the requirement after seeing results.

## 7. Literature search must now prioritize causal + bank-free mechanisms

When searching 2026 distant-field literature, add the following explicit questions:

1. How do recent natural-science methods learn **causal latent state** rather than predictive correlation?
2. How do they separate invariant causes from environment-specific nuisance?
3. How do they learn dynamics/operators that generalize across geometry/discretization/regimes?
4. How do rare-event and committor methods predict intervention-conditioned future events without brute-force path libraries at each new system?
5. How do operator-learning / scientific-ML methods condition on geometry and boundary conditions in unseen domains?
6. How do autonomous-science systems choose interventions under model uncertainty without hand-tuned acquisition weights?
7. What identifiability or invariance tests distinguish a genuinely causal representation from a high-performing correlational surrogate?

Priority mother-idea families include, but are not limited to:

- causal representation learning / invariant mechanism learning;
- causal state-space and latent dynamical models;
- stochastic operator learning conditioned on geometry/boundary conditions;
- rare-event committor / transition-path objects;
- coarse-grained Markovian embedding / Mori–Zwanzig memory closure;
- Lagrangian coherent / transport-mode representations when source identity remains identifiable;
- uncertainty-calibrated experimental design / causal information gain;
- physics-informed amortized inference that can operate zero-shot on new environments.

Do not choose a generic foundation model or neural network merely because it removes a bank. The new provider must preserve the causal source–transport–sensor semantics.

## 8. Required additional falsification for causality

In addition to earlier destructive controls, explicitly test:

- environment-label removal / House-ID prohibition;
- source-strength intervention while holding source region fixed;
- transport-regime intervention while holding source fixed;
- sensor-memory intervention / reset tests;
- geometry perturbation;
- wind perturbation;
- source-label permutation;
- action intervention consistency;
- counterfactual consistency where simulator interventions are available;
- invariant performance of source representation across nuisance changes;
- degradation when the causal edge claimed by a module is destroyed.

A candidate should be rejected if it only works because House identity or scene-specific bank contents reveal the source indirectly.

## 9. Practical two-track rule

Do not block the currently frozen bank-assisted CREL–TSDC–PIP closed-loop experiment. That experiment remains scientifically useful because it establishes whether the current causal components are load-bearing under controlled conditions.

Run G2 bank-free work in a separate branch/worktree:

- Track A: finish current frozen bank-assisted closed-loop validation unchanged;
- Track B: develop G2 causal bank-free architecture and zero-shot deployment.

Use Track A results as diagnostic evidence only after they are produced. Do not retroactively tune Track A.

## 10. Required new deliverables

In addition to the existing G2 deliverables, create:

- `CAUSAL_MAIN_INNOVATION_THESIS.md` — one clear paper-level causal thesis, causal graph, assumptions and novelty boundary;
- `BANK_DEPENDENCE_AUDIT.md` — exactly where the current method consumes site-specific bank information;
- `BANK_FREE_CAUSAL_OPERATOR_DESIGN.md` — mathematical/operator design and runtime API;
- `ZERO_SHOT_DEPLOYMENT_CONTRACT.json` — what is and is not allowed in a new environment;
- `LEAVE_ONE_HOUSE_OUT_PROTOCOL.md` — no held-out-House bank at runtime;
- `CAUSAL_INTERVENTION_FALSIFICATION.md` — intervention/invariance controls;
- `BANK_ASSISTED_VS_BANK_FREE_ABLATION.md` — explicit task comparison;
- final `G2_CAUSAL_BANKFREE_GO_NO_GO.json`.

The final G2 recommendation must separately answer:

1. Is the causal representation genuinely supported rather than merely correlated?
2. Do M1, M2 and M3 each improve the downstream task?
3. Does the full system beat classic PMFS by the preregistered >=10% target?
4. Does that advantage survive when the new environment has **no pre-generated predictive bank**?
5. Can the robot start localization from geometry + live sensing without a site-specific simulator campaign?

Do not call G2 complete until all five questions have evidence-backed answers.
