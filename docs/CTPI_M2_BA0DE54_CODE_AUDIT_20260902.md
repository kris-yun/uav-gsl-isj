# CTPI M2 `ba0de54` code audit — pre-generation blockers

Audited commit: `ba0de54311b762a22ba43a712b4f60a37b08ff5e`

Audit status: `BLOCKED_BEFORE_M2_CAL_GENERATION`

No CAL/CONFIRM observation tape existed when this audit was started. Therefore these defects can still be corrected without contaminating confirmatory data.

## P0-1 — cross-House source dimension is incompatible with the pooled API

The previously frozen Stage-1 evidence has different carrier counts:

- H01: 210 carriers;
- H02: 201 carriers;
- H03: 206 carriers.

`fit_calibration_table()` and `evaluate_confirmatory_gate()` both require one rectangular `[event, source]` NumPy array, while `evaluate_confirmatory_gate()` simultaneously requires H01/H02/H03 in one call. The three Houses therefore cannot be pooled without an undocumented padding convention.

Padding is not an admissible silent repair because the current source/action-variation checks inspect every source column without a valid-source mask, so padded columns can create false variation.

Required repair: use ragged/per-House batches and pool only sufficient statistics/losses, or add an explicit immutable valid-source mask whose semantics are preregistered and tested. Do not choose a padding rule after CAL is observed.

## P0-2 — the confirmatory Gate validates the posterior mixture, not the source-conditional law used by M3

The Gate scores only

`q_j = sum_s pi_j(s) p_j(s)`

against the realized event. M3 will consume the full set of source-conditional probabilities

`p_j(s) = P(Y_next | S=s, action, history)`

and its information utility depends on differences among sources.

Improved mixture NLL/Brier/ECE does not imply that the source-conditional contrasts are correct. A calibration map can improve `q_j` while compressing or distorting the source differences used by M3.

The current `minimum_distinct_table_values` and `source_variation` checks prove only non-constancy, not correctness.

Required repair before M3 authorization: add a separately preregistered source-conditional predictive validation. A controlled simulator source label may be used only inside this predictive validation if explicitly declared as the conditioning variable of the predictive experiment; it must never enter M1 localization, planner reward, localization error, or model selection on CONFIRM. If source labels remain sealed, then M2 PASS must be described only as mixture-forecast calibration and cannot by itself validate the source-conditioned law required by M3.

## P0-3 — M1 cadence is undefined for the 15 M2 transitions

The frozen M1 evidence has 15 completed stops but only 5 source updates: source posterior updates occur after 3, 6, 9, 12, and 15 completed stops.

The new M2 freeze instead refers to a pre-event `pi_j(s)` for every one of 15 events. No rule specifies whether M1 is recomputed after every stop or whether the last frozen source-update posterior is held between updates.

Recomputing M1 after every stop changes the already-passing M1 runtime cadence and violates the M1 freeze.

Required repair: freeze the exact pre-event posterior schedule before CAL generation. The conservative parity-preserving rule is piecewise constant: use the initial M1 prior before stops 1--3, the frozen posterior after stop 3 before stops 4--6, after stop 6 before stops 7--9, after stop 9 before stops 10--12, and after stop 12 before stops 13--15. Any other rule requires a new M1 parity Gate.

## P0-4 — RNG disjointness is asserted from a hand-written seed list, not proven from prior assets

`tools/ctpi_m2_make_provenance.py` hard-codes 13 forbidden integers and then writes `new_vs_predictive_and_default_numeric_disjoint=true` if the new seeds avoid that list.

It does not scan the frozen predictive-bank manifests, historical observation evidence, or prior RNG provenance and therefore cannot establish the stronger claim that every new observation-world key is disjoint from every previously used key/domain.

Required repair: materialize a legacy RNG inventory from the authoritative old manifests/evidence, hash that inventory, and make provenance generation consume it. The pre-generation proof must fail closed if the inventory is missing or if a prior seed/domain cannot be resolved.

## P0-5 — generator runtime provenance omits a previously known OpenMP dependency

Earlier prospective transport validation established that the native stochastic generator is sensitive to OpenMP runtime configuration: `OMP_NUM_THREADS=4` reproduced the frozen reference, while multiple other thread counts did not. That older runner also froze `OMP_DYNAMIC=FALSE`, BLAS thread counts, `PYTHONHASHSEED`, exact GADEN build paths, and hashes for the RNG hook / math / RunningSimulation sources.

