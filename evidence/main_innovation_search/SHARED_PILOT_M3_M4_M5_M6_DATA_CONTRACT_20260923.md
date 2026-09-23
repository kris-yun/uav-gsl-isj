# SHARED PILOT DATA CONTRACT — M3/M4/M5/M6

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Goal

Generate **one small, frozen, source-blind GADEN-RT pilot dataset** that can falsify the four current big-idea candidates without creating separate datasets for each method.

Candidates:

- M3 — stochastic plume world model;
- M4 — causal compositional plume world model;
- M5 — generative Lagrangian filament world model;
- M6 — dynamics-lifted physics foundation PMFS.

No model-specific tuning is allowed during data generation.

---

## 1. Environment

Use one House first.

Preferred:

`House02`

Reasons:
- existing PMFS/VGR evidence;
- hit-bearing behavior is expected to be more informative than House01 all-miss-dominated snapshots;
- 27×39 PMFS grid / ~631 free cells is computationally modest.

Freeze:
- geometry;
- gas type;
- GADEN numerical parameters;
- sensor-height plane;
- simulation duration;
- output sampling schedule.

---

## 2. Source interventions

Choose **4 source positions** source-blind.

Selection rule:

1. free valid cells;
2. space-filling / maximin spatial spread over feasible source region;
3. no source chosen using localization performance;
4. include different room/obstacle contexts if House02 geometry permits;
5. save exact positions before simulation.

Call them:

[
S_1,S_2,S_3,S_4.
]

At least one source must be reserved from specific downstream training splits.

---

## 3. Wind interventions

Choose **2 physically defensible wind conditions**.

Priority:

### W1/W2 option A
Two existing independent CFD/GADEN wind configurations for the same House.

### Option B
Two existing materially distinct replayable wind regimes/sequences.

### Option C
If no second configuration exists:
use a predeclared scalar speed transform of one physical field,

[
W_2(x)=gamma W_1(x),
]

which preserves flow topology.

Do not arbitrarily rotate the field through walls.

Freeze W1/W2 before plume generation.

---

## 4. Stochastic realizations

For every source × wind combination:

- seed A;
- seed B.

Total:

[
4	imes2	imes2=16
]

GADEN plume realizations.

Seeds must be deterministic and predeclared.

---

## 5. Simulation mode

Prefer GADEN-RT `RunningSimulation`.

- reuse environment/wind preprocessing where possible;
- `saveResults=false`;
- do not generate huge compressed 3-D concentration files by default;
- query compact outputs online.

Before the 16-run batch:
benchmark exactly one new source realization.

Record wall-clock and stop if unexpectedly expensive.

---

## 6. Required outputs from every run

### A. Manifest

Include:
- House;
- source ID / xyz;
- wind-condition ID;
- plume seed;
- simulation parameters;
- code/version hash;
- GADEN config hashes;
- start/end timestamps;
- wall-clock;
- CPU/GPU/RAM;
- output hashes.

### B. Sensor-height concentration field

At a frozen temporal schedule, e.g. every fixed (Delta T) after warmup:

[
C_t(x_i),quad x_iin	ext{all free PMFS cells}.
]

Store compact matrix:

- time;
- cell index;
- x,y,z;
- concentration.

Do not choose sampling times using source truth.

### C. Wind field

At the same grid/times where needed:

- wind_x;
- wind_y;
- wind_z if available;
- speed.

### D. Geometry features

Can be generated once for the House:

- occupancy/free mask;
- xyz;
- SDF to boundary;
- nearest-wall/boundary direction.

### E. Filament states

At the same or a coarser frozen temporal schedule:

- filament index/ID if available;
- xyz;
- sigma/radius;
- age/birth information if available.

If persistent IDs are unavailable, state this explicitly.

### F. PMFS-compatible derived field

From concentration or filament ensemble derive, using a **single frozen sensor model**:

- hit probability; or
- binary hit-event probability.

Do not create a different transform per method.

---

## 7. Required splits

### Split P — foundation transfer (M6)

Low-data train fractions fixed before training:

- 5%;
- 10%;
- 25%;
- 50%;
- 100%.

Held out:
- at least one source position;
- one independent seed.

Compare GeoPT pretrained vs same Transolver from scratch.

### Split C — compositional intervention (M4)

Example fold:

Train:
- S1-W1;
- S2-W1;
- S1-W2.

Test:
- S2-W2.

Repeat with another source pair if initial signal is positive.

### Split S — stochastic-field necessity (M3)

Train on seed A.

Test stochastic predictive distribution on seed B.

The stochastic model must beat a deterministic residual model.

### Split L — Lagrangian dynamics (M5)

Train one-step/path transition model on selected source/wind/seed combinations.

Hold out:
- seed;
- preferably source or wind condition.

Compare to native Gaussian/random-walk transition.

---

## 8. Universal downstream gate

All forward-model candidates ultimately generate candidate-source predictions.

Use a frozen PMFS-style replay contract.

Primary metric:

[
oxed{	ext{truth-containing source-candidate rank}}
]

Secondary:
- field error;
- calibration;
- endpoint/top-5 centroid.

No field metric can rescue a method that does not improve source identity.

---

## 9. Destructive nulls from the same dataset

Generate no extra simulations initially.

Use:

### Wind shuffle
Pair source/plume samples with the wrong W label/field.

### Source shuffle
Permute source labels.

### Geometry permutation
Destroy obstacle relation while preserving free-cell count.

### Temporal/filament shuffle
Destroy path structure while preserving marginal filament positions.

### Seed-label swap
Used only as a sanity check; independent seeds should remain exchangeable.

---

## 10. One-source benchmark before batch

Before generating 16 runs:

Run exactly one new source with one W and one seed.

Report:

- 300 s simulated duration or predeclared smoke duration;
- wall-clock;
- memory;
- concentration-slice query cost;
- filament export cost;
- disk size.

Decision:

- if cheap: launch full 16-run pilot;
- if expensive: reduce snapshot density first, not scientific factor coverage.

Do not drop source/wind combinations after seeing truth.

---

## 11. Why this pilot is efficient

The same 16 runs answer four different scientific questions:

### M6
Does cross-physics foundation pretraining reduce gas data requirements?

### M4
Can source and wind mechanisms recombine to predict an unseen intervention pair?

### M3
Does stochastic process modeling add source-relevant information beyond deterministic fields?

### M5
Are filament transition residuals structured/non-Gaussian enough to require generative particle dynamics?

Thus one dataset can kill several elegant but unnecessary ideas quickly.

---

## 12. Batch launch condition

Do not launch the full batch until:

1. Native baseline recovery artifacts remain clean;
2. one-source GADEN-RT benchmark is committed;
3. S1–S4 and W1–W2 are frozen in a manifest;
4. seeds and temporal sampling schedule are frozen;
5. no model has been trained on pilot truth yet.

Status:

`READY FOR ONE-SOURCE COST BENCHMARK`.
