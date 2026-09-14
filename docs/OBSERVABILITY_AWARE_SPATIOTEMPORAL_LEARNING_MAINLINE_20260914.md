# Observability-Aware Spatiotemporal Learning Mainline
# 可观测性感知时空学习主线

Date: 2026-09-14

Branch: `codex/dual-uav-two-point-premise-20260913`

Status: **CANDIDATE MAIN INNOVATION — NOT YET CONFIRMED**

---

## 1. Why this document exists

This document records the next high-level research direction after the recent sequence of negative mechanism tests.

The project must **not** relabel previously tested causal / spatiotemporal representation ideas as a new innovation.

The following family has already been substantially explored and is therefore **not a new main innovation**:

- Causal Spatiotemporal Representation Learning（因果时空表征学习）
- source / transport disentanglement（源 / 输运解耦）
- CTT / SCTT causal-transport trajectory ideas（因果输运轨迹）
- factorized neural first-passage / arrival-phase learning（分解式神经首次到达 / 到达阶段学习）
- simple temporal lag / signed two-point increment / direct source latent representation variants

The new question is different:

> **Do the current spatiotemporal observations actually contain enough information to distinguish competing source hypotheses?**
>
> 当前这段气体—风场—运动时空观测，是否真的包含足够的信息去区分不同源假设？

This changes the learning target from **“what is the source?”** to **“what source information is observable right now?”**.

---

## 2. Evidence that motivates the new learning target

Recent experiments show that the dominant problem is not merely a weak inference model.

Under fixed routes / winds / 150 s horizon, different source interventions can produce:

- extremely weak source separation;
- rank collapse in the source-response operator;
- very small weakest singular directions;
- exact or near-exact source-response collisions;
- source / wind cases with essentially zero exposure;
- temporal effects that can be explained by robot motion revisit rather than plume transport.

Therefore, when

\[
S_i \neq S_j
\]

but

\[
Y(S_i) \approx Y(S_j),
\]

no downstream Transformer, causal encoder, posterior repair, or contrastive objective can reliably reconstruct information that is absent from the measurements.

This is the central physical-learning bottleneck exposed by the previous experiments.

---

## 3. Proposed main theoretical direction

### 3.1 Working name

**Observability-Aware Spatiotemporal Learning for Robotic Gas Source Localization**  
**面向机器人气体源定位的可观测性感知时空学习**

A more specific formulation is:

**Learning Source Distinguishability under Partial Observation**  
**部分观测条件下的源可辨识性学习**

The exact paper title is **not frozen** at this stage.

---

## 4. What is actually learned

The model should **not** directly learn only

\[
X_{1:t} \rightarrow (x_s,y_s).
\]

It should first learn an observation-dependent information state:

\[
X_{t-L:t}
\rightarrow
Z_{\mathrm{obs}},
\]

where the input history can contain

\[
X_{t-L:t}
=
\{c,\;u,\;x,\;v,\;c^+,\;c^-\}_{t-L:t},
\]

including, where available:

- gas concentration（气体浓度）;
- wind（风场）;
- robot position and motion（机器人位置与运动）;
- multi-receiver measurements（多接收器观测）;
- temporal history（时间历史）.

The learned state `Z_obs` should represent **source distinguishability / source observability（源可辨识性 / 源可观测性）**, not source identity alone.

At minimum it should capture information related to:

1. local or windowed information rank（信息秩）;
2. weakest observable direction / singular spectrum（最弱可观测方向 / 奇异谱）;
3. pairwise source distinguishability（源假设两两可辨识程度）;
4. measurement reliability / support（观测可靠性 / 信息支撑）;
5. temporal information support（时间上的有效信息支撑）.

The important capability is that the model is allowed to say:

> **The present observations are insufficient to distinguish these source hypotheses.**
>
> 当前观测不足以区分这些源假设。

This is fundamentally different from always forcing a source estimate.

---

## 5. Training-only privileged supervision

The simulator gives access to information that will not be available online during deployment.

For a fixed route / wind / measurement configuration, multiple source interventions can be generated:

\[
\{Y(S_1),Y(S_2),...,Y(S_K)\}.
\]

These counterfactual source responses can define a **teacher observability signal（教师可观测性监督信号）**.

Possible teacher quantities include:

### 5.1 Pairwise distinguishability

\[
d_{ij}^{(t)}
=
D\left(Y_i^{t-L:t},Y_j^{t-L:t}\right),
\]

forming a source-distinguishability matrix

\[
D_t=[d_{ij}^{(t)}].
\]

### 5.2 Source-response operator geometry

For the source-response operator / centered response matrix, teacher labels may include:

- numerical rank;
- singular values `sigma_1, sigma_2, sigma_3, ...`;
- `sigma_3 / sigma_1` or corresponding weakest-direction ratio;
- source-pair collision indicators;
- exposure support per source and temporal third;
- existing frozen `Q_energy`-style information support quantities.

These labels are **not automatically the final loss**. They are candidate teacher signals that must be evaluated without changing previously frozen definitions after seeing results.

---

## 6. Teacher–student formulation

### Teacher（训练阶段）

Teacher has access to multiple source interventions under the same physical condition:

\[
\{Y(S_1),...,Y(S_K)\}
\rightarrow
Z_{\mathrm{obs}}^*.
\]

### Student（部署阶段）

Student only sees the actually available history:

\[
f_\theta(X_{t-L:t})
\rightarrow
\widehat{Z}_{\mathrm{obs}}.
\]

The core falsifiable question is:

> Can a student infer the current source-distinguishability state from a single physically realizable observation history?

