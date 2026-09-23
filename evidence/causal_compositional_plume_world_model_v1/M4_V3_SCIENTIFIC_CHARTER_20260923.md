# M4-v3 Scientific Charter — Interventional Evolution Propagator for PMFS

Date: 2026-09-23  
Branch: `research/m4-v3-interventional-evolution-propagator`  
Status: **DEVELOPMENT ONLY — NO SCIENTIFIC ADVANCE CLAIM**

## 0. Why M4-v2 was killed

M4-v2 produced a real same-House field-MSE advantage, but the frozen transport-response audit showed that its W1→W2 response amplitude was only 4.31%–5.25% of the paired real-GADEN wind intervention, while its source-intervention response retained 80.60%–85.83% of the real source intervention. The predicted wind/source response ratio was only 5.35%–6.11% of the true ratio.

Therefore the v2 advantage is not accepted as evidence for a reusable transport mechanism. The likely reason is structural: v2 used fixed spatial convolutions and allowed wind to modulate them through pointwise gates, so wind did not explicitly move state along the local velocity field.

M4-v3 must repair this mechanism, not tune v2.

---

## 1. Scientific thesis

The main claim to test is:

> For a prescribed geometry and wind history, plume generation can be represented by a **source-agnostic causal evolution propagator** acting on a separate source-injection process. Source interventions change the forcing term; wind interventions change the propagation operator.

For a passive scalar concentration field (C),

[
partial_t C = mathcal L_{W(t),O} C + Q_S(t) + eta,
]

where:
- (Q_S) is source injection;
- (mathcal L_{W(t),O}) contains advection, diffusion, obstacle/boundary effects and loss;
- (eta) represents unresolved stochastic plume variability.

The corresponding non-autonomous evolution form is

[
C(t) =
U_{W,O}(t,t_0) C(t_0)
+
int_{t_0}^{t} U_{W,O}(t,	au) Q_S(	au),d	au .
]

This is the mechanistic compositionality that M4-v3 tests.

### Intervention semantics

- `do(S=s')`: change (Q_S), keep (U_{W,O}) fixed.
- `do(W=w')`: change (U_{W,O}), keep (Q_S) fixed.
- `do(O=o')`: change the propagation domain/boundary component, keep source identity separate.

A learned architecture is not called causal merely because it has separate modules. The intervention effects must match the physical intervention effects on held-out GADEN data.

---

## 2. Why this is physically appropriate for GADEN

GADEN/GADEN-RT uses a filament/Lagrangian dispersion model:
- gas is represented by discrete filaments;
- filaments are advected by the local airflow field;
- turbulence/molecular effects spread the filament distribution;
- concentration is obtained by summing filament contributions.

Therefore a source-independent transport mechanism is physically meaningful: source location determines where mass is injected, while local wind drives subsequent transport.

M4-v3 targets this distinction directly.

---

## 3. Prior-art boundary — claims that are forbidden

The following are already occupied and cannot be presented as our novelty:

1. **Physics-guided neural networks for GSL**  
   Prieto Ruiz et al., ISOEN 2024, `10.1109/ISOEN61239.2024.10556061`.

2. **Green-function-based GSL**  
   Prieto Ruiz et al., EUSIPCO 2024, `10.23919/EUSIPCO63174.2024.10715286`.  
   This work uses a parameterized Green's function for a Poisson-model GSL formulation.

3. **Inverse advection-diffusion PINNs for pollution-source localization**  
   Chuprov et al., 2025, arXiv:2503.18849.

4. **Generic physics-informed neural operator for GSL**  
   Quanqi Zheng and Lei Chen, accepted IROS 2026, title:  
   *A physics-informed neural operator for gas source localization in turbulent environments*.  
   Until its full manuscript is publicly inspectable, M4-v3 must assume that generic claims such as
   "first neural operator for GSL" or "first physics-informed operator for GSL" are unavailable.

5. **Generic causal/compositional world-model language**  
   WM3C (ICLR 2025) is a conceptual inspiration, not evidence that our plume factorization is identifiable.

Therefore M4-v3 novelty must be narrower:

> **Dynamic interventional source/transport factorization with a source-agnostic evolution propagator whose wind action is implemented as explicit characteristic transport, then used as the candidate forward model inside probabilistic source localization.**

---

## 4. 2025–2026 scientific anchors

### A. Compositional causal dynamics
WM3C, ICLR 2025:
- motivates reusable causal components and recombination;
- does not supply plume physics.