The new M2 freeze records only the multistream binary and source hashes. It does not freeze the OpenMP configuration or the dynamically loaded GADEN runtime provenance.

Therefore the same numeric seed is not yet a fully specified observation world.

Required repair: restore an explicit generator environment contract and preflight. At minimum freeze `OMP_NUM_THREADS=4`, `OMP_DYNAMIC=FALSE`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `NUMEXPR_NUM_THREADS=1`, `PYTHONHASHSEED=0`, the exact ROS/GADEN overlay order, and hashes for the GADEN RNG hook / MathUtils / RunningSimulation implementation used by the binary.

## P0-6 — no committed observation-tape generator enforces the frozen world contract

Commit `ba0de54` contains the freeze documents, provenance generator, forecast core, and selftest, but no committed CAL/CONFIRM materializer/runner that enforces:

- one independent world per invocation;
- exact environment/hash preflight;
- read-only bank root;
- fresh output directories;
- exactly 1500 physical samples;
- exactly 1502 causal FOPDT samples;
- exactly 15 completed-stop events;
- source-coordinate sealing;
- per-world output hashes and terminal status.

Required repair: commit and selftest the tape materializer before the first CAL world is generated.

## P1-1 — the implemented `action_variation` check has no action variable

`evaluate_confirmatory_gate()` accepts no action ID, action coordinates, or decision-time identifier. `visited_action_variation_every_house` is computed by taking a range across rows of `m2_source`, so variation due to time/history/tape differences can satisfy a check described as action variation.

Required repair: pass explicit action metadata. Do not label across-row variation as action-conditioned variation. Counterfactual action discrimination remains a separate M3 offline Gate.

## P1-2 — the current M2 implementation is a calibration layer, not yet the full claimed predictive-law module

`GLOBAL_POSTERIOR_WEIGHTED_ISOTONIC_EVENT_RELIABILITY` reduces M2 to a nine-value monotone table `g(k)` over the eight-member hit count. This may be useful as a reliability calibration mechanism, but isotonic calibration itself is standard methodology and should not be presented as the main CTPI innovation.

The conceptual M2 remains the action-conditioned predictive law. The isotonic table should be described as one candidate implementation/calibration layer unless a stronger transport-conditioned predictive operator is later established.

## P1-3 — declared target conditions on history, implementation does not

The scientific target is

`P(Y_next | S=s, action=a, history_t)`.

The current implementation returns `g[K_j(s)]`, where `K_j(s)` is a raw physical member-hit count. It has no explicit causal sensor/history state even though the realized `Y_j` is produced after a FOPDT sensor operator with memory/dead time.

A global reliability table can average over history but is not the same object as a history-conditioned sensor-event predictive law.

This does not force reintroduction of the rejected persistent-sensor *source scorer*. A sensor forward state used only to predict the next observation is a different role. However the mismatch must be resolved or the scientific claim narrowed before M3.

## P1-4 — `_posterior()` silently renormalizes frozen M1 input

The code accepts any positive row mass and silently divides by that mass. Since M1 is frozen and ownership/parity is a formal requirement, malformed M1 posterior input should fail closed rather than be repaired by M2.

Required repair: assert each posterior row already sums to one within the frozen numerical tolerance; then copy/read it without semantic renormalization.

## P1-5 — the selftest contains future-outcome leakage in its fixture

The synthetic confirmatory selftest constructs `post` directly from the future `y` event. This does not prove production leakage, but it means the passing selftest is compatible with an impossible pre-event posterior and therefore cannot detect the timing error that the real pipeline is supposed to forbid.

Required repair: construct synthetic posteriors from variables fixed before synthetic outcomes, add explicit pre-event/action indices, and add negative tests that reject future-index mismatch.

## Decision

Do not generate `M2_CAL` yet.

The correct next terminal state is:

`CTPI_M2_BA0DE54_PREGEN_AUDIT=BLOCKED`

Generation becomes admissible only after P0-1 through P0-6 are resolved in committed code/manifests and the revised selftests pass. P1 items must be resolved before claiming M2 as an action-conditioned predictive-law module or authorizing M3.
