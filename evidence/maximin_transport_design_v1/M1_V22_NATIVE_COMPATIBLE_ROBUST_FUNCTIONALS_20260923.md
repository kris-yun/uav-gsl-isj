# M1 v2.2 — Native-compatible robust source scoring and robust candidate variance

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Status: algebraically derived; empirical gate waits for repaired Native baseline

## 1. Why this revision

The official PMFS implementation already has two central ingredients:

1. source scoring by a product of per-cell agreement between measured and simulated hit probability;
2. movement driven by the weighted variance of candidate-source simulated hit probabilities.

Therefore the cleanest first implementation of transport ambiguity is **not** to replace PMFS with a different likelihood or a new information-theory reward.

Instead, transport ambiguity turns each nominal candidate hit value

\[
h_{s,i}
\]

into an admissible interval

\[
h_{s,i}\in[\ell_{s,i},u_{s,i}],
\]

and then robustifies the existing PMFS functionals.

At zero ambiguity, every formula below collapses exactly to ordinary PMFS.

## 2. Native PMFS per-cell compatibility

For source candidate s and map cell i, define:

- measured hit probability: m_i;
- measured-map confidence: c_i in [0,1];
- PMFS source discrimination power: gamma;
- simulated hit probability: h_{s,i}.

The ordinary PMFS source factor is

\[
a_{s,i}(h)=1-c_i\gamma |m_i-h|.
\]

Ordinary candidate score:

\[
S_s=\prod_i a_{s,i}(h_{s,i}).
\]

## 3. Robust compatibility from a transport-induced hit interval

Given

\[
h_{s,i}\in[\ell_{s,i},u_{s,i}],
\]

the smallest and largest possible absolute mismatch are

\[
d^{min}_{s,i}=dist(m_i,[\ell_{s,i},u_{s,i}])
\]

and

\[
d^{max}_{s,i}=\max(|m_i-\ell_{s,i}|,|m_i-u_{s,i}|).
\]

Hence

\[
a^-_{s,i}=1-c_i\gamma d^{max}_{s,i},
\qquad
a^+_{s,i}=1-c_i\gamma d^{min}_{s,i}.
\]

Under the Level-A rectangular relaxation across cells,

\[
S^-_s=\prod_i a^-_{s,i},
\qquad
S^+_s=\prod_i a^+_{s,i}.
\]

Interpretation:
- S^-_s: pessimistic compatibility of source s;
- S^+_s: optimistic compatibility of source s.

This interval is an outer relaxation because physically valid transport perturbations couple cells. Arbitrary endpoint choices at every cell may not be jointly realizable. That conservatism is acceptable for Level-A falsification but must not be confused with the final transition-native ambiguity set.

## 4. Source probability bounds

If candidate-score uncertainty is represented by boxes S_s in [S^-_s,S^+_s], then

\[
\underline{\pi}_s=
\frac{S^-_s}{S^-_s+\sum_{j\neq s}S^+_j},
\qquad
\overline{\pi}_s=
\frac{S^+_s}{S^+_s+\sum_{j\neq s}S^-_j}.
\]

At zero ambiguity, these exactly collapse to the normalized ordinary-PMFS candidate score.

For F1 only, predeclare the conservative ranking statistic as lower posterior bound \underline{\pi}_s. Report upper bound and interval width as diagnostics. Do not switch the ranking statistic after seeing truth.

## 5. Robustification of the actual PMFS movement quantity

The active ordinary-PMFS movement code uses weighted candidate-source variance of simulated hit probabilities.

Let w_s be normalized current source weights and h_s(x) the candidate-source hit probability at proposed cell x.

Ordinary weighted variance is

\[
V_0(x)=\sum_s w_s(h_s(x)-\mu(x))^2,
\qquad
\mu(x)=\sum_s w_s h_s(x).
\]

Under transport ambiguity, h_s(x) is in [\ell_s(x),u_s(x)].

Define robust separability variance

\[
V_{rob}(x)=
\min_{q_s\in[\ell_s,u_s]}
Var_w(q_s).
\]

This asks how much candidate-source separation is guaranteed to remain if nature can move each candidate prediction anywhere inside its admissible transport interval.

