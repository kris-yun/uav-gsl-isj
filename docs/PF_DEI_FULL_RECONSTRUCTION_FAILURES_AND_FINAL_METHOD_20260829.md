# PF-DEI full reconstruction from failure history

Date: 2026-08-29
Status: MASTER SCIENTIFIC RECONSTRUCTION / DOES NOT INTERRUPT THE CURRENT H01 SOURCE-INFORMATION AUDIT

This document rebuilds the method from the complete failure lineage rather than from the latest Codex status string. It distinguishes verified repository evidence, negative results, historical development-only results, and the physically closed method that remains scientifically defensible.

## 1. What has already been tried and must not be repackaged as new

### 1.1 ME-ACI V10 / inverse-causal sequential assimilation

The frozen repository history at commit `c7f665f...` already implemented an inverse cause-from-effect viewpoint inspired by Assimilative Causal Inference (ACI), together with sequential evidence accumulation, two disjoint temporal folds, spatial hit replication, conditional elimination of an unknown release/sensor intercept, and marginalization over a 54-member transport-discrepancy family.

Development evidence in the frozen V10 repository reported 6/6 House01/02/03 seed0/1 improvements, pooled error 4.782312 m -> 2.822042 m (40.990% reduction). This was strong development/mechanism evidence, but the formula and release rule were developed with those House outcomes visible and the repository itself required a later truth-blind confirmatory study. Therefore ACI, sequential assimilation, temporal splitting, spatial replication and nuisance marginalization are prior project lineage, not new 2026-08-29 contributions.

A later conversation reported a V11 held-out 3/3 improvement (18.8% pooled), but the current independent reconstruction has not recovered the complete immutable V11 evidence package from the currently inspected repository state. It is therefore not used here as a primary verified claim.

### 1.2 RMFE / amplitude-sensitive forward ranking

RMFE demonstrated that a transport-forward score can be non-degenerate yet source-invalid. In the frozen H02 full32x2 result, OFF error 3.2146 m became ON 3.5065 m for both seeds (0/2 improvement). The near-true source candidate required a fitted amplitude far from the frozen amplitude and was badly ranked. Lesson: source location cannot be inferred with a forward family whose amplitude/source-strength nuisance is incorrectly fixed.

### 1.3 SCTT / ordered transport representation

SCTT explicitly attempted temporal transport representation. Its downstream result did not beat Classic PMFS, and a shuffle control outperformed ordered SCTT. Lesson: merely preserving order, or calling a representation spatiotemporal, does not prove useful temporal dynamics. Any final method must pass an order-sensitive falsification after the observation model is physically correct.

### 1.4 CG-PC-CTT V3

The V3 family produced partial paired improvements (18/30) but only about +4% pooled and degraded H01. It could deconcentrate already-good PMFS posteriors. Lesson: replacing a native posterior with a learned/causal posterior is unsafe unless the new evidence is absolutely calibrated and minimum-change semantics are respected.

### 1.5 V4

V4 introduced cumulative causal assimilation and minimum-change logic but its evidence representation fragmented into many components. Truth-blind coverage was only 7/150 accepted contexts and ACCEPT occurred in only 6/30 runs. Lesson: a representation may be non-degenerate while remaining source-invalid; exact component identity is not a robust source variable.

### 1.6 V5

V5 fixed the exact V4 trajectory deadlock by accumulating physical stops and adding Active Probe, but fresh passive replay had 0/30 runs with any ACCEPT. Independent audit also found that Active Probe overlapped strongly with existing information-driven sensing, could amplify a misspecified forward family, did not implement true anytime-valid sequential inference, and overclaimed causality. Lesson: active sensing cannot rescue a misspecified source-evidence model and is not the main novelty.

### 1.7 V6-A

V6-A removed hard components and directly marginalized transport members within context, yet had 0/30 continuous predictive PASS; transfer-only pass counts were H01 1/10, H02 0/10, H03 2/10, with zero absolute-adequacy passes. Lesson: frequency-only transport evidence is insufficient even after component fragmentation is removed. This is stronger evidence against the compressed representation, not proof that the entire physical transport family is useless.

## 2. The decisive failure mechanism discovered later

The major conceptual mistake was not a missing Gate. It was an incorrect observation-generative model.

Old approximations implicitly behaved like:

`source -> occupancy/frequency/propensity -> local HIT/MISS evidence`.

