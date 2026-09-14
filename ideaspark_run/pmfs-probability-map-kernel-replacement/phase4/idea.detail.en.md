# Permutation-Equivariant Whole-History Ratio Maps for Gas-Source Localization

**Method.** Permutation-Equivariant Whole-History Ratio Map (PE-WHRM)

## Motivation
**Problem framing.** Sparse mobile gas measurements create a structural mismatch between field reconstruction and source localization. A learner can assign calibrated uncertainty to a concentration field while discarding the ordered, candidate-relative evidence that distinguishes one source location from a fixed rival. The relevant object is therefore not only a field value at the current measurement, but the likelihood ratio between a candidate source and the entire adaptive measurement history.

The closest adjacent methods stop on either side of this object. Physics-guided sparse inversion inserts a deterministic Green-function surrogate (semanticscholar:c930ca69d5ed8553c0638ebe60205fe9c1845e58), and probabilistic neural operators score distributions over output functions (dblp:journals/corr/abs-2502-12902). XIT instead assumes a posterior mean-variance field and uses it for planning (dblp:journals/corr/abs-2602-13739). None of these constructions identifies whether each successive history prefix increases the true source's evidence relative to the same wrong candidate. PE-WHRM targets that missing source-relative, ordered-history object while preserving the frozen PMFS source grid and updater interface.

**Why now.** The gap is timely because 2026 work already couples posterior fields to active gas-mapping decisions in XIT (dblp:journals/corr/abs-2602-13739) and compares calibrated uncertainty methods for sparse autonomous reconstruction (dblp:journals/corr/abs-2604-06387), yet both still organize inference around field reconstruction or a supplied field posterior. Existing source-labelled PMFS trajectories now provide the complete prefixes and counter-source pairings needed to estimate a joint-versus-product density ratio, while permutation-equivariant shared scoring supplies a concrete structural tool for preserving source-grid symmetry. Together, these ingredients make it possible to test source-relative evidence directly rather than treating field calibration as a proxy for localization.

**Why prior work stopped.**
- `semanticscholar:c930ca69d5ed8553c0638ebe60205fe9c1845e58` (European Signal Processing Conference 2024): The EUSIPCO 2024 method embedded Poisson and Green-function structure in a neural sparse-inversion pipeline for distributed gas-source localization.
  - _Did not do_: It did not learn a whole-history likelihood ratio for every candidate source or expose prefix-wise true-versus-fixed-rival evidence.
  - _Structural reason_: Its inference object remained a deterministic candidate-response surrogate, so it lacked a measurement for source-relative evidence under adaptive histories.
- `dblp:journals/corr/abs-2502-12902` (Trans. Mach. Learn. Res. 2025): The probabilistic neural operator learned calibrated distributions over output functions using a proper field-space scoring rule.
  - _Did not do_: It did not convert joint source-history versus product pairings into prior-normalized source probabilities or fixed-rival prefix increments.
  - _Structural reason_: Its target was functional uncertainty rather than candidate-source identification, so ordered source labels were absent from the estimand.
- `dblp:journals/corr/abs-2602-13739` (arXiv 2026): XIT used a supplied posterior mean-variance field to trade off exploration and exploitation during active gas-distribution mapping.
  - _Did not do_: It did not replace the posterior updater with a source-relative whole-history map or test whether measurements improve a fixed-rival localization margin.
  - _Structural reason_: Planning consumed the posterior as an input, leaving the evidential semantics of the posterior outside the method's scope.
- `dblp:journals/corr/abs-2604-06387` (arXiv 2026): The 2026 uncertainty study compared reconstruction-oriented uncertainty estimators for sparse autonomous-vehicle observations.
  - _Did not do_: It did not train an ordered-history source-ratio estimator or test destructive permutations that retain marginal measurements.
  - _Structural reason_: Its evaluation object was field reconstruction and calibration, so it lacked a source-pair intervention that could identify localization evidence.

