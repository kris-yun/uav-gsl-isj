# Codex directive — CTPI three-module redesign after M2 NO-GO

Base: `9a4e163683e08e90bde7b08c7fb971069296c19b`

Machine-readable preregistration: `docs/CTPI_THREE_MODULE_REDESIGN_PREREGISTRATION_20260902.json`.

## Frozen prior result

- M1 CREL: **PASS**.
- Complete-count-law M2: **NO-GO**.
- M3: **NOT EVALUATED**.
- The old H01/H02/H03 seed0--9 observation tapes are development/failure-analysis data only.
- Do not implement formal C++/ROS closed loop until the replacement M2 and the M3 offline gates pass.

The previous M2 failed because eight coherent members were used to estimate an exact `N+1`-category cumulative-count law. Sparse categorical floors destroyed the smooth distance information already retained by F00. Source-law reassignment controls show the physical source-law association is real; the failed component is the assimilation rule, not CREL or the bank.

## 1. Do not rescue or rename rejected ideas

Do not tune the failed complete-count likelihood on the old 30 cases. In particular, no alpha/temperature/bin/smoothing/posterior-blend search is allowed.

Do not reintroduce under a new name:

- old CPIR persistent sensor state;
- old stop-resolved current-source likelihood;
- fixed coherent transport-member identity across stops without a new premise gate;
- per-stop transport redraw as a current-source scorer;
- previously rejected first-passage / temporal-order source scoring.

## 2. New load-bearing module graph

```text
M1 CREL current-route source inference
        |
        v
posterior pi_t(s)
        |
        +-------------------------------+
        |                               |
        v                               v
M2 action-conditional future        feasible actions a
sensor-event predictive law            |
P(Y_next | s,a,history_t)               |
        |                               |
        +---------------+---------------+
                        v
M3 posterior-weighted predictive-information planner
                        |
                        v
selected action -> UAV motion -> fresh observation -> M1
```

### M1 — CREL

Freeze the passing F00 implementation bit-for-bit. Do not change its formula, support, prior, route-event statistic, or source-law association while qualifying M2/M3.

M1 owns source inference from the **already executed** route.

### M2 — action-conditional future sensor-event predictive law

M2 does **not** assimilate the same current observation a second time and does not write `sourceProbability`.

Its output is

`P(Y_next | S=s, candidate_action=a, allowed_history_t)`

for every relevant source/action pair before the action is executed.

Start with a directly observable future event such as next completed-stop hit/no-hit unless a richer event is preregistered before confirmatory data are opened.

M2 may use the frozen CREL transport ensemble as a predictive provider, but transport member identity must not become a persistent hidden state unless separately proven.

Forbidden during M2 design/selection:

- source truth;
- localization error;
- source rank;
- future realized gas;
- planner reward;
- downstream closed-loop outcome.

## 3. New data authorization

Do **not** generate a new predictive bank for this gate.

Reuse the exact frozen predictive bank/provider used for the M1 PASS.

Generate new **observation tapes only**, because seed0--9 truth has already been opened.

For each House create two disjoint provenance-locked sets:

- `M2_CAL`: calibration/development;
- `M2_CONFIRM`: untouched confirmation.

Suggested minimum if runtime permits: 10 tapes per House per set.

Before generation, prove every observation RNG key/domain is absent from all old observation worlds and disjoint from the predictive-member RNG domain. Do not assume integer seed labels alone prove independence.

CAL may tune M2 only with proper predictive metrics. CONFIRM may be evaluated once after the formula and all hyperparameters are frozen.

## 4. M2 predictive Gate — before truth

For every held-out transition, create the prediction using information available strictly before that transition and score the newly observed event.

Primary metrics:

- event NLL, lower is better;
- Brier score, lower is better;
- reliability/calibration error.

Baseline forecast: the frozen uncalibrated finite-member predictive probability implied by CREL, unless another baseline is preregistered before CONFIRM is opened.

`CTPI_M2_PREDICTIVE_GATE_PASS` requires:

1. pooled confirmatory NLL improves;
2. pooled confirmatory Brier improves;
3. calibration is not materially worse;
4. no House has a stable reverse on both NLL and Brier;
5. predictor is finite and nondegenerate;
6. source/action predictive variation remains nonzero — calibration must not collapse the signal.

If this fails, stop. Do not use M3 to hide a bad predictor.

## 5. Ownership Gate

With M2 enabled in forecast-only mode and the native planner retained:

- M1 posterior must remain bit-for-bit unchanged;
- no current measurement is assimilated twice;
- M2 may read M1 posterior but may not mutate it;
- M2 may only use allowed past/current state plus candidate action;
- forecasts must vary for at least some source/action pairs.

