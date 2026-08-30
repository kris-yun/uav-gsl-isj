# CTT causal first-passage event inference — final method freeze

Date: 2026-08-30
Status: FINAL OFFLINE FALSIFICATION CONTRACT / CLOSED LOOP NOT AUTHORIZED

## 1. No method reset

The paper-level main innovation remains **Causal Transport Tomography (CTT)** and must contain three load-bearing mechanisms simultaneously:

1. causal physical factorization;
2. native temporal/spatiotemporal transport dynamics;
3. a neural transport solver surrogate.

The V1--V7 residual-TCN chain is a frozen negative audit. It is not the method to be repaired by another blend, projection, ranking head, gate, temperature or threshold.

## 2. Binding causal chain

The observation model is

`S -> Z_t -> C_t -> R_t -> M_t -> Y_t`,

where source `S` is global, transport `Z_t` evolves, physical concentration is `C_t`, gas-sensor internal state `R_t` is run-persistent, measured concentration is `M_t`, and temporal event observations `Y_t` are generated from the measured sensor signal. A context reset of `R_t` and any occupancy-to-ppm conversion are forbidden.

## 3. M1 neural first-passage field

M1 is a physical solver surrogate. For candidate source `s`, causal route/wind/map context `c_t`, and transport nuisance marginalized by simulator supervision, it predicts

`pi_theta(F=n | s,c_t), n=0..79,never`.

`F` is the first native 0.2-s sample within the eight completed 10-sample PMFS blocks at a physical stop for which the persistent measured sensor exceeds the native threshold 0.1 ppm. `never` is explicit.

Training contains simulator-derived first-passage labels only. Forbidden training/checkpoint signals include source rank, localization error, PMFS posterior, planner outcome, future observation and closed-loop reward.

## 4. M2/M3 exact evidence factorization

M2 owns temporal placement/phase conditional on event count/reach. M3 owns count/non-arrival/survival. The full likelihood is the exact sequence/first-passage likelihood; the same observation may not also be consumed by native PMFS in the same posterior update.

Required causal rule: `predict -> freeze -> observe -> score`.

## 5. H01 premise findings frozen before neural M1

### Coarse 8-block HIT tape

Contract: `CTT_H01_BLOCK_EVENT_FACTORISATION_PREMISE_V1`.

Result: `CTT_H01_EVENT_PREMISE_NO_GO`.

Time permutation and candidate-temporal-label destruction hurt, but M2 conditional phase did not improve over its iid comparator and full A3 did not significantly improve over count/survival J3. Therefore 10 samples -> 1 block bit is too destructive to qualify the temporal mechanism.

### Native 0.2-s first passage

Contract: `CTT_H01_NATIVE_SAMPLE_FIRST_PASSAGE_PREMISE_V1`.

Result: `CTT_H01_NATIVE_FIRST_PASSAGE_PREMISE_PASS` on 1280 predictive8 leave-one-transport-member-out cases.

- full first-passage mean normalized rank: 0.1417109;
- survival-only: 0.2564070;
- time-permuted: 0.1573191;
- candidate-phase-label shuffled: 0.3040221;
- full vs survival: 788 wins / 283 losses / 209 ties, p=6.56e-56;
- full vs time-permute: 346 / 175 / 759, p=2.84e-14;
- full vs label-shuffle: 781 / 322 / 177, p=7.69e-45.

This is model-premise evidence only, not disjoint-observation localization qualification.

## 6. Neural M1 H01 physical gate preregistration

Source split is deterministic SHA-256 ordering of the 210 H01 carriers:
- 150 train;
- 30 validation;
- 30 test.

Trajectory split:
- train: 4001,4002,4003;
- validation: 4004;
- test: 4005.

All 8 predictive transport/placement members are stochastic simulator labels. Test truth ranks are not used for checkpoint selection.

Capacity-matched arms:
- `CONDITIONAL`: candidate/source geometry + causal pose/route context + actual wind context;
- `STATIC-WIND`: identical network capacity/dimension but dynamic wind features are replaced by the train-set mean.

Primary proper scores:
- categorical first-passage NLL;
- integrated Brier score for arrival-by-time.

Advance only if all are true on held-out source carriers + trajectory4005:
1. source-cluster bootstrap lower 95% CI of `STATIC - CONDITIONAL` NLL is > 0;
2. source-cluster bootstrap lower 95% CI of `STATIC - CONDITIONAL` Brier is > 0;
3. shuffling dynamic context across held-out test examples worsens conditional NLL with lower 95% CI > 0;
4. probability normalization max error < 1e-6.

No threshold can be changed after opening the test result.

## 7. Downstream authorization

A neural M1 PASS is necessary but not sufficient for closed loop. It must next be inserted into the frozen first-passage/event-survival scorer and pass H01 offline source-evidence controls. Strict final confirmation should use the disjoint reserved observation bank if the exact original asset can be recovered.

Until all offline and runtime-parity gates pass:

`CLOSED_LOOP_NOT_AUTHORIZED`.
