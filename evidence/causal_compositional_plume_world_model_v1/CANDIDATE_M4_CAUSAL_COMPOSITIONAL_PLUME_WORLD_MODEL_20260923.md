# Candidate M4 — Causal Compositional Plume World Model

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`  
Status: **KEEP — high-level main-thesis candidate pending intervention/data falsification**

## 1. Mother idea

The candidate transfers **compositional causal world modeling** into PMFS-style gas-source localization.

The scientific shift is:

> PMFS candidate evaluation is treated as a counterfactual intervention problem rather than a collection of unrelated forward simulations.

For candidate source `s`, PMFS effectively asks:

[
	ext{What would I observe if } do(S=s)?
]

The proposed world model explicitly factorizes the plume-generation process into reusable causal mechanisms and predicts outcomes under interventions on source, wind, geometry and other physical components.

Working name:

**Causal Compositional Plume World Model (CC-PWM)**

Paper-facing alternative:

**Counterfactual Plume World Modeling for Probabilistic Gas-Source Localization**

---

## 2. 2025 remote-field parent idea

### P1 — WM3C, ICLR 2025

Wang & Huang, *Modeling Unseen Environments with Language-guided Composable Causal Components in Reinforcement Learning*, ICLR 2025.

Core transferable principle:

- learn a world model as **composable causal mechanisms** rather than one entangled transition function;
- reuse learned components in unseen combinations;
- causal modularity supports compositional generalization;
- identification of meaningful components matters because new environments can be constructed by recombining known mechanisms.

The language-guided decomposition in WM3C is not transferred directly.

For plume physics, the decomposition is available from known physical semantics:
- source injection;
- wind/advection;
- obstacle/boundary transport;
- turbulent residual;
- sensing.

### P2 — Causal representation + invariance, ICLR 2025

Yao et al., *Unifying Causal Representation Learning with the Invariance Principle*, ICLR 2025.

Useful boundary:
- causal representation learning can often be understood through invariance/symmetry structure;
- causal claims should not be made only because a latent space is disentangled.

For this project, the causal structure must therefore be grounded by **actual interventions and physical mechanism changes**, not naming latent variables “causal.”

---

## 3. PMFS-specific causal graph

A minimal structural graph is:

[
S ightarrow Q
]

[
(W,O,Q,Z_{m turb}) ightarrow C
]

[
(C,X_{m robot},M_{m sensor}) ightarrow Y
]

where:

- (S): source candidate/location;
- (Q): source injection mechanism;
- (W): wind field;
- (O): obstacle / boundary geometry;
- (Z_{m turb}): unresolved stochastic turbulence;
- (C(x,t)): concentration / filament-density field;
- (X_{m robot}): robot measurement location;
- (M_{m sensor}): sensor response / threshold mechanism;
- (Y): HIT/MISS or concentration observation.

Important:

**robot motion does not change the plume dynamics** in the current benchmark.

It changes only the observation location.

This avoids the earlier invalid “action controls plume dynamics” world-model interface.

---

## 4. Intervention semantics

### Source intervention

[
do(S=s)
]

changes source injection while preserving:
- wind mechanism;
- obstacle mechanism;
- sensor mechanism.

### Wind intervention

[
do(W=w')
]

changes transport while preserving:
- source;
- geometry;
- sensing.

### Geometry intervention

[
do(O=o')
]

changes boundary/obstacle mechanism.

### Sensor intervention

[
do(M_{m sensor}=m')
]

changes concentration-to-observation conversion without changing physical dispersion.

The key value of a causal world model is that these mechanisms should be reusable independently.

---

## 5. Proposed world-model factorization

A practical first factorization:

[
Q_s = f_Q(S)
]

[
C_{t+1}
=
f_T(
C_t,
W_t,
O,
Q_s,
Z_t
)
]

[
Y_t
=
f_Y(
C_t,
X_t,
M_{m sensor}
).
]

Instead of one entangled model

[
F_	heta(S,W,O)ightarrow C,
]

learn structured modules:

[
f_Q,quad f_T,quad f_Y.
]

A stronger compositional version can split transport further:

[
f_T
=
f_{m advect}
oplus
f_{m obstacle}
oplus
f_{m diffuse}
oplus
f_{m stochastic}.
]

Do not over-factorize before data supports the decomposition.

---

## 6. Physical anchoring

The causal modules must be physically constrained.

### Source mechanism

[
Q_s(x)
]

must be localized to the candidate-source region.

### Advection mechanism

Wind enters through a vector transport term:

[
-
ablacdot(WC).
]

### Diffusion / stochastic spreading

Approximate:

[

ablacdot(D
abla C)
]

or learn only the unresolved residual around a low-fidelity physical operator.

### Obstacle mechanism

Walls change the boundary/transport mechanism, not merely pixels in an image.

Use:
- free-space mask;
- no-through-wall / no-flux behavior;
- PMFS/GADEN obstacle semantics.

### Observation mechanism

Convert concentration/filament density to:
- concentration measurement; or
- PMFS-style hit probability / HIT-MISS.

This separates physical forward error from sensor calibration error.

---

## 7. Why this is more than a neural surrogate

A normal source-conditioned PINO learns:

[
(S,W,O)mapsto C.
]

CC-PWM instead aims to learn mechanisms such that:

[
do(S=s'), do(W=w'), do(O=o')
]

can be recombined without retraining the entire forward map.

The scientific hypothesis is:

> causal modularity gives better **cross-source / cross-wind / cross-House compositional generalization** than a monolithic learned plume operator.

That is the hard empirical claim.

---

## 8. PMFS integration

Preserve:

- discrete PMFS source candidates;
- source probability map;
- closed-loop search.

Replace the candidate forward call.

### Native PMFS

[
s ightarrow h_s(x)
]

via independent filament simulation.

### CC-PWM

For every candidate:

[
do(S=s)
]

inside the same learned environmental mechanisms:

[
(W,O,f_T,f_Y).
]

Generate:

[
p_	heta(Y_{1:m}mid do(S=s),W,O,X_{1:m}).
]

Then update the PMFS source belief.

This makes PMFS candidate evaluation explicitly counterfactual.

---

## 9. Important novelty boundaries

Do NOT claim:

- first causal inference in source localization without a final search;
- first world model for robotics;
- first neural forward model for gas-source inversion;
- first PINN/PINO source inversion;
- first counterfactual simulation in science.

The current novelty hypothesis is narrower:

> **causal compositional world modeling of source / wind / geometry mechanisms for PMFS-style gas-source localization, with source candidates represented as interventions and tested for unseen mechanism recombinations.**

A final direct GSL collision audit is mandatory.

---

## 10. Main risk: causality may be unnecessary branding

This candidate is immediately NO-GO if a monolithic world model with the same capacity generalizes equally well.

The causal/compositional claim requires:

- known intervention labels;
- cross-combination generalization;
- module-swapping tests;
- mechanism-specific destructive nulls.

If the result is merely “factorized network works better,” do not call it causal.

---

## 11. Data requirement

This line needs **intervention structure**, not only random trajectories.

Minimum pilot dataset should vary:

### Source interventions
Several source positions under the same House/wind.

### Wind interventions
At least two wind conditions with some source positions held fixed if possible.

### Turbulence realizations
Multiple stochastic plume seeds for identical source/wind.

### Geometry environments
House01/02/03 provide environment changes.

A complete factorial grid is not initially required.

A deliberately sparse combinatorial design is actually useful:

train on some combinations and test on **unseen recombinations**.

Example:

- train: S1-W1, S2-W1, S1-W2;
- test: S2-W2.

This is the direct compositional-generalization test.

---

## 12. Tiny falsification — C0

Do NOT build a large causal latent model first.

Start from explicit known physical factors.

For one House:

1. choose 4 source positions;
2. choose 2 wind configurations if available;
3. generate 2 plume seeds per combination;
4. deliberately hold out source×wind combinations.

Compare:

A. monolithic small residual model:

[
F(S,W,O)ightarrow C
]

B. factorized causal/compositional model:

[
f_Q(S) + f_T(C,W,O)
]

with matched or lower parameter count.

Primary source-blind metrics:
- held-out combination field error;
- HIT/MISS predictive likelihood;
- physics residual.

Then freeze models and perform PMFS candidate replay.

Hard metric:

**truth-containing source-candidate rank on held-out source×wind combinations.**

If the factorized model does not beat the monolithic model in compositional generalization and source rank, kill M4.

---

## 13. Stronger C1 intervention test

For matched source/location:

- intervene only on wind;
- check whether source/injection representation remains invariant.

For matched wind:

- intervene only on source;
- check whether wind/transport representation remains invariant.

Required:

mechanism-specific representations should change only where physically expected.

If all latent modules shift under every intervention, the causal decomposition failed.

---

## 14. Destructive nulls

### N1 — intervention-label shuffle
Shuffle source/wind intervention labels.

Compositional benefit should collapse.

### N2 — mechanism swap
Swap wind modules between incompatible wind fields.

Prediction should change according to the swapped transport mechanism.

### N3 — source-module swap
Swap source injection module while preserving environment.

Predicted plume origin should follow the source intervention.

### N4 — obstacle destruction
Shuffle obstacle geometry while preserving free-cell ratio.

Cross-House generalization should degrade.

---

## 15. Comparison to M3 stochastic plume world model

### M3
Main claim:
- represent a **distribution over plume fields**;
- stochasticity/intermittency is the key missing object.

### M4
Main claim:
- represent plume generation as **composable causal mechanisms**;
- intervention/generalization is the key missing object.

They are independent hypotheses.

Do not merge them initially.

If both pass:
- M4 could become the main architecture;
- M3 stochastic generation could become the unresolved-turbulence module.

If M4 fails but M3 passes:
- use stochastic world model without causal claims.

---

## 16. Why M4 fits the requested “big idea” criterion

The mother idea is not an optimizer or score.

It is:

> **causal world modeling + compositional generalization under interventions.**

The gas-specific physics gives explicit mechanism semantics:
- source injection;
- wind transport;
- obstacle boundary interaction;
- stochastic turbulence;
- sensor observation.

This is a materially different scientific representation of PMFS candidate simulation.

---

## 17. Kill conditions

M4 is NO-GO as main if:

1. direct GSL prior art already performs equivalent causal compositional source/wind world modeling;
2. available/generated data does not contain sufficient interventions;
3. factorized model does not outperform a monolithic matched-capacity model on unseen combinations;
4. source-rank does not improve;
5. causal modules are not intervention-specific;
6. benefit survives intervention-label destructive null;
7. gains require House/source-specific truth tuning.

---

## 18. Current verdict

Mother-idea strength: **very high**.  
Physical interpretability: **very high**.  
GSL direct-collision risk found so far: **low-to-moderate; final audit required**.  
Data requirement: **moderate-to-high but intervention generation is controllable in GADEN**.  
Training complexity: **lower than full stochastic OFM if tested with small explicit modules first**.

Status:

`KEEP — PARALLEL LEAD CANDIDATE WITH M3`.
