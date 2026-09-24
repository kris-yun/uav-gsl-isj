# LOM-PD v1 — House02 Development Screen

Date: 2026-09-24  
Branch: `research/path-occupation-open-system-v1`  
Status: **PROMISING DEVELOPMENT SIGNAL — NOT ADVANCE / NOT CONFIRMATORY**

## 0. Candidate name

**LOM-PD: Lagrangian Occupation-Measure Plume Dynamics**

The candidate main idea is to augment the resolved plume state with candidate-specific path occupation measures rather than treating the instantaneous 2-D concentration field as a closed Markov state.

This branch starts from the frozen M4-v3 failure. It does not change or revoke:

`D0_FAIL_STOP_M4_V3`.

M4-v3 remains NO-GO as a complete main model.

---

## 1. Why this candidate exists

Frozen M4-v3 established a specific pattern:

- characteristic transport materially responds to wind;
- response amplitude and bulk displacement are not the main failure;
- full wind-intervention geometry is wrong;
- a generic memory auxiliary improves field error but does not repair the geometry;
- a hand-written wall-slide rule does not repair it;
- a simple vertical-exchange rule lowers field error but worsens wind-response geometry.

Additional House02 development diagnostics show that the real GADEN source×wind interaction is large:

[
I=C_{22}-C_{21}-C_{12}+C_{11}.
]

The norm of this interaction is of the same order as, and slightly larger than, the S2 wind intervention itself (about 1.07–1.14× depending on plume realization), while the real W1→W2 response fields at S1 and S2 are almost orthogonal.

Therefore the same wind intervention does **not** induce a source-independent 2-D response geometry.

The working interpretation is:

> The resolved 2-D concentration slice forgets the path by which mass arrived at each cell.  
> Candidate source location changes which corridors, wall regions and directional transport histories are occupied.  
> Those path histories alter the effective projected transport law.

---

## 2. Scientific state augmentation

For each source candidate, let the resolved coarse plume be (ho_t(x)).

Define source-conditioned path occupation fields such as

[
mu_{mathrm{res}}(x,t)=int_0^t arho_	au(x),d	au,
]

[
mu_{mathrm{wall}}(x,t)=int_0^t
arho_	au(x),b(x),d	au,
]

and directional occupation

[
mu_u(x,t)=int_0^t arho_	au(x),u(x,	au),d	au,
qquad
mu_v(x,t)=int_0^t arho_	au(x),v(x,	au),d	au,
]

where (arho) is the normalized candidate plume occupancy and (b(x)) is a geometry-only wall-proximity weight.

These are updated causally. No future wind or target concentration is needed at deployment.

The scientific motivation is the classical occupation-measure idea: time-integrated path occupancy retains information discarded by an instantaneous projected state.

Recent examples using occupation measures as history-bearing state representations include:

- Béthencourt, Catellier & Tanré, *Brownian Particles Controlled by Their Occupation Measure*, SIAM Journal on Control and Optimization, 2025, DOI 10.1137/24M1656220.
- *Accelerated First-Passage Dynamics in a Non-Markovian Feedback Ornstein–Uhlenbeck Process*, Journal of Statistical Physics, 2025, DOI 10.1007/s10955-025-03509-7.

These are scientific anchors, not novelty claims for occupation measures themselves.

---

## 3. Why the projected model is open-system

A fixed-height 2-D slice of a 3-D plume is not mass closed.

Conceptually,

[
partial_t C_{2D}+
abla_{xy}cdot J_{xy}
=
Q_s-partial_zJ_z+	ext{unresolved wake/recirculation exchange}.
]

A pure 2-D conservative flux correction was tested and did **not** repair the M4-v3 wind geometry.

Therefore the development candidate uses a positive open-system exchange law rather than forcing all correction into an in-plane divergence.

---

## 4. Positive open-system form

The current development form is

[
C^+(x,t)
=
C_{mathrm{coarse}}(x,t)
exp[-alpha a_	heta(x,t)]
+
alpha b_	heta(x,t),
]

with

[
a_	hetage 0,qquad b_	hetage 0.
]

Interpretation:

- (a_	heta): unresolved attenuation / loss from the observed 2-D state;
- (b_	heta): unresolved re-entry / recirculation / spreading contribution.

Both are source-blind shared laws conditioned on the current coarse state and the candidate-specific occupation state.

The development model is deliberately simple linear ridge regression over local features. No deep model is required for the current signal.

---

## 5. Development-only feature set

The minimal tested occupation family excludes full 3-D wind and does **not** require (W_z).

It uses:

- current coarse log concentration;
- local first/second spatial differences;
- current map-frame downwind (u,v), speed;
- wall proximity;
- simple current-state × wind/wall interactions;
- residence occupation;
- wall-weighted occupation;
- directional occupations (mu_u,mu_v);
- local spatial derivatives of those occupation maps.

This is compatible in principle with a mapped 2-D wind estimate and occupancy map.