**What changes when the gap closes.** Closing the gap yields an auditable probability-map update whose increments can be attributed to ordered evidence for one source over a fixed rival, rather than to field calibration alone. It would let posterior-driven planners such as XIT (dblp:journals/corr/abs-2602-13739) consume a map with explicit localization semantics and would separate the source-identification question from the functional-uncertainty objective of probabilistic neural operators (dblp:journals/corr/abs-2502-12902). The resulting claim is narrower but causal: destroying the history-source relation must destroy the localization margin.

## Method
**Pipeline.** PE-WHRM receives a frozen candidate-source grid and each ordered prefix of an existing source-labelled PMFS trajectory. It forms matched source-history pairs and independently re-paired product controls, then applies one shared candidate scorer to all sources so source relabeling cannot change the scoring rule. Balanced binary logits are checked as density ratios and combined with the PMFS prior to produce a normalized source probability map at every prefix. Consecutive logits are differenced for the true source and fixed rivals, yielding the cumulative evidence margin and final rank used by the falsification test. Ratio-moment, exact-equivariance, time-position permutation, and source-pair permutation checks determine whether the map uses the claimed ordered source-relative mechanism.

### M0_data_setup
*Prepare ordered source-history pairs and the product-of-marginals control from the frozen PMFS data.*

1. **Construct ordered prefix pairs** (`S1`)
   - For each source-labelled trajectory, serialize the ordered prefix $H_{t}$ as a fixed-schema record containing source-coordinate s, measurement positions, timestamps, wind/context channels, validity masks, and gas readings up to t. Create one positive record $(s,H_{t})$ for every observed source-prefix pair. Create the product-of-marginals records by sampling a source from a different trajectory within the same declared context stratum and pairing it with $H_{t}$; reject self-pairs and preserve the empirical source and history counts. Draw equal numbers of positive and negative records, and store split, stratum, $trajectory_{id}, prefix_{id}$, and pairing_type so every later control is reproducible.
   - _Why:_ The bottleneck is missing source-relative information in the ordered history, so the learning problem must contrast dependence with a control that retains source and history marginals.

### M1_shared_ratio_map
*Estimate shared source-history ratios and convert them into a prior-normalized source probability map.*

2. **Estimate the shared history ratio** (`S2`)
   - Implement $D_{theta}(s,H_{t})$ as a shared encoder: a coordinate/context encoder for s, a masked sequence encoder for the ordered $H_{t}$, and a bilinear or concatenated head whose weights are shared for every candidate. Use balanced binary cross-entropy, apply inverse source-frequency weights only when correcting a declared sampling imbalance, and calibrate the held-out logit with a monotone calibration fit learned on a separate calibration split. Emit one logit and one calibration diagnostic for every candidate-prefix pair; no candidate-index embedding or source-specific head may be present.

*Balanced binary loss separating matched source-history prefixes from independently paired prefixes.*
$$ \mathcal{L}_{\mathrm{ratio}}(\theta)=-\mathbb{E}_{p(s,H_t)}\log D_\theta(s,H_t)-\mathbb{E}_{p(s)p(H_t)}\log\!\left(1-D_\theta(s,H_t)\right) \tag{1} $$


*The classifier logit estimates the source-history density ratio under balanced class priors.*
$$ \ell_\theta(s,H_t)=\log\frac{D_\theta(s,H_t)}{1-D_\theta(s,H_t)}\approx\log\frac{p(s,H_t)}{p(s)p(H_t)} \tag{2} $$

   - _Why:_ The joint-versus-product contrast targets dependence between a candidate source and the whole history, while parameter sharing encodes source-grid permutation equivariance by construction.
3. **Validate and prior-normalize ratios** (`S3`)
   - Evaluate the calibrated scorer on an independently paired product-control table and compute the exponential ratio moment with numerically stabilized logits; record its estimate and confidence interval before accepting ratio interpretation. For each intact prefix, add the frozen PMFS prior $log pi_{0}(s)$ to the calibrated logit, subtract the log-sum-exp over the complete frozen source grid, and write $q_{theta}(s|H_{t})$ together with normalization residual, prior version, and split identifiers.

