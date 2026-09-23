# MAIN INNOVATION SEARCH CHARTER — PMFS/UAV Gas Source Localization

**Date:** 2026-09-23  
**Branch:** `research/main-innovation-search-parallel-v1`  
**Purpose:** Parallel main-innovation search for ChatGPT + Codex.

## 0. Mission

Find a **paper-level main innovation** for PMFS-style mobile gas-source localization (GSL), then only after that main idea survives, design two auxiliary modules.

The target is NOT a small PMFS tweak.

The target is a recent, high-level scientific/ML paradigm from a **remote field** that has not already been instantiated in GSL in essentially the same form, then make a gas-specific second derivation with real transport physics.

Examples of the *level* of idea requested:
- world models;
- causal learning;
- generative physical dynamics;
- stochastic process models;
- new scientific representation/learning paradigms;
- similarly large ideas.

Examples that are too small to be the main theme:
- replace one score/reward;
- another uncertainty metric;
- another Bayesian temperature;
- another acquisition function;
- another stopping threshold;
- generic robustness/DRO;
- generic OED;
- generic PINN/GNN/FNO transfer.

---

## 1. PMFS identity that should remain recognizable

Large changes are allowed, but the final method should remain recognizably descended from PMFS.

Preserve at least the following outer shell unless a very strong scientific reason says otherwise:

1. **candidate source space** rather than direct end-to-end coordinate regression;
2. **source probability/belief map** over candidates;
3. **physics-based or physics-anchored forward reasoning** from a candidate source to expected gas observations;
4. **closed-loop mobile sensing/search**.

Internals may be replaced aggressively:
- the forward simulator;
- the candidate likelihood/evidence model;
- the representation of plume uncertainty;
- movement criterion;
- source update;
- state representation.

The innovation should feel like:

> “PMFS rethought under a new scientific paradigm,”

not:

> “PMFS plus a patch.”

---

## 2. Hard definition of an acceptable main innovation

A candidate survives only if it satisfies **all** of the following.

### G1 — Big-idea level
The parent idea must be a recognizable scientific/ML paradigm, not a local optimization trick.

### G2 — Recency
Prefer 2025–2026 work. 2024 is acceptable only when it is the immediate foundation of a 2025–2026 direction.

### G3 — Venue/source quality
Prioritize:
- NeurIPS / ICML / ICLR / AISTATS / COLT / RSS / CoRL / ICRA / IROS;
- Nature-family / Science-family;
- top statistics/applied-math venues;
- strong domain venues when the idea is genuinely new.

Do not rely on random preprints as the sole scientific anchor when better sources exist.

### G4 — Remote-field transfer
The parent idea should come from a field meaningfully outside classical GSL:
- generative modeling;
- scientific ML;
- computational biology;
- physical world models;
- operator learning;
- causal representation learning;
- modern dynamics learning;
- etc.

### G5 — GSL novelty
Before implementation, search for direct collisions in:
- gas/odor source localization;
- plume source inversion;
- methane leak localization;
- mobile source-search robotics;
- convection/advection-diffusion source inversion.

A broad idea already used in GSL is not a valid main novelty just because our notation differs.

### G6 — Physical meaning
The gas-specific derivation must use real physical structure.

At minimum inspect:
- wind vector field;
- advection;
- stochastic dispersion/intermittency;
- obstacles/walls;
- source injection;
- relevant conservation/continuity/Fokker–Planck structure when appropriate.

**Wind must not be merely concatenated as a feature token if the parent idea supports a stronger physical role.**

### G7 — PMFS interface fit
There must be a concrete path from the parent idea to PMFS’s candidate-source probability-map workflow.

### G8 — Minimal falsifiability
Before full implementation, there must be a small offline test that can kill the idea quickly.

### G9 — Source identity
The main scientific gate is:

> **truth-containing source-candidate rank.**

Endpoint error, top-5 centroid, pretty maps, NLL, or reconstruction error cannot rescue a candidate whose source-identity ranking does not improve.