---

## 6. House02 development result

Training cells remain:

- S1-W1
- S2-W1
- S1-W2

Development holdout:

- S2-W2

Two frozen M4-v3 checkpoints are used (1729, 2718).

The closure is shared across both base checkpoints and both source candidates.

For the current positive open-system form, with development constants

- epsilon = 0.05
- alpha = 0.80

the held-out S2-W2 metrics across 2 base checkpoints × 2 plume realizations are:

- minimum wind-delta cosine: **about 0.568**
- minimum wind-delta amplitude ratio: **about 0.506**
- mean source-delta cosine: **about 0.758**
- mean source×wind interaction cosine: **about 0.330**
- mean held-out field MSE: **about 0.179**

The output is nonnegative by construction.

The interaction geometry is improved but remains incomplete. This is a remaining mechanism risk.

---

## 7. Necessary-mechanism ablations

The earlier additive development screen is retained because it isolates which state variables carry the signal.

### No history

Current-state-only correction can raise wind cosine, but minimum wind-response amplitude collapses to about **0.435**.

Interpretation:
current-state correction can suppress wrong directions but does not preserve the physical response scale.

### No wall information

Removing wall/path-boundary features drops the minimum wind cosine to about **0.449**.

Interpretation:
boundary/path context is necessary for the House02 signal.

### No directional history

Removing directional occupation history drops the minimum wind cosine to about **0.494**.

Interpretation:
where mass travelled and in what direction contains information not present in the instantaneous field.

### No vertical wind

Removing (W_z)-related features does not remove the positive signal.

Interpretation:
the current House02 gain does not require deployment access to a dense vertical wind field.

### Pure conservative flux closure

A small divergence-form occupation-flux closure does not pass the physical response gate.

Interpretation:
forcing the 2-D projected correction to conserve in-plane mass is too restrictive for this slice representation.

---

## 8. Sparse inverse-source screening

This is **not Native PMFS-compatible ranking** and not a closed-loop result.

It is a concentration-space two-candidate diagnostic using geometry-only probe locations.

For 50 independent source-blind random geometry probe sets at each observation budget, the fraction of probe sets in which all four comparisons rank true S2 above S1 changes approximately as follows:

| probes | frozen M4-v3 | LOM-PD open-system |
|---:|---:|---:|
| 10 | 0.72 | 0.80 |
| 20 | 0.78 | 0.98 |
| 30 | 0.80 | 0.96 |
| 50 | 0.96 | 1.00 |

At 50 probes the corrected mean source margin is positive for all 50 geometry probe sets.

This is the first post-M4 House02 development result in which:

1. wind-intervention geometry improves;
2. wind-response amplitude remains material;
3. source-intervention structure remains strong;
4. sparse source discrimination improves in the same direction.

It is still only development evidence.

---

## 9. Why this is not “M4 plus another patch”

The proposed scientific claim is no longer that a concentration field alone is a complete reusable transport state.

Instead:

> Candidate-specific transport history is represented by an occupation-measure state, and the projected 2-D plume evolves as an open system conditioned on that path state.

M4-v3 becomes only the resolved coarse transport used to construct candidate path occupancy.

The new state variable is the main change.

---

## 10. Prior-art / novelty boundary

Do not claim:

- first use of occupation measures;
- first non-Markovian plume model;
- first path-history model;
- first neural operator for GSL;
- first physics-informed GSL model.

Target novelty to investigate and verify:

> **Using candidate-specific Lagrangian occupation measures as the hidden transport state for a probabilistic gas-source forward model, with an open-system closure whose predictions are used for source-candidate likelihood/ranking.**

A targeted 2026-09 search has not yet identified a direct gas-source-localization method using this construction.

This remains provisional novelty screening, not exhaustive clearance.

---

## 11. Real-world compatibility

The current necessary variables are available in principle during flight:

- candidate source hypothesis;
- occupancy map;
- map-frame downwind (u,v) estimate;
- elapsed history of the candidate forward state.

The current positive signal does not require (W_z).

Before physical deployment, estimated wind must still pass the previously frozen W0 direction/magnitude interface audit.

---

## 12. Current hard boundary

### House02

**PROMISING DEVELOPMENT SIGNAL.**

### Scientific ADVANCE

**NOT YET.**

House02 has been repeatedly inspected and tuned and can never become confirmatory evidence.

### Next authorized action

Freeze the minimal LOM-PD architecture and constants before generating/opening new confirmatory target data.

Then test on fresh House01 and House03 factorial source×wind banks.

Required confirmation endpoints:

1. wind-delta cosine and amplitude;
2. source-delta response;
3. source×wind interaction geometry;
4. multi-candidate source rank, not merely two candidates;
5. observation-budget robustness;
6. estimated-wind robustness;
7. runtime / memory budget for candidate propagation.

No PMFS/ROS 300 s closed loop should be used as the first confirmation test.
