# HD-PLF action implementation and OPEN software smoke

Status: `ACTION_FUNCTION_IMPLEMENTED / VGR_BINDING_NOT_IMPLEMENTED / NO_CLOSED_LOOP_RESULT`.
This is an independent development branch. The historical AOD F1 decision and
the AOD conditional-filter STOP are unchanged. The distance audit is closed;
no radius, source, or probe was selected from its outcomes.

## Three actual call chains

1. **Source probability.** `PMFS::stopAndMeasure()` calls
   `simulations.updateSourceProbability()` in `ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp:325`.
   The simulator scores a candidate through `sourceProbFromMaps()` at
   `internal/Simulations.cpp:926`, normalizes, and copies the result to
   `sourceProb.data` at `internal/Simulations.cpp:853-859`. This branch makes
   no changes to those PMFS C++ files. In the intended Native configuration,
   `q_t` must be read from this output after the normal measurement update.
   The new controller cannot create or overwrite a source posterior.
2. **Next goal.** Native `MovingStatePMFS::chooseGoalAndMove()` computes its
   information/exploration evaluation and calls `sendGoal(goal)` at
   `MovingStatePMFS.cpp:27-223`. The frozen pure
   `LocalActionPolicy.decide()` in `research/verified_local_encounter_v0/`
   handles a first real ten-sample stop hit and one revocable A-B-A(-C) cycle.
   New `HDPLFLocalController` subclasses that policy and replaces only its B
   waypoint selection with `HDPLFActionSelector.choose()`. The source map,
   planner's Native goal, navigation, and source estimate are not changed by
   these Python modules. **No ROS/VGR call site imports this controller yet.**
3. **Where rawu acts.** Existing AOD code prepares `u` and `rawu` amplitude
   templates and uses B2 for offline ranking. The new
   `HDPLFActionSelector._pair_separation()` builds candidate amplitude views
   from actually visited memory cells plus each proposed goal; `choose()`
   scores reachable goals using the supplied Native q. `LF-u` and `LF-rawu`
   differ only in the amplitude map array. `HDPLFLocalController._candidate_b()`
   routes the selected `rawu`/`u` goal into the local memory state machine.
   Thus rawu **does affect the pure controller's next waypoint**, but **has
   not yet affected an executed VGR waypoint**.

## Action rule and safeguards

The signed `HD_PLF_ACTION_CONTRACT_20260928.json` was committed before the
OPEN smoke. For each candidate source s, the predicted view contains template
values at unique previously visited cells and proposed goal x. For a<b,

`D_ab(x) = 1 - <v_a,v_b>² / (||v_a||² ||v_b||²)`.

The action value is `sum_{a<b} q_a q_b D_ab(x) - 0.01*BFS_path_metres`.
Only geometry-feasible goals 0.60–1.20 m from the measured anchor with path
length <=2.70 m are scored. Zero-norm views contribute no invented
separation. Invalid q/map/memory or no feasible goal returns the unchanged
Native goal. The pair score uses an exact second-moment identity so runtime
scales as `O(number_of_sources * number_of_memory_cells²)` per proposed goal
rather than materializing all candidate pairs. No truth coordinate, truth
distance, or 0.5 m outcome is an input.

The 0.01/m cost is one implementation constant, chosen before opening saved
OPEN maps for this smoke. It was not fit on target concentration or AOD F1
outcomes. This software check is not a scientific gate for that coefficient.

## Read-only H01/H02 OPEN software smoke

The input is 3,168 previously saved `u/rawu` products: 3 OPEN environments,
6 source hypotheses, 11 wind states, 8 replicas, and two amplitude channels.
The script did **not** run PMFS forward or open target concentrations. Its
six-source mean maps project back to the frozen 30-probe AOD templates with
maximum absolute difference `1e-9`. Their NPZ SHA256 is
`13261bbf9c064b4dd2f1060129afcdf0d944de399f8655445a3330414a012a88`.
The anchor is the lowest-rank frozen OPEN probe with at least two feasible
nearby coarse-grid stops; it is a geometry-only hypothetical stop, not a
recorded hit. Each arm uses the same six-source **uniform software weight**,
the same anchor and occupancy/BFS goal set. This is not a runtime Native q
snapshot or the full legal 596/630-source deployment support.

| OPEN environment | LF-u goal cell / separation / travel m | LF-rawu goal cell / separation / travel m | rawu−u separation |
|---|---|---|---:|
| House01 | 567 / 0.1110 / 1.095 | 593 / 0.0080 / 0.671 | −0.1030 |
| House02 W0 | 633 / 0.1356 / 0.971 | 501 / 0.2032 / 1.395 | +0.0676 |
| House02 W2 | 548 / 0.1969 / 1.271 | 501 / 0.1022 / 1.395 | −0.0948 |

The selected goal differs in all three environments. A one-position history
has zero pair separation under a free positive gain; the listed values are
the gain after adding the proposed second view. LF-rawu has higher modeled
separation in one environment and lower in two. These model scores are not
source localization results and provide **no consistent LF-rawu advantage**.
The output is byte-identical on repeated computation.

## Verification and remaining boundary

- 11 HD-PLF tests and 8 frozen memory tests pass. They cover proportional
  views, newly non-collinear views, common positive scaling, identical arm
  logic, rawu changing the selected goal, q input immutability, fallback,
  pair-score identity, and memory transitions.
- `git diff e54d5057` reports no modifications to the three Native PMFS C++
  inference/planner files named above.
- Full legal source support, actual Native q cycle alignment, conversion of
  real completed stop windows to memory cells, and VGR goal execution remain
  **unimplemented**. Until those are audited, no batch 300 s closed loop is
  warranted. The OPEN smoke cannot promote HD-PLF as a main innovation.
