# CTT H01 final offline verdict — 2026-08-30

Status: **FINAL LOCAL OFFLINE FALSIFICATION / CLOSED LOOP NOT AUTHORIZED**

## Executive conclusion

The paper-level CTT hypothesis is not rejected at the physical-premise level: native 0.2-s first-passage timing contains strong candidate-relative source information beyond survival/ever-reachability. However, every locally trainable H01 neural surrogate tested on the packaged predictive8 bank failed to preserve that phase information in a nuisance-stable source likelihood. Therefore the existing H01 offline assets are insufficient to authorize a neural CTT closed loop.

No further head, blend, temperature, rank projection, loss weight, or threshold rescue is permitted on these consumed H01 splits.

## Frozen positive premise

`CTT_H01_NATIVE_FIRST_PASSAGE_PREMISE_PASS`

1280 predictive8 leave-one-transport-member-out cases:

- full first-passage mean normalized rank: 0.1417109;
- survival-only: 0.2564070;
- TIME-PERMUTE: 0.1573191;
- candidate-phase-label shuffle: 0.3040221;
- full vs survival: 788 wins / 283 losses / 209 ties, p=6.56e-56;
- full vs TIME-PERMUTE: 346 / 175 / 759, p=2.84e-14;
- full vs phase-label shuffle: 781 / 322 / 177, p=7.69e-45.

Therefore the native first-passage observable is scientifically load-bearing.

## Frozen coarse-representation failure

`CTT_H01_EVENT_PREMISE_NO_GO`

Compressing 80 native 0.2-s samples into eight 10-sample HIT bits destroys too much phase information. Full Markov order did not significantly beat count/survival, although destructive controls showed some timing association. This representation is permanently rejected for the main temporal mechanism.

## Provenance correction

The packaged H01 predictive8 generator accepts **one fixed native `--wind` input** for all reserved trajectories. The separately packaged trajectory-specific `H01_wind35.bin` estimates are therefore not causal conditioning variables of predictive8.

Two exploratory neural gates that used trajectory-local wind are retained as negative/provenance diagnostics and must not be interpreted as a rejection of wind-conditioned CTT. The earlier CTT-V13 H03 M1 physical gate remains the valid direct evidence for wind conditioning.

## H01 fixed-wind neural field results

A nonlinear geometry/route first-passage field was trained only on simulator labels.

Frozen test proper scores on trajectory4005/member7:

- temporal/route neural: NLL 0.54078, Brier 0.11540;
- geometry neural: NLL 0.54339, Brier 0.10129.

Route/time permutation strongly hurts NLL, but temporal/route conditioning did not beat geometry on both proper scores. Verdict remains NO-GO for that incremental claim.

The frozen geometry neural field significantly beat a linear softmax field in source ranking and Brier, but its NLL cluster CI narrowly crossed zero; this is partial evidence for nonlinear neural-field utility, not an advance gate.

## Frozen neural source-evidence failure

Using the frozen geometry neural first-passage distribution on trajectory4005/member7:

- neural full mean normalized rank: 0.26860;
- survival-only: 0.26149;
- TIME-PERMUTE: 0.27116;
- phase-label shuffle: 0.27498;
- linear full: 0.41164.

Neural nonlinearity was strongly useful versus linear (151 wins / 57 losses / 2 ties, p=2.66e-11), but neural full did not beat survival and destructive temporal controls did not remove significant source gain. Hence the neural field learned useful nonlinear reachability but not robust candidate-relative phase.

## Final factorized neural implementation

To match the exact M2/M3 factorization, the final network used two heads:

- survival head: `p_e = P(F < never | x)`;
- conditional phase head: `p_phi(t | F < never, x)`.

Full distribution:

- `P(F=t|x)=p_e p_phi(t|event,x)`;
- `P(F=never|x)=1-p_e`.

Training objective is fixed, proper and non-tuned:

`L = BCE(ever) + CE(first-passage-bin | ever)`.

No localization/rank/posterior/planner signal enters training or checkpoint selection.

Fresh final combination:

- train trajectories 4001–4003, members 0–4;
- validation trajectory4004/member5;
- source-rank test trajectory4005/member6;
- member7 unused by this final version.

Test proper score:

- NLL 0.4908565;
- integrated Brier 0.0972097;
- normalization error 2.98e-7.

But source evidence failed the preregistered mechanism gate:

- full mean normalized rank 0.23545;
- survival-only 0.22873;
- TIME-PERMUTE 0.23716;
- phase-label shuffle 0.23363;
- full vs survival: 54 wins / 72 losses / 84 ties, p=0.9549;
- full vs TIME-PERMUTE: 46 / 35 / 129, p=0.1332;
- full vs phase-label shuffle: 59 / 99 / 52, p=0.9995.

Final verdict:

`CTT_H01_FACTORIZED_NEURAL_FIRST_PASSAGE_FINAL_NO_GO`

## What is and is not rejected

Rejected on the current packaged H01 bank:

- 8-block temporal compression;
- generic residual TCN source scoring;
- post-hoc physics projection rescue;
- current small-data neural first-passage surrogates as a closed-loop source likelihood.

Not rejected:

- native first-passage physical information;
- the CTT causal factorization;
- wind-conditioned neural physical fields in general (H03 direct M1 physical gate previously passed);
- a neural first-passage field trained on a sufficiently varied, correctly conditioned physical bank.

## Required next data, not a new method

The next operation must change **data coverage**, not the method:

1. generate a fresh H01 physical M1 training bank with explicit wind-context identity matching the actual forward simulator;
2. include many independent wind contexts and transport keys, with complete held-out wind contexts and held-out keys;
3. retain native concentration and persistent-sensor measured traces at 0.2 s; do not reduce to block HIT fractions;
4. train the already frozen factorized first-passage neural field on simulator-only labels;
5. run the same proper-score and source-evidence destructive controls;
6. only after PASS proceed to runtime parity/shadow/closed loop.

This is a data-identifiability/coverage requirement, not permission to invent V8/V9 post-processing.

## Authorization

`CLOSED_LOOP_NOT_AUTHORIZED`

Codex may be used next for reproducible **offline physical bank generation and independent replay**, not for closed-loop performance experiments until all frozen offline gates pass.
