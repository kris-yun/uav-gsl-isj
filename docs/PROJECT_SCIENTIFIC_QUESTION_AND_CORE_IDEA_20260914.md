# Scientific Question and Core Idea

Date: 2026-09-14

## 1. The scientific question is no longer 'how do we improve the posterior?'

The project has tested multiple increasingly sophisticated ways of processing essentially the same gas/wind observation stream. The recurring pattern is that some representations improve selected cases, but source identity remains unstable across environments, winds, candidate supports, or seeds.

The current scientific question is therefore:

> **Under turbulent transport, intermittent exposure, obstacles, and slow sensor dynamics, how should a mobile robot design its sensing trajectory or multi-robot measurement geometry so that physically different source locations generate sufficiently distinct observations across transport regimes before source inference is performed?**

This is an **observability / experiment-design / inverse-problem question**.

It is upstream of Bayesian updating.

## 2. Failure mechanism currently supported by evidence

For a fixed measurement design `R`, let the processed response from source hypothesis `s` under transport regime `w` be

\[
y_{s,w}(R)\in\mathbb R^T.
\]

Stack `S` source interventions:

\[
Y_w(R)=
\begin{bmatrix}
y_{1,w}^T\\
\vdots\\
y_{S,w}^T
\end{bmatrix}.
\]

Remove the source-common component:

\[
C_w(R)=P_SY_w(R),
\qquad
P_S=I-\frac1S\mathbf1\mathbf1^T.
\]

For four source hypotheses, the maximum source-contrast rank is three.

The project repeatedly sees the following state:

```text
numerical rank = 3
but sigma3 << sigma1
```

That means the third source direction technically exists but has negligible physical energy relative to the dominant source contrast. The inverse problem is therefore practically ill-conditioned.

The latest synchronized dual-UAV test is a particularly clean example:

```text
SIGNED_INCREMENT sigma3/sigma1
W_fast    = 0.001345
W_slow    = 0.000683
W_altfast = 0.001384
```

The route also produces highly unequal exposure among source interventions. The issue is therefore not simply posterior weighting; the measurement operator itself does not provide balanced information about all source directions.

## 3. Core candidate idea

Working name:

# Transport-Robust Persistent-Excitation Sensing
# 输运鲁棒持续激励感知

### Plain-language version

Do not let the robot collect an arbitrary trajectory and then hope the inference algorithm can rescue ambiguous measurements.

Instead:

> **actively choose where and how to sense so that every plausible source direction produces a measurable and different physical response, and require this distinction to survive more than one transport regime.**

Only after this condition is satisfied should PMFS accumulate source probability.

## 4. Mathematical object

Define the per-transport conditioning ratio

\[
\gamma_w(R)
=
\frac{\sigma_{S-1}(C_w(R))}{\sigma_1(C_w(R))}.
\]

For four sources, this becomes

\[
\gamma_w(R)=\frac{\sigma_3}{\sigma_1}.
\]

The primary robust design target is

\[
J_{cond}(R)=\min_{w\in\mathcal W_{design}}\gamma_w(R).
\]

But shape conditioning alone is insufficient. The weakest source direction must also have non-negligible physical amplitude. Therefore retain an energy criterion such as the existing

\[
Q_{energy}
=\frac{\lambda_3\left(\sum_l R_lR_l^T\right)}{\lambda_1\left(\sum_l R_lR_l^T\right)}.
\]

A route may qualify only when it also satisfies source exposure, temporal coverage, collision-free motion, and real deployment constraints.

A future continuous formulation can replace the finite source bank with a local sensitivity/Jacobian:

\[
J_S(R,w)=\frac{\partial y(R,w;s)}{\partial s},
\]

and optimize the smallest singular value / Fisher-information eigenvalue. That is not yet authorized because current evidence is based on the finite controlled source bank.

## 5. Why this is scientifically different from existing PMFS planning

Classic PMFS-style planning usually asks questions such as:

- where is source probability high?
- where is map uncertainty high?
- which move is likely to improve the posterior?
- how should exploration/exploitation be balanced?

The current candidate asks a different upstream question:

> **Does the planned measurement make the source parameter physically identifiable at all?**

The algorithm should not reward a route merely because it changes posterior entropy if the corresponding source-response operator is nearly rank-collapsed.

