# Candidate M1 — Adversarial Transport Identifiability for PMFS

Date: 2026-09-23  
Status: **KEEP FOR FALSIFICATION; NOT YET A MAIN INNOVATION**  
Branch: `research/maximin-transport-design-v1`

## 1. One-sentence thesis

Replace PMFS's implicit assumption that one nominal plume simulator is trustworthy with a **maximin source-identifiability game**: the UAV selects where to observe, while an adversarial "nature" is allowed to perturb the transport-generated observation law inside a predeclared ambiguity budget; the selected action and belief update are those that preserve source information under the worst admissible transport misspecification.

This keeps the recognizable PMFS shell:

- discrete candidate-source space;
- simulated probability / hit maps;
- online source-probability map;
- closed-loop movement;

but changes the scientific assumption from **single-model expected informativeness** to **transport-robust identifiability**.

## 2. Remote-field parent ideas

### P1 — Maximin Robust Bayesian Experimental Design (2026)

Abdulsamad, Iqbal, Naesseth, Matsubara, Corenflos, *Maximin Robust Bayesian Experimental Design*, 2026, arXiv:2603.14094.

Key transferable result:

- formulate experimental design as a max-min game under likelihood/model misspecification;
- nature selects a worst-case data-generating law in a KL ambiguity neighborhood;
- the resulting robust expected information gain is governed by Sibson alpha-mutual information;
- the consistent robust posterior is an alpha-tilted / power-likelihood posterior;
- alpha is linked to ambiguity radius rather than introduced only as an arbitrary temperature.

Reference:
https://arxiv.org/abs/2603.14094

### P2 — Robust nonlinear-PDE optimal experimental design (SIAM JSC 2026)

Chowdhary, Attia, Alexanderian, *Robust Optimal Experimental Design of Infinite-Dimensional Bayesian Nonlinear Inverse Problems*, SIAM Journal on Scientific Computing 48(2), 2026.

This is an important **novelty boundary**, not a claim source:

- worst-case robust OED already exists for nonlinear PDE inverse problems;
- uncertainty can include simulation model / prior / observation model;
- demonstrated for sensor placement.

Therefore our novelty CANNOT be "we apply robust OED to an inverse problem."

DOI:
https://doi.org/10.1137/24M1693921

### P3 — Generalised Bayesian robust experimental design (2025)

Barlas, Sloman, Kaski, *Robust Experimental Design via Generalised Bayesian Inference*, 2025, arXiv:2511.07671.

Useful boundary / fallback:

- replaces standard likelihood-based Bayes with generalized / Gibbs inference;
- defines Gibbs expected information gain;
- handles likelihood misspecification.

Reference:
https://arxiv.org/abs/2511.07671

## 3. Nearest GSL collisions found so far

### C1 — Wiedemann et al. model-mismatch GSL (2019)

*Analysis of Model Mismatch Effects for a Model-Based Gas Source Localization Strategy Incorporating Advection Knowledge*.

They explicitly study gas-dispersion model mismatch, use probabilistic uncertainty, and drive information-based exploration.

This means we cannot claim:
- first GSL aware of model mismatch;
- first probabilistic GSL robust to imperfect dispersion;
- first uncertainty-based active sampling under imperfect plume physics.

But their mechanism is not a distributionally robust max-min transport game and not Sibson-alpha robust information.

DOI:
https://doi.org/10.3390/s19030520

### C2 — Cumulative informative path planning for GSL (IROS 2025)

Jin, Leroy, Bösel-Schmid, Martinoli, *Cumulative Informative Path Planning for Efficient Gas Source Localization with Mobile Robots*, IROS 2025.

They:
- use a Bayesian source PDF;
- evaluate information along robot paths;
- dynamically trade information and travel;
- benchmark KLD-based informative planning.

Therefore "information-driven path planning" or "path-integrated information" is not novel enough.

DOI:
https://doi.org/10.1109/IROS60139.2025.11246224


### C3 — "Many wrong models" odor-source localization (Journal of Turbulence 2025)

Piro, Heinonen, Cencini, Biferale, *Many wrong models approach to localise an odour source in turbulence with static sensors*, Journal of Turbulence 26(5), 2025.

This is a **critical near-neighbor**.

They explicitly:
- assume turbulent transport models are unavoidably misspecified;
- run a discrete bank of wrong stochastic plume models;
- rank the models using an overlap integral;
- blend the resulting source-location beliefs into a master belief;
- show that this improves robustness and gives a more reliable stopping criterion.

