# CODEX VALIDATION CHARTER — Physics-Anchored Stochastic Plume World Model

**Date:** 2026-09-23  
**Priority:** current lead candidate, but kill aggressively if gates fail.

## 0. Thesis under test

The hypothesis is not “a neural network can approximate a plume.”

The hypothesis is:

> A PMFS source candidate should predict a **distribution over stochastic plume fields**, physically anchored by known wind/obstacle/source transport, instead of one Monte-Carlo-averaged hit map.

Working name:

**Physics-Anchored Stochastic Plume World Model (PA-SPWM)**

The proposed world model keeps the PMFS source-candidate probability-map shell.

---

## 1. Verified remote-field anchors

### Operator Flow Matching — NeurIPS 2025
Use as the primary mother idea.

Key property to verify from the paper/code:
- stochastic process learning in function space;
- predictive density at arbitrary collections of points;
- functional regression.

### Curly Flow Matching — NeurIPS 2025
Use as a possible physics/dynamics auxiliary.

Key property:
- non-gradient dynamics;
- non-zero-drift reference process;
- approximate/measured velocity information enters the reference dynamics;
- tested on CFD/ocean-current style systems.

### Important novelty boundary
Generic PINN/GNN/neural-operator GSL is already occupied.

Search specifically for:
- probabilistic/generative gas plume operator;
- flow matching for plume/gas dispersion;
- stochastic function-space plume model for source localization;
- diffusion/Schrödinger bridge plume source localization;
- world-model GSL;
- stochastic neural operator GSL.

If a direct generative stochastic-field GSL collision is found, mark M3 NO-GO as main before implementation.

---

## 2. Proposed physical representation

Do not directly generate an arbitrary “hit score image.”

Preferred physical latent field:

[
\rho(x,t)
]

representing gas/filament density or concentration-like mass.

Continuous transport anchor:

[
\partial_t \rho
=
-\nabla\cdot(w\rho)
+
\nabla\cdot(D\nabla\rho)
+
q_s
-
\lambda\rho.
]

Required physical roles:

- (w(x,t)): vector wind/advection field;
- (O(x)): obstacle/wall geometry;
- (q_s): source injection tied to candidate source;
- stochastic term/residual: unresolved turbulence/intermittency.

Only after this field is modeled should the PMFS/sensor contract convert it into hit probability.

---

## 3. Architecture hypothesis

Low-fidelity anchor:

[
H_s^0
=
F_{PMFS}(s,w,O).
]

High-fidelity stochastic field:

[
H_s
=
\Psi
\left(
H_s^0
+
R_\theta(s,w,O,\xi)
\right).
]

The learned model should focus on the stochastic residual, not relearn all transport physics from scratch.

For a dynamic version, test the Curly-FM-inspired structure only after a simpler residual model succeeds:

[
dZ_t
=
b_{wind}(Z_t,w,O)dt
+
r_\theta(\cdot)dt
+
\sigma dW_t.
]

Do not begin with the most complex architecture.

---

## 4. W0 — local GADEN data/cost audit

The uploaded historical tar archives do **not** contain full plume fields.

However the user's VM contains GADEN realization roots referenced by runtime manifests.

First inspect one realization root and record:

- file tree;
- formats;
- number of timestamps;
- filament data;
- wind data;
- whether full concentration grids are stored;
- how a sensor-height 2-D field can be reconstructed.

Then benchmark one **new source position**.

### Prefer GADEN-RT/core online sampling
The current GADEN core API exposes:
- `RunningSimulation`;
- `AdvanceTimestep()`;
- `Simulation::SampleConcentration(point)`;
- `SampleWind(point)`;
- `GasSource::sourcePosition`.

Therefore prefer:

1. preprocess/load one House + wind configuration once;
2. alter only `sourcePosition`;
3. run gas dispersion with `saveResults=false`;
4. at predeclared times, sample a 2-D grid at the robot sensor height using `SampleConcentration`;
5. store compact slices + metadata.

Do **not** enable huge full-grid serialization before benchmarking.

Record for one new source:
- wall-clock;
- CPU/GPU;
- RAM;
- disk;
- number of useful temporal slices;
- whether wind preprocessing is reusable.

### W0 decision
If a small multi-source training set is impractical to regenerate, mark M3 HOLD/NO-GO.

---

## 5. Existing source-position coverage problem

Current independent GADEN data provide only:

- House01: one source position, two plume realizations;
- House02: one source position, two plume realizations;
- House03: one source position, two plume realizations.

This is insufficient for source-conditioned world-model training.

If generation is cheap, create only a tiny pilot:

- 4–8 source positions in one House;
- 2 independent plume seeds per source;
- source-blind space-filling positions;
- reserve at least one source position as unseen-source validation.