Source audit and native forward closure established the actual chain:

`S -> U -> Z_t -> C_t -> R_t -> M_t -> PMFS block decision`.

Where:

- `S`: persistent planar source carrier region, the actual localization target;
- `U`: unresolved physical 3-D placement inside that carrier;
- `Z_t`: stochastic 3-D plume transport state/realization;
- `C_t`: physical concentration at the robot;
- `R_t`: run-persistent sensor internal state;
- `M_t`: measured ppm available to PMFS.

Key verified consequences:

1. CTT occupancy is not physical concentration and cannot be mapped empirically to ppm.
2. PMFS block evidence is based on averaged measured concentration, not occupancy bits.
3. The native sensor is stateful across stops; historical replay found 159/4049 ideal-vs-native block-decision flips. Sensor memory is a real deterministic aliasing mechanism, but because flips are bidirectional and only 3.93% overall, it is not by itself the full generalization failure.
4. Forward-operator closure reproduced 4049/4049 historical block decisions and native query/sensor parity.
5. The source state is a 2-D region, not the stored carrier centroid. All H01/H02/H03 carriers have legal 3-D placement support when the original carrier free-cell region is used.
6. Explicit GADEN RNG control is parity-proven and can generate distinct stochastic plume realizations without changing the physics equations.

## 3. Failure lessons that now constrain the final method

### Lesson A — do not confuse identifiability gating with information creation

ME-ACI/V4/V5 showed that a Gate can prevent bad updates but cannot manufacture source information. Final inference must first demonstrate source separability in held-out physical predictive distributions.

### Lesson B — do not fix nuisance variables that alter source ranking

RMFE exposed amplitude/source-strength confounding. Current simulator benchmark freezes Q only because the benchmark contract independently fixes it. Real-world deployment must either control/calibrate Q source-independently or marginalize it before observing localization outcomes.

### Lesson C — do not use proxy observations when the true observation operator is available

Occupancy/frequency cannot substitute for ppm. Final training/inference must use native physical concentration passed through the parity-proven persistent sensor.

### Lesson D — do not destroy nuisance trajectory coherence

SCTT/V6-A showed that compressed order/frequency representations are unsafe. A transport member must remain one coherent whole trajectory across time. Member identity may be marginalized across trajectories, but must not be reselected independently at each time point.

### Lesson E — do not claim novelty from mechanisms already used

ACI, sequential assimilation, temporal splitting, spatial replication and nuisance marginalization already exist in project history. They can remain theoretical lineage or inherited components, but cannot be presented as the new central contribution.

### Lesson F — do not make the neural network the scientific claim

The H01 reference TCN already extracts source-related information (Top-5 29.69%, median normalized rank about 0.0383, positive posterior/prior gain) but fails the strict 75% Top-5 reference threshold. It proves some signal is learnable, not that TCN is the correct final estimator. The ongoing model-free audit must decide whether neural amortization is necessary at all.

### Lesson G — do not deploy House-specific neural weights

A final real-world method requiring retraining for every room is not acceptable. New environments may regenerate a source-independent geometry/wind-conditioned physics bank and calibrate sensors without source labels; final inference weights, if neural, must be shared and frozen across environments.

## 4. Reconstructed final method — fixed scientific core

The final method is not ME-ACI renamed and not a TCN classifier. Its fixed core is a physics-closed predictive source-inference problem.

### M1 — Physics-Closed Causal Generative Factorization

Target variable:

`S = persistent planar carrier region`.

Latent physical nuisance:

`U = intra-region 3-D source placement`,
`Z = coherent stochastic transport realization`,
`R_t = persistent sensor state`.

Generative chain:

`(S,U,Z,Q) -> C_1:T -> R_1:T -> M_1:T`.

The novelty here is not generic causality; it is the project-specific correction from approximate local source->HIT evidence to a source/3-D-transport/sensor-closed causal state factorization, backed by source-code and parity evidence.

### M2 — Coherent Predictive Ensemble over Physical Nuisance

For each candidate source carrier `s`, generate a finite predictive ensemble:

`P_s = { M_sim^(j)[1:T] }_{j=1..J}`

where each `j` is one frozen joint `(U_j,Z_j)` realization propagated through the same native sensor. The whole trajectory of a member is indivisible. Source evidence is based on the distribution of coherent predicted trajectories, not frequency summaries or independently selected members.

