# Novelty audit v2 — Transport-Orthogonal PMFS

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`

## Bottom line

The following broad ideas are **not novel** and must not be claimed:

1. robust / worst-case experimental design;
2. active model discrimination;
3. sequential model discrimination;
4. optimal design with nuisance parameters;
5. distributionally robust gas sensor placement under wind uncertainty;
6. model ensembles for odor localization;
7. Rényi-information odor-source search;
8. nuisance-invariant gas-source inference in general.

The candidate only remains interesting at a much narrower interface:

> **transport-tangent deconfounding of PMFS source-candidate predictions, with sequential spatial measurements selected to preserve source identity after removing the component explainable by shared plume-transport perturbations.**

## 1. Direct conceptual collisions

### 1.1 Sequential OED can already handle nuisance + multiple models

Shen, Dong & Huan, *Variational sequential optimal experimental design using reinforcement learning*, Computer Methods in Applied Mechanics and Engineering 444 (2025) 118068.

The framework explicitly handles:
- nuisance parameters;
- implicit likelihoods;
- multiple models;
- model discrimination;
- sequential experimental design.

DOI: 10.1016/j.cma.2025.118068

Consequence:
- do not claim "first sequential OED for model discrimination with nuisance";
- do not claim general target-vs-nuisance sequential design as our theoretical novelty.

### 1.2 Multi-stage active model discrimination under uncertainty already exists

Niu, Shen & Yong, *Active model discrimination: A multi-stage approach with adaptive partitions*, Automatica 190 (2026) 113067.

It designs separating inputs for discrete-time affine models under bounded uncertainties and adapts design using information revealed at run time.

DOI: 10.1016/j.automatica.2026.113067

Consequence:
- do not claim multi-stage robust model discrimination itself.

### 1.3 Classical model-discrimination projection / maximin ideas are old

Examples include:
- model-robust/model-discriminating design criteria based on subspace angles and prediction differences;
- T-optimal discrimination with least-favorable parameter configurations;
- semiparametric KL-optimal discrimination.

Therefore a projection formula or inner least-squares minimization alone is not a novelty claim.

## 2. 2025–2026 semiparametric bandit connection — useful but not a direct algorithm transfer

### COLT 2025

Kim, Kim & Oh, *Experimental Design for Semiparametric Bandits*, COLT 2025, PMLR 291:3215–3252.

Their reward contains:
- a structured linear target component;
- an unknown, potentially adversarial shift.

They derive an experimental-design approach around orthogonalized regression.

### AISTATS 2026

Kim, *Nearly Optimal Best Arm Identification for Semiparametric Bandits*, AISTATS 2026, PMLR 300:4402–4410.

They derive nearly optimal fixed-confidence best-arm identification with orthogonalized regression and an XY-design over shifted linear features.

### Mapping limit

PMFS does **not** satisfy their model directly.

In PMFS:
- the experiment/action is a spatial measurement location;
- the latent target is a discrete candidate source;
- the observation law is produced by a nonlinear stochastic filament simulator;
- transport nuisance changes the simulator output nonlinearly.

There is no established single linear parameter \(\theta\) such that both measurement actions and source candidates can simply be inserted into the semiparametric bandit XY-design.

Therefore:
- use COLT/AISTATS as the **parent principle** "target identification after nuisance orthogonalization";
- do not claim their regret/sample-complexity theorems for PMFS;
- do not copy their XY-design formula and relabel symbols.

## 3. 2026 nuisance-invariant GSL near-neighbor

Jin, Duranceau, Erünsal & Martinoli, *Calibration-Free Gas Source Localization with Mobile Robots: Source Term Estimation Based on Concentration Measurement Ranking*, arXiv:2605.13208 (2026).

They remove dependence on unknown sensor calibration by replacing absolute measurement matching with relative-ranking features.

Consequence:
- do not claim "first nuisance-invariant probabilistic GSL."

Remaining distinction:
- their nuisance is sensor calibration/response;
- ours is plume **transport**;
- their mechanism is rank invariance;
- ours is transport-sensitivity/tangent deconfounding;
- ours actively chooses spatial measurements to break source-vs-transport confounding.

## 4. What can still be scientifically distinctive

A defensible contribution must establish all of the following experimentally:

1. **A PMFS-specific pathology:** native candidate hit-map variance contains a component explainable by transport perturbation.
2. **A measurable confounding geometry:** transport sensitivity of candidate maps is stable enough to estimate source-blind.
3. **A sequential deconfounding mechanism:** two or more individually ambiguous measurements can become jointly source-identifying because their source-difference vector leaves the transport-nuisance tangent span.
4. **An exact PMFS reduction:** in the zero-nuisance limit, the acquisition collapses to the native PMFS candidate variance.
5. **Real source-identity benefit:** repaired-Native truth-source rank improves on independent plume realizations.
6. **Mechanism-specific null failure:** destroying the source/transport sensitivity geometry destroys the gain.

If any of 1–3 fail, this line should not be promoted to the main innovation.

## 5. Claim discipline

Potential future wording if evidence supports it:

> We introduce a transport-orthogonal source-identification criterion for PMFS-style mobile gas-source localization. Rather than treating nominal disagreement among candidate plume simulations as source information, the criterion removes the component that can be explained by a shared local transport perturbation and actively chooses complementary spatial observations that make competing source signatures transverse to the transport-nuisance tangent.

Do not use "first" until a final systematic literature audit is completed.
