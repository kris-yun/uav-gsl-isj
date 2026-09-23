# C0.5 REAL-GADEN INTERVENTION BANK CHARTER — M4 Causal Compositional Plume World Model

Date: 2026-09-23
Branch: `research/causal-compositional-plume-world-model-v1`
Priority: **P0 scientific gate before any closed-loop implementation**

## 0. Scientific question

Test the following specific hypothesis on **real GADEN plume data**:

> A source-conditioned plume should be modeled as a source-injection intervention passed through a reusable transport operator,
>
> [
> Q_s = I_S(s), qquad C = T_{W,O}(Q_s),
> ]
>
> rather than as one monolithic mapping over entangled source/wind inputs.

This is the first real-data gate for M4.

The previous C0-pre evidence:
- rejected additive source + transport factorization;
- retained operator composition as a candidate;
- did **not** scientifically validate M4.

Do not reuse synthetic development results as evidence for this gate.

---

## 1. Non-negotiable factorial design

Use **one House only**.

Need exactly:

- 2 source interventions: `S1`, `S2`;
- 2 physically valid wind interventions: `W1`, `W2`;
- 2 genuinely independent plume RNG seeds per source × wind cell.

Total:

[
2 	imes 2 	imes 2 = 8
]

realizations.

### Required cells

- S1-W1-seedA
- S1-W1-seedB
- S1-W2-seedA
- S1-W2-seedB
- S2-W1-seedA
- S2-W1-seedB
- S2-W2-seedA
- S2-W2-seedB

All eight must share:
- House geometry;
- occupancy;
- gas type;
- filament numerical parameters;
- sensor-height convention;
- simulation duration;
- sampling/export schedule.

Only the intended source and wind interventions may differ.

---

## 2. House selection

Before generating anything, audit House01/02/03 and select the House satisfying:

1. at least two physically valid, distinct wind configurations for the **same geometry**;
2. source positions can be changed without invalid wall/obstacle placement;
3. generation cost is manageable;
4. spatial field export is supported.

Selection must be source-blind.

Do NOT choose a House because a known source is easier to localize.

Create:

`evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.md`

with:
- candidate House;
- wind directory paths;
- grid dimensions;
- wind iteration count;
- wind speed min/median/max;
- hashes;
- occupancy hash;
- reason for selected House.

### Hard stop

If no House has two physically valid wind fields for the same occupancy geometry:

**STOP C0.5.**

Report:
`C0.5 HOLD — NO VALID SAME-GEOMETRY WIND INTERVENTION`

Do not:
- rotate wind arbitrarily through walls;
- synthesize an unphysical second wind and call it a scientific intervention;
- proceed to model training.

A source-blind speed scaling may be used only as a separate development diagnostic, never as the scientific C0.5 gate.

---

## 3. Source interventions

Choose two valid free-space source locations `S1`, `S2`.

Rules:

- predeclare coordinates before any plume outcome is inspected;
- spatially separated enough to produce a meaningful inverse problem;
- both valid under W1 and W2;
- not selected using PMFS truth rank;
- not chosen to deliberately make one model look better.

Record:
- xyz;
- nearest-wall distance;
- free-space validity;
- source-to-source distance.

The source intervention is implemented only through GADEN source-position parameters:

- `source_position_x`;
- `source_position_y`;
- `source_position_z`.

Everything else stays fixed.

---

## 4. Wind interventions

Preferred:

Use two independently generated/canonical physical wind fields:
- same House;
- same occupancy geometry;
- different valid flow configuration.

For every wind field record:
- directory;
- all relevant iteration hashes;
- speed statistics;
- directional summary;
- grid alignment with occupancy.

The intervention must be:

[
do(W=W_1)
quad	ext{vs}quad
do(W=W_2)
]

with source held fixed.

Do not use measured robot wind traces as the intervention definition.

The intervention is the **forward transport field** used by GADEN.

---

## 5. Plume stochastic replication

Use two genuinely independent plume RNG seeds per factorial cell.

Seeds must produce numerically distinct plume realizations.

After generation run a replication audit:

For every source × wind cell verify:
- field/slice files are not byte-identical;
- concentration summary statistics differ beyond floating-point noise;
- seed manifests differ as intended;
- geometry/wind hashes remain identical within the cell.

If any nominal seed pair is a pseudoreplicate:

**C0.5 FAIL DATA INTEGRITY**

Do not replace it post hoc after seeing model performance.

---

## 6. Simulation duration benchmark first

Before generating all eight cases:

Run one new source case at:

- 30 s;
- 120 s;
- 300 s.

Record:
- wall-clock;
- CPU utilization;
- peak RAM;
- disk;
- active filament count if available;
- number of exported field slices.

