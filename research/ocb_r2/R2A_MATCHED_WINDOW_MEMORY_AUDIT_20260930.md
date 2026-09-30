# OCB-R2 R2A — Matched-Window Memory Audit Before Multi-Source Expansion

Date: 2026-09-30

Status: **PREREGISTERED DISCOVERY-ONLY AUDIT / NOT METHOD DEVELOPMENT**

Parent R2 decision:

`OCB_R2_R2_MZ_PATH_FACTOR_DISCOVERY_ADVANCE`

Parent evidence commit:

`85d9f4f3554cdd6c1e7acbd7ffda9cbbdbb085c2`

## Why this audit is required

R2 Gate A compared H1 and H3 predictive-memory gains using different eligible
prediction-time sets:

- H1 used t = 0..8
- H3 used t = 2..8

Therefore the positive H3-H1 contrast mixes two effects:

1. longer observed history;
2. different prediction-time support.

Before using Mori-Zwanzig / projection-induced non-Markovian memory as the
central physical mother theory, remove this ambiguity.

Gate B is not re-opened or re-tuned. This audit concerns only the physical
interpretation of Gate A.

## 1. Inputs

Reuse exactly the same 64 frozen 10x30 binary tensors and metadata as R2.

Require exact parity with:

- R2 input hashes
- R0/R1 observation contract
- encounter threshold C > 0
- same K=3 leave-one-realization-out candidate construction

No new GADEN, no target extraction, no PMFS forward, no confirmation, no H03.

## 2. Common prediction support

Use prediction anchors only:

`t = 2,3,4,5,6,7,8`

for **both** H1 and H3.

Both predict the same future slots:

`t+1 = 3,4,5,6,7,8,9`

For each held-out target and truth-source K=3 reference bank:

### H1-common

Match reference realizations using only snapshot Y[t].

### H3-common

Match reference realizations using the history block:

`Y[t-2:t+1]`

For either H:

- distance = normalized binary Hamming distance
- ties averaged
- intact future error = future error from the same matched realization identity
- shuffled future error = mean error across all three future realization identities

Define:

`M_common(H) = mean_t(error_shuffled - error_intact)`

and the primary contrast:

`D_MZ_COMMON = M_common(H3) - M_common(H1)`

This now changes only available history length, not evaluated future times.

## 3. Primary aggregation

Primary unit:

source x context group, averaging its four held-out target realizations.

Report:

- 64 target values
- 16 source x context group means/medians
- 8 context means
- H01 median
- H02 median
- fast/slow
- gas10/gas13
- leave-one-context-out pooled medians

## 4. Frozen decision gate

### `OCB_R2_R2A_MZ_MATCHED_WINDOW_PASS`

Use only if all hold:

1. House01 median group D_MZ_COMMON > 0
2. House02 median group D_MZ_COMMON > 0
3. at least 12/16 source-context group means > 0
4. at least 6/8 context means > 0
5. every leave-one-context-out pooled median > 0
6. exact one-sided 8-context sign-flip reference <= 0.05
7. deterministic repeat byte-identical

Interpretation:

broad history improves future prediction beyond the current projected state on
identical prediction-time support. This strengthens the projection-induced
memory / non-Markovian-closure interpretation.

It still does not prove an exact Mori-Zwanzig generalized Langevin equation.

### `OCB_R2_R2A_MZ_MATCHED_WINDOW_HOLD`

Use if the pooled effect remains positive but any stability condition above
fails.

Interpretation:

retain broad-memory path dependence as the inference mechanism, but do not use
Mori-Zwanzig as the central physical claim yet.

### `OCB_R2_R2A_MZ_MATCHED_WINDOW_NO_SIGNAL`

Use if the common-support effect is non-positive overall or reverses in one
House.

Interpretation:

R2 Gate B remains valid as path-dependence evidence, but the previous Gate-A
physical interpretation was partly attributable to time-support mismatch.
Downgrade Mori-Zwanzig to inspiration only.

## 5. Secondary checks

Descriptive only:

- H2-common using history Y[t-1:t+1] on the same t=2..8 anchors
- monotonicity of median M_common(H1), M_common(H2), M_common(H3)
- per-anchor D_MZ_COMMON to detect one-time-slot dominance

These cannot rescue the primary gate.

## 6. Stop boundary

After the R2A label:

- STOP
- do not generate the multi-source panel automatically
- do not design/freeze new source coordinates using plume outcomes
- do not open confirmation/H03
- do not train any model
- do not run closed loop

If PASS, the next authorized task is **geometry-only design and freeze** of a
new prospective multi-source discovery panel.

## 7. Required outputs

- `research/ocb_r2/r2a_matched_memory/R2A_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/r2a_matched_memory/R2A_INPUT_PARITY.json`
- `evidence/ocb_r2/r2a_matched_memory/R2A_TARGETS.tsv`
- `evidence/ocb_r2/r2a_matched_memory/R2A_GROUPS.tsv`
- `evidence/ocb_r2/r2a_matched_memory/R2A_CONTEXTS.tsv`
- `evidence/ocb_r2/r2a_matched_memory/R2A_ANCHOR_EFFECTS.tsv`
- `evidence/ocb_r2/r2a_matched_memory/R2A_DETERMINISTIC_REPEAT.json`
- `research/ocb_r2/r2a_matched_memory/R2A_DECISION_REPORT.md`