Required marker:

`M2_FORECAST_ONLY_OWNERSHIP=PASS`

## 6. M3 offline Gate

M3 utility is posterior-weighted predictive mutual information:

`I(S;Y|a)=H(sum_s pi_s P(Y|s,a))-sum_s pi_s H(P(Y|s,a))`.

Inputs only:

- frozen M1 posterior;
- a predictive-event-law provider;
- truth-blind feasibility;
- travel cost only as a frozen tie break / constraint rule.

Offline fixed tapes may prove mathematical validity and action discrimination only, not localization improvement under counterfactual actions.

Require:

- finite nonnegative information scores;
- deterministic ties;
- no truth/future observation access;
- nontrivial contexts where M3 changes the action;
- destructive source/action-law controls alter the intended information structure in the expected direction.

Only then authorize runtime parity work.

## 7. Four-arm true closed-loop isolation

The final task-level design must permit all three modules to carry a distinct measurable increment.

### A0

Native PMFS.

### F00

Passing M1 CREL source inference + native planner.

Tests M1:

`M1 task increment = F00 - A0`.

### F10

M1 + **baseline uncalibrated finite-member future-event forecast** + M3 predictive-information planner.

M2 replacement is OFF; M3 is ON using the frozen baseline forecast.

Tests M3:

`M3 task increment = F10 - F00`.

F10 must actually change selected actions/trajectory. If it does not, M3 is NO-GO.

### F11

M1 + qualified M2 predictive law + **the exact same M3 planner** used in F10.

F10 and F11 must differ only in the predictive-event-law provider. M3 utility, feasible actions, tie handling, budgets, start state, observation world, and M1 posterior definition must be identical.

Tests M2 at robot-task level:

`M2 task increment = F11 - F10`.

This is the critical task-level ablation: if better held-out prediction does not improve decisions when inserted into the same M3, M2 cannot be claimed as a useful closed-loop module even if its NLL is better.

Optional `F01` is engineering-only: M1 + M2 forecast + native planner. Its trajectory/task result should match F00 by construction; use it only to prove forecast-only ownership and no double assimilation.

## 8. Closed-loop task metrics and PASS logic

Primary task metrics:

- final localization error;
- error-time AUC;
- time-to-2m.

Also log true-source rank/support as secondary evidence.

For every decision log:

- M1 posterior hash/state;
- baseline forecast used by F10;
- qualified M2 forecast used by F11;
- M3 information scores;
- native candidate action;
- selected action;
- command acknowledgement;
- pose before/after;
- fresh next observation;
- next posterior.

Required causal markers:

- `NO_TRUTH_LEAKAGE=PASS`
- `NO_DOUBLE_ASSIMILATION=PASS`
- `M2_FORECAST_ONLY_OWNERSHIP=PASS`
- `POSTERIOR_TO_ACTION=PASS`
- `ACTION_TO_MOTION=PASS`
- `FRESH_OBSERVATION=PASS`
- `TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS`

Do not claim a three-module PASS unless:

- M1 has a task increment `F00 > A0`;
- M3 has a task increment `F10 > F00` with actual trajectory change;
- M2 first passes the independent held-out predictive Gate and then has a task increment `F11 > F10` under the identical M3;
- full F11 has no stable reverse House on the preregistered primary metrics.

If one increment fails, report that module NO-GO. Do not compensate by retuning another module.

## 9. Strict alternative if M2 must directly refine the current posterior

This is disabled by default and must not be tried in parallel on CONFIRM.

The only structurally admissible development candidate after the current failure is **exact-M1-alias-only refinement**:

1. group source hypotheses with exactly equal frozen F00 mean projection;
2. preserve each group's total F00 posterior mass exactly;
3. use richer member-law information only to redistribute mass inside that M1-indistinguishable group;
4. forbid movement of posterior mass between different M1 groups.

Any smoothing/calibration constant must be chosen on CAL with truth-blind predictive criteria and frozen before CONFIRM. If it fails once on CONFIRM, abandon direct source-refinement M2.

## 10. Deliverables before formal ROS closed loop

Commit:

1. CAL/CONFIRM provenance manifests;
2. RNG-domain disjointness proof;
3. frozen M2 mathematics;
4. truth-blind M2 confirmatory NLL/Brier/calibration report;
5. M2 ownership/double-assimilation audit;
6. M3 offline action-discrimination audit;
7. Python selftests and destructive controls;
8. terminal markers for each Gate.

No CPIR/TADM alias may be relabeled as CTPI. No formal closed-loop run is authorized until all upstream gates pass.
