# CODEX M6 STAGE-1 — Physics Foundation PMFS Offline Hard Gate

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`  
Priority: **P0 current lead main-innovation candidate**  
Do NOT start closed loop yet.

## 0. Main thesis under test

The main innovation candidate is:

> **Use a cross-physics, dynamics-lifted pretrained physics foundation representation as the candidate-source forward model inside PMFS.**

This is not generic FNO/PINO.

GeoPT provides the pretrained environment representation:

[
E_{m physics}(O,W),
]

where:
- (O) = indoor geometry / wall structure;
- (W) = wind dynamics field.

A small PMFS-specific source adapter injects candidate source (s):

[
H_s
=
D(
E_{m physics}(O,W),
A_s(s)
).
]

The final paper claim survives only if pretraining improves **truth-source candidate rank under scarce gas/plume supervision**.

---

## 1. Read before execution

Read:

- `evidence/geopt_physics_foundation_pmfs_v1/CANDIDATE_M6_DYNAMICS_LIFTED_PHYSICS_FOUNDATION_PMFS_20260923.md`
- `evidence/geopt_physics_foundation_pmfs_v1/G0_INTERFACE_AUDIT_20260923.md`
- `evidence/geopt_physics_foundation_pmfs_v1/G0_5_RUNTIME_REAL_HOUSE_PROBE_20260923.md`
- `evidence/geopt_physics_foundation_pmfs_v1/PHOENIX_UNET_NOVELTY_BOUNDARY_AND_SANDBOX_20260923.md`
- `evidence/geopt_physics_foundation_pmfs_v1/build_pmfs_geopt_features.py`

Do not reinterpret the task as “train a neural operator.”

---

## 2. G0.5-B — actual checkpoint load

Official artifact:

- repo: `GeoPT/GeoPT_Pretrained_Models`
- file: `GeoPT_8layers.pt`
- expected SHA256:
  `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`

Official architecture:

- Transolver;
- coordinate input: 3;
- `fun_dim=11`;
- hidden 256;
- heads 8;
- layers 8;
- slice_num 32;
- mlp_ratio 2.

### Required evidence

1. download checkpoint;
2. SHA256 verify;
3. instantiate exact official architecture;
4. use official/compatible filtered state-dict loader;
5. save:
   - checkpoint key count;
   - loaded key count;
   - total model parameters;
   - loaded parameters;
   - loaded percentage;
   - all excluded/mismatched keys and reason.

PASS target:

> all internal pretrained geometry/dynamics layers load; only final downstream task head is intentionally replaced.

Then use a real House geometry+wind tensor and run the actual pretrained forward pass.

Record:
- token count;
- CPU/GPU;
- time;
- RAM/VRAM;
- output shape.

Commit before proceeding.

---

## 3. G1-A — one-new-source generation cost

Do not generate a large dataset yet.

Use one House with clean GADEN assets, preferably House02 unless a better House has simpler tooling.

Use:
- existing occupancy;
- existing physical wind directory;
- fixed gas parameters;
- one source-blind new valid source position.

Benchmark:
- 30 s;
- 120 s;
- 300 s.

Record:
- wall clock;
- peak RAM;
- disk;
- frames;
- active filament counts if available.

Prefer the existing GADEN generator or gaden_core `RunningSimulation`.

Wind must be reused; do not rerun CFD.

Commit.

### Stop rule

If 300 s generation makes even a tiny 4–8 source pilot impractical, mark M6 HOLD/NO-GO and stop.

---

## 4. G1-B — tiny multi-source pilot dataset

Only if generation cost passes.

One House, one fixed physical wind field.

Choose source-blind valid free-space locations:

- minimum 4 sources;
- target 6–8 if cheap;
- at least 2 independent plume seeds/source.

Predeclare split:

- training source locations;
- at least 1 fully held-out source location;
- independent held-out plume seed.

Do not choose sources based on PMFS truth rank or final error.

### Field target

Preferred:
- sensor-height 2-D concentration field at predeclared timestamps.

Efficient route:
- run GADEN;
- use `SampleConcentration(point)` or reconstruct from saved filament states;
- store only compact 2-D slices.

Also store:
- geometry;
- wind;
- source;
- timestamp;
- plume seed;
- hashes.

---

## 5. G1-C — three-arm low-data transfer test

Keep architecture/capacity as matched as possible.

### Arm A — Native PMFS forward
Current repaired Native PMFS simulator.

### Arm B — GeoPT architecture from scratch
Same gas adaptation architecture, but random backbone.

### Arm C — pretrained GeoPT + source adapter
Pretrained environment backbone + small candidate-source injection adapter + gas output head.

### Source adapter rule

Do NOT change the pretrained raw 14-channel input projection.

Recommended:

[
r_s(x)
=
[x-s,|x-s|,Q_s(x)]
]

then a small adapter after the pretrained embedding.

Record exact adapter parameter count.

The adapter should remain a small fraction of the backbone.

---

## 6. Low-data curve

Use predeclared fractions of the same pilot:

- 25%;
- 50%;
- 100%.

If enough samples exist, additionally 10%.

Train B and C with:
- same optimizer;
- same epochs/early-stop rule;
- same head/adapter capacity;
- same random seeds where applicable.

No source-truth tuning.

Primary representation question:

> Does pretrained C beat scratch B most clearly in the low-data regime?

---

## 7. G1-D — scientific hard endpoint

Field metrics are not sufficient.

Freeze Arm B/C.

For each PMFS source candidate in a held-out replay:

1. generate/predict candidate forward field;
2. use the same source-inference rule for both learned arms;
3. compare against Native PMFS forward;
4. freeze all scores;
5. only then reveal truth.

Primary metric:

**truth-containing source-candidate rank**.

Report:
- Native rank;
- scratch rank;
- pretrained rank;
- candidate count;
- top-5 candidates;
- truth score;
- field error secondary.

### ADVANCE requirement

M6 advances only if:

1. pretrained GeoPT beats scratch in low-data forward prediction;
2. pretrained GeoPT improves truth-source rank on held-out source/seed;
3. gain repeats on at least one independent plume realization;
4. no House/source-specific tuning.

If C improves field MSE but not source rank:

`NO-GO AS MAIN INNOVATION`.

---

## 8. Destructive controls

### N1 — random backbone
Arm B is mandatory.

### N2 — wind shuffle
Shuffle wind field/source pairing while preserving marginals.

Pretrained advantage should materially degrade.

### N3 — source adapter shuffle
Swap source labels/adapters.

Source-rank gain should disappear.

### N4 — geometry destruction
At minimum shuffle wall-direction/SDF features while preserving their marginal distribution.

If pretrained performance is unchanged, the claimed geometry/dynamics transfer is suspect.

---

## 9. Novelty language

PHOENIX-UNet (Building and Environment 2026) already provides:
- obstacle-aware learned gas dispersion;
- source conditioning;
- meteorological conditioning;
- unseen source/wind generalization.

Therefore DO NOT claim those.

The M6 claim is:

> **cross-physics foundation pretraining reduces the gas-specific high-fidelity data required for PMFS candidate forward modeling and preserves/improves source identity.**

Generic gas-PINO/FNO is also not novel enough.

---

## 10. Git checkpoints

Commit after:

1. `evidence: G0.5-B actual GeoPT checkpoint load`
2. `evidence: G1-A one-source generation cost`
3. `evidence: G1-B pilot dataset manifest`
4. `evidence: G1-C low-data pretrained-vs-scratch`
5. `evidence: G1-D source-rank replay`
6. `decision: M6 advance/no-go`

Push after every stage.

---

## 11. Closed-loop prohibition

Do **not** implement closed-loop planning yet.

Closed loop starts only if G1-D is positive.

If positive, stop and commit the evidence. Then the next branch will define the full PMFS integration / 300-s closed-loop comparison.

If negative, mark M6 NO-GO and return to the general main-innovation search.
