# Codex directive — CTPI three-module redesign after complete-count-law NO-GO

Branch base: `9a4e163683e08e90bde7b08c7fb971069296c19b`

This directive starts from the terminal result:

- M1 CREL: **PASS**.
- Complete-count-law M2: **NO-GO**.
- M3: not evaluated.
- No C++/ROS/closed-loop claim is authorized yet.

The previous 30 H01/H02/H03 seed0--9 tapes are now **development/failure-analysis only**. They may be used to diagnose mechanisms and write tests, but they must never be reused as confirmatory evidence for a replacement M2.

## 1. Scientific decision

Do **not** rescue the failed M2 by changing Jeffreys alpha, temperature, smoothing strength, count bins, likelihood blending, posterior weights, or any source-truth-selected hyperparameter.

Do **not** rename any previously rejected module and reintroduce it. In particular, the replacement M2 must not be equivalent to:

- the old CPIR persistent sensor-state module;
- the old stop-resolved source likelihood;
- a fixed coherent transport-member identity across stops;
- a per-stop latent transport redraw model;
- first-passage / temporal-order source scoring already rejected in earlier gates.

The failed complete-count-law result establishes that the current route contains useful source-law information (M1 passes and source-law reassignment controls degrade), but exact cumulative-count categorical assimilation is a bad way to extract additional source evidence from only eight members.

## 2. Freeze the new three-module graph

The preferred redesign is:

```text
M1 CREL current-route source inference
        |
        v
posterior pi_t(s)
        |
        +------------------------------+
        |                              |
        v                              v
M2 action-conditional future        candidate actions a
sensor-event predictive law           |
P(Y_{t+1} | s, a, history_t)           |
        |                              |
        +--------------+---------------+
                       v
M3 predictive-information planner
argmax_a I(S;Y_{t+1} | a, history_t)
                       |
                       v
UAV motion -> fresh observation -> M1 update
```

### M1 — CREL

M1 is frozen from the passing F00 implementation. Do not modify its formula, prior, route-event definition, candidate support, or bank association while qualifying M2/M3.

Role: infer the current source posterior from the robust route-encounter statistic already proven useful.

### M2 — Action-conditional Sensor-Event Predictive Law

M2 is **not another source-posterior update on the same current observation**.

Its job is to predict the distribution of the *next unseen sensor event* under each feasible candidate action and each source hypothesis:

`P(Y_next | S=s, action=a, history_t)`.

This prevents double assimilation and prevents M2 from fighting an already strong M1 posterior on the same executed-route evidence.

The initial event should remain simple and observable, e.g. next completed-stop hit/no-hit, unless existing frozen data contain a richer pre-registered event whose calibration can be evaluated without source truth.

The predictive provider may use the coherent transport members supplied by CREL, but member identity itself must not be treated as a persistent hidden state unless a new independent premise gate first validates it.

M2 must not read source truth, localization error, future realized gas, planner reward, or downstream rank while being fitted/calibrated.

### M3 — Predictive-Information Planning

M3 consumes only:

- M1 posterior `pi_t(s)`;
- M2 predictive event law for feasible candidate actions;
- truth-blind feasibility/travel constraints.

The default scientific utility is posterior-weighted predictive mutual information:

`I(S;Y | a) = H(sum_s pi_s P(Y|s,a)) - sum_s pi_s H(P(Y|s,a))`.

No localization truth, source distance, future observation, or post-outcome tuned planner weight is permitted.

M3 must actually change selected actions/trajectory relative to the native planner in at least a nontrivial subset of cases; a telemetry-only score is not a main module.

## 3. New data authorization — observation tapes only

A new bank is **not** authorized for this gate.

Reuse the exact frozen predictive bank / transport-member provider used for the M1 PASS.

Authorize generation of new **observation tapes** only, because the old 30 tapes have been opened for failure analysis.

Create two disjoint, provenance-locked sets for each House:

- `M2_CAL`: development/calibration observation tapes;
- `M2_CONFIRM`: untouched confirmatory observation tapes.

Use fresh RNG-domain-separated observation seeds. Do not assume simple integer seeds are automatically independent: before running, scan existing manifests and prove that every new observation RNG key/domain is absent from all prior H01/H02/H03 seed0--9 evidence and from the predictive-member RNG domain.

The predictive bank/member RNG domain and observation-world RNG domain must remain disjoint.

Suggested minimum scope if runtime cost permits:

- 10 CAL observation tapes per House;
- 10 CONFIRM observation tapes per House.

If fewer are generated, document the loss of statistical power before truth is opened; do not change the Gate afterward.

Do not use source truth in CAL formula fitting either. CAL may use only proper predictive scores of actually observed future events. Source truth is allowed only in downstream Stage 2 after M2 has been frozen.

## 4. M2 Stage-1 predictive Gate

Before any downstream localization evaluation and before source truth is read, freeze M2 and evaluate one-step-ahead predictions on `M2_CONFIRM`.

For every executed transition, construct the M2 prediction using only data available before that transition, then score the newly observed event.

Primary predictive metrics:

1. event negative log likelihood (NLL), lower is better;
2. Brier score, lower is better;
3. calibration / reliability error, with explicit bin counts and confidence intervals where practical.

Reference comparator: the uncalibrated finite-member predictive event probability implied by the frozen M1/CREL provider. If another comparator is used, it must be frozen before CONFIRM is opened.

M2 PASS requires all of the following:

- pooled confirmatory NLL improves;
- pooled confirmatory Brier improves;
- calibration is not materially worse;
- no stable reverse House on both NLL and Brier;
- no NaN/floor-dominated or degenerate constant predictor behavior;
- action/source predictive variation remains nonzero (the calibration method must not erase source/action discrimination).