### B. Source-agnostic solution operators
Neural Green's Functions, NeurIPS 2025, `10.52202/085713-1599`:
- explicitly targets solution operators that generalize across source and boundary functions;
- motivates separating a reusable operator from the source function.

### C. Evolution-operator structure
SINGER, ICLR 2025:
- treats the PDE solution as an evolution operator;
- explicitly emphasizes semigroup and stability structure.

DISCO, ICML 2025:
- separates discovery/representation of dynamics from repeated state evolution.

### D. Characteristic transport
Franck et al., *Neural semi-Lagrangian method for high-dimensional advection-diffusion problems*, CMAME, DOI `10.1016/j.cma.2025.118481`:
- transports the solution along characteristic curves before neural approximation/update;
- supplies the direct mechanism missing from M4-v2.

These works are inspiration/parent principles. M4-v3 is not a reproduction of any one of them.

---

## 5. Minimal M4-v3 architecture

The first implementation must be deliberately small.

### 5.1 Source injection

[
Q_s(x) = a_s,K_epsilon(x-s),
]

where (K_epsilon) is a compact nonnegative injection kernel.

Source location is **not** concatenated into the transport network.

The transport parameters receive no source ID and no absolute source coordinate.

### 5.2 Explicit semi-Lagrangian advection

For each internal step,

[
	ilde C_{k+1}(x)
=
C_k(x - Delta t,W_k(x)).
]

Implementation uses differentiable bilinear backtracing/grid sampling.

This is mandatory. Wind must alter the coordinates from which transported state is sampled; it cannot enter only as a gate or embedding.

### 5.3 Source-independent residual transport

After explicit advection,

[
C_{k+1}
=
Pi_Oleft[
mathcal D_	heta(	ilde C_{k+1},W_k,O)
ight]
+
Q_s .
]

(mathcal D_	heta) is restricted to unresolved diffusion/turbulence/boundary correction.

Hard restrictions:
- no source ID;
- no source coordinates;
- no source-conditioned weights;
- no direct path from source map to transport parameters.

### 5.4 Obstacle projection

The occupancy mask is applied every internal step.

No mass may be propagated through obstacle cells by the learned residual without an explicitly documented boundary rule.

### 5.5 Nonnegativity

Concentration state is constrained to be nonnegative.

### 5.6 Time-varying wind

The scientific version must consume the canonical GADEN wind sequence, not a single frozen wind slice.

House02 single-slice data may be used only for an early development smoke test.

---

## 6. Why v3 is scientifically different from v2

M4-v2:

[
z_{k+1}
=
z_k + K_	heta(z_k)odot g_	heta(W,O,t)
]

where the wind mostly gates a fixed spatial propagation pattern.

M4-v3:

[
C_{k+1}(x)
leftarrow
C_k(x-Delta t W_k(x))
]

before any learned correction.

Therefore wind changes the **transport map itself**.

This yields a falsifiable first-order prediction:

> If the physical wind intervention causes a large spatial plume displacement, the frozen v3 prediction must show a comparable displacement magnitude, not merely a weak correlated perturbation.

---

## 7. Development stage D0 — House02 only

House02 has already been inspected and is contaminated for confirmatory evidence.

It is authorized only for architecture development.

### D0 objective

Determine whether explicit characteristic transport fixes the failure diagnosed in M4-v2.

### D0 comparisons

- frozen M4-v2 operator;
- matched monolithic predictor;
- M4-v3 source-agnostic evolution propagator;
- ablation: v3 with characteristic advection disabled.

### D0 metrics

For paired S2 W1→W2 intervention:

1. wind-delta amplitude ratio
   [
   r_W=|Delta_W^{pred}|/|Delta_W^{true}|;
   ]

2. wind-delta spatial cosine;

3. centroid-displacement magnitude ratio;

4. source-delta amplitude ratio;

5. relative wind/source response
   [
   r_{WS}=
   rac{|Delta_W^{pred}|/|Delta_S^{pred}|}
        {|Delta_W^{true}|/|Delta_S^{true}|};
   ]

6. held-out field error.

### D0 development target

A v3 implementation is worth freezing only if, across both existing plume realizations and both training seeds:

- wind amplitude ratio is no longer catastrophically suppressed;
- target range for development: (0.5 le r_W le 1.5);
- wind-delta cosine (>0.5);
- centroid-shift magnitude ratio (>0.5);
- (r_{WS}>0.5);
- source sensitivity remains nontrivial;
- characteristic-advection ablation loses the transport response.

These are development thresholds only. Passing them is **not** evidence for the paper.

If D0 cannot meet these without target-specific tuning:
**STOP M4-v3.**