*PMFS prior normalization converts candidate ratio logits into a probability map over the frozen source grid.*
$$ q_\theta(s\mid H_t)=\frac{\pi_0(s)\exp\ell_\theta(s,H_t)}{\sum_{u\in\mathcal{S}}\pi_0(u)\exp\ell_\theta(u,H_t)} \tag{3} $$

   - _Why:_ A classifier score alone is not a probability map; the moment check tests the density-ratio interpretation and prior normalization preserves the intended Bayesian source support.

### M2_fixed_rival_evidence
*Turn consecutive ratio logits into per-update and cumulative evidence against fixed wrong candidates.*

4. **Extract fixed-rival evidence increments** (`S4`)
   - Choose the true source s* from the trajectory label and choose fixed rivals before reading the model output using a pre-registered rule: the nearest non-true grid candidate and the highest-prior non-true candidate, with ties resolved by grid order. Store logits for every prefix, calculate consecutive differences for s* and each rival, subtract the rival increment from the true increment, and accumulate from t=1; report the final rank and margin with bootstrap intervals over trajectories.

*Prefix differences isolate the new whole-history evidence for the true source against a fixed rival.*
$$ \Delta_{\theta,t}(s)=\ell_\theta(s,H_t)-\ell_\theta(s,H_{t-1}),\qquad \delta_{\theta,t}(s^*,r)=\Delta_{\theta,t}(s^*)-\Delta_{\theta,t}(r) \tag{4} $$

   - _Why:_ Localization improvement requires relative evidence against persistent wrong candidates; positive true-source increments alone do not establish that distinction.

### M3_validation
*Test source-grid equivariance and whether destructive permutations remove the ordered source-relative evidence.*

5. **Enforce structural falsification checks** (`S5`)
   - For the equivariance check, apply one recorded bijection to the candidate grid, rerun the same scorer without retraining, inverse-permute the resulting map, and record the maximum absolute residual and rank agreement. For the destructive controls, keep each measurement value and marginal count unchanged while (i) reassigning readings to different time-position slots within a prefix and (ii) pairing sources with histories from other trajectories within the same stratum. Recompute S1-S4 with frozen model and splits, and store intact and control traces plus the predeclared pass/fail thresholds.

*Exact source-grid permutation equivariance requires relabeling candidates to relabel the map identically.*
$$ \mathbf{q}_\theta(H_t;\Pi\mathcal{S})=\Pi\,\mathbf{q}_\theta(H_t;\mathcal{S}) \tag{5} $$

   - _Why:_ The contribution is the ordered source-relative mechanism, so controls must selectively destroy that relation while leaving marginal field information available.

## Reviewer concerns
- **Concern [non_blocking]:** Paper-pointed threat: openalex:W4391952441 (collision_hits). This paper establishes that neural binary classifiers can approximate likelihood ratios through the likelihood-ratio trick, so the candidate cannot claim novelty for classifier-based density-ratio estimation itself. It does not subsume the candidate's narrower contribution because the retrieved result does not supply an ordered adaptive gas-history object, exact source-grid permutation equivariance, PMFS-prior normalization, prefix-difference fixed-rival evidence, or destructive history controls; the candidate explicitly labels neural ratio estimation as standard and makes those source-localization-specific elements carry the claim.
  - **Response:** The defense is anchored in `core_claim`, S1-S5 of `method_flow.steps`, and the destructive-control clause of `falsification_prediction`: none claims novelty for classifier-based density-ratio estimation. Consistent with the Phase 3.2 rationale summarized in the attack, the claimed delta is the localization-specific composition of ordered adaptive histories, exact source-grid equivariance, PMFS-prior normalization, fixed-rival prefix evidence, and controls that selectively destroy the history-source relation.

