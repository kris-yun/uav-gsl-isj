# M4-v3 + Tiny Causal Memory Closure — D1 Decision

Date: 2026-09-23  
Branch: `research/m4-memory-closure-v1`  
Workflow run: `35889560161`  
Decision: **D1_MEMORY_AUX_NO_GO — DO NOT ENTER CLOSED LOOP**

## Question

Can a very small source-blind causal memory auxiliary repair the specific M4-v3 failure
(wrong W1→W2 response geometry) without replacing the coarse characteristic transport?

## Frozen development design

- Frozen M4-v3 checkpoints: seeds 1729 and 2718.
- Closure: one shared 3×3 Conv2d, 6→1, **55 trainable parameters**.
- Inputs: current coarse log field, first/second temporal differences, current wind u/v/speed.
- No source ID or source coordinates enter the closure.
- Training cells only: S1-W1, S2-W1, S1-W2.
- Held-out development cell: S2-W2.
- One closure is shared across both frozen M4 base checkpoints.
- Bounded correction: `0.5*tanh(raw)`.
- 80 epochs, lr 5e-3, seed 4242.
- Predeclared pass requires all four held-out comparisons to exceed wind-delta cosine 0.5,
  mean cosine gain >=0.10, and no loss of coarse physical response.

## Result

| Base seed | Plume | Base wind cosine | +Memory cosine | Gain | Base MSE | +Memory MSE |
|---|---|---:|---:|---:|---:|---:|
| 1729 | A | 0.35057 | 0.38156 | +0.03099 | 0.28387 | 0.24398 |
| 1729 | B | 0.38325 | 0.41389 | +0.03064 | 0.29916 | 0.25094 |
| 2718 | A | 0.34069 | 0.37307 | +0.03238 | 0.29315 | 0.25200 |
| 2718 | B | 0.36975 | 0.40219 | +0.03243 | 0.30833 | 0.25881 |

Other checks:
- field MSE improves in 4/4;
- wind amplitude remains approximately 0.50–0.55 of truth;
- source amplitude remains approximately 0.84–0.88 of truth;
- correction norm is only ~25.4% of base norm, so the auxiliary did not dominate;
- nevertheless all four required wind-cosine gates fail;
- mean wind-cosine gain = **0.03161**, below frozen +0.10 gate.

## Supporting residual-memory audit

A no-training audit of frozen M4 residuals found:
- temporal-order signal in 8/8 source×wind×base-seed residual sequences;
- adjacent residual cosine approximately 0.953–0.987, significantly above time-shuffle nulls;
- a cross-combination scalar AR(2) model reduced S2-W2 residual prediction MSE over AR(1)
  by **33.67%** and **34.80%** for the two M4 checkpoints.

However:
- realization-specific residual energy was only ~0.6–0.8% median and <1.6% maximum;
- an older 12-case project audit already showed that candidate-specific delayed forcing did not
  yield source-specific memory benefit and declared direct Mori–Zwanzig source-memory transfer NO-GO.

Therefore temporal predictability is real, but it is **not sufficient localization evidence**.

## Multi-angle diagnosis

1. **Optimization is not the main issue.**  
   The auxiliary improves field MSE in every held-out comparison yet leaves the intervention geometry wrong.

2. **Memory exists but is mostly predictable model-form bias.**  
   It is useful for smoothing/correcting average fields, not for recovering the missing source-discriminative transport geometry.

3. **The remaining error is spatial-mechanistic.**  
   M4 captures bulk displacement and wind-response magnitude but misses deformation/redistribution structure.

4. **A stochastic diffusion/flow auxiliary is not justified by this bank.**  
   A/B realization-specific residual energy is too small relative to shared bias.

5. **Full-field memory is not directly deployable.**  
   A UAV does not observe ground-truth concentration fields over the map; any future auxiliary must use
   candidate predictions plus actual sensor/wind history only.

6. **Closed-loop testing now would be scientifically weak.**  
   Prior project audits repeatedly show that lower field error/endpoint can coexist with poor truth-source rank.

## Stop

Do not:
- lower the 0.5 cosine gate;
- increase memory width/depth or horizon against S2-W2;
- add diffusion/flow matching to rescue D1;
- integrate this D1 closure into PMFS/ROS;
- run a 300 s closed loop from this branch.

The next credible mechanism should target **spatial deformation / transport geometry**, not generic memory.