The target is therefore not only 'informative on average'. It is **worst-direction source observability across transport regimes**.

## 6. Why this maps to a big-science theory rather than a cosmetic algorithm change

### A. System identification — persistent excitation

In system identification, parameters cannot be reliably identified unless the experimental input excites the relevant modes. Persistent excitation formalizes this requirement.

Our translation is:

```text
control input / excitation trajectory
        -> UAV sensing trajectory / formation
unknown system parameters
        -> source location
measured system response
        -> gas sensor time series
insufficient excitation
        -> source-response rank collapse
```

The new contribution would be the translation from dynamical-system parameter excitation to **source-location excitation under stochastic transport**.

### B. Optimal Experimental Design (OED)

OED treats sensor locations, sampling schedules, or experimental inputs as design variables rather than fixed conditions.

Our specific twist is not generic EIG maximization. It is a robust source-observability target:

\[
\max_R\min_w\sigma_{min}(C_w(R))
\]

or its normalized/energy-constrained form.

### C. Inverse-problem measurement design

The underlying problem is an inverse map

\[
\text{source}\rightarrow\text{transport}\rightarrow\text{sensor response}.
\]

When the measurement operator maps different sources to nearly identical responses, a more sophisticated inverse solver cannot recover information that was never measured.

The scientific strategy is therefore to redesign the measurement operator.

## 7. Current secondary innovation candidate

If one trajectory cannot satisfy the persistent-excitation gate, the strongest current secondary-module candidate is:

# Collective Multi-Trajectory Informativity
# 多轨迹集体可辨识性

Two UAVs should not be used as two redundant PMFS agents or as a fixed difference pair. Instead, choose complementary trajectories `R1` and `R2` so that their **stacked measurement operator** is collectively informative:

\[
C_w^{joint}
=
\left[C_w(R_1)\; C_w(R_2)\right].
\]

Then optimize

\[
\max_{R_1,R_2}
\min_w
\frac{\sigma_3(C_w^{joint})}{\sigma_1(C_w^{joint})}.
\]

The scientific meaning is:

> one trajectory may fail to excite one source mode, while another trajectory can supply the missing mode; the team is designed to be collectively persistently exciting.

This is a much stronger and more principled use of two UAVs than ordinary belief fusion or signed concentration difference.

It is only a candidate. It is authorized only if the single-route observability study shows that one feasible trajectory cannot provide adequate conditioning but complementary trajectories can.

## 8. Biophysical candidate that remains outside the main line

2026 Nature work on Drosophila plume navigation reports that flies use plume boundaries as dynamic landmarks and maintain directional memory of the plume edge rather than simply following absolute concentration.

This may eventually motivate a physically interpretable route prior:

```text
seek/revisit high-contrast plume boundaries
```

because boundary transitions may provide stronger spatial excitation than plume-core sampling.

However, this is currently only a route-generation hypothesis. It must not be promoted to a contribution until:

1. the observability-first principle passes;
2. boundary-seeking demonstrably increases weakest source-mode observability;
3. existing plume-edge / casting / infotaxis literature is screened for novelty collision.

## 9. What 'causal' means now

Causal language is no longer the main innovation label.

Controlled source interventions and transport interventions remain valuable **evaluation tools** for asking whether source identity survives transport changes. But the current main candidate is a measurement-design principle, not a causal-inference algorithm.

Allowed statement:

> controlled source/transport interventions are used to measure whether a sensing design preserves source identifiability.

Not allowed today:

> the proposed method is a validated causal source-localization algorithm.

## 10. Falsifiable predictions

The core idea is useful only if it predicts all of the following:

1. The old route has poor weakest-mode conditioning and unequal source exposure.
2. A source-blind observability-designed route improves `sigma3/sigma1` and weakest-mode energy on design winds.
3. The route remains source-identifying on a held transport regime that was not used for route selection.
4. The **same inference rule** performs better after route redesign; otherwise the claimed mechanism is mixed with a new estimator.
5. If single-trajectory excitation is impossible, complementary multi-trajectory measurements should improve the joint rank/conditioning in a way that ordinary redundant multi-robot sampling does not.

If these predictions fail, the current core idea must be rejected rather than rescued with a new posterior formula.
