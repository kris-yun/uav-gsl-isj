# AUX PRO ASSIGNMENT — After Track A/B Review, Before D1C

Date: 2026-09-25

Role:
auxiliary theory / literature / red-team expert.

The primary thread has digested your four memos and accepts the main warnings.

## Mainline decision

Track B remains the current main-innovation candidate, but the claim is narrowed to:

**causal-emergence-inspired multiscale statistical source identifiability**

Do NOT yet call the GSL mechanism “causal emergence” as an established fact.

The primary thread accepts your points that:

- a fixed unknown source cell is not a physical Markov microstate;
- deterministic coarse-graining cannot create Shannon information under the same prior;
- uniform-macro EI / macro accuracy can be a changed-task artifact;
- the final endpoint must return to the same microcell support, same source prior, and fresh-target proper scoring;
- any benefit must come from finite-sample estimation/generalization risk reduction while unresolved within-basin uncertainty remains explicit.

Track A is frozen as a possible auxiliary observation model. Do not continue broad A/B competition unless the primary thread asks.

## Codex is now doing only D1R

Codex is authorized to construct:

- 168 dense source microcells;
- 16 fresh reference realizations/source;
- 2688 total House02/W2 simulations;
- no final targets;
- no partition choice;
- no scientific PASS/STOP.

While D1R is running, prepare the exact theory and analysis contract that the primary thread will apply to the returned reference bank.

## Task 1 — make B14/B24 operational without target leakage

Turn the memo’s statistical-identifiability idea into an implementable reference-only selection procedure.

Specify:

1. the exact legal observation channel(s);
2. the fixed microcell prior;
3. how a candidate hard partition g is learned from reference only;
4. how macro probability is lifted back to microcells with mass conservation;
5. the exact microcell proper score used for model selection and later D1C;
6. the reference-only cross-fitting scheme using 16 realizations/source;
7. what may be tuned on references and what must remain fixed before targets.

Do not use final targets to choose K, partition, smoothing, calibration, temperature, probability floor, or model family.

## Task 2 — define a finite search family, not an impossible global optimum

For the 168-cell dense region, compare a small preregistrable set of partition families:

- identity;
- all-in-one negative control;
- connected geometry-only hierarchy;
- encounter-profile clustering with connectedness constraints;
- size-matched random partitions;
- ordinary hierarchical pooling / shrinkage;
- one causal-emergence-inspired / information-fidelity construction if mathematically distinct.

For each:
- exact algorithm;
- search/tuning budget;
- deterministic/random seed policy;
- computational complexity;
- baseline versus innovation role.

The final paper cannot claim a global optimum over all partitions.

## Task 3 — partition stability and fidelity contract

Derive implementable reference-only metrics for:

- VI and ARI between partitions learned on independent reference halves;
- co-membership uncertainty;
- within-group information loss / fidelity loss;
- group connectedness and wall crossing;
- size / area / diameter;
- whether stable amplitude information is removed by encounter-only grouping.

Recommend principled tolerances/ranges, while separating:
- theory-motivated bounds;
- engineering defaults;
- values that the primary thread must freeze.

Do not invent thresholds from previous failures.

## Task 4 — proper-score confirmation and effect-size logic

For future locked targets, derive:

Delta_B = (1/N) sum_s (1/J_s) sum_r log2[ q_g*(s|y_sr) / q_identity(s|y_sr) ].

Explain:

- why this is the correct same-task comparison;
- how to form uncertainty intervals without treating 300 coordinates as independent;
- whether source is the primary resampling unit, realization nested within source, or both;
- how to choose a minimum meaningful effect delta_B before target generation;
- how calibration non-inferiority should be defined;
- how exact rank / MAP distance / 0.5 m / 1.0 m mass stay diagnostics instead of alternative primary endpoints.

Do NOT assign final numeric PASS thresholds unless independently justified.

## Task 5 — strongest ordinary-baseline attack

The key red-team question is:

> Is the entire apparent “emergent source scale” explainable by ordinary Bayesian pooling, hierarchical shrinkage, MDL, or profile clustering?

Build the strongest versions under equal:
- reference budget;
- observation input;
- source prior;
- model-selection budget;
- microcell support.

State exactly what empirical result would be required before the stronger causal-emergence-inspired interpretation remains useful.

## Task 6 — naming and paper-claim boundary

Prepare two paper-safe framings:

Conservative:
“multiscale statistical source identifiability under stochastic plume realizations”

Stronger conditional:
“causal-emergence-inspired source macrostates”

For the stronger wording, list evidence required beyond D1C before using “causal emergence” in the title/abstract.

Pay special attention to:
- observation-protocol dependence;
- cross-wind / cross-House reproducibility;
- same-prior micro/macro information accounting;
- avoiding a fake source-transition matrix.

## Deliver only

1. D1R_TO_D1C_OPERATIONAL_THEORY.md
2. PARTITION_SEARCH_AND_BASELINES.md
3. D1C_PROPER_SCORE_AND_POWER.md
4. CAUSAL_EMERGENCE_CLAIM_BOUNDARY.md
5. one short primary-thread decision checklist.

Do not run experiments.
Do not generate targets.
Do not revive Track A as a competing mainline.
Do not change R0 or D1R.
