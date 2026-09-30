# OCB-R2 R2 — Projection-Induced Broad-Memory Path Factor

Date: 2026-09-30

Status: **DISCOVERY DEVELOPMENT / METHOD-FREEZE STAGE / NOT CONFIRMATION**

Parent evidence:

- R0: `OCB_R2_MECH_CROSS_TIME_STABLE`
- R1: `OCB_R2_R1_BROAD_MEMORY_REQUIRED`
- exploratory memory probe: history improves future prediction, but naive
  source-specific nearest-history prediction is not stable across both Houses.

## Scientific purpose

Do not build a large neural model.

R2 asks whether the current evidence supports a coherent source-inference
object derived from the proposed mother theory:

> sparse projection of high-dimensional plume dynamics leaves broad temporal
> memory, and source inference should use the part of trajectory compatibility
> that disappears when cross-time realization identity is destroyed while
> each-time spatial snapshot distributions are preserved.

R2 has two separate gates:

1. **MZ-physics support:** does broader observed history improve future
   prediction beyond the current snapshot alone?
2. **Source-inference support:** can a candidate-wise broad-memory path factor
   stably favor the true source across Houses and contexts?

Passing both licenses a new multi-source prospective discovery experiment.
It does not license confirmation/H03 or closed-loop experiments.

## 1. Inputs and seals

Reuse only the frozen 64 S2+S2X discovery tensors:

- 8 matched contexts
- 2 sources/context
- 4 independent realizations/source
- shape `10 x 30`
- encounter definition `C > 0`
- same observation-time mapping and E1 probes as R0/R1

Require exact hash parity with R0/R1 inputs.

No:

- new GADEN
- new PMFS forwards
- new target extraction
- confirmation
- House03
- learned source classifier
- diffusion/flow network
- hyperparameter tuning
- closed loop

If input parity fails: STOP.

## 2. Gate A — projection-memory physics diagnostic

Use the parameter-free nearest-history predictive diagnostic already described
in the exploratory report.

For target trajectory `Y` and a candidate-source K=3 reference bank:

- for history length H, match the target history ending at t to the nearest
  reference history using normalized Hamming distance;
- ties are averaged;
- intact prediction uses the future snapshot from the same matched realization;
- shuffled expectation is the mean future error across all K future
  realization identities.

Define:

`M_s(H) = error_shuffled - error_intact`

Primary physics contrast:

`D_MZ = M_truth(H=3) - M_truth(H=1)`

H=3 is frozen because R1 independently established robust lag-3 source
information and H=3 is the smallest explicitly broad-memory history tested.

Primary group unit: source x context, four held-out realizations averaged.

Gate A = `R2_MZ_MEMORY_SUPPORT` only if all hold:

1. House01 median D_MZ > 0
2. House02 median D_MZ > 0
3. at least 12/16 source-context groups have D_MZ > 0
4. at least 6/8 context means have D_MZ > 0
5. all leave-one-context-out pooled medians > 0
6. exact 8-context one-sided sign-flip reference <= 0.05
7. deterministic repeat byte-identical

H=5 vs H=1 is robustness only and cannot rescue a failed primary gate.

Interpretation boundary:

Passing Gate A is consistent with non-Markovian closure after projection, but
is not a mathematical proof that the underlying projected process is exactly a
Mori-Zwanzig generalized Langevin system.

## 3. Gate B — candidate-wise broad-memory path evidence

For each held-out target `y`, candidate source `s`, and temporal lag
L in {1,2,3}:

1. use the intact K=3 candidate-source lag-pair bank;
2. compute the same fair-U Energy Score as R1:
   `ES_RAW_s,L(y)`;
3. independently permute second-snapshot realization labels exactly as in R1,
   preserving both 30-D snapshot multisets and all each-time spatial
   statistics;
4. compute 1000 shuffled scores and take their median:
   `ES_Q_s,L(y)`.

Define candidate-specific dependence evidence:

`E_s,L(y) = ES_Q_s,L(y) - ES_RAW_s,L(y)`

Higher E means the candidate's intact cross-time dependence explains the
target better than that candidate's own marginal-preserving Q-time reference.

Freeze a broad-memory evidence term with no fitted weights:

