# Latent-dynamics / history-aware observation channel: authoritative R2 update-local screen

Date: 2026-09-23

Status: **NO_GO_AS_OBSERVATION_LAYER_ON_CURRENT_PMFS_FORWARD_FAMILY**

## Mother idea

ICLR 2026: Xiao, Si & Chen, *LD-EnSF: Synergizing Latent Dynamics with Ensemble Score Filters for Fast Data Assimilation with Sparse Observations*.

The relevant principle is not “add an LSTM”. The new semantics are a latent dynamical state evolved in a compact world model plus a history-aware observation encoder that maps sparse/irregular measurements into that state before score-based assimilation.

## Why this screen was needed

The independent H01 continuous-path ACI zero-gate showed:
- physical true-gas positive-hit truth rank 16/121;
- measured-gas positive-hit truth rank 22/121;
- measured full-path Brier truth rank 17/121;
- circular-shift null fraction 0.006.

That isolated a local measured-vs-physical observation gap, but the predeclared ACI primary gate still failed.

Before treating sensor history as a main mechanism, the authoritative R2 six-run bank was checked with correct temporal semantics.

## Correct update-local contract

A first exploratory calculation incorrectly paired the final update-5 candidate field with the entire earlier trajectory. That is physically invalid because the final candidate bank is conditioned on the later PMFS context.

The result below fixes this:

- six authoritative R2 Native runs (House01/02/03 x seed0/1);
- all five source updates per run = 30 update-local cases;
- for update k, only sensor samples after update k-1 and through update k are evaluated;
- those samples are paired only with update k's frozen candidate bank and simulated-hit field;
- threshold remains native `th_gas_present = 0.1 ppm`;
- truth is used only for post-score rank evaluation.

For each candidate, scores use the simulated marginal hit probability at the robot's actual path cells:
- positive-hit support: mean candidate probability at hit samples;
- full-path Brier score;
- hit-minus-miss contrast.
Both measured gas and simulator true gas are evaluated. For hit-bearing measured segments, a 100-repetition circular shift keeps the complete hit sequence and path but breaks hit-location association.

## Result

Across 30 update-local cases, 28 contain measured positive hits.

Key source-identity counts:

- measured positive-hit support in top 20% of candidates: **1/28**;
- physical true-gas positive-hit support in top 20%: **0/28**;
- measured positive-hit support improves on Native truth rank: **7/28**;
- true-gas positive-hit support improves on Native: **7/28**;
- measured Brier enters top 20%: **5/30**;
- true-gas Brier enters top 20%: **3/30**;
- measured Brier improves on Native: **15/30**;
- true-gas Brier improves on Native: **14/30**;
- circular-shift location null is <=0.05 in only **1/28** hit-bearing cases, and that case still has a poor absolute truth rank.

Median truth-rank fraction is approximately:
- Native: 0.757;
- measured positive-hit support: 0.836;
- true-gas positive-hit support: 0.842;
- measured Brier: 0.816;
- true-gas Brier: 0.822.

Full per-update table: `LDENSF_OBSERVATION_CHANNEL_R2_UPDATE_LOCAL.csv`.

## Decision

The cross-House R2 evidence rejects the hypothesis that the main PMFS failure is simply a memoryless observation layer.

Crucially, **physical true-gas effects are not source-identifying under the current candidate forward family either**. Therefore a history-aware observation encoder placed on top of the existing PMFS forward simulator would be an advanced engineering patch, not a load-bearing main innovation.

This does **not** falsify LD-EnSF as a completely new learned latent forward world model. It says that to use the ICLR-2026 idea as a main contribution, we would need to replace the present candidate forward semantics and train/validate a source-conditioned latent dynamical model across many source positions and independent plume realizations. The current six R2 runs contain one true source per House and are insufficient for a fair learned-world-model gate.

Do not tune sensor deconvolution, thresholds, or sequence windows on these 30 cases to rescue the observation-layer version.