Do not select a calibration formula/hyperparameter by localization error or source rank.

If M2 fails this predictive Gate, terminate this candidate. Do not run M3 to compensate.

## 5. M1 + M2 downstream sanity Gate

After M2 Stage-1 is frozen and hashed, source truth may be opened for a downstream sanity analysis.

This analysis must **not** require M2 to re-update the current source posterior; M2's scientific role is future-event prediction. Therefore point-localization equality between M1 and M1+M2 under the same native planner is expected by construction and is not a failure.

Instead verify:

- M1 posterior remains bit-for-bit unchanged by enabling M2 in forecast-only mode;
- M2 does not read or mutate `sourceProbability` except through a read-only M1 posterior interface;
- M2 forecast at decision time depends only on past/current allowed state and candidate action;
- forecast output changes across at least some `(source, action)` pairs.

Output a machine-readable `M2_FORECAST_ONLY_OWNERSHIP=PASS` only if all checks pass.

## 6. M3 offline counterfactual Gate

Before ROS implementation, use frozen M1 posterior + frozen M2 forecast to compute candidate-action information scores on held-out contexts.

This stage may test mathematical validity and action discrimination only. It must not claim localization improvement from fixed historical tapes because historical observations were generated under different actions.

Required checks:

- information score finite and >= 0 within numerical tolerance;
- deterministic tie handling;
- no source-truth access;
- no future-observation access;
- at least some contexts where the M3-selected feasible action differs from the native planner action;
- destructive source-law or action-law permutation reduces/changes the intended information structure in the expected direction without using truth.

Only then authorize C++ parity.

## 7. C++/ROS integration boundary

Do not reuse CPIR/TADM mode aliases.

Implement a dedicated CTPI runtime contract only after M2 predictive and M3 offline gates pass.

Runtime invariants:

- M1 owns source inference for the current executed-route observation;
- M2 is forecast-only before the next action;
- M3 reads M1 posterior and M2 forecasts to choose an action;
- the same observation is never assimilated twice;
- PSRG/old diagnostic geometry is not silently inserted as a planner weight;
- no truth is available to inference/planner code.

Required true-loop trace:

`posterior_t -> M2 forecast_t(a) -> M3 selected_action_t -> command -> pose_{t+1} -> fresh observation_{t+1} -> posterior_{t+1}`.

Required terminal checks:

- `NO_TRUTH_LEAKAGE=PASS`
- `NO_DOUBLE_ASSIMILATION=PASS`
- `M2_FORECAST_ONLY_OWNERSHIP=PASS`
- `POSTERIOR_TO_ACTION=PASS`
- `ACTION_TO_MOTION=PASS`
- `FRESH_OBSERVATION=PASS`
- `TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS`

## 8. Closed-loop arm ladder

Do not pretend every module must lower point error in a fixed replay. Use role-consistent gates.

Closed-loop formal arms after all upstream gates pass:

- `A0`: native PMFS.
- `F00`: passing M1 CREL source inference + native planner.
- `F11`: M1 + passing M2 forecast + M3 predictive-information planner.

For implementation diagnostics also log:

- native action under F00 at every decision;
- M3 action under the same pre-action state;
- M2 predictive distribution and M3 information score.

If a four-arm implementation is required for engineering isolation, `F01` may mean M1+M2 forecast-only with the native planner. By construction its trajectory and localization must match F00; its purpose is ownership/parity checking, not a claimed robot-task increment.

The main module-specific evidence is therefore:

- M1: robot-task increment `F00 vs A0` — already PASS offline and must be rechecked closed-loop;
- M2: independent held-out predictive-skill PASS;
- M3: closed-loop task increment `F11 vs F00` together with actual action/trajectory change.

This is a scientifically valid three-module chain because every module has a distinct indispensable role and an independently testable output. Do not force M2 to manufacture a second localization update merely to obtain another error delta.

## 9. Strict alternative only if a source-refinement M2 is mandatory

Do not run this alternative on CONFIRM in parallel with the preferred forecast-only design.

If the project explicitly requires M2 itself to change the current source posterior, the only admissible structural candidate after the current failure analysis is an **M1-alias-only refinement**:

- partition source hypotheses into exact M1 mean-projection equivalence classes;
- preserve each class's total F00 posterior mass exactly;
- use richer member-law information only to redistribute mass *within* a class that M1 cannot distinguish;
- forbid any change between classes.

This architecture cannot overturn robust M1 evidence and makes the incremental question precise: can full-law shape resolve hypotheses that have exactly the same M1 projection?

Any smoothing/calibration constant must be selected from CAL using source-truth-free predictive criteria and frozen once. Then evaluate exactly once on CONFIRM. If it fails, abandon source-refinement M2 rather than trying more formulas.

## 10. Deliverables before asking for closed-loop authorization

Commit all of the following:

1. provenance manifest for CAL and CONFIRM observation tapes;
2. proof of RNG-domain/seed disjointness;
3. frozen M2 mathematical specification;
4. M2 truth-blind predictive Stage-1 outputs and hashes;
5. M2 confirmatory NLL/Brier/calibration report;
6. M2 ownership/double-assimilation audit;
7. M3 offline mathematical/action-discrimination audit;
8. explicit terminal decision:
   - `CTPI_M2_PREDICTIVE_GATE_PASS`, or
   - `CTPI_M2_PREDICTIVE_GATE_NO_GO`.

Do not implement the formal ROS closed loop unless the PASS verdict is supported by untouched confirmatory tapes.