Do not generate a full candidate grid yet.

---

## 6. W1 — residual-structure gate before neural training

For every pilot source/seed:

1. generate high-fidelity GADEN field (H^{HF});
2. generate corresponding Native-PMFS anchor (H^{PMFS});
3. align grid/time/height;
4. define residual in a stable transform:
   - concentration residual; or
   - log concentration residual; or
   - logit hit-probability residual.

Before fitting a model, measure:

- cross-seed residual correlation;
- spatial correlation length;
- temporal persistence;
- low-rank/PCA energy;
- dependence on wind-aligned coordinates;
- obstacle-boundary structure;
- source-relative structure.

### W1 destructive nulls

- shuffle wind fields between plume realizations;
- shuffle source labels;
- spatially permute residuals within free cells;
- obstacle-mask permutation preserving free-cell fraction.

The real residual structure must be stronger/more predictable than the nulls.

### W1 hard decision

If residuals are essentially unstructured stochastic noise, do not train OFM.

Mark M3 NO-GO/HOLD.

---

## 7. W2 — tiny deterministic residual baseline

Before any generative model, fit the smallest credible residual predictor.

Purpose:
- test whether high-fidelity forward correction contains source-relevant information.

Allowed examples:
- low-rank regression;
- small MLP on local physical features;
- tiny CNN/operator block;
- very small FNO only if needed.

Inputs:
- PMFS anchor;
- wind;
- obstacle map;
- candidate source position.

Outputs:
- corrected field or residual.

Freeze all choices source-blind.

### W2 hard endpoint
Replay source inference on held-out plume realization/source.

Primary metric:

**truth-containing source-candidate rank.**

If deterministic residual correction gives no source-rank signal, do not jump to OFM to rescue the line.

---

## 8. W3 — stochastic world-model necessity gate

Only if W2 is positive.

Train a minimal stochastic process model based on OFM or a faithful simplified implementation.

Compare:

1. Native PMFS;
2. deterministic residual correction;
3. stochastic residual world model.

The stochastic model must improve on the deterministic model on independent plume realizations.

Possible supporting metrics:
- field NLL;
- calibration;
- CRPS/energy;
- spatial covariance;
- hit/miss likelihood.

But the hard metric remains truth-source rank.

If stochasticity adds no source-identification value, demote OFM from the main idea.

---

## 9. W4 — wind-referenced dynamics auxiliary

Only if W3 is positive.

Test whether wind should be more than an input channel.

Compare:
- ordinary conditional stochastic residual model;
- non-zero-drift / wind-referenced formulation inspired by Curly-FM.

Required evidence:
- better cross-wind or cross-House generalization;
- better recirculation/obstacle-region field prediction;
- better source rank.

Do not claim Curly-FM transfer if implementation is only “concatenate wind to network input.”

---

## 10. W5 — hard/strong physical constraint auxiliary

Search 2025–2026 physics-constrained generative modeling for a second auxiliary.

Priority:
- constraint-preserving flow matching;
- projected/manifold flow matching;
- conservative generative dynamics.

Potential constraints:
- obstacle no-through-wall;
- source injection locality;
- positivity;
- boundary/no-flux condition;
- approximate conservation balance.

Prefer hard/projection-style constraints over generic PINN soft penalties when technically feasible.

Do not implement until W2/W3 establish value.

---

## 11. Final required ablations

If M3 survives:

- remove PMFS anchor;
- remove wind;
- shuffle wind;
- remove obstacle geometry;
- deterministic-only;
- stochastic-only;
- remove source conditioning;
- random residual null.

The claimed physical/generative advantage must disappear in the expected ablations.

---

## 12. Kill conditions

M3 is NO-GO as main if any of these hold:

1. direct prior-art collision: generative stochastic plume/operator world model already used for GSL in essentially the same way;
2. multi-source GADEN pilot is too expensive to produce;
3. residual structure is not learnable beyond nulls;
4. deterministic residual model cannot improve source rank;
5. stochastic model does not improve over deterministic residual;
6. gains require House-specific truth tuning;
7. gains vanish on independent plume realization;
8. model improves field reconstruction but not source identity;
9. the final implementation reduces to generic PINO/FNO with wind concatenated as an input feature.

---

## 13. Git checkpoints

Commit after:

1. `audit:` direct prior-art / gas-PINO collision audit;
2. `evidence:` W0 GADEN file/cost audit;
3. `evidence:` W1 residual-structure analysis;
4. `evidence:` W2 deterministic residual source-rank probe;
5. `evidence:` W3 stochastic-vs-deterministic comparison;
6. `decision:` M3 advance/hold/no-go.

Do not wait for all stages.

If M3 fails, keep all evidence and return to the general search charter.
