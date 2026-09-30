# OCB-R2 R2B — Dense-Time Joint-Path Amplification Screen

Date: 2026-09-30

Status: **PREREGISTERED DISCOVERY-ONLY / NO NEW GADEN / NO MODEL TRAINING**

Parent clean discovery:
- R0 cross-time stable
- R1 broad-memory required
- R2 candidate-wise broad-memory factor positive
- R2A matched-window Mori-Zwanzig interpretation HOLD

Parent evidence commit:
`e5393356f15f78340939ba959de71ba6cc4189da`

## Why this stage exists

The current positive path signal is scientifically real but practically weak.

A critical limitation has not yet been tested:

> the "temporal" mechanism was discovered from only 10 snapshots spaced 50 s
> apart, although each clean GADEN run contains 1803 native records over about
> 1000 s.

Therefore the current analysis discards the overwhelming majority of temporal
information before asking whether temporal joint structure is useful.

Before generating new Houses, training a density-ratio model, or claiming a
new method, test whether the existing clean H01/H02 data contain a substantially
stronger source-conditioned path signal at an operationally denser cadence.

This is a mechanism-amplification screen, not a new theory search.

## 1. Inputs

Use exactly the same 64 S2+S2X clean discovery runs.

No:
- new GADEN
- new source positions
- confirmation
- House03
- R3A/R3B generation
- neural network
- diffusion/flow/copula model
- hyperparameter search
- source-coordinate tuning

Use the already archived raw clean plumes and the frozen E1 30 source-blind
probe coordinates.

Require exact parent run / generator / occupancy / wind / gas / source / seed
parity.

## 2. Dense observation contract

Freeze primary physical interval:

`50 s <= t <= 300 s`

Freeze requested cadence:

`3 s`

Requested times:

`50, 53, 56, ..., 299 s`

Use the same nearest-native-record rule as the existing OCB-R2 extraction.

Requirements:
- mapping must be strictly increasing;
- no native record may serve two requested times;
- report max and median absolute requested-to-native time error;
- all 64 runs must have the same requested time grid;
- no concentration value may be inspected before the time mapping and E1 probe
  list hashes are frozen.

The 300 s endpoint is chosen because the downstream localization benchmark uses
a 300 s search budget. The 3 s cadence is frozen before extraction and must not
be tuned after seeing results.

## 3. Representation

Primary R2B representation remains **binary encounter only**:

`B[t,q] = 1[C[t,q] > 0]`

Do not use continuous amplitude yet.

Reason:
R2B isolates whether the weak effect came from the extremely sparse 50 s
temporal sampling. Continuous concentration is reserved for a later stage if
R2B does not yield a sufficiently strong amplification.

Tensor shape should be:

`84 x 30`

per run.

## 4. Candidate banks

Exactly as before:

- each context has two source candidates;
- each source has four realizations;
- a target replicate r uses the other three truth realizations;
- the alternative candidate omits the same replicate index r in the primary
  view and uses its remaining three realizations;
- K=3 for both candidates.

Repeat all four alternative 3-of-4 omission views as robustness.

## 5. Full dense-path score

Do **not** average selected lags.

For candidate source s and target y:

### RAW

Use each K=3 reference realization as one intact full path over all 84 time
slots and 30 probes.

Flatten each path to D = 2520 binary coordinates.

Use the same fair-U Energy Score structure as R0, but normalize every Euclidean
distance by `sqrt(D)` so scores are comparable across path lengths:

`d(x,y) = sqrt(HammingCount(x,y) / D)`

`ES_RAW_dense = mean_i d(x_i,y) - [1/(K(K-1))] sum_{i<j} d(x_i,x_j)`

Use the exact fair-U coefficient implemented in R0/R1; only the distance is
dimension-normalized.

### Q-time surrogate

For each candidate source and each time slot independently, permute the K=3
realization labels of the complete 30-D snapshot.

This must preserve exactly:
- each time-specific 30-D snapshot multiset;
- every coordinate marginal at each time;
- K;
- binary support.

It destroys only the realization identity that links one time slot to another.

Use 1000 deterministic surrogates per candidate/target.

Freeze deterministic seed derivation before scoring.

Let:

`ES_Q_dense = median_b ES_Q_dense,b`

Candidate-specific dense path factor:

`E_DENSE(s,y) = ES_Q_dense(s,y) - ES_RAW_dense(s,y)`

Truth-vs-alternative margin:

`Delta_DENSE(y) = E_DENSE(truth,y) - E_DENSE(alt,y)`

Higher is better.

## 6. Frozen sparse reference recomputation