If the answer is no, this candidate main innovation must be rejected rather than rescued by post-hoc tuning.

---

## 7. Difference from previous causal / spatiotemporal representation work

This distinction is mandatory.

| Previous direction | Primary learned / designed object |
|---|---|
| CTT / SCTT | causal / transport trajectory or temporal correspondence |
| source–transport disentanglement | latent source and transport factors |
| neural first-passage | plume arrival / temporal phase |
| signed two-point increment | compressed spatial difference |
| route observability redesign | manually designed route to improve observability |
| **new candidate** | **whether the current measurement history contains distinguishable source information** |

Therefore the new candidate must **not** be described as merely another causal representation model.

---

## 8. Relation to the current C0–C3 sensing-support experiment

The active sensing-support upper-bound experiment remains useful and should **not** be cancelled.

Its role is now clearer:

- `C0`: single-center processed measurement reference;
- `C1`: center raw oracle;
- `C2`: deployable ordered dual-channel processed measurement;
- `C3`: ordered dual-channel raw oracle.

These configurations test which physical measurement constraints alter source observability.

The result should be treated as **mechanism evidence and label-generation evidence**, not as the final main innovation by itself.

Especially:

- if `C2` materially improves observability, multi-channel sensing becomes a load-bearing measurement substrate;
- if only raw-oracle cases improve, sensor dynamics may be the main bottleneck;
- if all remain collapsed, the 150 s sensing-support premise itself is likely insufficient.

No result from C0–C3 alone is allowed to establish the learning innovation.

---

## 9. First learning falsification experiment

Before any large network, closed loop, new GADEN bank, or paper claim, run a small offline falsification.

### Goal

Test whether a model can predict source observability from a single observation history.

### Fixed principle

Use already available source-intervention data first.

Do **not** generate additional simulation merely because the initial learning result is weak.

### Candidate task

Input:

\[
X_{t-L:t}
\]

Target:

\[
Z_{\mathrm{obs}}^*
\]

constructed only from pre-frozen source-response definitions.

### Required baselines

At minimum compare against:

1. constant / mean predictor;
2. gas-only history;
3. gas + wind;
4. gas + wind + motion;
5. if available, ordered two-channel measurement history.

### Mandatory mechanism controls

At minimum include:

- time permutation / temporal shuffle;
- wind permutation where physically meaningful;
- motion-history ablation;
- receiver-channel swap / drop for dual-channel inputs;
- held-out wind or held-out physical condition only after model / label definitions are frozen.

The learning method must demonstrate that the temporal / physical channels it claims to use are actually load-bearing.

---

## 10. Promotion / rejection logic

### Candidate may continue only if

A model trained on allowed design conditions can predict observability / distinguishability substantially better than trivial baselines, **and** the result survives precommitted mechanism controls.

The exact quantitative promotion thresholds must be frozen before aggregate evaluation.

### Immediate rejection conditions

Reject or downgrade this direction if any of the following occurs:

- performance is explained mainly by source-ID leakage or route-ID leakage;
- time shuffle does not damage a model whose claimed mechanism is temporal;
- wind / motion inputs are unused despite claimed physical conditioning;
- success disappears under a precommitted held condition;
- observability labels are effectively constant and therefore not learnable in a meaningful way;
- the model predicts only exposure / zero-hit status and adds no richer distinguishability information;
- performance requires target-source information unavailable during deployment.

Do not rescue a failure by changing labels, windows, rank tolerances, thresholds, source subsets, or held-out conditions after seeing the result.

---

## 11. Current scientific status

### CONFIRMED

- Previous causal / spatiotemporal representation direction has already been explored and cannot be claimed again as a new innovation.
- The recent source-response experiments expose severe observability / distinguishability collapse under some current sensing conditions.
- The previous approximately 5 s phenomenon is compatible with motion-revisit confounding and is not authorized as a plume-transport lag mechanism.
- Route-only redesign did not repair the 150 s single-channel observability collapse in the frozen 12-route test.

### CURRENTLY TESTING

- Sensing-support upper bound across `C0–C3`.

### CANDIDATE IDEA

- Observability-aware spatiotemporal learning / source-distinguishability learning.
- Teacher supervision from multi-source intervention responses.
- Student prediction from a single realizable observation history.

### REJECTED / NOT TO BE RELABELED

- Repackaging causal spatiotemporal representation learning as a new main contribution.
- SCTT as the main innovation.
- Pure signed two-point increment as the main innovation.
- Pure route design as the main innovation.
- Directly adding a larger neural network without proving what information it is learning.

---

## 12. Paper-level claim boundary

At present the following claim is **NOT AUTHORIZED**:

> We have developed a new observability-aware learning method that improves gas source localization.

The only authorized statement is:

> Source observability / distinguishability has emerged as a candidate learning target motivated by prior negative mechanism tests, and must now pass offline falsification before promotion to the paper's main innovation.

No abstract / title / contribution list should present this candidate as confirmed until the learning falsification and held-condition tests pass.

---

## 13. Recommended next handoff to Codex

After the current `C0–C3` sensing-support experiment finishes and its result is audited, the next Codex contract should:

1. freeze one observability teacher-label definition before model fitting;
2. construct the smallest valid offline dataset from already generated source interventions;
3. run simple baseline models before any large neural architecture;
4. test whether temporal, wind, motion, and multi-channel information are actually load-bearing;
5. stop immediately if the learning target cannot be predicted robustly;
6. only after a clean positive result consider integrating the learned observability state into PMFS or a localization policy.

The next stage must therefore answer **“is source observability learnable from deployable observations?”**, not **“can we build a more complex localization network?”**.