---

## 8. Freeze before any new confirmation data

If D0 is successful, freeze:

- architecture;
- internal time step;
- source kernel;
- wind interpolation;
- obstacle rule;
- residual transport capacity;
- loss;
- optimizer;
- training schedule;
- normalization;
- candidate bank rule;
- observation budget;
- source scoring rule;
- all mechanism thresholds.

Record hashes.

No House01/House03 concentration target may be opened before this freeze.

---

## 9. New confirmatory data

Generate fresh factorial GADEN banks for House01 and House03.

For each House:

- 2 geometry-only predeclared source locations;
- 2 canonical same-geometry physical wind configurations;
- 2 independent plume RNG seeds;
- 300 s;
- full time-varying wind sequence;
- spatial concentration snapshots at a predeclared schedule.

Total new confirmatory realizations:

[
2;	ext{Houses}	imes2S	imes2W	imes2;	ext{seeds}=16.
]

House02 is development/training infrastructure only and is never relabeled as confirmation.

---

## 10. Hard mechanism gate C1

For each untouched House separately:

Train without one source×wind combination and evaluate the held-out recombination.

Required on both plume seeds:

1. v3 beats matched monolithic on held-out field prediction;
2. v3 recovers the physical wind intervention:
   - (r_W) within frozen acceptable range;
   - positive, substantial delta cosine;
   - centroid displacement has correct direction and material magnitude;
3. source swap changes injection origin;
4. wind swap changes transport path/magnitude;
5. disabling characteristic advection destroys the transport advantage.

A field-MSE win with suppressed wind response is an automatic failure.

---

## 11. Hard inverse-GSL gate C2

After all forward models are frozen, build a geometry-only multi-candidate source bank.

For each held-out plume realization:
- use the same sparse observation coordinates/times for every model;
- use the same concentration-space observation likelihood for every learned forward model;
- rank all candidate sources.

Primary endpoint:

[
oxed{	ext{truth-containing source-candidate rank}}
]

Report:
- candidate count;
- truth rank and percentile;
- top-5 candidates;
- top-1 margin;
- distance of MAP candidate to truth;
- rank versus observation budget.

M4-v3 must improve source rank over the matched monolithic model. Field error alone cannot pass.

Native PMFS remains a separate baseline using its own native forward/scoring contract.

---

## 12. Cross-House G3

Architecture and thresholds remain frozen.

Use two independent target-House folds:

- target House01;
- target House03.

Training may use other Houses according to a predeclared fold design, but no target-House plume labels may influence architecture/hyperparameters.

M4-v3 advances as the paper's main innovation only if the source-agnostic propagator improves inverse-source rank over matched monolithic and Native PMFS on both plume seeds in **both** held-out Houses, with the characteristic-transport null removing the gain.

---

## 13. Mandatory destructive controls

### N1 — no-advection
Set characteristic displacement to zero.

Expected: transport-response and rank advantage collapse.

### N2 — wind reversal
Use (-W) in the propagator on a diagnostic copy.

Expected: predicted transport displacement reverses correspondingly.

### N3 — wind time permutation
Permute the frozen W(t) sequence.

Expected: dynamic plume prediction degrades.

### N4 — source swap
Change only (Q_s).

Expected: source origin changes while propagator parameters remain identical.

### N5 — source leakage audit
Hash/trace all inputs to the propagator and prove that source ID/location cannot reach propagator weights or conditioning.

### N6 — monolithic capacity control
A matched-capacity entangled model receives the same physical inputs.

---

## 14. Claim boundary

If all gates pass, the defensible main claim is:

> A probabilistic gas-source localizer benefits from replacing an entangled source-conditioned forward surrogate with a source-agnostic, wind-driven evolution propagator derived from the causal structure of passive-scalar transport.

Do **not** claim:
- first neural operator for GSL;
- first Green's-function GSL;
- generic causal discovery;
- exact recovery of Navier–Stokes physics;
- proof that all plume dynamics are linear.

The contribution is the interventional source/transport factorization, its characteristic transport realization, and its demonstrated inverse-localization benefit under unseen source×wind and unseen-House interventions.

---

## 15. Current authorization

Authorized now:
1. extract the complete House02 W1/W2 time-varying wind sequence at sensor height;
2. implement the minimal v3 propagator;
3. run D0 on already-open House02 data;
4. preserve all failures.

Not authorized:
- generating House01/House03 confirmation data before v3 is frozen;
- PMFS/ROS integration;
- closed loop;
- 300 s method comparison;
- scientific ADVANCE claim.
