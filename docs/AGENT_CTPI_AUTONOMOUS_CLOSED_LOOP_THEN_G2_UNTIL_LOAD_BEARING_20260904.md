# Autonomous directive — finish frozen CTPI closed loop first, then iterate G2 until all three modules are load-bearing

## Mission
Proceed autonomously from the current VM state. Do not return for routine engineering approval. The work has two strictly separated tracks:

1. **Track A — finish the currently frozen CREL–TSDC–PIP true closed loop first.** This is the immediate priority because M1 and M2 already have offline/fresh evidence and the full causal chain has not yet received a clean, frozen true-closed-loop test.
2. **Track B — if Track A is scientifically insufficient, continue autonomously into G2 redesign.** G2 keeps **causal mechanism / causal representation** as the paper-level main innovation, but the three modules must be founded on different distant scientific mother theories and must ultimately remove the site-specific predictive-bank requirement.

The user does not want to manually supervise each engineering or research iteration. You may continue autonomously through environment repair, runtime correctness repair, exploratory theory, offline falsification, ablation, and fresh closed-loop testing, subject to the scientific anti-gaming rules below.

## Current confirmed scientific state
Treat these as historical evidence, not assumptions to re-prove before every run:

- **M1 CREL (Causal Route-Encounter Law): downstream PASS** on prior offline/frozen evaluation. It improved localization error and source rank and is the strongest existing evidence that causal source evidence is useful.
- **M2 TSDC (Transport–Sensor Detection Committor): fresh-confirm PASS** as a future detection committor. It improved NLL/Brier on fresh worlds. This proves predictive closure is useful internally, but not yet that it improves robot localization downstream.
- **M3 PIP (Predictive Information Planning): frozen for true closed-loop evaluation.** Its downstream value still must be demonstrated.
- Frozen scientific ablation remains:
  - `A0 = native PMFS`
  - `F00 = CREL M1 + native planner`
  - `F10 = CREL M1 + raw finite-8 predictive probability + PIP`
  - `F11 = CREL M1 + TSDC M2 + same PIP`
  - M1 contribution = F00 − A0
  - M3 contribution = F10 − F00
  - M2 downstream contribution = F11 − F10
  - Full contribution = F11 − A0
- Frozen runtime intent remains 3/3/1 source-update cadence, 240 s horizon, 0.4 m/s, dt=0.2 s, dwell=80 samples, bank time samples=1500 unless a later G2 branch explicitly replaces the bank architecture.

## Current runtime state and completed repairs
The H01 raw observation runtime was reconstructed because its old `/dev/shm/house1_*` runtime had been lost. Do not treat this as scientific innovation.

Completed/validated engineering repairs include:

- reconstructed `/dev/shm/house1_raw_query` from the historical H01 oracle source and validated it on real H01 GADEN snapshots;
- reconstructed the `raw_house1_snapshot` consumer in `vgr_sim_node` using the historical stdin/stdout query protocol;
- repaired the broken `vgr_bridge` install;
- repaired the incomplete result-contract glue required by the benchmark runner;
- normalized the H01 bank cell manifest line endings and kept integrity hashes consistent;
- corrected CPIR observation time to use the gas message timestamp instead of callback wall time;
- implemented causal timestamp–pose association using a pose history: for each gas sample at `t_gas`, use the latest historical pose with `t_pose <= t_gas`; do not use future pose and do not use callback-time current position.

The timestamp–pose association repair is considered **runtime correctness**, not a new module. Keep the causality audit (`pose_stamp_used <= gas_stamp`).

## Immediate blocker and authorized resolution
The remaining observed blocker is **navigation/free-cell resolution mismatch**:

- CPIR predictive lookup uses the reduced ~0.3 m grid / free-cell manifest;
- the simulator navigation path has been interpolating on the finer ~0.1 m occupancy representation;
- therefore a straight-line transit can pass through positions that are free on the fine map but correspond to a non-queryable/occupied coarse CPIR lookup cell;
- `CPIR_POSE_NOT_FREE_LOOKUP_CELL` is therefore correctly protecting the posterior from invalid lookup, and must not be disabled.

### Preferred fix order
Use the following order autonomously:

1. **Navigation-layer consistency fix (preferred).** Make the executed transit path respect the same coarse free-space topology required by the CPIR lookup contract. Use obstacle/free-cell-aware path generation (e.g. grid path/BFS/A* over the appropriate free-cell topology) rather than direct Euclidean interpolation when the direct segment crosses non-queryable CPIR cells.
2. Apply the same navigation-runtime correction to all comparable arms so A0/F00/F10/F11 remain fair. The fix must not depend on the active scientific arm or source truth.
3. Preserve moving observations; do not silently discard navigation-period samples merely to avoid the cell Gate unless a later theory branch explicitly demonstrates that only completed-dwell observations are part of the frozen M1 observation contract.
4. Do not project an invalid pose to an arbitrary nearest free CPIR cell, because that changes which bank cell generated the observation evidence.
5. Do not regenerate/redefine the frozen bank for Track A.
6. Do not relax `CPIR_POSE_NOT_FREE_LOOKUP_CELL`.