---

## 3. Target architecture: 1 main + 2 auxiliaries

Final paper architecture should eventually contain:

- **1 main innovation:** carries the paper’s scientific thesis;
- **2 auxiliary innovations:** solve two specific weaknesses of the main idea.

The three modules may come from different remote fields.

Do **not** invent the two auxiliaries before the main idea has a positive empirical signal.

Auxiliaries must not be decorative.

Examples of legitimate roles:
- enforce physical constraints;
- calibrate uncertainty;
- make the main representation computationally tractable;
- improve source declaration;
- make active sensing exploit the new representation.

---

## 4. Search loop

Run this loop continuously until multiple serious candidates survive.

### Step A — remote-field discovery
Search 2025–2026 top work for high-level paradigms.

For each candidate save:
- paper;
- venue/year;
- one-sentence mother idea;
- why it could map to PMFS;
- what scientific assumption in PMFS it would replace.

### Step B — GSL collision audit
Search GSL/source-inversion literature before coding.

Classify:
- **DIRECT COLLISION** — same scientific idea already used for source localization;
- **NEAR COLLISION** — broad idea exists, but proposed gas-specific mechanism may differ;
- **OPEN** — no close GSL instantiation found.

If DIRECT COLLISION: kill as main and keep only if useful as an auxiliary.

### Step C — interface audit
Write down exact PMFS objects changed.

Examples:
- `candidate source -> one mean hit map`
  becomes
  `candidate source -> stochastic field distribution`;

or:
- `heuristic probability update`
  becomes
  a new representation/inference object.

If the mapping is only “replace reward X with reward Y,” kill.

### Step D — physics derivation
Show how:
- wind;
- obstacles;
- source position;
- transport;
- stochasticity

enter the new mechanism.

### Step E — data gate
Before training/building:
- identify exact existing data;
- identify missing data;
- estimate regeneration cost;
- do not assume data exist.

### Step F — tiny falsification
Build the smallest possible source-blind test.

No full closed loop yet.

### Step G — truth reveal
Only after all candidate outputs/parameters are frozen.

Primary outcome:
- truth-source candidate rank.

### Step H — independent realization + null
A positive signal must survive:
- an independent plume realization;
- a destructive null;
- a geometry-confound check.

### Step I — decision
Commit one of:
- `ADVANCE`
- `HOLD`
- `NO-GO`

If NO-GO, continue the search automatically. Do not ask the user whether to continue.

---

## 5. Experimental discipline

### No truth-driven tuning
Forbidden:
- choosing hyperparameters after inspecting truth rank;
- one coefficient per House;
- selecting a candidate only because one seed happened to improve;
- changing the evaluation subset after truth reveal.

### Independent plume realizations
A candidate must eventually be evaluated across independently generated plume realizations.

### Destructive nulls
Each mechanism must have a null that destroys the proposed causal/physical structure while preserving simple marginals.

Examples:
- shuffle wind-to-plume pairing;
- shuffle source labels;
- spatially permute residuals;
- destroy graph/obstacle geometry;
- rotate/permute physical vector fields.

If performance survives the null, suspect a shortcut.

### Geometry confounds
Check whether gains are really due to:
- distance to source;
- room/obstacle geometry;
- source-grid density;
- candidate-cell size;
- path length.

### No endpoint-only rescue
Truth-source rank is the hard gate.

---

## 6. Baseline integrity

The historical six R2 runs are **VGR-adapted PMFS**, not proven strict Native PMFS.

The baseline-recovery branch has already established:
- the user’s official PMFS ZIP matches audited upstream `humble` files;
- official ground-truth-wind runtime path can be restored;
- old R2 differed materially from official PMFS settings.

Use repaired Native evidence for new main-method decisions whenever available.

Do not turn a baseline bug into a claimed paper innovation.

---

## 7. Known NO-GO / collision history

Do not restart these as the main idea unless a genuinely new scientific derivation changes the problem.

