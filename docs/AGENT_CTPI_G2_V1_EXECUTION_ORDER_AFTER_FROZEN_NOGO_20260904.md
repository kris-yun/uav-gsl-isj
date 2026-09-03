# CTPI G2-v1 execution order after frozen three-module NO-GO

## Decision
Do not ask the user to choose between "M1 only first" and "three modules all at once". Use a two-level strategy:

1. **Architecture-level parallel design**: derive the full three-module G2 causal architecture and freeze the interfaces before implementation.
2. **Evidence-level sequential falsification**: validate/falsify in causal order **M1 -> M2 -> M3 -> joint closed loop**.

This preserves a coherent paper-level system while preventing downstream modules from being optimized on top of a broken source posterior.

## Frozen scientific interpretation of the screen failure
The current frozen CREL-TSDC-PIP system is scientifically NO-GO on the H01 3-seed downstream screen. Do not rescue it by post-hoc tuning.

Observed qualitative failure pattern to preserve as the G2 starting point:
- adding modules increased task error while the posterior became more concentrated;
- this indicates overconfident wrong-source contraction, not lack of confidence;
- M1 is upstream and must be repaired first because every M2/M3 action is conditioned on the source belief it receives;
- M2/M3 still require redesign because the final paper requires three non-redundant, load-bearing modules.

## Paper-level main innovation
Keep **causal mechanism-driven gas-source localization** as the unified paper paradigm, but do NOT make all three modules three pieces of one causal-learning method.

The three modules must have distinct mother disciplines:

### G2-M1 — source/nuisance causal inverse representation
Mother disciplines: causal representation learning + geophysical/statistical inverse problems.
Goal: infer source state while marginalizing/separating source strength, transport variability and sensor-memory nuisance.
Output interface must be a calibrated source belief `p_t(S)` plus any explicit nuisance uncertainty needed by downstream modules.

### G2-M2 — bank-free transport-observation world model
Mother disciplines: nonequilibrium statistical physics + turbulence/Lagrangian transport + rare-event/committor theory + operator learning.
Goal: replace site-specific predictive-bank lookup with a transferable operator of the form
`(geometry/map, recent/online wind, source hypothesis, candidate action, sensor state) -> predictive future observation law`.
New-environment deployment must not require regeneration of a source×transport×action GADEN bank or environment-specific retraining.

### G2-M3 — active experimental design
Mother disciplines: Bayesian experimental design + information geometry + autonomous science.
Goal: choose physical intervention/action that maximally separates remaining source hypotheses using M1 belief and M2 predictive law, without arbitrary outcome-tuned planner weights.

## Mandatory execution sequence

### Phase 0 — freeze the old NO-GO
Archive the exact H01 3-seed screen metrics, gates, code/runtime hashes, and the mechanism diagnosis. Mark the frozen CREL-TSDC-PIP scientific branch REJECTED for downstream performance. Do not use later G2 work to rewrite that result.

### Phase 1 — derive the complete G2-v1 system before coding
Produce equations, causal timing and interfaces for all three modules now. Specifically freeze:
- M1 inputs/outputs and nuisance variables;
- M2 conditioning variables and future-observation object;
- M3 action objective and feasibility contract;
- information passed M1->M2->M3;
- what is trained once across environments vs computed online;
- truth/future-leakage prohibitions;
- bank-free new-environment contract;
- ablation design that isolates M1, M2 and M3.

Do not implement three unrelated modules and connect them later.

### Phase 2 — attack M1 first with cheapest destructive tests
M1 is the first implementation target because the current system shows overconfident wrong-source contraction.

Use DEV_SPENT/historical data first. Required M1 falsification should test at least:
- source-strength perturbation while source location is fixed;
- transport-member/regime perturbation while source location is fixed;
- sensor-dynamics perturbation;
- House holdout;
- source-label permutation/destruction control;
- calibration AND true-source rank/mass;
- overconfidence diagnostics: entropy or effective support must not collapse while source error/rank worsens.

A candidate M1 is not accepted merely because NLL improves. It must improve source evidence under nuisance intervention and avoid the exact failure mode `more concentrated -> more wrong`.

If M1-v1 fails, freeze it as REJECTED and derive M1-v2 from the measured failure mechanism. Do not tune against confirmatory worlds.

### Phase 3 — only after M1 qualifies, validate M2 bank-free
M2 must be tested using held-out environments without site-specific predictive banks.

Minimum qualification:
- source-conditioned future-observation prediction is better than a simple transferable baseline;
- source contrast is preserved, not washed out by global calibration;
- rare-event/encounter tails are represented correctly;
- no environment-specific GADEN bank is generated at deployment;
- hold one House/environment out from training/development and run M2 using only permitted online geometry/wind/gas/state inputs.

The old bank may be used as DEV_SPENT ground-truth data for training/evaluation research, but the deployed M2 interface must not query the held-out environment's site-specific bank.

### Phase 4 — only after M1 and M2 qualify, validate M3
M3 must be tested on action quality, not its internal score.

Required controls:
- action/route shuffle;
- posterior permutation;
- M2 prediction destruction;
- compare selected action against native planner on expected and realized source-resolution gain;
- prove that better internal information score actually changes downstream localization.

No arbitrary `J - lambda * distance` tuning after task outcomes.

### Phase 5 — pre-register joint ablation and run closed loop
Before fresh task outcomes, freeze an ablation that isolates all three increments. Preserve an interpretable structure such as:
- A0 = classic/native PMFS;
- G100 = qualified G2-M1 + native planner;
- G110 = G2-M1 + transferable/raw M2 baseline + same G2-M3;
- G111 = G2-M1 + qualified bank-free G2-M2 + same G2-M3.

Then isolate:
- M1 = G100 - A0;
- M3 = G110 - G100;
- M2 = G111 - G110;
- Full = G111 - A0.

If the exact mathematics needs a different factorial, freeze an equivalent design before task outcomes.

## Success target
Final acceptance requires all of the following, not only one:
- each module has a positive downstream increment on the preregistered primary task metric;
- full G2 improves over classic/native PMFS by at least 10% relative on the preregistered continuous primary metric (prefer 240 s localization error AUC), or +10 percentage points if a success-rate metric is preregistered as primary;
- no systematic catastrophic House reversal;
- final confirmation uses fresh worlds/seeds not used for model selection;
- the final claimed deployment result is **bank-free on a held-out/unseen environment**.

The 10% target is an acceptance target, not permission to tune repeatedly on confirmation outcomes. Failed versions become REJECTED and a new version is derived from failure analysis.

## Autonomy
Continue autonomously through theory, literature review, offline falsification, code, tests and fresh closed-loop evaluation. Do not return to the user for ordinary implementation choices. Return only for a genuine external-resource blocker, or when a scientifically meaningful milestone is reached (qualified architecture, definitive NO-GO, or final PASS).
