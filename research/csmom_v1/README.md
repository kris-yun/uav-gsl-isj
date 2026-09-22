# CS-MoM V1 — Correlation-Scale Median-of-Means Posterior

Date: 2026-09-22  
Branch: \`research/correlation-scale-mom-posterior-v1\`  
Status: **MAIN-INNOVATION CANDIDATE / STAGE-2 POSITIVE OFFLINE SCREEN**

## 1. Main scientific thesis

**Turbulent gas-source localization should treat a PMFS likelihood field as a spatially correlated, partially contaminated inverse-problem observation — not as hundreds of independent witnesses whose likelihoods may be multiplied without qualification.**

The frozen TNQC R2 evidence exposes the failure mode directly: the native PMFS posterior can become extremely concentrated while remaining far from the source in all six authoritative 300 s cases.

CS-MoM changes the semantics of evidence accumulation:

1. keep the exact native PMFS cell discrepancy and confidence;
2. group spatial cell losses at the pre-existing PMFS correlation scale;
3. use a Median-of-Means (MoM) risk across spatial blocks so a minority of mismatch-dominated regions cannot dominate the source score;
4. remove arbitrary block-origin dependence by evaluating every block-grid offset and taking a second median;
5. map the resulting candidate scores through the unchanged final PMFS partition and ordinary softmax posterior.

This is not a new plume feature, posterior temperature, cell-pruning heuristic, or another information-gain planner.

## 2. Remote-field mother idea

The mother idea is modern robust statistics / robust Bayesian inference under adversarial contamination and model misspecification.

Relevant recent anchors include:

- de Juan & Mazuelas, **On the Optimality of the Median-of-Means Estimator under Adversarial Contamination**, NeurIPS 2025.
- Minsker & Yao, **Generalized median of means principle for Bayesian inference**, Machine Learning, 2025.
- recent dependent-data MoM analyses for correlated time-series observations (2026).

Transferred principle:

> when observations are dependent and a subset can be badly misspecified, arithmetic accumulation of all local losses can create overconfidence; robust block risks can preserve the majority-supported signal while limiting contaminated regions.

The project-specific transfer is to **spatially correlated turbulent source-likelihood fields**, with the block scale fixed by the PMFS transport-map correlation length.

## 3. Frozen physical block rule

No endpoint tuning is used to choose the winning block width.

All six authoritative R2 runs use:

- PMFS cell size = 0.3 m;
- \`kernelSigma = 0.5 m\`;
- \`confidenceSigmaSpatial = 0.5 m\`.

We therefore freeze

\[
B = \left\lceil \frac{2\,\sigma_{\mathrm{kernel}}}{h} \right\rceil
  = \left\lceil \frac{1.0}{0.3} \right\rceil
  = 4
\]

cells per block side.

A 4×4 block is thus the pre-existing two-sigma spatial correlation footprint, not a truth-selected hyperparameter.

## 4. Candidate score

For candidate source hypothesis \(s\), native aligned cell \(i\) has

\[
\ell_i(s)
= -\log\left(1-c_i\left|p_i^{meas}-p_i^{sim}(s)\right|\right).
\]

For each of the \(B^2\) possible block-grid offsets:

1. partition supported cells into B×B spatial blocks;
2. average \(\ell_i(s)\) inside each block;
3. take the median across block means.

Then take the median of those \(B^2\) offset-level robust risks.

The final candidate log-score is the negative robust risk multiplied by the candidate support-cell count, retaining the approximate native score scale.

No extra posterior temperature is used.

## 5. Authoritative data contract

The screen uses the uploaded/released final archive:

\`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz\`

SHA256:

\`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708\`

Cases:

- House01 seed0 / seed1
- House02 seed0 / seed1
- House03 seed0 / seed1

The endpoint remains the native 300 s

\`ExpectedValue(sourceProbability, 0.05)\`

top-5% error.

The exported candidate support, candidate partition, cell likelihood equation and posterior softmax are unchanged.

## 6. Stage-2 result

Native pooled top-5% error:

**5.5551 m**

CS-MoM pooled top-5% error:

**3.9393 m**

Pooled reduction:

**29.09%**

Case errors, native → CS-MoM:

- H01 seed0: 5.527 → **7.213 m** (worse)
- H01 seed1: 4.002 → **3.490 m**
- H02 seed0: 4.107 → **1.797 m**
- H02 seed1: 3.701 → **1.934 m**
- H03 seed0: 7.782 → **1.623 m**
- H03 seed1: 8.212 → **7.578 m**

Summary:

- non-worse: **5/6**
- false-confident collapse: native **6/6**, CS-MoM **0/6**

The robust posterior is not simply a uniform distribution: casewise maximum cell probabilities remain approximately 0.006–0.041, while posterior spatial variances remain 3.15–20.26 m².

## 7. Necessary controls already passed

### Posterior temperature

Pure score-temperature controls produce only small gains:

- T=0.25: about 1.0% pooled improvement;
- T=0.5: about 0.2%.

Therefore the CS-MoM result is not explained by generic posterior softening.

### Fixed source-blind cell subsampling

Checkerboard/hash half-cell controls give only small or inconsistent gains.

Therefore the effect is not explained by simply using fewer cells.

### Random blocks

Thirty source-blind random partitions into groups of approximately 16 cells preserve the same block count scale but destroy spatial correlation structure.

Mean random-block endpoint:

**5.315 m**

Mean improvement:

**4.32%**

Most random seeds still produce 4–5 false-confident-collapse cases.

Therefore **spatially coherent correlation-scale blocking is load-bearing**.

### Block-origin dependence

A single 4×4 grid origin can materially change the result. CS-MoM therefore does not select one favorable origin.

It evaluates all 16 spatial offsets and robustly aggregates them by the median.

### Sliding-window corroboration

A separate overlapping 4×4 sliding-window median construction also improves the pooled endpoint by roughly 23%, with 5/6 cases better and no false-confident collapse.

Thus the signal is not unique to one non-overlapping partition implementation.

## 8. Block-size sensitivity

Translation-invariant offset-median screens:

- B=2: about -0.4%
- B=3: about +11.1%
- **B=4: +29.1%**
- B=5: about +16.9%
- B=6: about +12.2%
- B=7: negative
- B=8: about +10.2%

The B=4 result is strong, but it is retained because it is independently fixed by the existing two-sigma PMFS correlation footprint, not because it is the maximum of this scan.

## 9. Novelty boundary

Not new by itself:

- Median-of-Means;
- robust Bayes / generalized Bayes;
- spatial blocking;
- robust statistics for contaminated samples;
- model-ensemble GSL.

Existing project code also contains medians/MADs in some planner robustness gates.

The targeted contribution is narrower:

**correlation-scale, translation-invariant robustification of a turbulent gas-source candidate likelihood field before posterior formation, treating spatially correlated transport mismatch as block contamination rather than independent evidence.**

This is distinct from:

- TNQC nuisance-quotient scoring;
- the project's prior planner-level median/MAD significance gates;
- e-process stopping;
- Piro et al.'s “many wrong models” source localization, which addresses forward-model misspecification through an ensemble of models rather than robust spatial aggregation of one candidate likelihood field.

A targeted literature/repository collision search has not found this construction in GSL/OSL.

## 10. Current failure and scientific status

H01 seed0 worsens substantially.

Therefore:

**CS-MoM is NOT authorized for closed-loop integration yet.**

Current status is:

**STAGE-2 POSITIVE MAIN-INNOVATION CANDIDATE.**

Next falsification tasks:

1. diagnose H01 seed0 without using source truth to tune a guard;
2. replay CS-MoM across the sequence of source-update snapshots, not only the terminal bank;
3. verify that robust block support has a source-blind reliability statistic that predicts when CS-MoM should abstain;
4. reproduce the endpoint with the linked/native evaluator;
5. only after those pass, implement an OFF / SHADOW / FUSED closed-loop comparison.

The main claim survives only if the H01 seed0 failure can be explained and controlled by a predeclared source-blind condition rather than a case-specific patch.
