# T0 postmortem and next mother-theory candidate: non-Markovian transport closure
Date: 2026-10-03

## Frozen result
Keep the formal decision unchanged:
`T0_FAIL_TASK_SUFFICIENCY_MAINLINE`

Do not rescue the frozen T0 gate by changing the endpoint, adding sources, or retuning the joint latent.

## What T0 did and did not falsify

T0 falsified the claim that the tested 8-D joint task-sufficient latent provides a measurable improvement over raw history on the frozen full-route source rank/AUC endpoint.

It did not show that history contains no useful dynamic information:
- full-route source rank/AUC are saturated for raw and joint;
- joint improves future hit prediction substantially over source-only;
- joint also improves per-window source accuracy over raw in all four cases, but this is exploratory because the frozen primary endpoint is per-simulation aggregated source rank/AUC;
- realization probes for generic and joint are both approximately chance, so nuisance suppression is not identifiable from this probe.

Therefore the strongest retained observation is:
**temporal history contains plume-dynamic information useful for future observation prediction, but the easy two-source full-route endpoint cannot demonstrate an additional source-ranking benefit.**

## Scientific pivot
Do not keep “task sufficiency” as the first-paper mother theory.

A more physically grounded candidate is:

**non-Markovian reduced transport / Mori-Zwanzig closure of unresolved plume dynamics.**

Physical mapping:
- resolved observables: UAV pose, local wind, gas concentration/hit, map context;
- unresolved variables: full 3-D wind, plume filament state, turbulent eddies, remote concentration field;
- source: static latent parameter to infer;
- consequence of projection: reduced observations are generally non-Markovian; unresolved plume degrees of freedom enter through a history-dependent memory term and stochastic residual.

A schematic candidate-source score:
`L_t(s) = L_0(o_t,s) + sum_{k=1..K} M_k(o_{t-k:t}, Δq, u, s) + ε_t`

This is not a generic GRU claim. The hypothesis is that the memory kernel is the mathematically required closure created by eliminating unobserved turbulent transport degrees of freedom.

## Why this is better aligned with current evidence
1. T0 future-prediction gain says history contains predictive dynamics beyond a source-only label.
2. R1A/R1B showed that instantaneous/local/path-mean flow descriptions can be insufficient or confounded.
3. Wisco audit showed real low-altitude state variability but not one stable lake-specific causal regime.
4. Therefore the general bottleneck is not “discover one lake-breeze state”; it is “close unresolved transport from sparse observations.”

## Cross-domain mother theory
Primary source:
- de Wit et al., PNAS 2026, Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows.

Secondary latest direction:
- Freitas et al., 2026 preprint, Learning turbulent transport via Mori–Zwanzig graph neural networks.

Related olfactory prior art:
- Rigolli et al., eLife 2022: intensity/timing statistics over short memory contain source-location information.
- Rando et al., eLife 2025: temporal memory tuned to whiff/blank physics improves turbulent odor navigation.

Novelty therefore cannot be “use memory”.
The new candidate must be:
**source-conditioned, physics-structured non-Markovian closure for probabilistic source inference**, with an explicit stochastic residual and a memory kernel tied to wind-relative transport history.

## Minimal next experiment: MZ0
Do not generate new plumes first.

Use an existing harder source-localization benchmark with non-saturated source rank:
priority:
1. existing House/VGR candidate bank with many source candidates;
2. existing House03 12-source/96-task evidence if the observation/forward data are directly usable;
3. only if neither supports clean memory testing, design a new benchmark.

Compare under identical observation budget:
A. current-observation/Markov evidence;
B. fixed-window hand statistics (intensity, intermittency, blank/whiff age);
C. generic GRU/LSTM;
D. finite-memory MZ-style source-conditioned closure.

Primary:
- true-source rank;
- Top1/Top3;
- localization error.

Mechanism:
- future observation Brier/NLL;
- learned memory contribution vs lag;
- whether optimal memory scale tracks measured whiff/blank correlation time;
- whether removing stochastic residual or wind-relative geometry degrades source rank.

No active sensing until a positive source-rank signal exists.

## MZ0 gate
The candidate is worth escalating only if D:
- improves median true-source rank over both B and C;
- improves or is non-inferior in >=3/4 frozen contexts;
- does not rely on a single seed/source;
- future-prediction gain and source-rank gain occur together;
- memory ablation shows a nonzero physically interpretable lag range.

Otherwise:
`MZ0_FAIL_NONMARKOVIAN_CLOSURE_MAINLINE`.

## Opening-report implication
The current Word version that presents task-sufficient representation as the settled main innovation is now scientifically ahead of the evidence and should not be submitted unchanged.

Until MZ0 or another mechanism passes, opening-report wording should remain hypothesis-level:
“针对有限移动观测无法显式获得完整三维输运状态的问题，研究历史观测中由未解析传播过程产生的时序记忆如何形成源位置判别信息，并构建面向源概率定位的紧凑动态传播表征。”

Do not name Mori–Zwanzig as the final algorithm in the thesis title before MZ0 passes.