Use the existing benchmark script:

`evidence/causal_compositional_plume_world_model_v1/benchmark_gaden_intervention_generation.sh`

Create:

`C0_5_GENERATION_COST_20260923.md`

### Duration selection

Use the shortest duration that gives a stable, nontrivial plume field for the mechanism test.

Do not choose duration using source-rank performance.

If 300 s is inexpensive, prefer 300 s for alignment with the project evaluation horizon.

Do not run 1000 s by default.

---

## 7. Required spatial output

C0.5 requires a **spatial plume target**, not only one robot trajectory.

Preferred target:

- 2-D concentration slice at the robot sensor height;
- same spatial grid for all eight realizations.

Use GADEN core/RT APIs where practical:
- `RunningSimulation`;
- `AdvanceTimestep()`;
- `SampleConcentration(point)`;
- `SampleWind(point)`.

Avoid huge full 3-D concentration serialization unless necessary.

### Export schedule

At predeclared times, export:

[
C_t(x,y,z_{m sensor})
]

over the common free-space grid.

Also save:
- obstacle mask;
- wind slice/vector field;
- source injection map;
- timestamp;
- plume seed.

Recommended first pilot:
- 10–30 evenly spaced field snapshots after warmup.

The exact schedule must be fixed before inspecting model outcomes.

---

## 8. Dataset layout

Create:

`evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank/`

Suggested structure:

```text
manifest.json
geometry/
  occupancy.*
  grid_metadata.json
winds/
  W1/
  W2/
sources/
  source_manifest.json
realizations/
  S1_W1_A/
  S1_W1_B/
  S1_W2_A/
  S1_W2_B/
  S2_W1_A/
  S2_W1_B/
  S2_W2_A/
  S2_W2_B/
```

Every realization must contain:
- provenance manifest;
- exact source;
- exact wind ID;
- seed;
- binary/config hashes;
- exported field/slice files;
- summary stats.

Do not commit huge binaries directly to Git if inappropriate.

Commit:
- manifests;
- scripts;
- hashes;
- compact metrics;
- representative tiny samples.

Large raw assets may remain on the VM with immutable paths/hashes documented.

---

## 9. Pre-registered held-out recombination

Primary fold:

Train on:
- S1-W1;
- S2-W1;
- S1-W2.

Hold out entirely:
- **S2-W2**.

Neither seed of S2-W2 may enter:
- training;
- hyperparameter selection;
- normalization fitted from targets;
- early stopping selection;
- architecture selection.

Second confirmatory fold, if the first passes:

Train on:
- S1-W1;
- S2-W1;
- S2-W2.

Hold out:
- **S1-W2**.

Do not rotate folds after seeing which one is easier.

---

## 10. Models to compare

### A. Native/physics reference

At minimum retain:
- Native PMFS/GADEN-compatible forward reference where available.

### B. Monolithic matched-capacity model

[
F_{m mono}(S,W,O)ightarrow C.
]

One entangled predictor.

### C. Operator-compositional model — M4

Required structural form:

[
Q_s = I_S(S)
]

then

[
C = T_{W,O}(Q_s).
]

This is **function composition**, not additive embedding fusion.

Forbidden M4 implementation:

[
z=z_S+z_W+z_O
]

followed by a decoder, if that is the only compositional structure.

Source injection must enter the transport operator as a physical/source field or state.

### Parameter fairness

C must not have materially greater trainable capacity than B.

Predeclare allowed parameter-count tolerance, suggested:

[
pm 10%.
]

Report exact trainable parameter counts.

---

## 11. Minimal architecture rule

Do not begin with:
- large transformer;
- full WM3C;
- OFM;
- diffusion model;
- GeoPT fusion;
- LLM decomposition.

C0.5 tests the mechanism, not architecture scale.

Use the smallest model that can express:

[
I_S ightarrow T_{W,O}.
]

If M4 only wins when dramatically larger than monolithic, the mechanism claim fails.

---

## 12. Training discipline

No truth/source-rank tuning.

Fix before holdout evaluation:
- normalization;
- optimizer;
- learning rate schedule;
- epochs;
- random training seeds;
- architecture;
- loss;
- stopping rule.

Use multiple training seeds if training is stochastic.

Do not change settings after inspecting S2-W2.

---

## 13. Source-blind field metrics

On held-out S2-W2 report:

- field MSE / normalized error;
- spatial correlation;
- concentration/hit calibration;
- plume centroid/direction diagnostics;
- obstacle/wall violations;
- physics/advection residual where valid.

These are **secondary scientific diagnostics**.

They cannot pass M4 alone.

---

## 14. HARD downstream PMFS source-identity gate

