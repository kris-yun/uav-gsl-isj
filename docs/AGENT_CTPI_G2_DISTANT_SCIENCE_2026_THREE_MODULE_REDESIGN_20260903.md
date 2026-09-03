# Agent directive — CTPI G2 distant-science three-module redesign (2026-09-03)

## Mission
Run a **parallel next-generation research track** while the currently frozen CREL–TSDC–PIP true-closed-loop validation continues unchanged.

The purpose is not to tune the current frozen method after seeing outcomes. The purpose is to use the **latest 2026 top-tier ideas from distant natural-science fields** to diagnose our historical failure mechanisms and derive a genuinely stronger second-generation three-module architecture for robotic/UAV gas-source localization.

Target: the final full three-module system should improve over classic/native PMFS by **at least 10% relative improvement on the preregistered primary continuous task metric** (prefer error-time AUC), or **at least +10 percentage points if the primary metric is a percentage success rate**, while preserving cross-House robustness. This is an aspirational preregistered target, not permission to cherry-pick metrics, seeds, Houses, weights, or post-hoc variants.

## Absolute separation from current frozen closed loop
Do not modify or contaminate the current frozen branch's scientific runtime while it is producing confirmatory outcomes. In particular do not alter CREL, frozen TSDC beta/features, PIP objective, action domain, tie-break, 3/3/1 cadence, 240 s horizon, predictive banks, current scientific Gates, or current smoke/formal outcomes.

Create a separate exploratory branch/worktree for G2. Existing closed-loop outcomes, when they become available, may be used as **failure evidence**, but never as a target for post-hoc tuning of the frozen confirmatory experiment.

## Literature scope
Build a literature corpus of at least **80 serious papers**, with 2026 as the dominant year (target >=60% from 2026; use 2025 only when needed to trace a still-current paradigm). Prioritize original research in top journals/conferences and major natural-science domains, not incremental gas-source-localization papers.

Required distant fields:
1. statistical physics / nonequilibrium physics / rare-event theory;
2. molecular dynamics / chemical physics / transition-path theory;
3. climate / Earth-system dynamics / extreme-event prediction;
4. turbulence / fluid mechanics / Lagrangian transport;
5. dynamical systems / operator learning / scientific machine learning;
6. experimental design / autonomous science / uncertainty-calibrated active learning;
7. geophysics / inverse problems;
8. optionally astronomy / quantum science when the transferable mechanism is genuinely useful.

Target venues include Nature, Science, Nature Physics, Nature Machine Intelligence, Nature Communications, PNAS, Physical Review Letters, Journal of Fluid Mechanics, major AGU journals, ICLR/NeurIPS/ICML scientific-ML work, and similarly selective venues. Do not use venue prestige alone: extract a mother principle and show why it transfers.

Gas-source-localization literature is for **novelty collision checking**, not as the mother source of the new module.

## 2026 seed directions — investigate, do not blindly copy
Use these only as starting points for the search:

- **Rare-event committor / iterative path ensembles.** PRL 2026 work on iterative path sampling and committor reconstruction suggests that the useful state is not a generic temporal feature but a probability of committing to a future event under the actual dynamics.
- **Extreme-event-aware learning.** Nature Communications 2026 work on extreme-event-aware learning addresses the failure of ordinary objectives to represent rare but high-consequence regimes; inspect whether plume encounter/non-encounter tails should be represented with a tail-aware physical objective rather than average likelihood.
- **Operator learning in function spaces.** Nature Machine Intelligence 2026 work on discretization-agnostic operator learning and free-boundary operators suggests learning a transport operator rather than a direct source classifier, especially for bank-free generalization.
- **Coupled climate modes.** Nature Machine Intelligence 2026 work on learning coupled global climate modes suggests separating recurrent latent dynamical modes and their couplings instead of compressing all transport variation into one count/statistic.
- **Uncertainty-calibrated experimental optimization.** Nature Machine Intelligence 2026 work on uncertainty-calibrated optimizers emphasizes that representation geometry and calibrated uncertainty can determine next-experiment quality, not predictive fit alone. Translate this into action selection only if it yields a principled information geometry, not a new arbitrary planner weight.
- **Meta-design / autonomous science.** 2026 work on quantum-experiment meta-design and autonomous scientific agents is relevant to extracting reusable design principles from action-outcome loops rather than merely optimizing a black-box score.

