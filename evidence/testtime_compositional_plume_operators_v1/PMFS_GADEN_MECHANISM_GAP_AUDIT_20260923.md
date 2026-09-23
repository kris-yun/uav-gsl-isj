# PMFS vs GADEN Mechanism-Gap Audit for M7

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## Decision

\`MECHANISM GAP = REAL AND STRUCTURAL\`

but

\`KNOWN GADEN MECHANISMS MUST NOT BE REBRANDED AS LEARNED NOVELTY\`.

Before training a residual operator dictionary, M7 must test a **mechanism-aligned analytical anchor** that includes all cheap, known, source-code-level corrections.

## 1. Source / particle birth

### PMFS candidate simulator

Official PMFS:

- fixed \`numFilamentsIteration = 5\`;
- every iteration releases five point filaments;
- for quadtree-region candidates the source point is sampled uniformly inside the candidate region;
- simulation is 2-D.

### GADEN

GADEN:
- uses \`numFilaments_sec\`;
- supports a 3-D source position;
- source parameters are explicit simulation metadata.

### Consequence

Source injection rates/units are not identical.

Do not attribute this mismatch to an unresolved learned transport mechanism before aligning the source-generation contract.

## 2. Advection

### PMFS

\[
X_{k+1}
=
X_k+\Delta t[W_{2D}(X_k)+\epsilon_k].
\]

- 2-D wind;
- local grid wind lookup;
- fixed Gaussian velocity noise.

### GADEN

GADEN:
- samples a 3-D CFD wind vector;
- advects the filament in 3-D;
- adds gas-dependent buoyancy in z;
- adds independent 3-D Gaussian random displacement/velocity variability.

### Consequence

Even with identical horizontal wind, the state transition is not the same physical process.

## 3. Filament spreading

### PMFS

A filament is effectively a point for the hit-map occupancy calculation.

There is no age-dependent filament radius in the PMFS forward simulator.

### GADEN

Each filament has \(\sigma\), and:

\[
\sigma
\leftarrow
\sigma
+
\frac{\Gamma}{2\sigma}\Delta t.
\]

Thus older filaments spread in space.

This affects concentration amplitude and support.

### Consequence

GADEN's diffusion/spreading mechanism is explicitly state/age dependent.

A fixed PMFS point-noise parameter cannot reproduce this exactly.

## 4. Wall / obstacle interaction

### PMFS

When direct movement crosses an obstacle, the current implementation steps along the path until the first blocked step and then backs up by one increment.

The filament effectively stops at the wall for that update.

The source comment explicitly notes that a better implementation would use a deflection so the filament moves along the wall rather than stopping.

### GADEN

When an obstacle is hit:

1. compute a wall-normal direction from the blocked step;
2. restore the previous valid position;
3. remove the normal component of the remaining displacement;
4. recursively continue with the tangential/rejected component.

Thus GADEN implements wall deflection/sliding.

### Consequence

Obstacle interaction is a structural mechanism mismatch, not a scalar hyperparameter mismatch.

## 5. Observation / field formation

### PMFS

Candidate hit map:
- each timestep marks whether at least one filament occupies a grid cell;
- multiple filaments in one cell/time are counted once;
- hit probability is temporal hit frequency;
- optional Gaussian blur is applied afterward.

Thus candidate output is directly a 2-D Bernoulli/frequency field.

### GADEN

Each filament is a 3-D Gaussian concentration blob.

For sample point \(x\):

\[
c_j(x)
=
c_{j,center}
\exp
\left(
-\frac{d(x,X_j)^2}{2\sigma_j^2}
\right).
\]

Center concentration decreases as approximately:

\[
c_{center}\propto\sigma^{-3}.
\]

GADEN:
- sums filament concentrations;
- truncates at ~3 sigma;
- requires line of sight between filament and sample point;
- outputs continuous ppm.

### Consequence

PMFS and GADEN do not merely produce the same field with different coefficients.

They construct the observable through different mechanisms.

## 6. Outlet / vertical effects

GADEN:
- explicitly removes filaments that enter outlet cells;
- contains vertical/buoyancy dynamics.

PMFS candidate forward is 2-D and its outside/removal behavior is based on map bounds/free-space traversal.

These differences can matter near ventilation/outlet geometry.

## 7. What this means for M7

There is enough structural mismatch to justify a mechanism-level investigation.

But many of these mechanisms are **known from source code**.

Therefore the initial residual operator must not be asked to relearn:
- wall sliding/deflection;
- Gaussian filament spreading;
- obvious source-rate scaling;
- line-of-sight blocking;

if they can be incorporated cheaply and deterministically.

Otherwise a neural model might appear successful simply because it rediscovers mechanisms already encoded in GADEN.

## 8. New hard baseline — mechanism-aligned analytical anchor

Before M7 O1, compare:

### P0 — Native PMFS forward

Original candidate simulator.

### P1 — mechanism-aligned analytical/cheap forward

Add as many source-code-known mechanisms as feasible without learned parameters:

- wall tangential deflection rather than stop;
- age-dependent spreading or an equivalent physical diffusion rule;
- source-rate normalization;
- obstacle/LOS-compatible field formation;
- 2.5-D/vertical correction only if data interface supports it.

No neural network.

### P2 — P1 + learned residual operator

Only after P1 is frozen.

## 9. Decision logic

### If P1 closes the source-rank gap

Then the main scientific problem was an explicit forward-model mismatch that can be repaired analytically.

M7 should be demoted.

Do not add neural operators merely for novelty.

### If P1 improves but leaves structured transferable residual

This is the strongest case for M7.

The learned operator dictionary is then genuinely modeling unresolved transport rather than known missing physics.

### If P1 does nothing and residual is unstructured

M7 is also weak.

## 10. Implication for O0

O0 should be interpreted in two levels:

### O0-A — field-level physical splitting
Does explicit advection/diffusion/boundary physics explain real plume evolution?

### O0-B — PMFS mechanism alignment
Do cheap source-code-known corrections materially improve the candidate forward/source-rank behavior?

Neural O1 begins only after both are understood.

## 11. Current scientific assessment

The PMFS↔GADEN gap is **not just a parameter-calibration problem**.

Strong candidate mismatch mechanisms exist:
- wall stop vs wall deflection;
- point occupancy vs growing Gaussian filaments;
- 2-D vs 3-D/buoyancy;
- temporal hit-frequency vs continuous concentration kernel.

This strengthens the motivation for a mechanism-level world model.

But it also raises the bar: M7 must beat a strong no-learning mechanism-aligned baseline.
