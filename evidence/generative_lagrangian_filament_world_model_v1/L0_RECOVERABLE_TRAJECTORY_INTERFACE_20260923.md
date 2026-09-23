# L0 Data-Interface Decision — Recoverable GADEN Filament Trajectories

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`

## Decision

\`L0 = POSITIVE / ADVANCE\`

GADEN does not serialize an explicit filament ID, but its update and storage contract contains enough deterministic structure to recover stable pseudo-identities for the current project generator.

This materially improves M5 feasibility.

## 1. What GADEN actually stores

Current \`gaden_core\` defines:

\`\`\`cpp
struct Filament
{
    Vector3 position;
    float sigma;
};
\`\`\`

Saved \`iteration_*\` files serialize the complete active-filament vector.

There is no persistent ID field.

Therefore a naive “same vector index = same particle” assumption is forbidden.

## 2. Ordering invariant

GADEN uses two ping-pong vectors.

At every simulation step:

1. \`AddFilaments()\` appends new filaments with \`emplace_back\`;
2. \`MoveFilaments()\` updates all current entries;
3. survivors are copied to the next vector **in original index order**;
4. filaments that exit through an outlet are omitted;
5. vectors are swapped.

Therefore:

> relative order of all surviving existing filaments is preserved, and newly born filaments are appended after older survivors.

Across saved frames:

\[
F_{t+\Delta}
=
\text{ordered subsequence}(F_t)
\;\Vert\;
\text{new births}.
\]

The vector index itself is not an ID, but birth order is preserved.

## 3. Sigma is an age clock

Every surviving filament obeys:

\[
\sigma_{k+1}
=
\sigma_k
+
\frac{\gamma}{2\sigma_k}\Delta t.
\]

This update is deterministic and independent of:
- wind;
- source location after birth;
- stochastic positional noise.

All filaments begin with the same predeclared initial sigma.

Therefore \(\sigma\) encodes filament age.

For a given project configuration:

- initial sigma;
- growth gamma;
- dt

define a deterministic lookup:

\[
\text{age steps}
\longleftrightarrow
\sigma.
\]

## 4. Project-specific uniqueness is especially strong

The existing independent-realization generator uses:

- \`num_filaments_sec = 7\`;
- \`deltaTime = 0.1 s\`.

Thus:

\[
7\times0.1=0.7
\]

filaments per simulation step in the release accumulator.

The current deterministic accumulator can release at most **one new filament per simulation step**.

Hence birth simulation step itself is a unique cohort label in the current project configuration.

This gives a natural pseudo-ID:

\[
\boxed{
ID_{\rm pseudo}
=
\text{estimated birth iteration}
}
\]

for every active filament.

## 5. Pseudo-ID recovery

For saved frame \(k\):

1. read current simulation/save iteration;
2. read each filament's \(\sigma\);
3. build the exact deterministic sigma trajectory:
   \[
   \sigma(1),\sigma(2),\ldots
   \]
   using the frozen GADEN update equation;
4. map saved sigma to nearest age step under float tolerance;
5. compute:
   \[
   birth\_step
   =
   current\_step-age\_steps;
   \]
6. use \`birth_step\` as pseudo-ID.

Validation:

- same pseudo-ID across adjacent saved frames must have sigma consistent with deterministic aging;
- positions must satisfy a broad physical displacement envelope;
- order of matched pseudo-IDs must remain monotonic;
- new IDs must appear only as younger suffix cohorts;
- disappeared IDs must never reappear.

## 6. Generalization if release rate changes

If future settings allow multiple births in one simulation step:

\[
ID_{\rm pseudo}
=
(birth\_step,\ cohort\_order).
\]

Because GADEN preserves vector ordering among survivors, within-cohort order can be propagated.

For the current 7/s × 0.1 s project, this extra complication is unnecessary.

## 7. Why this matters scientifically

M5 can train on actual **Lagrangian path supervision** rather than:

- inferring pseudo trajectories from concentration maps;
- nearest-neighbor matching particles blindly;
- learning only Eulerian snapshots.

Each recovered track provides:

\[
\{
X_t,\sigma_t,W(X_t),O(X_t)
\}_{t=t_{\rm birth}}^{t_{\rm exit}}.
\]

This matches the remote-field mother idea from physics-grounded generative point-trajectory models.

## 8. First trajectory object

Do not immediately train a diffusion transformer.

First construct transition residuals:

\[
R_t
=
X_{t+\Delta}
-
X_t
-
W(X_t)\Delta.
\]

Also record:

- nearest-wall distance/direction;
- whether the segment hits/slides along an obstacle;
- sigma/age;
- local wind magnitude/direction;
- source-relative location.

## 9. L1 source-blind diagnostics

Before learning:

### Gaussianity
Does

\[
R_t
\sim\mathcal N(0,\sigma^2I)
\]

actually fit?

Measure:
- skewness;
- kurtosis;
- energy distance;
- multimodality.

### Heteroscedasticity
Test residual variance versus:
- wall distance;
- wind magnitude;
- recirculation region;
- filament age.

### Temporal structure
Measure:
- residual autocorrelation along a track;
- conditional persistence.

### Obstacle mechanism
Compare residual/path deflection:
- near walls;
- open space.

### Destructive null
Shuffle residuals across:
- spatial locations;
- wind contexts;
- wall-distance bins.

If structure disappears under the null and real residual is strongly non-Gaussian/context-dependent, M5 receives a real mechanism signal.

## 10. Critical caveat

The current GADEN simulator itself generates positional stochasticity using Gaussian noise plus deterministic obstacle handling.

If training supervision comes only from GADEN generated with that exact law, a learned model may merely rediscover GADEN.

Therefore M5's paper-level value requires at least one of:

1. transfer from richer/high-fidelity plume data;
2. learning obstacle/wind-conditioned effective transitions not represented in PMFS's much simpler 2-D filament simulator;
3. source-rank improvement when the learned GADEN-informed transition replaces PMFS forward dynamics;
4. independent real/experimental plume evidence.

This is a hard scientific boundary.

## 11. Current verdict

Data feasibility: **high**.

Mother-idea relevance:
- PhysCtrl, NeurIPS 2025: generative physics over 3-D point trajectories conditioned on physics parameters/forces.

PMFS fit:
- exceptionally high because PMFS is already a filament simulator.

Main unresolved question:

> Does GADEN contain source-identification-relevant Lagrangian structure beyond the simple PMFS transition law?

That is now the L1 hard gate.

Status:

\`ADVANCE TO L1 RESIDUAL-STRUCTURE AUDIT\`.
