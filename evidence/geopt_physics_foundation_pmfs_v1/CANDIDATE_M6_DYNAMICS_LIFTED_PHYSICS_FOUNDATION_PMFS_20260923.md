# Candidate M6 — Dynamics-Lifted Physics Foundation Model for PMFS

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`  
Status: **KEEP — high-priority feasibility candidate**

## 1. Mother idea

Transfer the 2026 **physics foundation model / dynamics-lifted geometric pre-training** paradigm into PMFS.

The scientific shift is:

> do not train a gas-specific neural operator from scratch; start from a geometry-aware physics foundation model pretrained to encode geometry–dynamics interactions, then adapt it to source-conditioned plume transport.

Working name:

**Dynamics-Lifted Physics Foundation PMFS (DLPF-PMFS)**

Paper-facing alternative:

**Foundation-Model Plume Simulator for Probabilistic Gas-Source Localization**

## 2. Remote-field parent idea

### GeoPT — ICML 2026

Wu, Guo, Li, Dou, Long, He, Matusik,  
*GeoPT: Scaling Physics Simulation via Lifted Geometric Pre-Training*, ICML 2026.

Core transferable idea:

- high-fidelity physics labels are expensive;
- static geometry pre-training alone misses dynamics;
- augment geometry with synthetic dynamics to create **dynamics-lifted self-supervision**;
- pretrain a single model that can later be configured by dynamics conditions;
- reduce labeled-data requirements for downstream physics tasks.

Official repository reports:
- >1M pre-training samples;
- geometry + synthetic dynamics pretraining;
- downstream physics configured through a dynamics field “prompt”;
- 20–60% lower downstream training-data requirement on reported tasks.

This directly addresses the current plume-world-model bottleneck: very limited high-fidelity GADEN source realizations.

## 3. PMFS mapping

### Geometry

Indoor obstacle map / 3-D environment:

[
O(x)
]

becomes the geometric input.

### Dynamics prompt

Wind field:

[
W(x)
]

is not merely a scalar feature. It serves as a spatial dynamics condition/prompt.

### Source prompt

Candidate source (s) adds a localized source/injection field:

[
Q_s(x).
]

### Output

Predict concentration / hit-probability field:

[
F_	heta(O,W,Q_s)
ightarrow
C_s(x,t)
quad	ext{or}quad
H_s(x).
]

Then feed this into the existing PMFS candidate-source probability map.

## 4. What PMFS assumption changes

Native PMFS assumes:

[
	ext{hand-coded filament simulator}
+
	ext{House-specific runtime wind}
]

for every candidate source.

M6 assumes:

[
	ext{pretrained geometry–dynamics representation}
+
	ext{small plume-specific adaptation}
]

can serve as the candidate forward simulator.

The main scientific claim is not “neural operator is faster.”

It is:

> a geometry–dynamics foundation representation can transfer across Houses and source conditions, reducing the amount of high-fidelity plume data required while retaining source-identification fidelity.

## 5. Why this is not generic PINO/FNO

Generic PINO/FNO:
- train a task-specific operator from plume data;
- require enough plume supervision for each environment/task.

M6:
- reuses a pretrained model whose representation was learned across broad geometry/dynamics distributions before seeing gas-plume labels;
- uses wind as a dynamics field condition;
- tests transfer/generalization with scarce GADEN supervision.

If we cannot actually use pretraining or transferred weights, this candidate collapses into generic neural operator and must be killed.

## 6. Physical structure

Required inputs:

- obstacle geometry;
- wind vector field;
- source injection field;
- optional sensor-height / boundary-condition channels.

Required constraints / interpretation:

### Mass/source locality
Candidate source injection must be localized:

[
Q_s(x)approx0
]

outside source support.

### Wind transport
Predictions must vary consistently with changes in vector wind field.

### Geometry/boundary interaction
Walls and openings must modify transport spatially.

### Positivity
Concentration / hit probability must remain nonnegative/in-range.

Optional later:
- conservation residual;
- no-through-wall regularization;
- PMFS low-fidelity anchor.

## 7. Strongest potential advantage over M3

M3 learns a stochastic plume world model from plume fields.

M6 may need far less plume-specific training because its backbone already encodes geometry–dynamics structure.

This matters because current high-fidelity data contains only:
- 3 source locations;
- 2 plume seeds per House source.

M6 is therefore a realistic response to limited data **if** pretrained GeoPT features transfer to indoor gas transport.

## 8. Major transfer risk

GeoPT's published downstream tasks are not indoor gas dispersion.

Potential mismatch:
- surface/industrial geometries vs occupancy/grid indoor geometry;
- deterministic simulation targets vs stochastic plume transport;
- different input/output discretizations;
- dynamics-prompt semantics may not directly accept indoor wind fields.

Therefore do not assume transfer.

The first gate is purely representation/interface compatibility.

## 9. G0 — pretrained-model interface audit

Before any data generation:

1. inspect GeoPT code and released checkpoints;
2. determine exact input representation:
   - point cloud / mesh / tokens;
   - geometry normalization;
   - dynamics-field representation;
3. determine whether indoor free-space/obstacle geometry can be represented without changing the pretrained backbone;
4. determine whether 2-D/2.5-D sensor-height plume field is a supported or minimally adaptable output.

PASS only if:
- pretrained weights can actually be loaded;
- geometry can be encoded faithfully;
- wind/source fields can enter through existing or minimally extended conditioning.

If the architecture must be substantially rebuilt, this is not a foundation-model transfer and M6 loses its main novelty.

## 10. G1 — zero-shot / frozen-feature probe

Do not fine-tune the full model first.

For a tiny GADEN pilot:

- freeze GeoPT backbone;
- train only a small output head / adapter;
- compare to:
  1. same architecture from scratch;
  2. small deterministic residual model;
  3. Native PMFS.

Measure:
- validation field error;
- convergence speed;
- amount of GADEN data required;
- truth-source candidate rank in frozen replay.

The foundation-model hypothesis requires the pretrained representation to help.

## 11. G2 — low-data scaling curve

Use source-blind fixed training subsets:

- 10%;
- 25%;
- 50%;
- 100% of pilot plume data.

Compare pretrained vs from-scratch.

The main claim only survives if pretraining yields a clear advantage in the low-data regime.

Do not select subsets based on truth-source rank.

## 12. G3 — cross-House / cross-source generalization

Train/adapt on selected Houses/source positions.

Test:
- unseen source position;
- unseen wind condition;
- ideally unseen House geometry.

Hard metric:

**truth-containing source-candidate rank.**

Field MSE alone is insufficient.

## 13. Destructive controls

### N1 — random pretrained weights
Same architecture, randomized backbone.

If performance is unchanged, GeoPT pretraining adds no value.

### N2 — static-geometry-only pretraining
Where feasible, compare against geometry-only representation.

Tests whether dynamics-lifted pretraining specifically matters.

### N3 — wind shuffle
Shuffle wind prompts.

Source-rank advantage should collapse if dynamics prompting is meaningful.

### N4 — source prompt shuffle
Break candidate-source injection mapping.

Inference advantage must disappear.

## 14. Direct prior-art boundary

Generic gas PINN/PINO and learned forward models already exist.

Do NOT claim:
- first neural operator for GSL;
- first pretrained physics model in general;
- first geometry-aware gas model.

Current novelty hypothesis:

> first/novel use of a **dynamics-lifted physics foundation representation** as the candidate-source forward model inside a PMFS-style localization framework.

A final literature audit is required before any “first” language.

## 15. Comparison to M4

### M4
Causal compositional world model:
- strongest scientific narrative;
- requires explicit intervention structure;
- goal: recombine causal mechanisms.

### M6
Physics foundation model:
- strongest data-efficiency / practical transfer narrative;
- easier to test with released pretrained model;
- goal: transfer geometry–dynamics representation into scarce-data plume modeling.

M4 is conceptually deeper.

M6 may be substantially easier to validate quickly.

## 16. Comparison to M3

### M3
Stochastic function-space world model:
- strongest plume-uncertainty representation;
- high data/training burden.

### M6
Pretrained deterministic/physics representation first:
- lower data burden;
- stochasticity can be added only if deterministic transferred model already improves source rank.

Do not add generative stochastic layers before G1/G2 pass.

## 17. Kill conditions

M6 is NO-GO as main if:

1. pretrained GeoPT representation cannot faithfully encode indoor geometry/wind/source inputs;
2. pretrained weights provide no low-data benefit over from-scratch;
3. source-rank does not improve;
4. gains are only reconstruction-speed gains;
5. transfer requires rebuilding most of the model;
6. a direct GSL foundation-model collision is found;
7. performance requires House-specific truth tuning.

## 18. Current verdict

Mother-idea strength: **high**.  
Recency/venue: **very high — ICML 2026**.  
Physical interpretability: **high**.  
Data-feasibility advantage: **potentially very high**.  
Direct GSL collision risk: **currently low, final audit required**.  
Risk of becoming generic PINO: **high if pretrained transfer fails**.

Status:

`KEEP — HIGH-PRIORITY FEASIBILITY CANDIDATE`.