For each candidate mother idea, identify the original scientific object, equations, assumptions, and what would be preserved vs changed in gas-source localization.

## Historical failure mechanisms that must be criticized explicitly
Do not propose a new module before explaining which failure it repairs.

At minimum analyze:

1. **RMFE fixed-amplitude failure**: true-near-source candidates required very different amplitude scaling; source identity was confounded with nuisance amplitude. Explain why a physically correct representation should separate source state from transport/intensity nuisance rather than lock A=1.

2. **Complete-count-law failure**: eight predictive members were asked to support N+1 exact count categories; sparse categorical floors and a categorical distance ignored how far counts differ. Explain why finite-ensemble prediction needs an appropriate coarse observable / probabilistic geometry.

3. **Global P(Y|K) compression failure**: pooled calibration improved mixture NLL but washed out source-conditioned mutual information and showed CAL→CONFIRM drift. Explain why calibration can destroy discriminative structure if it marginalizes over the latent cause we later need for planning.

4. **Old persistent-sensor source-posterior NO-GO**: sensor memory did not work as a second source-inference module. Preserve the lesson that memory belongs in predictive closure when coarse-graining creates non-Markovian observations; do not reuse it as duplicated source evidence.

5. **Temporal / first-passage surrogate NO-GO**: a physical first-passage signal existed but the temporal surrogate was nuisance-unstable as source evidence. Do not revive generic temporal classification under a new name.

6. **Planner-disconnection failure**: earlier geometry/predictive modules could look good internally but not affect robot localization because the planner did not consume them. Every proposed module must have a precise place in the closed-loop causal chain.

7. **Current timestamp/pose association problems** are runtime observation-alignment bugs, not scientific innovation. Do not present engineering repairs as new modules.

## Design requirement: three modules, three distinct scientific responsibilities
The new system must remain a genuinely causal three-part architecture. Names and mathematics may change, but responsibilities must remain non-redundant:

- **Module 1 — inverse source evidence / latent source representation.** It must infer source state from executed observations while separating source identity from transport/sensor nuisance.
- **Module 2 — future observation dynamics.** It must predict a source-conditioned future observation law under candidate actions, carrying any required non-Markovian transport/sensor closure without re-assimilating the current observation into the source posterior a second time.
- **Module 3 — active experimental design / planning.** It must use M1 posterior + M2 predictive law to choose actions that maximally resolve source uncertainty under physical feasibility. No decorative module and no arbitrary planner-weight tuning.

Prefer mother principles that make these three responsibilities mathematically compatible rather than three unrelated tricks.

## Load-bearing requirement
A module is not accepted merely because its internal NLL/calibration/rank metric improves.

Freeze an ablation before task outcomes. At minimum preserve an interpretable structure analogous to:

- A0 = classic/native PMFS;
- F00 = M1 + native planner;
- F10 = M1 + a baseline/raw predictive law + the same M3 planner;
- F11 = M1 + qualified M2 + the same M3 planner.

Then:
- M1 downstream contribution = F00 vs A0;
- M3 contribution = F10 vs F00;
- M2 downstream contribution = F11 vs F10;
- full-system contribution = F11 vs A0.

If G2 mathematics requires another factorial, pre-register an equivalent design that isolates all three contributions. Each module must have an independently interpretable downstream increment. Full-system gain cannot be credited to one strong module carrying two decorative ones.

