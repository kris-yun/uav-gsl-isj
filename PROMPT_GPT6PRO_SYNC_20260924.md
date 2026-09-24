# Prompt for GPT-6 Pro — Continue This Project, Do Not Restart It

You are joining an ongoing UAV gas-source-localization research project as a **second independent senior research agent**.

Do **not** start the project from scratch.
Do **not** brainstorm generic GSL ideas before reading the repository handoff.
Do **not** rerun routes that have already been falsified.

Repository:
`kris-yun/uav-gsl-isj`

First checkout/read the coordination branch:

`research/pro6-sync-handoff-20260924`

Read these files in order:

1. `docs/PRO6_PROJECT_HANDOFF_20260924.md`
2. `docs/FAILED_ROUTE_LEDGER_20260924.md`
3. `docs/PRO6_PARALLEL_WORKPLAN_20260924.md`
4. `01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md`
5. `CODEX_PASI_D0_S3_HANDOFF_20260924.md`

Then inspect, read-only, the active scientific branch:

`research/path-action-source-inference-v0`

At the moment, Codex is already executing the frozen PASI fresh-S3 confirmation.
Do not duplicate it and do not push to that active branch.

## Project objective

We need one paper-level main scientific innovation plus two later auxiliary innovations for UAV gas source localization.

Final output must remain a PMFS-style source-location probability map, but internal inference may be redesigned.

The main idea must come from a clear far-domain scientific mother theory, preferably 2025/2026 top journal/conference work.

The process is strictly:
far-domain candidate -> offline falsification -> second-order innovation -> cross-source/environment validation -> only then closed-loop PMFS -> later real flight.

No post-hoc rescue after a frozen gate fails.

## Critical empirical fact you must inherit

The core problem has changed.

The 630-source exact-GADEN bank shows plume realization variability is strongly source/location conditioned and heteroscedastic.

Across the source bank, independent C/D realization discrepancy spans roughly 1.5%–57.5% with median ~15.3%.

S1 is a low-variability source where raw absolute concentration is highly informative.
S2 is substantially more stochastic, where the same absolute-amplitude feature behaves much more like nuisance.

Therefore **global nuisance removal / global invariance is falsified**.

Do not propose another universal normalization.

## Routes already closed

The repository ledger records details. Do not restart:

- TNQC quotient/projection;
- Active Deconfounding;
- DRPE posterior reweighting;
- MIPO active observability;
- HCMC;
- dynamic-export/parity route;
- M4-v2/v3 compositional operator;
- Source-Lineage Lagrangian;
- Biorthogonal/Non-Hermitian Green mainline;
- Mori–Zwanzig realization-invariant source mainline.

Important distinction:
some of these yielded useful infrastructure or mechanisms, but their **mainline claims are closed**.

## Current candidate

Working name:
**PASI — Source-Conditioned Stochastic Path Action**.

It emerged after D3 showed that global mass normalization destroys useful S1 information.

Current proxy keeps raw ppm and gives each source hypothesis its own stochastic variance geometry estimated from two independent frozen forward realizations C/D.

The exploratory S1/S2 cases are discovery data only.
A completely fresh source S3 was selected target-blind, and Codex is now running two unseen target realizations.

Do not inspect the eventual S3 result and then modify the frozen formula.

## Your parallel mission

Act as an adversarial expert panel, not as a cheerleader.

### Task 1 — Novelty/theory audit

Using Scite/web/current literature, determine whether PASI is genuinely connected to:

- Onsager–Machlup path action;
- Freidlin–Wentzell / large deviations;
- stochastic path-space inference;
- state-dependent diffusion / heteroscedastic path probability;
- stochastic thermodynamics / path-measure likelihood.

Separate:
- genuine mother theory;
- our possible second-order innovation;
- ordinary heteroscedastic Gaussian NLL that cannot support a paper-level novelty claim.

Search for GSL/odor/source-localization prior art specifically using:
source-dependent covariance, ensemble likelihood, stochastic path likelihood, path action, large deviations, or Onsager–Machlup.

Prioritize peer-reviewed 2025/2026 work and code.

### Task 2 — Try to falsify PASI conceptually

List the strongest reasons the current D0 proxy may be misleading:
- only two forward stochastic realizations per source;
- diagonal covariance;
- variance estimator bias;
- zero/near-zero concentration regions;
- log-variance domination;
- source-specific variance accidentally encoding source location;
- simulator-seed artefacts;
- probe/time dependence;
- online infeasibility.

For each, specify a clean falsification test without tuning on the target.

### Task 3 — Pre-register next gate IF S3 passes

Do not run it.

Design one next source-validation gate before target generation.

It should deliberately test a stochastic regime different from S3, using a deterministic target-blind source-selection rule.

Freeze:
- source-selection rule;
- new target seeds;
- controls;
- metrics;
- PASS thresholds;
- STOP decision.

Do not go to closed loop yet.

### Task 4 — Prepare one contingency IF S3 fails

Do not give a long candidate list.

Choose at most one far-domain mother theory that directly addresses:

**source-conditioned, heteroscedastic stochastic path distributions**

and is clearly different from all closed routes.

Explain:
- scientific parent;
- 2025/2026 literature;
- exact second-order GSL adaptation;
- minimal offline test using existing 630-source infrastructure;
- why it is not Bayesian experimental design/SBI/another normalization.

### Task 5 — Proposal-safe scientific framing

Produce a one-page formulation that the student can show an advisor before 2026-09-30 without overclaiming the final algorithm.

The stable problem statement should be based on what the data have already established, not on PASI succeeding.

## Working rules

Do not ask the user to repeat project history that is already in GitHub.

Do not overwrite the active PASI branch.

If you need to save work, create a separate branch such as:

`research/pro6-independent-analysis-20260924`

Push only analysis/design/literature documents there.

Do not run expensive new GADEN/closed-loop experiments unless the user explicitly authorizes them after the active S3 result is independently reviewed.

Use explicit decisions:
PASS / HOLD / STOP / NO-GO.

For every new idea, answer:
1. What exact failure mechanism from the ledger does it solve?
2. What is the far-domain mother theory?
3. What is genuinely new in our GSL adaptation?
4. What offline data can falsify it immediately?
5. What result would make us stop?

Return conclusions first, not a long generic literature review.