If the preferred navigation consistency repair is technically impossible without changing Track-A scientific semantics, stop only long enough to write a precise blocker report, then choose the least semantic runtime repair and document why it preserves the observation model. Do not tune scientific formulas to get past an engineering Gate.

## Track A execution order — finish the existing three modules before redesign
After runtime correctness is frozen:

### A1. Freeze and commit the runtime repair
Before producing performance evidence:
- commit all environment/runtime-correctness changes;
- record changed files and binary SHA-256;
- prove M1/TSDC/PIP scientific formulas and frozen parameters are unchanged;
- create a clean runtime identity and new run roots;
- do not reuse debug/probe results as performance evidence.

### A2. Single-arm path probe
Run F00 first only to prove the observation→posterior→planner/navigation→new observation loop can execute repeatedly without:
- duplicate/reversed sample index;
- raw sample gap;
- timestamp/pose causality violation;
- non-free lookup cell;
- result-contract failure;
- action failure caused by infrastructure.

This F00 probe is not a scientific win claim.

### A3. H01 seed0 frozen smoke
Run the frozen `F00/F10/F11` H01 seed0 true closed-loop smoke from fresh run roots. Require:
- `CTPI_FASTTRACK_CASE_TERMINAL=PASS` for each case;
- `CTPI_M3_ACTION_SANITY=PASS` for F10/F11;
- `TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS`;
- `CTPI_H01_SEED0_SMOKE=PASS`.

The causal chain must actually show:
`posterior_t -> candidate action scores -> selected action -> executed navigation -> fresh gas/wind -> posterior_(t+1) -> next action`.

### A4. H01 12-run screen
Only after smoke PASS:
`H01 seeds0–2 × A0/F00/F10/F11 = 12 runs`.

Freeze the screen analysis before inspecting all outcomes. Report at least error AUC, final error, time-to-2m, success, route length, failure status, and module increments.

### A5. Cross-House fresh confirmation
Only if the H01 screen supports the frozen method:
`H01/H02/H03 × fresh seeds3–5 × A0/F00/F10/F11 = 36 runs`.

Use the previously defined exact paired sign-flip/randomization logic or an equivalently pre-registered paired test. Do not change the metric or seed subset after outcome inspection.

## Track A scientific interpretation
Do not force a PASS.

- If F00 > A0: M1 remains downstream load-bearing.
- If F10 > F00: M3 is downstream load-bearing.
- If F11 > F10: M2 is downstream load-bearing.
- If the full F11 does not materially beat A0, or one module is consistently non-load-bearing, classify that exact mechanism as the next G2 failure target.

Current CREL/TSDC/PIP has prior offline evidence, so test it cleanly first. But if fresh true closed-loop evidence rejects any module, **do not outcome-tune the frozen Track A**. Freeze the failure and move to Track B.

---

# Track B — G2 autonomous redesign after Track A failure/sufficiency audit

## Paper-level main innovation remains causal, but modules must not all be “causal-learning submodules”
The paper-level paradigm should remain a **causal mechanism / causal representation view of robotic gas-source localization**:

`source -> transport -> plume encounter -> sensor dynamics -> observation -> belief -> intervention/action -> new observation`.

However, do **not** make three modules that are merely one causal-learning method split into three names. The modules must have **different scientific responsibilities and different mother fields**, connected through a common causal state/intervention interface.

Preferred high-level structure:

### G2-M1 — source/nuisance separation
**Mother fields:** causal representation learning + geophysical/statistical inverse problems.

Responsibility: infer source state while separating source identity from nuisance transport/intensity/sensor factors.

This module must directly attack the RMFE fixed-amplitude failure and source–nuisance confounding.

### G2-M2 — bank-free future transport/observation dynamics
**Mother fields:** nonequilibrium statistical physics + turbulence/Lagrangian transport + rare-event/committor theory + operator learning/dynamical systems.

Responsibility: predict the future observation distribution under candidate interventions/actions without a site-specific precomputed predictive bank.

Target interface:
`(geometry/map, online wind/history, source hypothesis, candidate action, sensor state) -> distribution of future observation`.

This module must attack count-law compression, global `P(Y|K)` information washout, and the site-specific bank limitation.

### G2-M3 — active experimental design
**Mother fields:** Bayesian experimental design + information geometry + autonomous science.

Responsibility: choose the action/intervention that best resolves remaining source uncertainty using M1 posterior and M2 predictive law. No arbitrary planner-weight tuning.

This module must attack the historical planner-disconnection failure.

The three modules must be distinct enough that an ablation shows each adds downstream task value, but compatible enough to form one causal closed loop.

## Bank-free / unfamiliar-environment requirement is mandatory for G2
The final G2 architecture must support **zero-shot site deployment** in an unfamiliar environment.

Allowed at deployment:
- map/geometry or online SLAM;
- robot pose and trajectory;
- real-time/online wind;
- gas observations;
- sensor state/history;
- a model trained once on development environments.

Forbidden at deployment on the held-out site:
- rerunning GADEN for candidate sources before the robot can fly;
- generating a site-specific `source × transport member × action` predictive bank;
- retraining/fine-tuning the scientific model on that held-out site before evaluation;
- using source truth or future measurements.