For a fair effect-size comparison, recompute the frozen 10-slot R2 candidate
factor using the same dimension-normalized distance.

Call it:

`Delta_SPARSE10`

This is not a new method; it is only a rescaled reference.

The sign / ordering should remain compatible with the frozen R2 result.
Any substantive mismatch with R2 arithmetic => STOP for implementation audit.

## 7. Observation-budget curves

Without tuning any cutoff, report dense-prefix results for fixed elapsed
durations from the 50 s start:

- 30 s
- 60 s
- 120 s
- 180 s
- full 249 s (through requested time 299 s)

For each prefix, recompute the same RAW/Q candidate factor with identical rules.

These curves are descriptive. The full path is the primary gate.

Purpose:
determine whether joint-path information accumulates early enough to have any
plausible online value, despite the final two-source M-FULL ceiling.

## 8. Primary aggregation

Primary unit:
source x context group, averaging its four held-out targets.

Report:
- 64 target Delta_DENSE values
- target positive count
- 16 group means / medians
- 8 context means
- H01 median
- H02 median
- leave-one-context-out pooled medians
- exact one-sided 8-context sign-flip reference
- max absolute context contribution
- four omission views
- deterministic repeat

## 9. Frozen amplification decision

The frozen R2 primary candidate-factor reference has:
- 53/64 primary targets with positive candidate margin;
- 16/16 positive source x context group means;
- 8/8 positive context means.

### `OCB_R2_R2B_DENSE_PATH_AMPLIFIED`

Use only if all hold:

1. H01 median group Delta_DENSE > 0
2. H02 median group Delta_DENSE > 0
3. 16/16 source x context group means > 0
4. 8/8 context means > 0
5. target-positive count >= 58/64
6. every leave-one-context-out pooled median > 0
7. exact one-sided 8-context sign-flip reference <= 0.01
8. no context contributes >40% of total absolute context effect
9. all four alternative-reference omission views retain positive H01, H02 and
   pooled medians
10. Q-time preservation audit passes
11. two complete computations are byte-identical
12. at least one of the 120 s or 180 s prefix curves already reaches
    >=56/64 positive targets

Interpretation:
the previously weak path mechanism was materially suppressed by sparse temporal
sampling and becomes substantially stronger at a denser, 300-s-compatible
observation cadence.

### `OCB_R2_R2B_DENSE_PATH_STABLE_NOT_AMPLIFIED`

Use if the full dense path remains directionally stable
(H01/H02 positive, >=12/16 groups, >=6/8 contexts) but any amplification
criterion above fails.

Interpretation:
the mechanism exists, but denser binary temporal observation alone does not
make it strong enough to promote as the main method.

### `OCB_R2_R2B_DENSE_PATH_NO_GO`

Use if the dense signal loses cross-House directional stability.

## 10. Scientific interpretation boundary

Do **not** call `E_DENSE` a formal PID/PIRD synergy term.

It is an operational, marginal-preserving source-conditioned temporal
dependence factor.

A formal "synergy" claim requires a later source-target information
decomposition that distinguishes:
- unique information from individual time blocks;
- redundant information;
- information available only jointly.

R2B is intentionally prior to that formalization.

## 11. Important online-observability warning

The E1 operator contains 30 spatial probes per time snapshot.

A UAV with one gas sensor does not observe 30 simultaneous spatial locations.

Therefore even a strong R2B PASS is still **field-level mechanism evidence**,
not a deployable UAV likelihood.

If R2B PASSes, the next stage must test a route-observable / sequential-sensor
version before any closed loop.

## 12. Stop boundary

After exactly one R2B label:

STOP.

Do not:
- use continuous concentration;
- add wind conditioning;
- train a classifier / density ratio;
- open another House;
- generate R3 data;
- open confirmation / H03;
- implement PMFS fusion;
- run closed loop.

Human review chooses the next amplification mechanism.

## 13. Required outputs

- `research/ocb_r2/r2b_dense_path/R2B_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/r2b_dense_path/R2B_INPUT_PARITY.json`
- `evidence/ocb_r2/r2b_dense_path/R2B_TIME_MAPPING.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_TENSOR_HASHES.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_TARGETS.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_GROUPS.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_CONTEXTS.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_PREFIX_CURVES.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_OMISSION_ROBUSTNESS.tsv`
- `evidence/ocb_r2/r2b_dense_path/R2B_QTIME_AUDIT.json`
- `evidence/ocb_r2/r2b_dense_path/R2B_DETERMINISTIC_REPEAT.json`
- `research/ocb_r2/r2b_dense_path/R2B_DECISION_REPORT.md`
