# TS-P3T-H0R — Exact source-update snapshot-difference temporal-closure test

Date: 2026-10-01
State: FINAL PRE-REGISTRATION / OFFLINE ONLY

Parent:
\`TS_P3T_H0_INVALID_STOP\`

H0-R is a new experiment. It does not repair, replace or reinterpret H0's INVALID decision.

## 1. Scientific question

Does the mismatch between long-accumulated PMFS observation memory and a short stateless candidate forward materially harm source inference?

The test uses an **exact** observation state from the final PMFS source-update interval rather than an approximate 40 s reconstruction.

## 2. Frozen cases

Exactly:
- House01_seed0_off_off
- House01_seed1_off_off
- House02_seed0_off_off
- House02_seed1_off_off

Use only the authoritative TNQC archive already verified by H0 P0.

For each case use:
- source_update_0004/measured_hit_probability.csv
- source_update_0005/measured_hit_probability.csv
- source_update_timing.csv
- the same occupancy/grid metadata and frozen parameters.

No substitute run is allowed.

## 3. Observation arms

### FULL
Archived update5 measured map, unchanged.

### RECENT
Exact update4 -> update5 contribution reconstructed by snapshot differencing.

For every free cell:

\[
L_R=L_0+(L_5-L_4)
\]

\[
\omega_R=\omega_5-\omega_4
\]

\[
c_R=1-\exp(-\omega_R/\sigma_\omega^2).
\]

Probability is the exact logistic transform of \(L_R\).

Use the frozen prior and \(\sigma_\omega=\) \`confidenceMeasurementWeight\` from historical configuration.

Do not derive RECENT by subtracting probabilities or confidences.

## 4. Integrity gates

Before source truth is opened:

1. update4/update5 map support, metadata and occupancy are identical;
2. \(\omega_5-\omega_4 >= -1e-12\) for every free cell; values in [-1e-12,0) may be clamped to zero only as floating-point cleanup and must be counted;
3. recomposition must recover update5:
   - \(L_4 + (L_R-L_0)=L_5\) to <=1e-12;
   - \(\omega_4+\omega_R=\omega_5\) to <=1e-12;
   - confidence recomputed from \(\omega_5\) matches archived confidence to <=1e-12;
4. exact final-interval duration is update5_time - update4_time and is not tuned;
5. no truth coordinate is read during reconstruction/scoring;
6. candidate prediction bytes/hashes are frozen before evaluation.

Failure -> \`TS_P3T_H0R_INVALID_STOP\`.

## 5. Candidate prediction arms

Do not run any new forward.

Primary:
- P3 saved point-3D candidate hit maps;
- G3 saved Gaussian-3D candidate hit maps.

Controls:
- P2;
- G2.

Use exactly the saved D0 candidate prediction maps. If a map archive must be extracted, verify against the D0 SHA256 manifest.

For each observation arm and candidate, recompute the unchanged PMFS score:

\[
\ell(s)=\sum_i
\log\left[
1-c_i\,|p_i-\hat p_i|\,D
\right],
\]

where \(D\) is frozen sourceDiscriminationPower, \(p_i\) is measured hit probability and \(\hat p_i\) is candidate simulated hit probability.

## 6. Source-blind diagnostics

Freeze before truth evaluation:

Per case:
- update4 and update5 times;
- RECENT duration;
- total terminal omega and RECENT omega;
- \(\sum_i\omega_{4,i}/\sum_i\omega_{5,i}\): fraction of terminal additive confidence evidence inherited from before the final update;
- number/fraction of free cells whose RECENT confidence is >0;
- FULL-vs-RECENT probability/logOdds field L1 and cosine;
- Spearman candidate-score/rank correlation FULL vs RECENT for P3 and G3;
- all candidate scores for all four arms.

## 7. Truth evaluation

After score freeze report, for P3 and G3 under FULL and RECENT:

- truth log score;
- truth midrank and pessimistic rank;
- truth-vs-best-wrong margin;
- truth tie count;
- top-5 candidate IDs.

Also report P2/G2 descriptively.

## 8. Frozen gate

A case is a temporal-closure improvement for an arm if all three hold:

- RECENT truth log score > FULL truth log score;
- RECENT truth midrank < FULL truth midrank;
- RECENT source margin > FULL source margin.

### Primary gate: G3

\`H0R_G3_SIGNAL\` requires:
- >=3/4 cases improve by the conjunction above;
- median truth-rank improvement >=10 positions;
- median margin change >0;
- no more than one case has worse truth rank.

### Representation robustness: P3

P3 must show the same direction in >=3/4 cases for truth rank and margin.

### Decision

- integrity fail:
  \`TS_P3T_H0R_INVALID_STOP\`

- G3 primary passes AND P3 robustness passes:
  \`TS_P3T_H0R_TEMPORAL_STATE_MISMATCH_SIGNAL\`

- G3 passes but P3 robustness fails, or exactly 2/4 G3 cases improve:
  \`TS_P3T_H0R_HOLD_REPRESENTATION_INTERACTION\`

- otherwise:
  \`TS_P3T_H0R_NO_RECENCY_SIGNAL_STOP\`

## 9. Interpretation

PASS establishes:

> the long-memory observation state is materially less compatible with the short stateless candidate forward than the exact final-update observation increment.

It does not establish that old observations should be discarded.

PASS authorizes H1 only:

> compare a full-history persistent transport-state oracle against the RECENT forgetting baseline.

H1 must show that preserving/evolving hidden transport state beats simply forgetting history; otherwise a world-model claim is not justified.

A STOP means this archived stateless forward does not show the needed recency signature. It does not prove all persistent-state approaches impossible, but this evidence chain stops.

## 10. Execution boundary

No new GADEN.
No new forward.
No training.
No H03/confirmation.
No closed loop.
No parameter/window tuning.
STOP after H0-R decision.
