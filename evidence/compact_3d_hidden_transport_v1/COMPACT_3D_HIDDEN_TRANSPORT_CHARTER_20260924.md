# Compact 3D Hidden Transport for GSL — Scientific Screening Charter

Date: 2026-09-24  
Branch: `research/compact-3d-hidden-transport-v1`  
Status: **CANDIDATE / DEVELOPMENT ONLY — NO ADVANCE CLAIM**

## 0. Why this candidate exists

M4-v3 is permanently STOP as a complete main model. Its frozen House02 D0 nevertheless established a narrower fact:

- explicit characteristic transport carries most of the predicted wind response;
- bulk displacement and wind-response magnitude are partly recovered;
- full-field wind-intervention geometry remains wrong.

Subsequent development-only diagnostics rejected generic explanations:

- causal memory improves field error but not intervention geometry;
- generic local residuals can raise cosine mainly by suppressing incorrect components and overtake the coarse model;
- fixed wall-slide and simple vertical-exchange rules do not restore the missing geometry;
- 2-D global path-exposure history, spatial exposure maps, directed 2-D path state, and simple D2Q9 directional state do not recover the source×wind interaction.

The remaining failure is therefore treated as a **state sufficiency problem**, not an architecture-width problem.

## 1. Root-cause evidence

### 1.1 Strong source×wind interaction

For the real House02 GADEN factorial bank,

[
I=C_{S2,W2}-C_{S2,W1}-C_{S1,W2}+C_{S1,W1}.
]

The interaction norm is of the same order as the wind intervention itself, while the W1→W2 response for S1 and S2 is almost orthogonal.

Therefore one 2-D concentration slice does not encode enough information to determine how the same future wind acts on plume mass injected from different source locations.

### 1.2 Error-localization oracles

Frozen M4-v3 errors concentrate in:
- near-boundary regions;
- high-strain regions;
- regions with large |Wz| or |ΔWz|.

Perfect oracle correction restricted to these source-blind regions can cross the frozen wind-cosine gate, while simple hand-written local rules cannot.

Interpretation: those regions mark unresolved transport channels; they are not themselves sufficient fixed correction laws.

### 1.3 Public House02 3-D CFD check

Using the official House02 `3,5-1_fast` raw 3-D CFD fields:

At the two frozen source locations near z=0.2 m, across the 11 wind snapshots:
- S1 median |Wz|/|Wxy| ≈ 0.866; 7/11 snapshots exceed 0.5;
- S2 median |Wz|/|Wxy| ≈ 0.058; only 1/11 exceeds 0.5;
- median time implied by local |Wz| to cross 0.1 m vertically is ≈2.28 s for S1 and ≈7.55 s for S2.

This demonstrates source-location-dependent access to different vertical transport channels under the same physical wind configuration.

### 1.4 3-D vs forced-2-D streamline check

For 10 source×snapshot cases from the same official CFD fields, integrating short streamlines with z free versus artificially fixing z=0.2 m yields:
- median horizontal endpoint separation ≈0.463 m;
- maximum ≈0.673 m;
- 80% of cases exceed 0.2 m separation.

Thus hidden vertical motion feeds back into future horizontal transport. A fixed-height 2-D state is not dynamically closed.

## 2. Scientific thesis

The deployable plume representation is a **partial observation** of an underlying 3-D transport state.

Let

[
z_t = 	ext{compact hidden-volume transport state}
]

and let the UAV-visible fixed-height plume statistic be

[
y_t = mathcal P_{z_0}(z_t).
]

The model should evolve

[
z_{t+1}=mathcal T_	heta(z_t, W_t, O)+B,Q_s
]

and project it to the sensor/PMFS observation layer

[
p(y_tmid s)=mathcal D(z_t).
]

The key claim is **not** “use a 3-D neural network”.

The claim to test is:

> The source×wind interaction relevant to gas-source localization can be represented by a compact hidden transport state that restores the unobserved vertical/path channels lost by fixed-height plume projection, while retaining a low-cost probabilistic observation interface for PMFS.

## 3. Recent parent ideas and novelty boundary

Scientific anchors:

1. AAAI 2025 — *How to Re-enable PDE Loss for Physical Systems Modeling Under Partial Observation*: jointly reconstruct a learnable hidden/high-resolution state and its transition instead of treating partial measurements as a complete physical state.

2. AAAI 2026 — *Learning Neural Operators from Partial Observations via Latent Autoregressive Modeling*: latent propagation is used to reconstruct dynamics under incomplete spatial observation.

3. NeurIPS 2024 — *Partial observation can induce mechanistic mismatches in data-constrained models of neural dynamics*: observationally matched surrogates can still possess incorrect hidden mechanisms under partial observation.

These works motivate the principle. They are not our novelty.

Forbidden claims:
- first latent neural operator;
- first partial-observation PDE model;
- first 3-D gas model;
- first physics-informed neural operator for GSL;
- first hidden-state model.

Potentially defensible target contribution, only if all gates pass:

> A compact hidden-volume transport belief for probabilistic gas-source localization that restores source-dependent 3-D transport channels omitted by fixed-height plume maps, and marginalizes/project them into PMFS-compatible source likelihoods.

## 4. Minimal model hierarchy

Do not start with a large learned 3-D model.

### H0 — exact physical 3-D control

Using the same canonical W1/W2 wind fields and occupancy:
- propagate a passive source state in the full 3-D grid/slab;
- no learned residual;
- project only the sensor-height observation.

Purpose: determine whether restoring 3-D state is sufficient to repair the M4 failure.

If H0 does not materially improve held-out wind/intervention geometry:
**STOP compact-3D line.**

### H1 — low-rank vertical/volume modes

Only if H0 survives.

Replace the full volume with K compact hidden modes, predeclared K ∈ {2,4,6}.

Requirements:
- source enters only as forcing;
- hidden modes evolve under wind/geometry;
- sensor-height output is a fixed/learned projection;
- no source ID conditions transition weights;
- parameter/computation budget must remain compatible with online candidate ranking.

### H2 — deployable hidden-state inference

Only after H1 survives oracle-wind tests.

Infer/update hidden modes from deployable information:
- 3-D occupancy/map if available;
- local 3-D anemometer observations;
- estimated wind belief;
- gas observations and timestamps;
- previous hidden belief.

Full simulator 3-D wind is a teacher/mechanism input only, never a required flight input.

## 5. Development split and gates

House02 remains development-only.

Train/identify from:
- S1-W1;
- S2-W1;
- S1-W2.

Evaluate:
- S2-W2 A/B.

Primary development gates, both frozen model seeds × both plume seeds:
- wind-delta cosine > 0.5;
- wind amplitude ratio 0.5–1.5;
- source response remains nontrivial;
- source×wind interaction geometry improves over M4-v3;
- field error does not regress materially;
- the hidden-state ablation loses the gain.

A model that improves only field MSE but not intervention geometry is NO-GO.

## 6. Inverse-GSL gate before closed loop

Even a successful H1 cannot enter autonomous closed loop merely from field metrics.

Before ROS/PMFS closed loop:
- freeze a geometry-only multi-source candidate bank;
- use identical sparse observations for all models;
- compare truth-containing candidate source rank against:
  - Native PMFS;
  - matched monolithic baseline;
  - frozen M4-v3 coarse component;
  - compact hidden-transport model;
  - hidden-state ablation.

Primary endpoint:

[
oxed{	ext{truth-containing source-candidate rank}}
]

Only source-rank signal authorizes closed-loop integration.

## 7. Real-flight boundary

A solution that requires full 3-D CFD truth at runtime is not the UAV method.

The evidence ladder remains:

oracle 3-D mechanism
→ compact latent state
→ estimated-wind hidden-state inference
→ hardware-in-loop
→ real stationary plume
→ controlled UAV flight
→ autonomous GSL.

## 8. Current authorization

Authorized:
1. export exact canonical House02 3-D occupancy + W1/W2 wind sequence into a compact immutable bundle;
2. run H0 exact 3-D physical sufficiency control locally;
3. if H0 survives, test K={2,4,6} hidden-volume modes.

Not authorized:
- House01/House03 generation;
- new confirmatory data;
- PMFS/ROS closed loop;
- real flight;
- large generative/particle model;
- scientific ADVANCE claim.