This module is where recent forward-simulator/SBI work is methodologically relevant, but the final external lineage should be assigned only after confirming that the mechanism is not already present in prior project variants.

### M3 — Sequential Source Evidence from Ordered Effects

Observed history is:

`D_1:t = { measured ppm, pose, wind, timestamps, sensing markers }_1:t`.

The desired update is:

`q_t(s) proportional q0(s) * Lambda_t(D_1:t, P_s)`.

Temporal order is intrinsic because both plume and sensor state are dynamic. The final implementation must fail an outcome-independent time-shuffle equivalence test: if ordered and shuffled histories produce equivalent source evidence, the claimed spatiotemporal mechanism is not established.

This sequential evidence idea is inherited from earlier project lineage; the new claim can only be that it now operates on the physically closed predictive distribution rather than hand-designed binary/propensity evidence.

## 5. The one unresolved implementation decision

`Lambda_t` is deliberately not frozen until the model-free H01 physical-information audit finishes.

### Branch A — physical predictive ensemble is already strongly source-separable

Prefer a **training-free sequential ensemble inference** implementation. This is scientifically cleaner, avoids House-specific training, is immediately transferable to a real room after regenerating the physics bank, and removes neural scene-memory criticism.

The estimator must preserve coherent member trajectories and use a proper predictive score or explicitly simulator-calibrated density approximation. Any bandwidth/scale must be set from simulator-only held-out nuisance data, never localization outcomes.

### Branch B — physics is clearly informative but direct finite-ensemble scoring is too weak

Use one **shared cross-environment neural amortizer** whose only task is to approximate the source predictive-evidence function. It must explicitly compare observations to candidate physics ensembles, preserve member-level temporal coherence, use no House ID, and pass strict leave-one-House-out evaluation. The neural model is an implementation of M2/M3, not a separate conceptual innovation.

### Branch C — held-out physical predictive ensemble is near null

Stop neural rescue. The limiting problem is the simulator/nuisance family, not network capacity. Do not switch architectures, increase epochs or add Gates.

## 6. What the current H01 information audit means

The current H01 TCN result already establishes only:

`there exists learnable source-related signal in the current simulation bank`.

It does not establish:

- that the physical ensemble itself is strongly identifiable;
- that the signal is not partly a simulator/trajectory shortcut;
- that a neural network is necessary;
- that the method generalizes across Houses;
- that closed-loop localization improves.

The ongoing strict model-free audit is therefore the correct next discriminating experiment. Shared/LOHO training should remain paused until it returns.

## 7. Paper-level contribution structure after reconstruction

Do not present the paper as three borrowed modules.

The strongest defensible central contribution is one integrated statement:

> Robotic gas-source localization is reformulated around a physically closed source-to-observation predictive distribution: a planar source region is linked to unresolved 3-D placement, stochastic transport, physical concentration and persistent sensor dynamics, and source evidence is inferred from coherent ordered predictive trajectories rather than proxy occupancy or independent local events.

Sub-contributions can then be:

1. physically closed causal state factorization and audited observation operator;
2. coherent nuisance-trajectory predictive inference over 2-D source / 3-D physics;
3. online ordered source-evidence update, implemented training-free if possible and otherwise by one shared cross-environment amortizer.

ACI remains historical/theoretical lineage, not a newly imported innovation. Any new external 2026 paper should be attached only to a genuinely new module after checking it against this project history.

## 8. Final falsification ladder

Before a paper claim, require in this order:

1. held-out model-free physical source separability vs permutation/null;
2. time-order shuffle falsification;
3. member/coherent-trajectory permutation/invariance tests;
4. sensor-state ablation consistent with the already proven memory mechanism;
5. if neural: strict leave-one-House-out with no held-out neural training;
6. historical truth-blind future-predictive improvement;
7. frozen 60-arm OFF/ON development matrix;
8. unseen-seed confirmatory matrix;
9. real-world deployment with source-independent map/wind/sensor preparation and no source-label retraining.

## 9. Current scientific status

The physical problem definition is now substantially closed. The project is no longer blocked by occupancy semantics, sensor dynamics, 2-D/3-D source identity, or GADEN RNG control. The remaining scientific question is narrower:

`Does the physically closed coherent predictive ensemble contain enough held-out source information to support robust sequential source inference?`

The answer to that question, not another renamed causal/temporal module, determines the next method branch.
