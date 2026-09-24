# IF-CV Candidate Freeze V1

Date: 2026-09-25

Status: PRE-D1R THEORY/ALGORITHM CONTRACT — NO D1R RESULTS USED

## Source support and prior

- N = 168 fixed dense micro source cells.
- pi_s = 1/168.
- Macro prior is induced by the micro prior; never independently uniformized.

## Geometry graph

Two source cells are spatial neighbors iff their original PMFS/free-cell footprints share a free face.

No kNN, radius completion or target-driven edge construction is allowed. Every candidate spatial macrostate is connected.

## Fidelity channels

Encounter channel: registered random-query hit/no-hit channel over the frozen 300 query IDs.

Amplitude-aware mark channel: per query, one zero atom plus training-reference positive-ppm bins.

Fidelity certificates apply only to these declared marginal/query channels. They are not full 300-D path certificates.

## Candidate hierarchy

Use the auxiliary-Pro IF hierarchy:
1. construct training-only uncertainty sets;
2. compute group fidelity upper bounds for encounter and mark channels;
3. merge only graph-adjacent groups;
4. lexicographic priority uses worst fidelity bound, amplitude-aware JS cost, encounter JS cost, deterministic ID tie key;
5. save every cut.

## Strong-claim fidelity tolerances

- epsilon_enc = 0.15 average-TV units;
- epsilon_mark = 0.20 average-TV units.

These are scientific approximation tolerances, not tuned hyperparameters.

If finite-reference simultaneous bounds are too wide to certify any nontrivial cut, the strong causal-emergence-inspired claim does not advance. Thresholds are not relaxed after D1R.

## Nested reference selection

Use source-stratified 4-fold realization CV.

For each outer fold:
- hold out four realizations/source;
- on the remaining 12, use three inner folds of 8 train / 4 validate;
- learn hierarchy/partition only inside the training split;
- select cut and common likelihood/calibration hyperparameters by held-out 168-cell micro log score, subject to fidelity eligibility;
- refit on all 12 outer-training realizations;
- predict the four outer-held-out realizations.

After audit, rerun the same OOF procedure over all 16 references, select one final recipe, refit once on all 16, serialize and hash it.

## Working predictive family

Common family for identity and hard-pooling competitors: zero-hurdle + log-amplitude Student-t posterior predictive.

Hit smoothing grid: eta in {1/2, 1, 2}.
Evidence inverse-temperature grid: {0, 1/300, 1/100, 1/30, 1/10, 1/3, 1/2, 1, 2}.
Fixed prior-contamination floor: epsilon = 2^-20.

## Honest micro lift

For partition g: q_s(y) = [pi_s / Pi_g(s)] Q_g(s)(y).

No centroid spike or hidden within-group source selector.

## Reference stability prerequisites

Strong ADVANCE requires all:
1. 1 < K < 168;
2. median pairwise ARI across the four outer learned partitions >= 0.70;
3. median normalized VI, VI/log2(168), <= 0.20;
4. at least 80% of source pairs co-grouped in final partition have bootstrap co-membership frequency >= 0.75;
5. all spatial groups connected;
6. fidelity constraints non-vacuously satisfied.

## Reference predictive prerequisites

Reference OOF candidate must beat identity and the locked ordinary champion and must not show a primary calibration pathology.

Outcomes:
- D1R_ADVANCE_IFCV_STRONG_MAINLINE
- D1R_HOLD_WEAK_PREDICTIVE_POOLING_ONLY
- D1R_STOP_FSEI_NOT_DISTINCT_FROM_ORDINARY_POOLING

Only ADVANCE authorizes a D1C target experiment.