A pre-trained general transport/world model is allowed. A site-specific lookup bank is not.

G2 confirmation must therefore include **bank-free held-out-environment evaluation** (e.g. leave-one-House-out or equivalent fresh environment holdout). A bank-assisted gain alone does not satisfy the final G2 objective.

## Distant-science literature and failure-driven redesign
Use the existing directive `docs/AGENT_CTPI_G2_DISTANT_SCIENCE_2026_THREE_MODULE_REDESIGN_20260903.md` and the causal/bank-free supplement as mandatory background.

Build/read a serious literature library, dominated by 2026 top-tier work from distant natural-science fields. Do not just collect titles. For each useful mother idea, extract:
- the scientific object/state variable;
- central equation or operator;
- assumptions;
- why it works in the home field;
- which CTPI/PMFS failure mechanism it repairs;
- what is preserved vs adapted in GSL;
- falsification test;
- collision risk with existing GSL literature.

Historical failures that must drive theory include at least:
- RMFE fixed-amplitude / nuisance confounding;
- complete-count-law sparsity and bad count geometry;
- global `P(Y|K)` source-information washout and CAL→CONFIRM drift;
- persistent-sensor-as-source-posterior NO-GO;
- nuisance-unstable temporal/first-passage surrogate NO-GO;
- planner-disconnection / internally-good-but-downstream-useless modules;
- site-specific predictive-bank dependence.

Use the pattern:
`failure -> hidden assumption -> why invalid -> distant-field principle -> new falsifiable prediction`.

## Autonomous G2 iteration loop
You may iterate multiple G2 versions without asking the user, but every iteration must follow this loop:

1. **Theory first.** Define which historical failure is being repaired and derive the new module mathematically.
2. **Separate worktree/branch.** Never mutate the frozen Track-A confirmatory branch after seeing outcomes.
3. **Cheap falsification first.** Use DEV_SPENT worlds, historical traces, existing banks as analysis data, destructive controls, and offline tests.
4. **Reject aggressively.** If a candidate only improves NLL/calibration/rank while not increasing source contrast/action quality, reject it.
5. **Freeze before downstream testing.** Freeze equations, features, action contract, ablation, metrics, development/confirmation split, and Gates before fresh task outcomes.
6. **Development loop only on development data.** A failed exploratory candidate may be redesigned as a new version, but never tune the same version against its held-out confirmation outcomes.
7. **Fresh confirmation.** Use new held-out seeds/worlds/environments for each promoted architecture.
8. **If confirmation fails, classify NO-GO and return to theory as G2-vNext.** Do not rescue it by changing thresholds or metrics post hoc.

## Required load-bearing condition
The final architecture must isolate all three module contributions. Preserve an ablation equivalent to:
- baseline classic PMFS;
- M1 only + baseline planner;
- M1 + baseline predictive law + M3;
- M1 + qualified M2 + same M3;
- full bank-free G2.

Every module must have a downstream increment. A single strong module carrying two decorative modules is unacceptable.

## Performance target
Treat this as a preregistered target, not a tuning license:

- preferred primary continuous metric: 240 s localization error AUC;
- final full G2 vs classic/native PMFS: target **>=10% relative improvement** on the frozen primary continuous metric;
- if the frozen primary metric is a percentage success rate, target **>=10 percentage points**;
- this target must survive bank-free held-out-environment evaluation;
- no systematic catastrophic House/environment reversal;
- all three modules must be directionally downstream-beneficial and scientifically interpretable.

Do not cherry-pick Houses, seeds, metrics, action subsets, planner weights, or variants to reach 10%.

## What “continue until effective” means scientifically
The user authorizes autonomous iteration, but “until effective” means:

- keep developing **new theory versions** after documented failures;
- keep using fresh confirmation data for promoted versions;
- preserve rejected versions and their evidence;
- continue until either a three-module architecture satisfies the frozen load-bearing + performance + bank-free criteria, or a genuine resource/data/theoretical impossibility is reached and documented.

It does **not** mean repeatedly tuning on the same confirmatory runs until the p-value or percentage crosses the target.

## GitHub/evidence discipline
For every material runtime repair or G2 version:
- commit reproducible code/scripts;
- record exact commit/binary/data hashes;
- keep evidence namespaces separate;
- label `CONFIRMED / CURRENTLY_TESTING / CANDIDATE / REJECTED`;
- maintain a concise machine-readable status JSON;
- preserve all NO-GO evidence;
- at each major transition, update a handoff file so another agent can resume without the user re-explaining the project.

## Final stopping condition
Do not ask the user for routine permission. Stop and report only when one of these occurs:

1. **Track A frozen CTPI cleanly PASSes or scientifically NO-GOs** after true closed-loop testing;
2. **a G2 architecture satisfies all three load-bearing increments, the preregistered full-system target, and bank-free held-out-environment confirmation**;
3. a hard external blocker requires credentials/hardware/data not available to the agent;
4. an ambiguity would require changing the scientific question rather than implementing or testing it.

Otherwise continue autonomously.