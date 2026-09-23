# O0 Charter — Analytical Mechanism-Splitting Adequacy Before Neural Operators

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`  
Priority: **P0 falsification for M7**

## 0. Goal

Before training any neural operator, determine whether a physically declared split

\[
\mathcal J_S
\rightarrow
\mathcal A_W
\rightarrow
\mathcal D
\rightarrow
\mathcal B_O
\]

is a useful representation of the real/high-fidelity GADEN plume.

This stage is deliberately **non-neural**.

If a simple physical split does not isolate a structured/reusable residual, there is no justification for building a learned operator library.

---

## 1. Data source

Use an existing GADEN realization on the user's VM.

Do **not** regenerate a plume for O0.

GADEN core supports:

- \`PlaybackSimulation\`;
- \`PlaybackSimulation::AdvanceTimestep()\`;
- \`Simulation::SampleConcentration(point)\`;
- \`Simulation::SampleWind(point)\`;
- \`PlaybackSimulation::GetFilaments()\`.

Existing saved \`iteration_*\` files can therefore be replayed and queried.

## 2. First case

Prefer:

- House02;
- one existing high-fidelity independent realization;
- a source with clear gas hits;
- recovered/canonical physical wind data.

Do not choose the case based on which algorithm performs best.

House02 is preferred because previous evidence suggests it is hit-bearing and therefore informative.

## 3. Minimal export

Choose a fixed sensor-height plane.

Export only **20–40 predeclared time snapshots** after plume warm-up.

For every free cell and snapshot store:

- x, y, z;
- occupancy/free-space mask;
- concentration;
- wind x/y/z;
- source position;
- timestamp.

Also store:

- full obstacle mask;
- cell size;
- GADEN realization path;
- hashes of realization metadata/wind/occupancy;
- exact GADEN binary/library provenance where available.

Optional:
- active filament positions and std-dev at the same timestamps.

Do not export a full 1000-s dense movie.

## 4. Exact replay requirement

The export script must prove:

- realization is opened in playback mode;
- each requested iteration is successfully loaded;
- concentration sampling uses GADEN's own \`SampleConcentration\`;
- no interpolation from robot-path observations is used.

## 5. Analytical split baseline

At one field snapshot \(c_t\), predict \(c_{t+\Delta}\) using a declared physical composition.

### J — source injection

Use a localized source term centered on the known simulation source.

For O0 this is evaluator-known because the purpose is forward-model mechanism analysis, not source inference.

No source tuning.

### A — advection

Use the actual sampled GADEN wind field.

Preferred:
- semi-Lagrangian backtrace; or
- conservative finite-volume advection.

Do not use the historical GMRF field.

### D — diffusion

Use one **predeclared panel** of physically plausible scalar diffusivities or an equivalent Gaussian-spreading coefficient.

Do not select a best value using PMFS truth-source rank.

For O0, selecting a value by source-blind field prediction on a designated calibration subset is allowed, but:
- calibration snapshots and evaluation snapshots must be separate;
- one value must be frozen before held-out evaluation.

### B — obstacle/boundary

At minimum:
- zero concentration inside occupied cells;
- prevent backtraces through walls.

Preferred:
- no-through-wall/no-flux treatment consistent with the chosen discretization.

## 6. Split variants to compare

Predeclare:

A. **advection only**  
\[
A_W(c_t)
\]

B. **diffusion only**  
\[
D(c_t)
\]

C. **advection + diffusion**  
\[
D\circ A_W(c_t)
\]

D. **Strang split**  
\[
D_{1/2}\circ A_W\circ D_{1/2}(c_t)
\]

E. **Strang + obstacle projection**  
\[
B_O\circ D_{1/2}\circ A_W\circ D_{1/2}(c_t)
\]

F. **simple persistence**  
\[
c_t
\]

Persistence is mandatory as a non-physics control.

## 7. Source-blind metrics

On held-out snapshot transitions:

- relative L2 field error;
- log-concentration L1/L2;
- plume centroid displacement error;
- downwind-axis error;
- support IoU above a predeclared concentration threshold;
- wall/obstacle violation mass.

Do not inspect source rank yet.

## 8. Residual-structure test

For best predeclared/frozen analytical split:

\[
R_t
=
c_{t+\Delta}
-
\hat c_{t+\Delta}^{split}.
\]

Measure:

- spatial autocorrelation;
- wind-aligned correlation;
- obstacle-distance dependence;
- temporal correlation;
- low-rank/PCA energy across snapshots.

### Required nulls

1. wind shuffle across snapshots;
2. obstacle-mask spatial permutation preserving occupancy ratio;
3. residual spatial permutation preserving marginal histogram.

A useful residual mechanism should show structure beyond these nulls.

## 9. Cross-condition reuse

If fast/slow or multiple physical wind configurations are available:

- calibrate diffusion/residual diagnostics on one transport condition;
- evaluate without retuning on the other.

If the physical split collapses under a mild transport change, the claimed reusable-mechanism story is weak.

## 10. O0 PASS signal

Advance M7 only if all are broadly true:

1. advection+diffusion+boundary materially beats persistence and individual mechanisms;
2. wrong-wind null degrades prediction;
3. obstacle handling reduces physically invalid mass/error;
4. residual after splitting is smaller than the raw one-step field change;
5. residual retains nontrivial structured dependence on wind/obstacle/local plume state;
6. the same frozen split parameters transfer to an independent plume realization.

This would justify learning only the unresolved mechanism.

## 11. O0 KILL signal

M7 is demoted if:

- persistence is as good as the physical split at useful horizons;
- wind shuffle does not matter;
- obstacle handling does not matter;
- residual is essentially unstructured noise;
- a different diffusion parameter is required for every case;
- the split only works after truth/source-rank tuning.

## 12. No neural rescue

If O0 fails:
- do not train DISCO;
- do not add GeoPT;
- do not add OFM;
- do not introduce test-time beam search.

Record NO-GO and return to the main-innovation search.

## 13. Required outputs

Under:

\`evidence/testtime_compositional_plume_operators_v1/o0_<house>_<realization>/\`

save:

- \`manifest.json\`
- \`snapshot_index.csv\`
- \`fields.npz\` or compact equivalent
- \`O0_METRICS.tsv\`
- \`O0_NULLS.tsv\`
- \`O0_RESIDUAL_STRUCTURE.json\`
- \`O0_DECISION.md\`

## 14. Git checkpoints

1. \`evidence:\` playback/export proof;
2. \`research:\` analytical split implementation;
3. \`evidence:\` held-out metrics/nulls;
4. \`decision:\` O0 PASS/HOLD/NO-GO.

Commit each stage immediately.