## Performance target and anti-gaming rules
Before confirmatory runs, select the primary metric and freeze it. Preferred primary metric: **240 s localization error AUC**, because it measures how quickly the robot becomes useful over the whole trajectory. Also report final error, time-to-2m, success rate, route length, and failure rate.

Success target:
- full G2 vs classic PMFS: >=10% relative improvement in the preregistered primary continuous metric; or >=10 percentage points for a percentage success metric;
- no House with systematic catastrophic reversal;
- all three module increments must be directionally beneficial and scientifically load-bearing;
- cross-House confirmation must use fresh seeds/worlds not used for model selection.

Do **not** tune until the target is met. Do not change metric, seed set, House subset, action candidates, temperature, planner weights, module router, feature set, or Gate after seeing confirmatory outcomes. If a candidate fails, classify the failure and return to theory on a new exploratory version.

## Work phases

### Phase A — literature library
Search and archive >=80 relevant papers. Produce a table with:
- citation/year/venue/field;
- mother scientific object or theory;
- central equation/state variable;
- what problem it solves in its home field;
- transferable mechanism to GSL;
- which historical failure it attacks;
- novelty collision risk with existing GSL;
- implementation/data requirements;
- falsification test.

Do not give me a superficial score list. Read enough of each promising paper to understand the mechanism.

### Phase B — failure-to-principle map
Write a technical memo mapping every historical NO-GO to the violated scientific principle. Example form:
`observed failure -> hidden assumption -> why assumption is invalid -> distant-field principle that repairs it -> new falsifiable prediction`.

This memo must exist before code.

### Phase C — derive at least three complete three-module candidate architectures
For each candidate:
- derive the equations;
- define variables and causal timing;
- define what is learned vs analytic;
- define offline assets needed;
- define runtime information flow;
- prove there is no truth/future leakage;
- state why each module is non-redundant;
- state the exact ablation that demonstrates each contribution.

At least one candidate should seriously examine a **rare-event / committor + coarse-grained memory + information-geometric experimental-design** family; at least one should examine a **transport-operator / latent dynamical-mode** family. Do not force either if falsification rejects it.

### Phase D — cheapest falsification first
Use existing frozen banks, DEV_SPENT worlds, historical closed-loop traces, and offline assets first. Do not request new GADEN campaigns until a candidate survives inexpensive falsification.

Required destructive controls should target the claimed physics: source-label permutation, transport-member destruction, sensor-state destruction, route/action shuffle, nuisance-amplitude perturbation, House holdout, and any theory-specific invariance test.

Reject any candidate that only improves mixture likelihood while reducing source contrast, only improves calibration without changing action quality, or wins by using truth/future information.

### Phase E — select one G2 architecture
Only after falsification choose one. Freeze equations, features, action contract, tie-break, metrics, seeds and Gates **before** true closed-loop confirmatory evaluation.

Do not merge it into the current frozen CREL–TSDC–PIP confirmatory branch. Use a separate G2 branch and evidence namespace.

## Required deliverables to GitHub
Create a dedicated folder such as `research_notes/ctpi_g2_2026/` containing:
1. `LITERATURE_LIBRARY_2026.md` + machine-readable CSV/JSON;
2. `HISTORICAL_FAILURE_MECHANISM_AUDIT.md`;
3. `DISTANT_FIELD_MOTHER_IDEAS.md`;
4. `THREE_G2_ARCHITECTURES.md`;
5. mathematical derivations for each candidate;
6. offline falsification code + tests;
7. evidence outputs;
8. final `G2_GO_NO_GO.json` with exact reasons;
9. a concise handoff explaining what is confirmed, rejected, still exploratory, and what the next agent should do.

## Reporting style
Report mechanisms, equations and falsification evidence, not hype. English technical terms should be followed by a short Chinese explanation when useful. Clearly label CONFIRMED / CURRENTLY TESTING / CANDIDATE / REJECTED. Do not call a literature-inspired idea our innovation until novelty collision checking is complete and our own falsification shows it solves a real failure mechanism.
