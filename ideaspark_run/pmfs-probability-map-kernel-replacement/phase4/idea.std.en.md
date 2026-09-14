# Permutation-Equivariant Whole-History Ratio Maps for Gas-Source Localization

**Method.** Permutation-Equivariant Whole-History Ratio Map (PE-WHRM)

## Motivation
Sparse mobile gas measurements create a mismatch between reconstructing a concentration field and locating the source. A model may give calibrated uncertainty for the field while losing the ordered, candidate-relative evidence needed to tell one source location from a fixed wrong candidate. The needed object is therefore not just the field value at the current measurement, but the likelihood ratio between each candidate source and the complete adaptive measurement history.

Physics-guided sparse inversion uses a deterministic Green-function surrogate (semanticscholar:c930ca69d5ed8553c0638ebe60205fe9c1845e58), while probabilistic neural operators score distributions over output functions (dblp:journals/corr/abs-2502-12902). XIT assumes a posterior mean-variance field and uses it for planning (dblp:journals/corr/abs-2602-13739). None asks whether each successive history prefix increases the true source's evidence against the same wrong candidate. The Permutation-Equivariant Whole-History Ratio Map (PE-WHRM) targets this missing ordered, source-relative quantity while preserving the frozen PMFS source grid and updater interface.

The gap is timely because 2026 work already couples posterior fields to active gas-mapping decisions in XIT (dblp:journals/corr/abs-2602-13739) and compares calibrated uncertainty methods for sparse autonomous reconstruction (dblp:journals/corr/abs-2604-06387), but both organize inference around field reconstruction or a supplied field posterior. Existing source-labelled PMFS trajectories contain the complete prefixes and counter-source pairings needed to estimate a joint-versus-product density ratio. Shared scoring that is equivariant to source-grid relabeling gives a concrete way to preserve source-grid symmetry. Together, these ingredients make it possible to test source-relative evidence directly instead of using field calibration as a proxy for localization.

The EUSIPCO 2024 method embedded Poisson and Green-function structure in a neural sparse-inversion pipeline for distributed gas-source localization (semanticscholar:c930ca69d5ed8553c0638ebe60205fe9c1845e58). It did not learn a whole-history likelihood ratio for every candidate source or expose prefix-wise true-versus-fixed-rival evidence. Its inference object remained a deterministic candidate-response surrogate, so it lacked a measurement of source-relative evidence under adaptive histories.

The probabilistic neural operator learned calibrated distributions over output functions using a proper field-space scoring rule (dblp:journals/corr/abs-2502-12902). It did not convert joint source-history versus product pairings into prior-normalized source probabilities or fixed-rival prefix increments. Its target was functional uncertainty rather than candidate-source identification, so ordered source labels were absent from the estimand.

XIT used a supplied posterior mean-variance field to trade off exploration and exploitation during active gas-distribution mapping (dblp:journals/corr/abs-2602-13739). It did not replace the posterior updater with a source-relative whole-history map or test whether measurements improve a fixed-rival localization margin. Planning consumed the posterior as an input, leaving the evidential semantics of the posterior outside the method's scope.

The 2026 uncertainty study compared reconstruction-oriented uncertainty estimators for sparse autonomous-vehicle observations (dblp:journals/corr/abs-2604-06387). It did not train an ordered-history source-ratio estimator or test destructive permutations that retain marginal measurements. Its evaluation object was field reconstruction and calibration, so it lacked a source-pair intervention that could identify localization evidence.

Closing the gap yields an auditable probability-map update whose increments can be attributed to ordered evidence for one source over a fixed rival, rather than to field calibration alone. Posterior-driven planners such as XIT (dblp:journals/corr/abs-2602-13739) could consume a map with explicit localization semantics, and the source-identification question would be separated from the functional-uncertainty objective of probabilistic neural operators (dblp:journals/corr/abs-2502-12902). The resulting claim is narrower but causal: destroying the history-source relation must destroy the localization margin.

## Method
### M0_data_setup
*Prepare ordered source-history pairs and the product-of-marginals control from the frozen PMFS data.*

1. Encode every trajectory prefix as one fixed-schema record with the source coordinate, ordered positions and timestamps, wind or context variables, validity masks, and gas readings seen so far. Keep the source label attached to the trajectory that generated the prefix for a matched example. Make a negative example by taking a source from a different trajectory in the same context stratum and pairing it with the prefix; forbid self-pairs and retain identifiers for the split, stratum, trajectory, prefix, and pairing type. Sample equal numbers of matched and negative records and write the resulting table as the training input for the scorer.
   - _Why:_ The missing information is how a source relates to the ordered history. Contrasting matched dependence with a control that keeps the source and history marginals unchanged targets that relation.

