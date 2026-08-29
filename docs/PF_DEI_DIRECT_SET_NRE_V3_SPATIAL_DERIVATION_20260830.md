# PF-DEI Direct Set-NRE V3 spatial evidence derivation

Date: 2026-08-30
Status: derivation + diagnostic protocol; no retraining and no closed-loop authorization
Parent: frozen `PF_DEI_DIRECT_SET_NRE_V2_NO_GO`

## 1. What V2 actually proved

V2 must not be described as "the neural network learned nothing". Its frozen result showed a reproducible source-ordering signal and a large reduction in carrier-centroid expected localization error, but it failed the predeclared exact-carrier rank and Top-10 gates. These facts are mathematically compatible because discrete source identity and spatial localization risk are different functionals of the same posterior.

The purpose of V3 is therefore not to rescue V2 by changing its gate after seeing the answer. V2 remains frozen NO-GO. V3 asks a new, narrower, preregistered diagnostic question:

> Did the frozen NRE factor move probability mass into a physically coherent source neighborhood, or did it merely improve the exact carrier rank without producing spatially usable information?

No training, hyperparameter search, temperature, blend, GADEN generation, House expansion, or closed-loop run is permitted in this stage.

## 2. NRE identity

Let `S` be a candidate source carrier and `D` the observed gas-response block set. V2 trains a balanced binary classifier between

- joint samples: `p1(s,D) = pi(s) p(D|s)`,
- product samples: `p0(s,D) = pi(s) p_pi(D)`,

where the source proposal `pi` is identical in the two classes and

`p_pi(D) = sum_s pi(s) p(D|s)`.

The population-optimal logit is therefore

`f*(s,D) = log p1(s,D) - log p0(s,D)`

`          = log p(D|s) - log p_pi(D)`.

The second term does not depend on `s`. For an independent deployment prior `q0(s)`, the posterior is

`q(s|D) proportional q0(s) exp(f_theta(s,D))`.

Thus the frozen V2 score is a source likelihood-ratio factor up to an observation-only constant. This is the correct mathematical object to audit spatially.

## 3. Why exact Top-K and localization error can disagree

For carrier centroids `x_i` and posterior masses `p_i`, exact carrier rank depends only on the ordering of `p_i` at one discrete index. Spatial localization objectives depend on geometry.

Examples include posterior-mean error

`L_mean = || sum_i p_i x_i - x* ||`,

and posterior expected radial error

`L_radial = sum_i p_i ||x_i - x*||`.

A posterior may move substantial mass from far-away false sources into several carriers surrounding `x*` while the exact true carrier is still outside Top-10. In that case `L_mean` and `L_radial` improve even though exact ID recovery remains weak.

Therefore:

- exact Top-K is a **discrete carrier-identifiability** test;
- spatial risk is a **localizability** test;
- neither can substitute for the other.

The frozen V2 gate remains valid for V2. V3 adds spatial diagnostics rather than retroactively changing that gate.

## 4. Geometry-only adaptive neighborhood

Each carrier already has physical dimensions `width_m` and `height_m`. Define its circumscribed support radius

`a_i = 0.5 sqrt(width_i^2 + height_i^2)`.

Define a deterministic geometry graph

`A_ij = 1[ ||x_i-x_j|| <= a_i + a_j ]`.

Self-membership is always included. This graph uses only carrier geometry. It has no fitted radius, no learned temperature, no truth dependence, and no outcome-tuned bandwidth.

The graph is intentionally conservative: two carriers belong to the same local support neighborhood only when their circumscribed physical support disks touch or overlap.

## 5. Regional posterior mass and evidence

For the already-frozen discrete posterior `p_i`, define regional posterior mass

`M_i = sum_j A_ij p_j`.

For the independent geometry prior `q0_j`, define regional prior mass

`M_i^0 = sum_j A_ij q0_j`.

The local regional Bayes-factor diagnostic is

`B_i = M_i / M_i^0`,

or numerically

`log B_i = log(M_i + eps) - log(M_i^0 + eps)`.

`M_i` answers: how much posterior mass is concentrated in the physical neighborhood around carrier `i`?

`B_i` answers: is that concentration larger than would be expected from geometry prior mass alone?

Neither quantity changes the frozen V2 posterior.

## 6. Truth-blind regional decision summaries

Two deterministic summaries are evaluated without access to truth:

### 6.1 Posterior-mass region mode

`i_M = argmax_i M_i`.

Within its neighborhood, report the posterior-weighted centroid

`mu_M = [sum_{j:A_iM,j=1} p_j x_j] / M_iM`.

### 6.2 Regional-evidence mode

`i_B = argmax_i log B_i`.

Report the analogous posterior-weighted centroid `mu_B`.

Stable ties are resolved by carrier ID. These are **decision summaries**, not a replacement posterior and not yet a planner input.

If a single isolated carrier has the largest point mass but a nearby group of moderately weighted carriers contains more coherent local mass, `mu_M` can represent that coherent source region. The included synthetic self-test verifies exactly this case and carrier-permutation invariance.

## 7. Frozen post-scoring spatial metrics

Only after all candidate scores are reconstructed are truth coordinates opened for evaluation. Report, per case and by source update:

1. exact true-carrier rank;
2. MAP-to-truth distance;
3. posterior-mean-to-truth distance;
4. posterior expected radial error;
5. minimum truth distance among Top-1, Top-5, and Top-10 carriers;
6. posterior mass within fixed diagnostic radii 0.5 m, 1.0 m, and 2.0 m;
7. posterior mass in the geometry-adaptive neighborhood of the true carrier;
8. prior mass in the same neighborhood;
9. true-neighborhood `log B`;
10. truth-blind `mu_M` and `mu_B` localization error.

The 0.5/1/2 m radii are descriptive only. They must not be selected, optimized, or used to tune a new inference rule from H01.

## 8. Interpretation matrix

### Case A — spatial signal is real

Expected signature:

- direct posterior expected radial error improves over PMFS;
- Top-K minimum distance improves even if exact Top-K fails;
- posterior mass near the true source increases over PMFS and over geometry prior;
- true-neighborhood `log B` is positive in a large fraction of cases;
- truth-blind regional mode is closer to the source than the raw exact MAP.

Interpretation: V2 learned physically local source information but its discrete carrier decision surface is too fragmented. A future method may legitimately move to region/continuous-source inference, but only under a new preregistered contract and fresh validation.

### Case B — only weak rank reshuffling

Expected signature:

- exact rank improves but radial error, nearby mass, Top-K distance, and regional mode do not;
- true-neighborhood `log B` is near zero or negative.

Interpretation: the network learned ordering artifacts that are not sufficiently spatially actionable. Do not retrain merely to sharpen Top-K.

### Case C — mixed evidence

If spatial metrics improve only at late updates or only for a subset of seeds, treat this as mechanism-localization evidence, not a closed-loop GO. The next design must explain the condition under which the information becomes available.

## 9. Non-negotiable scientific boundary

This V3 stage is intentionally diagnostic.

It does **not**:

- reverse the frozen V2 NO-GO;
- authorize retraining;
- authorize H02/H03 expansion;
- authorize posterior smoothing inside PMFS;
- authorize a planner change;
- claim continuous-source inference has already been validated.

Its purpose is to determine which scientific branch is justified next:

- spatially coherent signal -> derive a preregistered region/continuous-source inference operator;
- non-spatial rank signal -> stop this learned-evidence route or change the physical representation, not merely the optimizer.
