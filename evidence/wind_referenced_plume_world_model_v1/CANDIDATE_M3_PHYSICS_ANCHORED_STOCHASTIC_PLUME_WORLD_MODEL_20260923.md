# Candidate M3 — Physics-Anchored Stochastic Plume World Model

Date: 2026-09-23  
Branch: \`research/wind-referenced-plume-world-model-v1\`  
Status: **LEAD MAIN-THESIS CANDIDATE — pending data/interface falsification**

## 1. Paper-level mother idea

Do **not** frame this as:
- a new PMFS score;
- a robust acquisition function;
- a generic PINN;
- a generic GNN;
- a deterministic neural-operator surrogate.

The scientific shift is:

> **replace PMFS's single deterministic/Monte-Carlo-averaged forward hit map for each source candidate with a physics-anchored stochastic world model over entire plume fields.**

The latent object is no longer one map

\[
h_s(x)
\]

but a conditional random function

\[
H_s(\cdot)\sim
\mathcal P_\theta
\big(
H\mid
s,\;w(\cdot),\;O(\cdot),\;\text{physics anchor}
\big).
\]

This is a different inferential representation:
- source candidate remains discrete;
- PMFS probability map remains;
- robot still performs closed-loop source search;
- but each source hypothesis predicts a **distribution over plausible plume fields**, not one averaged field.

Working name:

**Physics-Anchored Stochastic Plume World Model (PA-SPWM)**

Alternative paper-facing name:

**Generative Plume World Model for Probabilistic Source Localization**

---

## 2. Remote-field parent ideas

### P1 — Operator Flow Matching, NeurIPS 2025

Shi, Ross, Asimaki, Azizzadenesheli,  
*Stochastic Process Learning via Operator Flow Matching*, NeurIPS 2025.

Key transfer:
- learn stochastic processes directly in function space;
- model distributions over functions, not fixed-resolution vectors;
- query arbitrary spatial points;
- provide predictive density and functional regression.

This is a stronger match to mobile plume sensing than an ordinary deterministic neural operator because the robot only observes sparse spatial samples while the latent plume is a random field.

### P2 — Curly Flow Matching, NeurIPS 2025

Petrović et al.,  
*Curly Flow Matching for Learning Non-gradient Field Dynamics*, NeurIPS 2025.

Key transfer:
- standard flow/bridge formulations can impose gradient/least-action biases;
- natural systems with circulation/rotation need non-gradient dynamics;
- use a **non-zero drift reference process** informed by measured/inferred velocities;
- demonstrated on single-cell dynamics, ocean currents and CFD.

Gas transport in obstacle-rich indoor wind is also non-gradient:
- recirculation;
- vortices;
- obstacle-induced turning;
- anisotropic advection.

The transferable principle is therefore:
- known/measured wind is not just another input channel;
- it should act as a **reference physical drift** around which stochastic residual dynamics are learned.

### P3 — Continuous Flow Operator, ICLR 2026

Hou, Huang, Perdikaris,  
*CFO: Learning Continuous-Time PDE Dynamics via Flow-Matched Neural Operators*, ICLR 2026.

Key transfer:
- flow matching can be combined with neural operators for continuous-time PDE dynamics;
- improves long-horizon stability and data efficiency;
- supports irregular temporal sampling.

This is relevant if dynamic plume snapshots are available.

### P4 — Flow world models, 2026 robotics

Recent world-model work uses flow matching to model stochastic multi-modal futures rather than deterministic mean futures.

This supports the broader world-model narrative but should not be used as the primary novelty anchor unless peer-reviewed/venue status is verified.

---

## 3. Critical GSL prior-art boundary

### C1 — Physics-guided neural network GSL already exists

Prieto Ruiz et al., ISOEN 2024:
- source location is an input;
- a physics-guided NN approximates gas dispersion;
- the network accelerates the inverse problem.

Therefore do not claim:
- first learned gas-dispersion surrogate for source localization;
- first physics-guided NN for GSL.

### C2 — Physics-informed neural operator GSL is already occupied

A 2026 IROS-accepted work by Quanqi Zheng and Lei Chen is publicly listed as:

*A physics-informed neural operator for gas source localization in turbulent environments.*

Therefore do not claim:
- first neural operator for gas source localization;
- first PINO for GSL;
- first source-conditioned operator surrogate.

### Current remaining distinction

The M3 candidate survives only if the model is genuinely:

1. **stochastic/generative**, not point-estimate operator regression;
2. **function-space**, so sparse mobile observations can condition/query the field at arbitrary points;
3. **physics-anchored**, with PMFS/advection-wind providing a reference model rather than being replaced by an unconstrained black box;
4. used to propagate **field-distribution uncertainty into candidate-source inference**, not only to accelerate a deterministic PDE solve.

A final audit of the 2026 IROS paper is required once full text/code becomes available.

---

## 4. Why PMFS gives the right shell

PMFS already has the correct outer structure:

1. discretize candidate source space;
2. simulate a plume/hit map for each source candidate;
3. compare predicted and measured gas maps;
4. update source probability;
5. move based on predicted information.

We retain 1, 4 and 5.

We replace only step 2's representation:

### Native PMFS

\[
s
\longrightarrow
h_s(x)
\]

one Monte-Carlo-averaged candidate hit map.

### Proposed world model

\[
(s,w,O,\xi)
\longrightarrow
H_s(x;\xi)
\]

where \(\xi\) indexes plausible stochastic plume realizations.

Thus each candidate source generates

\[
\{
H_s^{(1)},\ldots,H_s^{(K)}
\}
\]

or a tractable conditional density in function space.

---

## 5. Physics anchor — do not learn plume physics from scratch

A pure generative network is not acceptable.

Define a low-fidelity anchor

\[
H_s^{0}
=
\mathcal F_{\rm PMFS}
(s,w,O)
\]

using:
- official PMFS filament simulation; or
- a cheap advection-diffusion approximation.

The learned world model predicts a stochastic correction:

\[
\boxed{
H_s
=
\Psi
\left(
H_s^{0}
+
R_\theta(s,w,O,\xi)
\right)
}
\]

where:
- \(R_\theta\) is a random function;
- \(\Psi\) enforces the output range, e.g. sigmoid/logit representation for hit probability.

This gives the architecture a clear interpretation:

> PMFS supplies the physics prior; the generative model learns the unresolved turbulent residual.

This is preferable to replacing PMFS with a black-box FNO.

---

## 6. Wind is a dynamical constraint, not a feature token

The wind field must enter at two levels.

### Level A — physical anchor

PMFS/advection physics uses the actual vector field

\[
w(x)
\]

to move material downwind.

### Level B — residual reference drift

For a dynamic formulation, the stochastic correction process should be centered around a non-zero wind-referenced drift rather than an isotropic/zero-drift generative bridge.

Conceptually:

\[
dZ_t
=
b_{\rm wind}(Z_t,w,O)\,dt
+
r_\theta(Z_t,s,w,O,t)\,dt
+
\sigma\,dW_t.
\]

- \(b_{\rm wind}\): physical/reference transport;
- \(r_\theta\): learned unresolved residual;
- \(\sigma dW_t\): stochastic plume variability.

This is the key Curly-FM-inspired second derivation.

Do not implement this full dynamic version before the residual stochastic-field probe is positive.

---

## 7. Physical constraints

The learned residual/world model must respect at least:

### P1 — obstacle support
No gas probability should propagate through occupied cells.

### P2 — wall boundary behavior
Use a no-through-wall / no-flux penalty or PMFS-consistent obstacle transition.

### P3 — advection alignment
Residual generation cannot systematically reverse the known wind-driven transport without evidence.

A possible soft constraint:

\[
\mathcal L_{\rm adv}
=
\|
\partial_t c
+
\nabla\cdot(wc)
-
\nabla\cdot(D\nabla c)
-
q_s
\|^2
\]

for dynamic concentration fields.

### P4 — positivity / probability range
Use a positive concentration transform or logit hit-probability representation.

### P5 — source injection locality
The source-conditioned field must inject mass/evidence from the candidate source region rather than arbitrary remote cells.

### P6 — optional global conservation balance
For a bounded control volume,

\[
\frac{d}{dt}\int_\Omega c\,dx
=
Q_s
-
\int_{\partial\Omega}cw\cdot n\,dS
-
\text{losses}.
\]

Do not enforce exact mass conservation if GADEN/source/sensor processing makes it invalid; use only after checking the data contract.

---

## 8. Why a stochastic field is scientifically useful

A deterministic PINO/FNO can output an accurate mean plume and still fail source localization in turbulent sparse sensing.

Two source candidates can have similar mean fields but different:
- intermittency;
- hit/miss distribution;
- spatial covariance;
- multimodal plume paths.

A stochastic process world model can represent

\[
p(
H(x_1),\ldots,H(x_m)
\mid s,w,O
)
\]

for the actual robot measurement locations.

This allows source inference to use:
- mean field;
- variance;
- spatial joint structure;
- multi-realization likelihood.

This is fundamentally different from the previously failed naive distributional-forward probe, which extracted stochastic statistics from the same fixed PMFS simulator.

Here the forward family itself is learned as a conditional stochastic process anchored to higher-fidelity plume physics/data.

---

## 9. Candidate source update

First version:

For observations

\[
Y_t=\{y_i\}_{i=1}^{m}
\]

at sampled locations \(X_t=\{x_i\}\),

compute source evidence from the world-model predictive density:

\[
\boxed{
L_s
=
p_\theta(
Y_t
\mid
X_t,s,w,O
)
}
\]

and update

\[
\pi_{t+1}(s)
\propto
\pi_t(s)L_s.
\]

If exact joint density from OFM is not practical in the first probe:

- use conditional ensemble likelihood;
- CRPS / energy score only as diagnostics;
- do not claim full probabilistic inference until density calibration is verified.

The hard scientific metric remains truth-source candidate rank.

---

## 10. Movement

Do not invent a new planner before the forward model passes.

Stage 1:
- retain Native PMFS movement;
- replace only source-forward representation/inference.

Only if source-rank improves should movement exploit generative uncertainty.

Possible later acquisition:
- expected reduction in candidate posterior entropy under samples from the world model;
- disagreement between source-conditioned stochastic processes.

This is an auxiliary, not part of the initial main-method proof.

---

## 11. Data requirement and feasibility audit

This line is only viable if we have enough high-fidelity field information.

### Preferred training supervision

For multiple source/wind/realization configurations:
- GADEN concentration or hit-probability snapshots/fields;
- source coordinates;
- wind fields;
- occupancy geometry.

### Lower-data strategy

Do not train a full world model from scratch.

Use:

\[
\text{high-fidelity field}
=
\text{PMFS low-fidelity field}
+
\text{learned residual}.
\]

This is data-efficient because the network models only systematic residual structure.

### Immediate question

Before training anything, inventory the existing VGR/GADEN archive for:
- full spatial concentration snapshots;
- plume simulation files;
- multiple time frames;
- multiple source positions/configurations;
- whether only robot-path measurements were saved.

If only sparse trajectory observations exist, full field OFM is likely not identifiable from current data and this candidate should be demoted unless additional simulation data can be generated cheaply.

---

## 12. Hard falsification plan

### W0 — data/interface gate

No training.

Inventory existing data.

PASS only if we have, or can cheaply regenerate:
- spatial plume fields or sufficiently dense simulator states;
- at least multiple independent plume realizations;
- exact source/wind/geometry labels.

If not: HOLD/NO-GO before model building.

### W1 — residual predictability gate

Using recovered Native PMFS and high-fidelity GADEN fields:

\[
R
=
H_{\rm GADEN}
-
H_{\rm PMFS}.
\]

Before any neural model, test whether residuals contain repeatable structure across:
- time;
- plume realization;
- neighboring source positions;
- wind-conditioned cases.

Metrics:
- cross-realization correlation;
- low-rank energy;
- conditional predictability from wind/obstacle/source geometry;
- destructive spatial permutation null.

If residuals are indistinguishable from unstructured noise, learning a world model is unlikely to help source identity.

### W2 — tiny deterministic residual baseline

Fit a very small residual operator/regressor.

This is not the final method.

Purpose:
- test whether learned forward correction improves truth-source rank at all.

If a simple residual learner cannot produce any positive source-rank signal, do not jump to OFM to rescue it.

### W3 — stochastic-process gain

Compare:
1. Native PMFS;
2. deterministic residual operator;
3. stochastic OFM residual world model.

Hard gate:
- truth-source rank on independent plume realizations.

The stochastic model must beat the deterministic residual model, not only Native PMFS.

Otherwise the "stochastic world model" narrative is unsupported.

### W4 — physics-ablation gate

Ablate:
- wind conditioning;
- PMFS anchor;
- obstacle constraint;
- stochastic residual.

Expected:
- removing physics anchor/wind should harm cross-environment generalization;
- removing stochasticity should harm cases with intermittent/multimodal plume evidence.

### W5 — cross-House generalization

Train/freeze without truth tuning per House.

Evaluate House01/02/03 held-out combinations.

If the model only memorizes one House, kill the main claim.

---

## 13. Destructive nulls

### N1 — wind shuffle
Pair plume fields with wrong wind fields while preserving marginal wind statistics.

Performance advantage should collapse.

### N2 — source-label shuffle
Break source-field correspondence.

Source-rank gain should disappear.

### N3 — obstacle shuffle
Preserve free-cell fraction but destroy geometry.

If performance remains unchanged, the claimed geometry/physics conditioning is suspect.

### N4 — residual permutation
Preserve marginal residual histogram but destroy spatial structure.

A useful learned residual model should fail.

---

## 14. Why this candidate meets the requested "big idea" criterion

The main story is not "we tuned PMFS."

It is:

> **move from deterministic simulation-based belief updates to a physics-anchored generative world model of stochastic plume fields.**

The cross-domain source ideas are:
- generative flow matching;
- stochastic-process learning in function space;
- non-zero-drift flow dynamics from biological/ocean trajectory inference;
- neural-operator world modeling.

The gas-specific second innovation is:
- wind/obstacle/source physics are not generic conditioning tokens;
- they define the anchor/reference dynamics;
- the network learns only unresolved stochastic transport.

---

## 15. Main risks

### R1 — direct 2026 gas-PINO collision
If the IROS 2026 paper is itself probabilistic/generative and models full source-conditioned field distributions, this line may lose novelty.

### R2 — data hunger
OFM can be too expensive for current data.

Residual anchoring is intended to reduce this risk.

### R3 — simulator-to-real gap
Training only on GADEN may learn GADEN, not reality.

Cross-realization/House tests are mandatory.

### R4 — stochastic model adds no source information
If deterministic residual correction performs equally well, OFM is unnecessary.

### R5 — PMFS shell becomes unrecognizable
Do not replace source-candidate probability map and closed-loop logic with an end-to-end source-coordinate network.

The paper should remain visibly a next-generation PMFS forward model.

---

## 16. Current verdict

**Mother-idea strength:** very high.  
**2025–2026 top-venue support:** very high.  
**Physical interpretability:** high.  
**Direct GSL collision risk:** moderate because PINO-GSL exists, but stochastic generative operator/world-model distinction appears open so far.  
**Data feasibility risk:** high and must be tested before implementation.

Status:

\`KEEP — LEAD MAIN-INNOVATION CANDIDATE PENDING W0/W1 DATA GATES\`.