After models are frozen:

For a fixed source-candidate bank, generate candidate forward fields under W2.

Run the same PMFS-compatible source-inference replay using:
- monolithic candidate fields;
- compositional M4 candidate fields;
- Native reference candidate fields if available.

Primary endpoint:

[
oxed{	ext{truth-containing source-candidate rank}}
]

For the held-out true source S2 under W2.

Report:
- candidate count;
- truth rank;
- truth score/evidence;
- top-5 candidate IDs;
- top-5 spatial centers;
- hashes of candidate forward fields.

Do not use endpoint/top-5 centroid to rescue a worse truth rank.

---

## 15. Mechanism nulls

M4 must fail the appropriate destructive controls.

### N1 — source-label shuffle

Shuffle source labels during training while preserving sample counts.

Expected:
- compositional source-rank advantage disappears.

### N2 — wind-label shuffle

Shuffle W1/W2 assignments.

Expected:
- held-out recombination advantage degrades.

### N3 — source-module swap

At inference, replace S2 source-injection module/input with S1 while holding W2 fixed.

Expected:
- predicted plume origin/source evidence follows the swapped intervention.

### N4 — transport swap

Keep S2 injection fixed, swap W2 transport conditioning with W1.

Expected:
- plume transport pattern changes according to W1.

### N5 — additive factorization control

Include the previously falsified shallow model where feasible:

[
C_S(S)+C_T(W,O).
]

Expected:
- does not outperform the proper compositional operator on held-out recombination.

---

## 16. Independent stochastic confirmation

A positive result is not accepted from one held-out plume realization.

Both independent S2-W2 plume seeds must be evaluated.

Minimum requirement for advance:
- same qualitative model ordering across both;
- no truth-tuned per-seed changes.

If one improves and one reverses strongly:
- `HOLD`, not PASS.

---

## 17. Decision rule

### ADVANCE M4

Only if all are true:

1. data integrity passes;
2. physically valid source and wind interventions are verified;
3. operator-compositional model beats matched monolithic model on held-out recombination;
4. improvement appears on both independent plume realizations;
5. truth-source candidate rank improves or is materially more stable;
6. intervention-label / module-swap nulls destroy the advantage;
7. no truth tuning.

Then write:

`C0_5_REAL_GADEN_DECISION_20260923.md`

with status:

`POSITIVE REAL COMPOSITIONAL-INTERVENTION SIGNAL`

This is still not yet a full closed-loop PASS.

### NO-GO M4 AS MAIN

If:
- monolithic matches/beats compositional;
- source rank does not improve;
- gain survives nulls;
- only field MSE improves;
- results require extra capacity/truth tuning.

Do not rescue with a larger model.

### HOLD

If:
- second physical wind is unavailable;
- data generation fails;
- replication integrity is unresolved.

---

## 18. Relationship to M6

Do **not** merge GeoPT into C0.5.

M6 remains a separate candidate/possible auxiliary.

If M4 C0.5 passes, a later stage may replace/initialize:

[
T_{W,O}
]

with a pretrained physics foundation transport backbone.

The logic would then be:

- M4 = main scientific architecture;
- M6 = cross-environment transport prior / data-efficiency auxiliary.

But C0.5 must first demonstrate the M4 composition mechanism without relying on M6.

---

## 19. No closed loop yet

Do not modify:
- PMFS ROS movement;
- source update in live loop;
- stopping logic.

C0.5 is offline/frozen.

Closed-loop authorization requires:
1. positive C0.5;
2. confirmatory fold/independent realization;
3. frozen model contract.

---

## 20. Required Git checkpoints

Commit and push immediately after each:

1. `audit:` House/wind intervention inventory;
2. `evidence:` generation-cost benchmark;
3. `data:` 8-realization bank manifest/hashes;
4. `research:` monolithic + compositional implementation;
5. `evidence:` held-out field metrics;
6. `evidence:` PMFS truth-rank replay;
7. `evidence:` destructive nulls;
8. `decision:` C0.5 final decision.

Preserve failures.

---

## 21. Final mandatory report

Create:

`evidence/causal_compositional_plume_world_model_v1/C0_5_REAL_GADEN_DECISION_20260923.md`

It must answer exactly:

1. Which House was used?
2. What are S1/S2?
3. What are W1/W2 and why are both physical?
4. Are the two plume seeds per cell genuinely independent?
5. What is the data-generation cost?
6. Does operator composition beat monolithic on held-out field prediction?
7. Does it beat monolithic on truth-source candidate rank?
8. Do nulls destroy the advantage?
9. Is M4 advanced, held, or killed?
10. If advanced, is closed-loop implementation now justified?

No claim beyond the evidence.