Weighted variance obeys

\[
Var_w(q)=\min_c\sum_s w_s(q_s-c)^2.
\]

Therefore

\[
V_{rob}=
\min_c\sum_s w_s\,dist(c,[\ell_s,u_s])^2.
\]

For fixed c,

\[
q_s^*(c)=clip(c,\ell_s,u_s).
\]

The remaining optimization is one-dimensional, convex and piecewise quadratic. A minimizer c^* can be found by bisection of

\[
g(c)=\sum_s w_s(c-clip(c,\ell_s,u_s)).
\]

Then q_s^*=clip(c^*,\ell_s,u_s) and V_rob=Var_w(q^*).

### Limiting cases

**Zero ambiguity:** if \ell_s=u_s=h_s for every source, V_rob=V_0.

**Common intersection:** if all source intervals share a common value, nature can make all candidate hit probabilities equal, hence V_rob=0.

This is exactly the desired response to the previously observed pathology: a cell may look highly discriminative under the nominal simulator but have zero guaranteed source separability once admissible forward error is acknowledged.

## 6. PMFS-native movement integration

For the first implementation, preserve all ordinary PMFS movement machinery and replace only

\[
varianceOfHitProb(x)
\]

with

\[
V_{rob}(x).
\]

Keep:
- current hit-map confidence multiplier (1-confidence);
- exploration phase;
- visibility/open/closed move sets;
- navigation feasibility;
- official stochastic exploration probability;
- strict-Native movement semantics, including any parity quirks documented separately.

The movement change is therefore a downstream consequence of the transport ambiguity set, not an independent handcrafted policy.

## 7. Three coupled outputs from one main idea

The same transport-induced interval family affects:

1. forward model: h_{s,i} -> [\ell_{s,i},u_{s,i}];
2. source inference: S_s -> [S^-_s,S^+_s] -> [lower pi_s, upper pi_s];
3. active movement: V_0(x) -> V_rob(x).

If only movement is changed, reject the method as a score/reward patch.

## 8. Novelty boundary

Do NOT claim:
- first uncertainty-aware source map;
- first Dempster-Shafer / interval source map;
- first robust path planning;
- first Renyi/alternative-information OSL;
- first model-mismatch-aware GSL.

The main claim under test is:

> A PMFS-style online gas-source localizer can represent forward-model misspecification at the stochastic transport-law level, propagate that ambiguity into candidate-source support, and move according to source separability that survives admissible transport perturbations.

## 9. F0 algebra gates

Must pass before repaired-baseline data:

1. zero-width hit intervals reproduce ordinary PMFS normalized source probabilities;
2. zero-width intervals reproduce ordinary weighted candidate variance;
3. widening intervals cannot make V_rob exceed nominal variance;
4. common overlap of all candidate hit intervals gives V_rob=0;
5. all source lower bounds are <= corresponding upper bounds;
6. no truth information enters any calculation.

## 10. F1 repaired-baseline frozen replay

For every repaired House/seed snapshot:

### Inference arm

Compare:
- native PMFS point score;
- robust lower-posterior score using a predeclared observation-law radius panel.

Primary endpoint: **truth-containing candidate rank**.

### Movement arm

Compare cell rankings:
- ordinary PMFS candidate variance;
- V_rob.

Then replay the same measurement budget/subset logic to test whether robustly separable cells improve subsequent truth rank.

Required positive signature:
- repeated truth-rank improvement across independent plume realizations;
- robust movement specifically avoids cells that are nominally high variance but whose candidate hit intervals overlap;
- effect strengthens under deliberate forward mismatch;
- effect shrinks toward native PMFS in the matched/zero-radius limit.

No endpoint-only rescue and no truth-tuned radius.

## 11. Relationship to error de-amplification

AISTATS 2026 R-IDeA provides a mechanism hypothesis: nominally informative active designs can amplify model misspecification.

We do NOT transplant its acquisition score.

Instead, after F1, test whether cells rejected by V_rob are exactly those where nominal PMFS shows the strongest simulator-vs-real discrepancy amplification.

If so, R-IDeA is supporting theory/mechanism evidence, not a separate module.