Therefore we also cannot claim:
- first odor/GSL method to exploit a family of wrong plume models;
- first model-uncertainty-aware Bayesian fusion for odor source localization;
- first robustness-oriented source posterior under turbulent model misspecification.

Important remaining distinction:
- their sensors are static;
- their primary mechanism is model ranking/blending after observing sensor data;
- they do not formulate the **measurement-location decision** as a max-min game;
- they do not optimize worst-case source information over an ambiguity set;
- they do not derive Sibson-alpha robust information or an adversarial transport design criterion.

DOI:
https://doi.org/10.1080/14685248.2025.2492711



### C4 — Rényi-infotaxis / Rényi-divergence OSL already exists (Entropy 2025)

Jia et al., *A Novel Distributed Hybrid Cognitive Strategy for Odor Source Location in Turbulent and Sparse Environment*, Entropy 27(8):826, 2025.

This is a **hard novelty constraint**. Their CGRInfotaxis family already uses Rényi divergence / Rényi-infotaxis-style exploration in odor-source localization.

Therefore M1 is immediately **NO-GO** if it reduces to any of the following:
- replace Shannon entropy / KL information with Rényi or Sibson information;
- tune an alpha parameter and call the result robust infotaxis;
- use power likelihood only as a heuristic temperature;
- claim alpha-information itself as the OSL novelty.

The only defensible route is a stronger derivation:

1. define an explicit uncertainty set over the **transport process / transition law**;
2. derive the worst-case observation law induced by that transport ambiguity;
3. derive the action criterion and belief update from the **same max-min game**;
4. calibrate the ambiguity radius source-blind, rather than tuning alpha against source truth;
5. show truth-source-rank benefit specifically under forward-model mismatch.

DOI:
https://doi.org/10.3390/e27080826


## 4. The novelty boundary we must defend

The candidate only survives if we can support this narrower statement:

> Existing GSL methods use nominal dispersion likelihoods, parametrically relaxed models, and even weighted ensembles of multiple misspecified plume models. We instead formulate **sequential mobile source localization as transport-ambiguous source identification**, choosing observations and updating source belief against the worst admissible perturbation of the plume-generated observation law.

The intended scientific object is NOT generic uncertainty and NOT merely a new reward.

It is:

**robust preservation of source identity under forward-transport misspecification.**

## 5. PMFS-native mathematical instantiation

Let:

- `s ∈ S`: PMFS candidate source leaf;
- `x`: candidate UAV measurement location/action;
- `Y`: next gas observation; start with binary hit/miss for the first probe;
- `π_t(s)`: current PMFS source probability map;
- `h_s(x)`: PMFS simulated hit probability at x for candidate source s.

Nominal observation law:

[
p(Y=1|s,x)=h_s(x), qquad p(Y=0|s,x)=1-h_s(x).
]

### 5.1 Robust action value

For fixed `alpha ∈ (0,1)`, compute Sibson alpha mutual information between source identity S and next observation Y:

[
I_alpha^S(S;Y|x)
=
rac{alpha}{alpha-1}
log
sum_{yin{0,1}}
left(
sum_s pi_t(s),p(y|s,x)^alpha
ight)^{1/alpha}.
]

Initial falsification uses:

[
x^* = argmax_x I_alpha^S(S;Y|x)
]

with **no distance term and no extra tunable rescue coefficient**.

At `alpha → 1`, this must recover nominal Shannon-MI design.

### 5.2 Robust belief update

After observing `y_t` at `x_t`:

[
pi_{t+1}(s)
propto
pi_t(s)
,p(y_t|s,x_t)^alpha.
]

This is not to be sold as "temperature scaling." Its legitimacy comes only if it is kept coupled to the same maximin ambiguity model used for the action criterion.

### 5.3 Candidate paper-level second derivation: transport-aware ambiguity

A generic KL ball around output likelihood may be too close to existing robust OED.

The stronger PMFS-specific version to investigate is an ambiguity set induced by **transport uncertainty** rather than arbitrary label/output perturbation.

Possible structure:

