# Repository Organization Map

Date: 2026-09-14

The repository contains many historical experiment branches. They are valuable evidence, but they also create a serious risk: a new agent may resume an old hypothesis that has already been rejected.

This document does **not** delete or rewrite history. It classifies branches by role.

---

# 1. Research-control branch — authoritative starting point

## `project/research-master-20260914`

Purpose:

- scientific question;
- current core idea;
- evidence ledger;
- big-science theory map;
- rejected-route registry;
- next execution contract;
- machine-readable current research state.

Every new Codex/agent session should read this branch first.

Do not run experiments directly from this branch unless a new experiment branch is explicitly created from its referenced evidence head.

---

# 2. Current evidence branch

## `codex/dual-uav-two-point-premise-20260913`

Current role:

- authoritative same-frame dual-UAV two-point experiment evidence;
- native occupancy parity;
- whole-map 2 m formation feasibility;
- source-blind 150 s formation route;
- synchronized raw/FOPDT traces;
- signed-increment NO-GO evidence.

Current scientific conclusion:

```text
STRUCTURAL_COMPLEMENTARITY_ONLY_NO_SOURCE_IDENTITY
```

Do not keep tuning the signed two-point module on this branch.

---

# 3. Recent diagnostic / audit branches — read-only scientific evidence

## `codex/m1-causal-review-20260912`

Role:

- M1/counterfactual physical pipeline review;
- code/theory/evidence audit;
- negative evidence preservation.

Do not treat it as proof that M1 is closed-loop validated.

## `codex/m1r-mechanism-audit-v41-20260912`

Role:

- historical M1R implementation/mechanism audit;
- distinguish what old positive results actually implemented.

Use for historical truth, not as an active method branch unless research-master explicitly reopens it.

## `codex/m1r-causal-repair-20260912`

Role:

- later M1R repair exploration.

Status: historical / non-authoritative for current main innovation.

## `codex/single-channel-ccde-20260913`

Role:

- single-channel CCDE/SCSP/CFIR and related identifiability diagnostics.

Current project use:

- evidence that further transformations of the same single-UAV concentration stream do not stably establish full source identity.

Do not resume as default main line.

---

# 4. Causal redesign / counterfactual branches — historical evidence, main line frozen

## `g3-cstar-causal-redesign-20260906`
## `g3-cstar-exec-closedloop-20260906`
## `g3-cstar-revise-before-exec-20260906`

Role:

- source-intervention / exact counterfactual work;
- forward-provider audits;
- wind-history binding;
- conditional observability development.

Retain because the exact microbank produced useful positive premise evidence.

Do not interpret these branches as a deployable causal source-localization solution.

---

# 5. CTPI / G2 / planning branches — historical, not current priority

Examples:

- `g2-bankfree-closedloop-20260904`
- `ctpi-agent-resume-20260903`
- `ctpi-runtime-results-20260904`
- `codex/ctpi-full-law-closedloop-20260902`
- `research/ctpi-*`

Role:

- previous M2/M3/planning experiments and theory designs.

Current status:

- useful provenance;
- do not restart planning/M3 while source observability remains unresolved.

---

# 6. CTT / temporal-causal branches — historical NO-GO context

Examples:

- `codex/ctt-v13-m1-go-checkpoint-20260826`
- `agent/ctt-final-hazard-closedloop-20260830`
- `research/ctt-*`
- `cg-pc-ctt-*`
- `v13-ctt-independent-review`

Role:

- temporal / first-passage / causal transport hypotheses;
- source observability / completeness investigations.

Current status:

- historically important for understanding why time structure alone did not yield stable source identity;
- not active main line.

---

# 7. ME-ACI branches — historical mechanism library, not validated current solution

## `meaci-v11-paper-three-contributions`
## `meaci-v11-reversible-cumulative`

Role:

- STRI / reversible-assimilation-style mechanisms;
- earlier positive small screens;
- later multiseed qualification context.

Current status:

- later frozen qualification is NO-GO;
- use only as failure-mechanism inspiration if a new audit specifically re-establishes the matching failure.

---

# 8. Older candidate branches — archive / provenance

Examples:

- `nacc-v14-semi-modular-causal-20260826`
- `prca-v14-proximal-causal-assimilation-20260826`
- `rcec-v13-frozen-candidate-20260826`
- `codex/rcec-v13-materialized-20260826`
- `research/pf-*`

Do not revive based on branch names. Any reuse requires an explicit research-master decision and a stated failure mechanism.

---

# 9. Branch-use rule for future agents

Before an agent changes code, it must answer:

```text
1. What scientific failure is being addressed?
2. Which research-master status authorizes this route?
3. Which branch contains the authoritative input evidence?
4. What exact pre-registered gate can falsify the idea?
5. Which old branches are forbidden to revive?
```

If any answer is missing, do not start implementation.

---

# 10. Recommended future branch pattern

Use:

```text
exp/<scientific-object>-<date>
```

for isolated experiments.

Each experiment branch should contain:

```text
docs/START_HERE.md
experiments/<name>/PRECOMMIT.json
experiments/<name>/FINAL_GATE.json
experiments/<name>/SHA256SUMS
```

When complete:

- preserve both PASS and NO-GO evidence;
- update `project/research-master-20260914` rather than silently changing the project direction inside the experiment branch.

---

# 11. Current next branch recommendation

After approval of `docs/NEXT_STAGE_EXECUTION_CONTRACT_20260914.md`, create a fresh branch such as:

```text
exp/active-source-observability-20260914
```

from the evidence-compatible current state.

Do not continue the failed signed-difference method inside the old dual-UAV branch.