### M1_shared_ratio_map
*Estimate shared source-history ratios and convert them into a prior-normalized source probability map.*

2. Build one scorer shared by all candidates. Encode the candidate coordinate and the masked ordered history with separate encoders, combine the two embeddings with a bilinear or concatenation head, and use the same weights for every source location. Train with balanced binary cross-entropy; only use inverse-frequency weights when the recorded sampler is imbalanced. Fit a monotone calibration map on a separate calibration split and emit a logit plus calibration diagnostics for each candidate and prefix. Do not add a candidate-index embedding or a source-specific output head.

*Balanced binary loss separating matched source-history prefixes from independently paired prefixes.*
$$ \mathcal{L}_{\mathrm{ratio}}(\theta)=-\mathbb{E}_{p(s,H_t)}\log D_\theta(s,H_t)-\mathbb{E}_{p(s)p(H_t)}\log\!\left(1-D_\theta(s,H_t)\right) \tag{1} $$


*The classifier logit estimates the source-history density ratio under balanced class priors.*
$$ \ell_\theta(s,H_t)=\log\frac{D_\theta(s,H_t)}{1-D_\theta(s,H_t)}\approx\log\frac{p(s,H_t)}{p(s)p(H_t)} \tag{2} $$

   - _Why:_ The joint-versus-product contrast targets dependence between a candidate source and the whole history, while parameter sharing makes source-grid relabeling act through the same scoring rule.
3. First evaluate the calibrated scorer on a product-control table that was not used for fitting. Compute the exponential ratio moment with stabilized logits and record its estimate and uncertainty before treating the logits as ratios. For every intact prefix, add the frozen PMFS prior in log space, normalize with a log-sum-exp over every source in the frozen grid, and save the probability map, normalization residual, prior version, and split identifiers.

*PMFS prior normalization converts candidate ratio logits into a probability map over the frozen source grid.*
$$ q_\theta(s\mid H_t)=\frac{\pi_0(s)\exp\ell_\theta(s,H_t)}{\sum_{u\in\mathcal{S}}\pi_0(u)\exp\ell_\theta(u,H_t)} \tag{3} $$

   - _Why:_ A classifier score is not itself a probability map. The moment check tests the density-ratio interpretation, while prior normalization preserves the intended Bayesian source support.

### M2_fixed_rival_evidence
*Turn consecutive ratio logits into per-update and cumulative evidence against fixed wrong candidates.*

4. Set the true source from the trajectory label and choose rivals before inspecting predictions: use the nearest wrong grid candidate and the highest-prior wrong candidate, breaking ties by grid order. Save the logit for every prefix, difference adjacent prefixes, subtract each rival's increment from the true-source increment, and accumulate from the first prefix. Report per-update margins, cumulative margins, final rank, and trajectory-bootstrap intervals.

*Prefix differences isolate the new whole-history evidence for the true source against a fixed rival.*
$$ \Delta_{\theta,t}(s)=\ell_\theta(s,H_t)-\ell_\theta(s,H_{t-1}),\qquad \delta_{\theta,t}(s^*,r)=\Delta_{\theta,t}(s^*)-\Delta_{\theta,t}(r) \tag{4} $$

   - _Why:_ Localization improvement requires evidence relative to persistent wrong candidates; positive true-source increments alone do not show that distinction.

### M3_validation
*Test source-grid equivariance and whether destructive permutations remove the ordered source-relative evidence.*

5. For the symmetry test, apply a recorded one-to-one relabeling of the source grid, run the same trained scorer without retraining, inverse-relabel the output, and record the largest absolute residual and rank agreement. For the two destructive controls, keep all readings and marginal counts but reassign readings to different time-position slots, and separately pair sources with histories from other trajectories in the same stratum. Re-run the full scoring and evidence calculation with the model and splits frozen, saving intact and control traces and the predeclared pass/fail thresholds.

*Exact source-grid permutation equivariance requires relabeling candidates to relabel the map identically.*
$$ \mathbf{q}_\theta(H_t;\Pi\mathcal{S})=\Pi\,\mathbf{q}_\theta(H_t;\mathcal{S}) \tag{5} $$

   - _Why:_ The claimed contribution is the ordered source-relative mechanism, so the controls should destroy that relation while leaving marginal field information available.

