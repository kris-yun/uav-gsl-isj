# CODEX TASK — M4 Pre-Network Mechanism Audit (I0 / S0 / P0)

Date: 2026-09-23  
Branch: \`research/invariant-mechanism-plume-world-model-v1\`  
Priority: **mechanism falsification only — do not train a neural model**

## 0. Goal

Test whether the M4 thesis has real physical structure in existing GADEN data before implementing any neural operator / MoE / GNN.

M4 thesis:

> plume dynamics can be decomposed into reusable physical mechanisms whose residual law is more invariant across Houses than the raw field dynamics.

Run three audits:

- **I0:** known-mechanism residual structure;
- **S0:** contextual local symmetry;
- **P0:** dissipativity / supply-balance sanity.

No source-localization truth metric is used in this task.

---

## 1. Read the branch docs first

Read:

- \`evidence/invariant_mechanism_plume_world_model_v1/CANDIDATE_M4_INVARIANT_MECHANISM_PLUME_WORLD_MODEL_20260923.md\`
- \`evidence/invariant_mechanism_plume_world_model_v1/M4_V2_MECHANISM_SPLITTING_ARCHITECTURE_20260923.md\`
- \`evidence/invariant_mechanism_plume_world_model_v1/AUX_A_CONTEXTUAL_LOCAL_SYMMETRY_20260923.md\`
- \`evidence/invariant_mechanism_plume_world_model_v1/AUX_B_DISSIPATIVITY_CONSTRAINED_FUSION_20260923.md\`

Do not modify the recovered Native-PMFS baseline branch or old R2 evidence.

---

## 2. Existing local GADEN realization roots

Use the 2026-09-22 independent realization set.

Find the exact roots/manifests under:

\`/home/zyc/hcmc_v1_independent_data_20260922/\`

Expected existing source positions:

- House01: approximately \`(-0.40,-2.90,-0.30)\`
- House02: approximately \`(0.00,-1.00,0.20)\`
- House03: approximately \`(-0.45,1.90,-0.10)\`

Each House has at least two independent plume realizations/seeds.

Do not regenerate these runs.

Record exact paths, simulation parameters, source coordinates, wind configuration, GADEN/gaden_core provenance.

---

## 3. Extract time-resolved 2-D fields

Preferred route:

- use installed GADEN playback/core API that reads the existing realization;
- query \`SampleConcentration(point)\` / equivalent at selected times;
- query the corresponding wind field;
- do not reverse-engineer compressed binary formats if the public API can read them.

If playback API is unavailable, use the same GADEN player/service stack used by the validated runs and batch-query the field.

### Height

Use the same physical gas-sensor height / 2-D plane used by the VGR benchmark for each House.

Record z exactly.

### Times

First pilot:

\[
t \in \{20,30,40,50,60\}\,\mathrm{s}
\]

or the nearest valid saved playback times.

If 20 s is still too early for a meaningful field, do not silently change the list; report it and add one predeclared secondary set \{60,90,120,150,180\} if available.

### Grid

Start from every 2nd or 3rd native 0.1-m cell:
- stride 0.2–0.3 m;
- free cells only;
- preserve occupancy and wall geometry metadata.

For every House × seed × time × sampled cell save:

\`x,y,z,t,c,wind_u,wind_v,wind_w,free,wall_distance,wall_nx,wall_ny\`

If wall normal/distance cannot be obtained robustly, compute them from occupancy with a documented deterministic distance transform.

---

## 4. Basic extraction parity gate

Before scientific analysis:

- sample 10 fixed source-blind points through both the extraction path and existing GADEN service/player if possible;
- verify concentration/wind agreement to numerical tolerance;
- verify occupied/free geometry alignment;
- hash the extracted datasets.

If extraction parity fails, stop.

---

## 5. I0 — mechanism residual audit

We need a diagnostic residual, not a perfect CFD solver.

For interior free cells away from source and outer boundaries, estimate:

\[
\partial_t c
\]

from adjacent extracted times if temporal spacing supports it.

If 10-s spacing is too coarse, extract a denser local time sequence for I0 only (e.g. 1–2 s) without changing S0/P0 datasets.

Compute advection:

\[
A=-\nabla\cdot(wc).
\]

Use a conservative finite-volume / finite-difference discretization consistent with the grid.

Compute diffusion for a **predeclared source-blind panel**:

\[
D \in \{0,\ D_1,\ D_2,\ D_3\}
\]

where nonzero values must be derived from:
- GADEN filament growth parameters, or
- documented physical conversion/metadata,

not chosen from source-localization truth.

Residual:

\[
R_D
=
\partial_t c-A-\nabla\cdot(D\nabla c).
\]

Exclude a small documented neighborhood around the source for this first audit if source-injection discretization is ambiguous.

### Report for each House/seed

- energy/norm of \(\partial_t c\);
- energy explained by advection;
- additional reduction from diffusion;
- residual norm ratio;
- residual spatial autocorrelation / Moran-like statistic or equivalent;
- residual correlation across independent plume seeds after matching physical context.

### Nulls

- wrong-House wind pairing;
- spatially shuffled wind;
- sign-reversed wind.

A physically meaningful mechanism subtraction should outperform these nulls.

---

## 6. S0 — contextual local-symmetry audit

Use the I0 residual field, not raw concentration alone.

### Free-space patches

Select patches:
- sufficiently far from walls;
- non-negligible wind;
- source-blind deterministic thresholds based on geometry/wind quantiles.

For every patch compare two representations:

A. raw map coordinates;  
B. translated patch + rotated so local wind points to +x.

Measure cross-House discrepancy with at least two simple metrics:
- covariance / feature distance;
- MMD or nearest-neighbor prediction error.

Primary sign:

\[
D_{\rm wind-frame}<D_{\rm raw}.
\]

### Wall patches

Select cells near one dominant wall.

Compare:

A. raw;
B. wind frame;
C. wall-normal/tangent frame with wind expressed as \((w_n,w_t)\).

Expected mechanism-specific sign:
- free patches: wind frame helps;
- wall patches: wall-relative frame helps more than a universal global frame.

### Destructive nulls

- random frame rotation;
- shuffled wind directions;
- shuffled wall normals.

Correct physical frames must outperform null frames.

---

## 7. P0 — dissipativity / supply-balance sanity

Define

\[
H(t)=\frac12\sum_i c_i(t)^2\,\Delta V
\]

on the extracted plane as a diagnostic only.

Because this is a 2-D slice of a 3-D open system, do **not** claim an exact conservation law.

Test whether a useful qualitative/relative accounting exists:

- estimate temporal change \(\dot H\);
- estimate advective boundary transport on the 2-D free-domain boundary;
- estimate diffusion contribution for the same source-blind D panel;
- separate source-near regions from source-far regions.

If the installed GADEN API makes it cheap, add one optional **source-off microexperiment** in House02:
- run source ON to a fixed time;
- switch source OFF;
- keep wind unchanged;
- observe whether concentration-storage decays after accounting for outflow.

Do this only if source toggling is straightforward. Do not rebuild GADEN.

### P0 PASS meaning

Not "port-Hamiltonian equation exactly holds."

PASS only means:
- storage/supply/dissipation decomposition has a stable empirical sign/relationship strong enough to constrain a learned residual.

If 2-D slicing destroys the accounting, mark P0 NO-GO and drop Aux B without affecting M4 main thesis.

---

## 8. Cross-seed / cross-House discipline

Use both plume realizations per House where feasible.

No House-specific thresholds tuned from the outcomes.

All analysis choices must be frozen in a config/manifest before comparing Houses.

---

## 9. Decision table

Create one final table:

| Gate | PASS criterion | Result |
|---|---|---|
| Extraction | field/wind/geometry parity | |
| I0 | known physics reduces dynamic residual vs nulls and leaves structured residual | |
| S0-free | wind canonicalization improves cross-House alignment vs random frames | |
| S0-wall | wall frame improves wall-regime alignment vs null frames | |
| P0 | useful storage/supply/dissipation relation exists | |

### Main M4 decision

- **KEEP** if I0 passes and at least one S0 regime passes.
- **HOLD** if extraction/data resolution blocks the test but structure is not disproven.
- **KILL** M4 main thesis if known mechanism decomposition provides no improvement over nulls and residuals remain House-specific/unstructured.

P0 is auxiliary-only:
- failure kills Aux B, not M4.

---

## 10. Required outputs

Commit under:

\`evidence/invariant_mechanism_plume_world_model_v1/pre_network_audit_20260923/\`

At minimum:

- \`PRE_NETWORK_AUDIT_DECISION.md\`
- \`provenance.json\`
- \`audit_config.json\`
- \`extraction_parity.csv\`
- \`I0_mechanism_residual_metrics.csv\`
- \`S0_symmetry_metrics.csv\`
- \`P0_balance_metrics.csv\`
- compact extracted field artifacts or hashes + paths if too large;
- exact scripts.

Do not commit multi-GB raw arrays to GitHub.

Commit and push after extraction parity, then after I0/S0/P0.

Stop before neural-model training.