`E_BM_s(y) = [E_s,1(y) + E_s,2(y) + E_s,3(y)] / 3`

The true-vs-alternative margin is:

`Delta_BM(y) = E_BM_truth(y) - E_BM_alt(y)`

This is algebraically the equally weighted mean of R1 `I_LAG` for lags 1--3,
but R2 must recompute and export the **candidate-specific** terms rather than
only their pairwise difference.

No lambda, logistic calibration, softmax, learned fusion, or target-dependent
lag weighting is allowed in R2.

Gate B = `R2_SOURCE_CONDITIONED_PATH_FACTOR` only if all hold:

1. House01 median group Delta_BM > 0
2. House02 median group Delta_BM > 0
3. at least 12/16 source-context groups have mean Delta_BM > 0
4. at least 6/8 context means > 0
5. every leave-one-context-out pooled median > 0
6. exact 8-context one-sided sign-flip reference <= 0.05
7. all four alternative-source 3-of-4 omission choices preserve positive
   House01 median, House02 median and pooled median
8. no one context contributes more than 40% of the sum of absolute
   context-level effects
9. all Q-time preservation assertions pass
10. deterministic repeat byte-identical

## 4. Complementarity diagnostics — descriptive, not rescue gates

Because M-FULL already classified 64/64 two-source discovery targets, R2 cannot
claim localization-accuracy improvement.

Report:

- Spearman correlation between group Delta_BM and group M-FULL margin;
- Delta_BM on the bottom quartile of target M-FULL margins, selected using
  baseline margin only;
- Delta_BM separately for fast/slow, gas10/gas13, source identity and House;
- whether broad-memory evidence is positive in both lower and upper halves of
  M-FULL group margins.

These diagnostics answer whether the path term appears complementary rather
than merely duplicating marginal evidence.

They cannot rescue Gate B.

## 5. Frozen R2 decisions

### `OCB_R2_R2_MZ_PATH_FACTOR_DISCOVERY_ADVANCE`

Use only if Gate A and Gate B both pass.

Meaning:

- projected history contains broad predictive memory;
- a source-conditioned broad-memory path factor can extract source evidence;
- the mother-theory direction is coherent enough to justify a new
  **multi-source prospective discovery panel**.

This is not method confirmation.

### `OCB_R2_R2_PATH_FACTOR_ONLY_HOLD_MZ`

Use if Gate B passes but Gate A fails.

Meaning:

path dependence is useful, but Mori-Zwanzig/non-Markovian closure should not be
promoted as the central physical explanation.

### `OCB_R2_R2_MZ_PHYSICS_ONLY_HOLD_INFERENCE`

Use if Gate A passes but Gate B fails.

Meaning:

projection-induced memory is plausible physics, but it is not yet a stable
source-inference term. Do not build a large model to rescue it.

### `OCB_R2_R2_NO_GO`

Use if both fail.

## 6. Stop boundary

After assigning exactly one R2 decision:

- STOP
- do not open confirmation
- do not open House03
- do not generate a multi-source panel automatically
- do not implement diffusion/flow/copula/MERLIN/MZ neural closure
- do not run closed loop

Human review decides whether to authorize the next prospective multi-source
discovery experiment.

## 7. Required outputs

- `research/ocb_r2/r2_broad_memory_path/R2_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/r2_broad_memory_path/R2_INPUT_PARITY.json`
- `evidence/ocb_r2/r2_broad_memory_path/R2_MZ_TARGETS.tsv`
- `evidence/ocb_r2/r2_broad_memory_path/R2_PATH_CANDIDATE_TERMS.tsv`
- `evidence/ocb_r2/r2_broad_memory_path/R2_GROUPS.tsv`
- `evidence/ocb_r2/r2_broad_memory_path/R2_CONTEXTS.tsv`
- `evidence/ocb_r2/r2_broad_memory_path/R2_OMISSION_ROBUSTNESS.tsv`
- `evidence/ocb_r2/r2_broad_memory_path/R2_COMPLEMENTARITY.json`
- `evidence/ocb_r2/r2_broad_memory_path/R2_DETERMINISTIC_REPEAT.json`
- `research/ocb_r2/r2_broad_memory_path/R2_DECISION_REPORT.md`
