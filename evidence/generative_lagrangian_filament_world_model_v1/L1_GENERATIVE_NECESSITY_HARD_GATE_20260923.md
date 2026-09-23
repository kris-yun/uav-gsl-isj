# L1 HARD GATE — Is a Generative Lagrangian Transport Model Actually Needed?

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`

## 0. Scientific question

Do not train PhysCtrl/flow/diffusion first.

The only question at L1 is:

> Does high-fidelity GADEN transport contain **source-relevant stochastic transition structure** that is not adequately represented by PMFS's simple filament law or by a small conditional Gaussian model?

If no, M5 is not a main innovation.

## 1. Input realizations

Start with one House that uses the normal GADEN player path, preferably House02.

Development realization:
- H02_R2026092211.

Independent validation realization:
- H02_R2026092212.

Both have:
- same House;
- same source;
- same canonical wind;
- different plume RNG seed.

Do not mix seeds during model selection.

## 2. Exact provenance contract

Generator:
- dt = 0.1 s;
- saveDeltaTime = 0.5 s;
- 7 filaments/s;
- sigma0 = 10 cm;
- gamma = 15 cm²/s;
- filament noise std = 0.01 m/s-equivalent velocity noise;
- wind loop 1..10;
- 1000 s simulation;
- writeConcentrations=false.

Expected saved frames:

\[
1803.
\]

Fail closed if actual count differs.

Use:

\`recover_filament_pseudo_ids.py\`

to reconstruct exact save-file-index → simulation-step mapping and birth-step pseudo-ID.

## 3. Trajectory extraction validation

For every saved frame:

1. load filament vector through the exact GADEN PlaybackSimulation API;
2. recover current simulation step from the float32 save schedule;
3. infer each filament's age updates from sigma;
4. infer birth step:
   \[
   b=k-a+1;
   \]
5. assign pseudo-ID = birth step.

Required validation:

- at most one new pseudo-ID per simulation step under 7 Hz × 0.1 s;
- same pseudo-ID's sigma follows deterministic growth;
- pseudo-ID order is monotonically increasing within frame after accounting for exited filaments;
- an ID that disappears may never reappear;
- no duplicate pseudo-ID in one frame;
- at least 99.99% of filament observations pass sigma-age matching; otherwise stop and audit serialization.

Do not repair identities using source truth or gas field similarity.

## 4. Transition dataset

For every pseudo-ID present in two consecutive saved frames:

record:

- start position \(X_t\);
- end position \(X_{t+\Delta}\);
- exact elapsed simulation time \(\Delta\) from save schedule;
- sigma / age;
- local wind at start;
- local wind at end;
- nearest obstacle distance;
- nearest obstacle direction;
- start/end occupancy state;
- current wind-file index;
- distance from source only as a diagnostic feature, not required by the final source-agnostic model.

Also identify:
- open-space transitions;
- near-wall transitions;
- outlet-disappearance events.

## 5. Baselines

### B0 — PMFS-like local drift

\[
\hat X_{t+\Delta}
=
X_t+W(X_t)\Delta.
\]

Residual:

\[
R^{(0)}
=
X_{t+\Delta}-\hat X_{t+\Delta}.
\]

This deliberately matches the conceptual simplicity of PMFS.

### B1 — fixed isotropic Gaussian

Fit only one global covariance on development seed:

\[
R^{(0)}
\sim
\mathcal N(\mu,\Sigma).
\]

No spatial context.

### B2 — small heteroscedastic Gaussian

Predict:

\[
\mu_\phi(z),\quad \Sigma_\phi(z)
\]

from a small predeclared context:

\[
z=
[
W(X_t),
\|W\|,
d_{\rm wall},
n_{\rm wall},
\sigma,
\Delta
].
\]

Keep model deliberately small.

No source ID/source coordinates in B2.

### B3 — known-physics reference

Where technically practical, integrate the known GADEN deterministic mechanisms over the saved interval:

- wind advection;
- obstacle StepTowards/sliding;
- buoyancy;
- sigma growth;

but exclude stochastic positional noise.

Then fit a single Gaussian residual.

This is the strongest anti-overengineering control.

If B3 already explains held-out trajectories, a generative neural world model is scientifically unnecessary.

## 6. Source-blind L1 diagnostics

On independent seed only:

### Distribution fit
- NLL;
- energy score;
- Wasserstein/energy distance of residuals;
- covariance calibration.

### Non-Gaussianity
Report:
- skewness;
- excess kurtosis;
- Mardia multivariate diagnostics if practical;
- multimodality test or density comparison.

### Context structure
Residual distribution conditioned on:
- wall-distance bins;
- wind-speed bins;
- recirculation/direction-change bins;
- filament-age bins.

### Temporal dependence
For each trajectory:
- lag-1 residual correlation;
- directional persistence;
- conditional autocorrelation after B2/B3 normalization.

## 7. Destructive nulls

### N1 — spatial residual shuffle
Shuffle residuals among positions within wind-speed quantiles.

### N2 — wall-context shuffle
Preserve residual magnitudes but permute wall distance/direction.

### N3 — time shuffle
Permute residual order within trajectories.

### N4 — wind-context shuffle
Pair transition residuals with wrong local wind context.

A claimed context-dependent structure must weaken under its corresponding null.

## 8. L1 pass condition for generative modeling

A true **GENERATIVE-NEEDED** signal requires all of:

1. B0/B1 are materially inadequate.
2. B2 improves but leaves reproducible non-Gaussian/multimodal or temporal structure on the independent seed.
3. That remaining structure depends on physical context and vanishes under destructive nulls.
4. B3, if implemented, still leaves source-relevant stochastic structure that a simple Gaussian cannot capture.

If only B0 is bad but B2/B3 are enough:

\`M5 MAIN = NO-GO; SIMPLE PHYSICS/GAUSSIAN CORRECTOR MAY BE AUXILIARY\`.

## 9. L2 gate if L1 passes

Only then fit a minimal generative residual model.

Compare on an **unseen source position without retraining**:

- B1;
- B2;
- B3;
- generative model.

Construct downstream concentration/hit maps.

The generative model must improve:
- distribution fit;
- field prediction;
- eventually PMFS truth-source rank.

## 10. Critical anti-self-distillation warning

GADEN itself uses:
- Gaussian random perturbation;
- deterministic obstacle handling;
- deterministic wind field.

Therefore a complex generative network trained only on GADEN can easily become an expensive emulator of known code.

The paper-level M5 claim survives only if the learned source-agnostic transport representation:
- improves over PMFS's simpler transition family;
- generalizes to unseen source injection by construction;
- and produces a downstream localization gain.

Do not claim the complexity of the GADEN simulator itself as learned discovery.

## 11. Required outputs

Under:

\`evidence/generative_lagrangian_filament_world_model_v1/L1/\`

save:

- trajectory extraction manifest;
- pseudo-ID validation report;
- transition parquet/csv summary (large raw data may remain external with hashes);
- B0/B1/B2/B3 metrics;
- null metrics;
- residual distribution plots;
- decision:
  - \`GENERATIVE_NEEDED\`;
  - \`GAUSSIAN_SUFFICIENT\`;
  - \`INVALID_DATA_INTERFACE\`.

Commit after extraction and again after L1 decision.
