# Candidate Mainline — Source-Conditioned Stochastic Path Action

Date: 2026-09-24  
Branch: `research/path-action-source-inference-v0`

Status: **EXPLORATORY SIGNAL FROZEN — FRESH S3 CONFIRMATION REQUIRED**

## 1. Failure inherited from the stopped MZ route

D3 falsified the global mass-normalization assumption.

Across the 630-source bank, independent prediction-realization variability is source-conditioned and heteroscedastic:

- relative C/D discrepancy range: ~1.5% to 57.5%;
- median: ~15.3%;
- Spearman correlation between relative variability and mean plume mass: ~-0.50;
- S1: low-variability regime (~7.9%);
- S2: more stochastic regime (~18.0%).

Therefore one observable component can be source-discriminative in one region and realization-dominated in another.

The new problem is:

> Compare source hypotheses under source-conditioned stochastic path distributions without globally deleting amplitude, morphology, or memory information.

## 2. Far-domain mother theory

The candidate mother idea is the **path-action / large-deviation viewpoint of nonequilibrium statistical physics**, especially Onsager–Machlup-type path probabilities.

The key conceptual shift is:

- deterministic fitting asks how close an observed trajectory is to a single mean path;
- path-action inference asks how probable the **entire observed path** is under each candidate stochastic process.

For heteroscedastic stochastic dynamics, deviation in a low-noise direction should be penalized strongly, while the same numerical deviation in a high-noise direction should be penalized weakly.

Recent relevant theory directions include:

- 2026 goal-oriented learning of stochastic differential equations using error bounds on path-space observables (Zou, Lie, Marzouk; arXiv:2603.20467);
- 2026 Onsager–Machlup work for stochastic transition paths / early warning;
- classical Onsager–Machlup / Freidlin–Wentzell / large-deviation action theory.

Prior-art boundary: parameter inference with Onsager–Machlup ideas exists outside GSL. The candidate novelty, if it survives fresh validation, is a **source-position-indexed stochastic path action used directly as the PMFS source likelihood**.

## 3. Frozen exploratory proxy

For each candidate source (s), the existing two independent prediction realizations C/D define

[
\mu_{s,k}=\frac{x^C_{s,k}+x^D_{s,k}}{2},
]

[
v^{local}_{s,k}=\frac{(x^C_{s,k}-x^D_{s,k})^2}{2}.
]

A source-independent unresolved-noise floor is computed before looking at a target:

[
\bar v_k = \frac{1}{N}\sum_s v^{local}_{s,k}.
]

The frozen variance used for the first confirmation gate is

[
v_{s,k}=v^{local}_{s,k}+\bar v_k.
]

No mass normalization is applied.

For observed raw concentration path (y), define the discrete heteroscedastic path-action proxy

[
A(s;y)=\sum_k
\left[
\frac{(y_k-\mu_{s,k})^2}{v_{s,k}+10^{-12}}
+
\log(v_{s,k}+10^{-12})
\right].
]

This is a diagonal Gaussian path-action / negative-log-likelihood proxy. It is **not yet claimed as the final Onsager–Machlup functional**.

## 4. Exploratory-only result on already-seen S1/S2 targets

Because the formula was discovered after inspecting S1/S2 failures, these targets are discovery data only.

Nevertheless, as an exploratory sanity check:

- S1_A: rank 1;
- S1_B: rank 1;
- S2_A: rank 1;
- S2_B: rank 1.

The result remains 1/1/1/1 when the global noise-floor multiplier is varied from 0.05 through 4.0. The confirmation formula is frozen at multiplier 1.0 because it is the unmodified additive local+global variance definition.

This robustness sweep is not confirmatory evidence.

## 5. Fresh S3 source selection — target blind

S3 is selected before generating any new target.

Selection rule:

1. exclude candidates within 2.0 m of S1 or S2;
2. compute for every candidate:
   - relative C/D discrepancy;
   - log mean path mass;
3. compute the global medians and median absolute deviations of those two quantities;
4. select the eligible candidate minimizing squared robust standardized distance to both medians.

This chooses a typical stochastic regime rather than an extreme/easy case.

Frozen result:

- source id: `pmfs_3_12`;
- xyz: `(-4.34273, -3.70088, 0.20)`;
- prediction C/D relative discrepancy: ~0.15391;
- global median discrepancy: ~0.15269;
- distance to S1: ~2.58 m;
- distance to S2: 6.60 m.

## 6. Fresh target seeds

Generate exactly two new independent W2 targets:

- S3_W2_E: seed `2026092403`;
- S3_W2_F: seed `2026092404`.

Prediction bank remains unchanged:

- C = 2026092401;
- D = 2026092402.

No target from S1 or S2 may be used to alter the formula after this freeze.

## 7. Frozen controls

For each target report:

1. raw exact-forward SSE rank;
2. homoscedastic Gaussian path score rank;
3. heteroscedastic residual-only rank (same variance, omit log variance);
4. full frozen path-action rank.

## 8. Fresh confirmation gate

PASS requires both E and F:

- full path-action truth rank <= 3;
- full path-action rank sum <= raw rank sum;
- full path-action rank sum <= homoscedastic rank sum;
- full path-action rank sum < heteroscedastic-residual-only rank sum OR full path-action is rank 1 on both targets.

PASS:

`PASI_D0_PASS_FRESH_S3_PATH_ACTION_SIGNAL`

Any failure:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

No rescue or coefficient tuning after target ranks are observed.

## 9. Scope

Even a PASS establishes only a fresh offline mechanism signal in House02/W2.

Before any PMFS closed loop, the route must still survive:

- another source / different stochastic regime;
- cross-House or cross-wind evidence;
- a practical online approximation that does not require full exact-GADEN ensembles per candidate.