### Previously empirically weak / killed
- HCMC/HCRC cross-scale renormalization;
- HCCE causal emergence;
- Mori–Zwanzig / memory kernels;
- Koopman/delay;
- large deviations;
- time irreversibility;
- computational mechanics;
- Hodge/Helmholtz;
- topology;
- probability current;
- simple proper scoring;
- first-passage/TPT;
- static operator correction;
- generic partial identification;
- generic candidate discriminability;
- naive active information gain;
- naive distributional-forward statistics extracted from the same PMFS simulator.

### Prior-art collisions / too adjacent
- generic SBI as the main idea;
- PINN/GNN in GSL;
- generic deterministic neural operator / PINO in GSL;
- generic OT/UOT;
- generic robust OED / sensor placement;
- multi-model plume fusion;
- Rényi-infotaxis;
- sequential OED with nuisance parameters;
- source localization with wind nuisance via vsOED;
- direct adjoint source localization;
- generic active multihypothesis testing.

### Demoted technical/auxiliary ideas
- transport-orthogonal source information;
- SATI / robust transport acquisition;
- e-process / anytime-valid source stopping.

These may be useful as auxiliaries, but they currently do not meet the requested main-theme standard.

---

## 8. What a strong candidate should look like

A strong candidate should change one of these deep objects:

### Representation
Example:
- one deterministic plume map
  -> a generative stochastic plume process/world model.

### Causal factorization
Example:
- source and environment entangled
  -> explicit causal mechanism/intervention structure.

### Dynamics model
Example:
- hand-coded stochastic simulator
  -> learned physics-anchored world dynamics with a principled reference process.

### Inference object
Only if it is a genuinely new scientific object, not merely a score.

---

## 9. Candidate-card template

For every serious candidate, create:

`evidence/main_innovation_search/<candidate_id>/CANDIDATE_CARD.md`

Required fields:

- **Mother idea**
- **Remote field**
- **2025–2026 anchors**
- **What PMFS assumption is replaced**
- **Exact PMFS interface**
- **Gas-specific physical derivation**
- **Wind role**
- **Obstacle role**
- **Stochasticity role**
- **Nearest GSL collisions**
- **Why it is not merely a score/reward tweak**
- **Data needed**
- **Tiny falsification**
- **Truth-rank gate**
- **Destructive null**
- **Kill conditions**
- **Current verdict**

---

## 10. Current lead candidate

Current lead:

**Physics-Anchored Stochastic Plume World Model**

Parent ideas:
- Operator Flow Matching / function-space stochastic process learning;
- non-zero-drift / non-gradient flow matching;
- physics-constrained generative dynamics.

Core proposed shift:

[
	ext{candidate source}
	o
	ext{single PMFS hit map}
]

becomes

[
	ext{candidate source + wind + geometry}
	o
	ext{distribution over physically plausible plume fields}.
]

This candidate is **not pre-approved**.

It must pass the separate validation charter.

---

## 11. Git discipline

Every meaningful stage is committed immediately.

Suggested prefixes:
- `search:`
- `audit:`
- `theory:`
- `evidence:`
- `decision:`

Do not wait until the end.

Do not delete failed branches/evidence.

Negative results are first-class evidence.

---

## 12. Reporting style to user

The user prefers:
- concise updates;
- results over long derivations;
- clear KEEP/HOLD/NO-GO;
- direct truth-rank numbers;
- minimal formula dump unless a derivation is essential.

Do the long derivation in GitHub evidence files, not in chat.

---

## 13. Stop condition for the search

Do not stop because one idea sounds elegant.

Stop only when at least one candidate has:

1. strong remote-field parent idea;
2. no direct GSL collision;
3. clear physical derivation;
4. compatible data/interface;
5. positive source-blind mechanism signal;
6. positive truth-source-rank signal;
7. independent-realization support;
8. destructive-null support.

Only then promote it as the paper’s main innovation.