[
mathcal U_t
=
{T':
D(T'Vert T_{m PMFS})le ho_t,
; T'	ext{ obeys obstacle and admissible wind/dispersion constraints}}.
]

Each transport T' induces:

[
p_{T'}(Y|s,x).
]

Then choose:

[
x^*
=
argmax_x
inf_{T'inmathcal U_t}
I(S;Y|x,T').
]

This is scientifically stronger because nature attacks the **plume physics**, not an unconstrained abstract likelihood.

Do NOT implement this full version before the simple falsification passes.

## 6. Why this is not the already-killed "native discriminability" idea

The killed probe chose locations with high variance across candidate hit maps under the **same nominal simulator**. H01/H03 showed that those cells could worsen truth-source rank.

That failure is actually the motivating pathology:

> nominal simulator discriminability can be anti-informative when the forward family is wrong.

This candidate changes the optimization target from:

[
	ext{large nominal separation}
]

to:

[
	ext{separation that survives admissible forward perturbations}.
]

Therefore the new candidate must beat both:
- random / geometric sampling;
- nominal PMFS candidate-variance or Shannon-information sampling.

## 7. Hard falsification plan after Native baseline recovery

Do NOT wait for full closed-loop implementation.

### F0 — algebra/unit test

Using any valid frozen PMFS candidate hit maps:

- verify alpha→1 numerically approaches Shannon MI ranking;
- verify alpha↓0 collapses robust information;
- verify no NaN / zero-probability pathology;
- runtime for all cells must be practical.

### F1 — source-blind ranking stability

For each House × independent plume realization:

1. freeze current source prior / candidate set;
2. compute top-k cells by:
   - nominal candidate variance;
   - Shannon MI;
   - Sibson MI for predeclared alpha values;
3. measure cross-realization ranking stability.

This is diagnostic only; it does not pass the method.

### F2 — truth-rank intervention test — HARD GATE

Using the **recovered Native PMFS forward contract**, select observation subsets / sequential next observations by each criterion and replay source updates.

Primary endpoint:

- truth-containing candidate rank.

Compare:

- Native PMFS existing selection;
- random reachable cells;
- nominal Shannon MI;
- nominal candidate variance;
- robust Sibson-alpha design.

Required positive signal:

- improvement in truth-source rank on multiple independent realizations;
- not only endpoint/top-5 centroid;
- no House-specific coefficient tuning.

If Sibson design is merely more stable but does not improve source rank, kill it.

### F3 — destructive null

Break the transport uncertainty relationship while preserving marginal map statistics, e.g. spatial permutation / candidate-label permutation appropriate to the recovered data.

Robust gain must disappear.

If it survives equally well under the null, it is exploiting geometry / smoothing rather than transport robustness.

## 8. Alpha / ambiguity parameter rule

This is a major risk.

NOT ALLOWED:

- choose alpha after looking at truth rank;
- choose one alpha per House;
- tune alpha to endpoint error.

Stage-1 probe may report a **predeclared sensitivity panel** such as alpha = {0.95, 0.8, 0.6, 0.4}, with no winner selected using truth.

For a publishable method, alpha must ultimately be tied to a source-blind ambiguity estimate or a statistically justified calibration rule.

Promising 2026 auxiliary literature to investigate ONLY AFTER F2 is positive:

- inverse conformal risk control (ICML 2026);
- conformal robustness control (ICLR 2026);
- conformalized ambiguity sets / Conformal-DRO (2026).

These may provide a principled way to calibrate robustness radius, but they are not part of M1 yet.

## 9. Decision criteria

### KEEP / advance

Only if repaired-baseline F2 shows:
- repeated truth-rank improvement;
- stronger effect under deliberately introduced transport mismatch than under matched simulation;
- advantage over nominal Shannon MI / candidate variance;
- effect disappears in destructive null.

### KILL

Immediately if:
- robust objective is just a monotone re-ranking of nominal entropy;
- source rank does not improve;
- benefit exists only for one House/seed;
- best alpha must be chosen using source truth;
- advantage vanishes once Native PMFS baseline is repaired;
- implementation requires a trained surrogate / large new dataset before any positive offline signal exists.

## 10. Current assessment

**Scientific narrative strength:** high.  
**Recency / remote-field strength:** high (2025–2026 robust experimental design / DRO).  
**Direct GSL collision risk:** currently moderate-low, but broad robust sensor-placement prior art is substantial.  
**Risk of becoming "just a new reward":** CRITICAL. 2025 Rényi-infotaxis is a direct collision if transport-ambiguity derivation does not survive.  
**Data/interface fit with PMFS:** unusually good because PMFS already supplies a discrete candidate-source probability map and per-candidate hit probabilities.  
**Next action:** wait only for the Native baseline artifacts, then run F0–F2 before any full code integration.
