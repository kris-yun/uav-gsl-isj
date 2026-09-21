# GCSI V1 — Godambe-Calibrated Composite Source Inference

Date: 2026-09-22  
Status: **CURRENT #1 MAIN-INNOVATION CANDIDATE / AUTHORITATIVE 300-S OFFLINE FALSIFICATION REQUIRED**

## 1. Paper-level thesis

**A PMFS-style spatial source posterior should not treat propagated / spatially correlated map cells as independent likelihood replications. Gas-source evidence is a composite likelihood, and its posterior concentration must be calibrated by the dependence geometry of the evidence.**

The target is not another source feature. The project already has strong source-discriminative structure.

The proposed change is the **inference semantics**:
- keep the physical candidate/source forward model;
- keep per-location source compatibility components;
- reinterpret their product/sum as a dependent composite score;
- calibrate its posterior curvature / evidence magnitude with a Godambe/sandwich-style dependence correction;
- preserve candidate ordering when the score is informative, while preventing computational grid density from manufacturing confidence.

## 2. Modern statistical roots

### 2025
Wang, Lin & Liu, *Exploiting Multivariate Network Meta-Analysis: A Calibrated Bayesian Composite Likelihood Inference*, Bayesian Analysis (2025), DOI 10.1214/25-BA1511.

Key transferable point:
a composite-likelihood posterior can be overly precise when correlated components are treated as if they supplied independent information; Open-Faced-Sandwich calibration corrects posterior uncertainty.

### 2026
Li, White & Prangle, *Optimal combination of composite likelihoods using approximate Bayesian computation with application to state-space models*, Journal of Computational and Graphical Statistics (2026), DOI 10.1080/10618600.2026.2718766.

Key transferable point:
composite sub-scores require principled combination and calibration; Godambe information captures the dependence-aware information geometry.

These papers are methodological roots, not GSL prior art.

## 3. Why this fits the frozen project evidence

The project has an apparent contradiction:

- controlled 240-s VGR concentration-space source identity is strong and distributed;
- the affine quotient is 12/12 at 240 s;
- both disjoint checkerboard halves independently recover the true source;
- source ranking survives 0.3 -> 1.8 m spatial coarse-graining;
- yet TNQC V5 produces essentially zero 300-s endpoint gain and 6/6 false-confident-collapse cases.

This is consistent with a distinction between:
1. **which source is better supported**, and
2. **how much independent evidence exists for that preference**.

GCSI targets (2).

## 4. New offline premise screen

Use a deliberately simple composite-score proxy:

1. affine-canonicalize the observed and candidate concentration fields;
2. each common spatial cell contributes a Gaussian squared-residual score;
3. compare SA vs SB by the per-cell score contrast;
4. compare naive additive/iid confidence with spatial block/sandwich confidence.

### Resolution test

The physical source ordering remains correct at every tested spatial scale:
0.3, 0.6, 0.9, 1.2, 1.8 m.

But the **summed composite log-evidence** changes by at least 5.23x in every one of the 12 cases and by as much as 8.93x.

For the fragile H02-SA cases:

- H02_SA_fast: summed evidence 3.796 at 0.3 m -> 0.726 at 1.8 m (5.23x drift);
- H02_SA_slow: 2.077 -> 0.499 (with a 7.96x max/min drift across scales).

Thus changing only the computational discretization can strongly change apparent evidence magnitude without changing source identity.

### Truth-blind spatial block result

Using 0.9-m contiguous block means of the pairwise SA-vs-SB score:

- H02_SA_fast: |robust z| = 0.469
- H02_SA_slow: |robust z| = 0.997

The other ten cases range from |z| = 1.221 to 3.163.

No source truth is needed to compute this statistic: truth is used only after scoring to label whether the preferred candidate was correct.

Interpretation:
the H02-SA source preference is real but weak in independent-evidence terms, precisely where a cell-product posterior is most vulnerable to spurious confidence.

## 5. Hard novelty boundary

Not new by itself:
- composite likelihood;
- Godambe information;
- sandwich covariance;
- Open-Faced-Sandwich adjustment;
- likelihood tempering;
- effective sample size;
- spatial blocking.

Targeted GSL novelty hypothesis:

**dependence-calibrated composite source inference that makes PMFS evidence concentration invariant to spatial discretization / propagated-map pseudo-replication while retaining physically correct source ranking.**

Targeted searches have not found a GSL/OSL method using composite-likelihood/Godambe/OFS calibration of a spatial source posterior.

The project has prior awareness of pseudo-replication and temporal effective sample counts. That is not enough for novelty. The new object must be the **source posterior's dependence-calibrated evidence geometry**, not merely an N_eff multiplier.

## 6. V1 mathematical object

For candidate source s and evidence components j:

    L_s = sum_j ell_{s,j}

is treated as a **composite score**, not a genuine iid log-likelihood.

Let u_j(s) denote the local source-score contribution (or local score-gradient / pairwise contrast in the discrete implementation).

Estimate dependence-aware variability J from physical spatial blocks / disjoint supports, and sensitivity H from the score curvature or a frozen finite-difference analogue.

The calibrated information is of Godambe form:

    G = H^T J^{-1} H

or its scalar/pairwise reduction.

The first V1 implementation should prefer a transparent scalar/pairwise sandwich calibration over a high-dimensional estimator.

No source truth may set H, J, block size, or a posterior temperature.

## 7. Required controls

A valid GCSI implementation must pass:

1. **Grid-refinement invariance**  
   Refining / coarsening the same physical evidence must not arbitrarily sharpen source confidence.

2. **Duplicate-cell / duplicate-evidence control**  
   Duplicating a spatial score component without adding a physical observation must not increase calibrated evidence.

3. **Candidate-order preservation**  
   Calibration may change confidence geometry but must not reverse a source ordering solely because the grid is repartitioned.

4. **Independent-support control**  
   When disjoint spatial blocks genuinely agree, calibrated evidence may strengthen.

5. **Correlation-destruction control**  
   If dependence is synthetically removed, the correction should approach the iid/composite baseline.

6. **No truth tuning**  
   Source truth is evaluator-only.

## 8. Authoritative 300-s falsification contract

Do not infer success from the 240-s two-source screen.

Use the frozen House01/02/03 x seed0/1 fixed trajectories and original:

    ExpectedValue(sourceProbability, 0.05)

at 300 simulation seconds.

Compare:
- native PMFS;
- an uncalibrated composite-score control;
- scalar magnitude/temperature calibration control;
- GCSI sandwich/Godambe calibration.

Primary promotion bar:
- pooled 300-s endpoint improvement >= 2% for the cheap development screen;
- >= 4/6 cases non-worse;
- zero new false-confident-collapse cases;
- calibrated confidence materially less sensitive to synthetic grid subdivision / duplicated map cells;
- improvement must exceed a single global-temperature control.

For paper-level promotion, retain the project's stronger >=10% target unless explicitly re-frozen under a new independent development protocol.

## 9. Current verdict

**STAGE-1 GO.**

GCSI is currently the strongest main-innovation candidate found in this screening cycle because:

- it explains a frozen project failure rather than only adding a new representation;
- its necessary pathology is directly observed in project data;
- the pathology is load-bearing across all 12 controlled cases;
- the modern statistical roots are 2025/2026;
- targeted GSL collision search is negative.

It is **not yet authorized for closed loop**.

Next step: implement an isolated 300-s fixed-trajectory counterfactual replay and try to falsify it against native PMFS and simple tempering before touching the planner.
