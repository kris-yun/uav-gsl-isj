# D0.5 selector × decoder cross-attribution

Date: 2026-09-28  
Branch: `research/d05-selector-decoder-cross-20260928`

## Scope

This is a read-only attribution of the frozen OPEN D0.5 result. It does **not**
change `HD_PLF_V0_ACTION_PROXY_NOT_VALIDATED_IN_OPEN_D05`, does not authorize
VGR, and does not start an invariance/causal-representation route.

Inputs are exactly:

- `evidence/hd_plf_v0/action_validity_d05/D05_RESULT.json`
- `evidence/hd_plf_v0/action_validity_d05/GOAL_COUNTERFACTUALS.csv`

The CSV already contains both B2 decoders for every feasible episode-goal pair.
Therefore the two frozen selectors can be crossed with the two frozen decoders
without new plume simulation, PMFS forward generation, fitting, or action
reselection.

Metric below is the frozen tie-aware true-source final rank; **lower is better**.
Uniform is the analytic mean over all feasible goals for that episode. Oracle is
the truth-aware minimum feasible rank and is diagnostic only.

## 2×2 result

| Environment | Decoder | LF-u selected point | LF-rawu selected point | Uniform feasible mean | Truth oracle |
|---|---|---:|---:|---:|---:|
| H01 fast | u-B2 | 2.000 | 2.167 | 2.210 | 1.125 |
| H01 fast | rawu-B2 | 1.917 | **1.667** | 2.062 | 1.042 |
| H02 W0 `3,5-1_slow` | u-B2 | 1.583 | 1.750 | 2.713 | 1.167 |
| H02 W0 `3,5-1_slow` | rawu-B2 | **1.458** | 2.125 | 2.723 | 1.250 |
| H02 W2 `4,5-3_slow` | u-B2 | 2.417 | 2.750 | 2.325 | 1.333 |
| H02 W2 `4,5-3_slow` | rawu-B2 | 2.250 | 1.917 | 1.796 | 1.250 |

Pooled across the 72 OPEN episodes:

| Decoder | Selector | Mean final rank | Mean rank gain | Uniform mean rank | Oracle mean rank |
|---|---|---:|---:|---:|---:|
| u-B2 | LF-u | 2.000 | 1.500 | 2.416 | 1.208 |
| u-B2 | LF-rawu | 2.222 | 1.278 | 2.416 | 1.208 |
| rawu-B2 | LF-u | **1.875** | **1.625** | 2.194 | 1.181 |
| rawu-B2 | LF-rawu | 1.903 | 1.597 | 2.194 | 1.181 |

The experiment is exactly balanced by source and target within each environment,
so the episode mean and source-balanced mean coincide here.

## Fixed selector -> decoder effect

At the **same LF-u selected point**, switching the decoder from u-B2 to rawu-B2:

- rawu better / tie / worse = **15 / 49 / 8** episodes;
- mean rank difference rawu-minus-u = **-0.125**.

At the **same LF-rawu selected point**:

- rawu better / tie / worse = **23 / 41 / 8**;
- mean rank difference = **-0.3194**.

Environment means at the LF-u selected point are directionally consistent:

- H01: 2.000 -> 1.917;
- H02 W0: 1.583 -> 1.458;
- H02 W2: 2.417 -> 2.250.

This is the cleanest current evidence that the AOD/rawu channel can improve the
B2 readout **without requiring rawu to choose the measurement location**.
The effect is not source-uniform, so this is not a universal amplitude claim.

## Fixed decoder -> selector effect

With u-B2 fixed, replacing the LF-u selector by LF-rawu gives pooled:

- rawu selector better / tie / worse = **18 / 40 / 14**;
- mean rank change = **+0.2222** (worse).

With rawu-B2 fixed:

- rawu selector better / tie / worse = **10 / 50 / 12**;
- mean rank change = **+0.0278** (essentially neutral/slightly worse pooled).

The environment interaction is large:

- H01 + rawu-B2: rawu selector improves 1.917 -> 1.667.
- H02 W0 + rawu-B2: rawu selector degrades 1.458 -> 2.125.
- H02 W2 + rawu-B2: rawu selector improves 2.250 -> 1.917.

Therefore there is no cross-environment evidence that the rawu template should
directly control geometry.

## Uniform and oracle diagnosis

For rawu-B2:

| Environment | Uniform | Oracle | Available uniform-to-oracle gap |
|---|---:|---:|---:|
| H01 | 2.062 | 1.042 | 1.020 |
| H02 W0 | 2.723 | 1.250 | 1.473 |
| H02 W2 | 1.796 | 1.250 | 0.546 |

The W2 result is particularly informative. The oracle is materially better than
uniform, so the local feasible action set still contains useful locations.
However both frozen selectors are worse than the uniform mean under rawu-B2
(2.250 and 1.917 vs 1.796). Thus W2 is not an “action space has no information”
case; it is a **current selector does not reliably find the useful actions** case.

Conversely, H02 W0 shows that the LF-u selector combined with rawu-B2 reaches
1.458, close to the 1.250 oracle and far better than the 2.723 uniform mean.
That is direct evidence for decoupling the location-selection representation
from the amplitude decoder rather than forcing one channel to do both jobs.

## Research consequence

This attribution supports the following narrow development decision:

1. Keep the AOD/rawu **readout** evidence alive.
2. Keep `HD_PLF_V0_ACTION_PROXY_NOT_VALIDATED_IN_OPEN_D05` frozen.
3. Do not start global source-invariance / causal-representation training from
   this result.
4. Do not require rawu geometry to drive action selection.
5. The next method question, if pursued, must target **realized decoder utility
   under the current belief/history**, because the oracle gap proves that useful
   actions exist in at least these OPEN local sets while the frozen proxy can
   miss them.

This is still a six-source, one-anchor, one-step, B2 OPEN diagnostic. It does
not establish improvement of Native `sourceProbability`, a deployable active
policy, or VGR/real-flight localization.

No new PASS label is introduced and the original D0.5 decision is unchanged.
