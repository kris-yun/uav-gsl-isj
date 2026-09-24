# D1C Effect-Size and Target-Power Precommit v0

Date: 2026-09-25

Status:
**PRE-D1R NUMERICAL PRINCIPLE — TO BE RED-TEAMED BY AUXILIARY PRO BEFORE FINAL FREEZE**

This document is written before any D1R reference outcomes are inspected.

Its purpose is to prevent post-reference or post-target threshold selection.

---

## 1. Primary effect unit

The D1C primary paired effect is measured in bits per target:

\[
b_{sr}
=
\log_2
\frac{
q_{\rm FSEI}(s\mid y_{sr})
}{
q_{\rm identity}(s\mid y_{sr})
}.
\]

The primary mean is

\[
\Delta_B
=
\frac1N
\sum_s
\frac1J
\sum_r b_{sr}.
\]

Interpretation:

\[
2^{\Delta_B}
\]

is the geometric-mean multiplicative change in probability assigned to the
true source cell.

---

## 2. Proposed minimum scientifically meaningful effect

A tiny positive score difference is not sufficient for the project.

Proposed main margin:

\[
\delta_{\rm id}
=
\log_2(1.15)
\approx
0.2016\ {\rm bits}.
\]

This corresponds to at least a 15% geometric-mean increase in true-source
probability over the identity model.

This margin is an application-level scientific minimum, not a theorem of
causal emergence.

Proposed uniqueness margin versus the strongest ordinary
pooling/shrinkage/clustering baseline:

\[
\delta_{\rm ordinary}
=
\log_2(1.05)
\approx
0.0704\ {\rm bits}.
\]

This requires at least a 5% geometric-mean true-source-probability advantage
beyond the strongest ordinary baseline, in addition to statistical evidence
that the paired difference is positive.

The auxiliary Pro must red-team these margins before final freeze.

---

## 3. Target-count selection must use variance only

D1R reference data may determine how many untouched targets/source are needed,
but D1R mean effect sizes must not be used to weaken the minimum effect margin.

After the final reference-only model is selected, use its **OOF paired score
differences** only to estimate variance components.

Model:

\[
b_{sr}
=
\mu
+
u_s
+
\epsilon_{sr},
\]

where:

- \(u_s\) is between-source effect heterogeneity;
- \(\epsilon_{sr}\) is realization-level stochastic variation within source.

Estimate:

\[
\sigma_u^2,\qquad \sigma_\epsilon^2
\]

from centered D1R OOF paired differences.

The planned D1C standard error for \(N=168\) and \(J\) targets/source is

\[
SE_J
=
\sqrt{
\frac{\sigma_u^2}{N}
+
\frac{\sigma_\epsilon^2}{NJ}
}.
\]

The D1R OOF grand mean is not used in this calculation.

---

## 4. Power rule

Candidate target counts:

\[
J\in\{2,4,8\}.
\]

Choose the smallest J such that, if the true effect equals
\(\delta_{\rm id}\), the design has at least 80% power for the lower bound of a
two-sided 95% interval to exceed zero.

Normal-approximation planning condition:

\[
SE_J
\le
\frac{
\delta_{\rm id}
}{
1.96+0.84
}.
\]

The final analysis itself should use the predeclared hierarchical/cluster
bootstrap, not rely solely on the normal approximation.

If even J=8 fails the reference-only power condition, the mainline must report
that the proposed confirmation is too noisy under the present observation
protocol rather than silently generate an arbitrarily large target set.

---

## 5. Primary D1C success logic — proposed

Subject to auxiliary-Pro review, a future D1C PASS should require all of:

### A. Identity superiority

- mean \(\Delta_B \ge \delta_{\rm id}\);
- 95% paired source/realization hierarchical-bootstrap CI lower bound > 0.

### B. Ordinary-baseline superiority

Against the single strongest ordinary baseline selected by the same reference
protocol:

- mean paired gain >= \(\delta_{\rm ordinary}\);
- 95% hierarchical-bootstrap CI lower bound > 0.

### C. Reference prerequisites remain satisfied

The partition/model must already have passed frozen D1R requirements for:

- stability;
- fidelity;
- connectedness;
- calibration/model validity;
- no hidden target leakage.

### D. Same-task integrity

All compared methods use:

- identical 168-cell support;
- identical micro prior;
- identical observations;
- identical final target realizations.

Failure of any primary condition is a scientific STOP for the FSEI mainline
under this configuration.

---

## 6. Secondary metrics

Always report, but never use as alternate rescue gates:

- truth rank;
- top1/top3;
- MAP spatial error;
- probability mass within 0.5 m;
- probability mass within 1.0 m;
- posterior entropy;
- multiclass Brier score;
- source-stratified performance.

A D1C primary failure cannot be converted into PASS because spatial error looks
better.

---

## 7. Why score differences, not 300-coordinate bootstrap

The 300 time-probe coordinates belong to one observation realization.

They are not 300 independent experiments.

The paired unit is a source-realization target.

D1C uncertainty must resample at source/realization level, preferably:

1. resample source IDs;
2. nested within each selected source, resample its J target realizations.

No bootstrap over individual time-probe coordinates is allowed for the primary
confidence interval.

---

## 8. Status

These numerical margins are deliberately proposed before D1R results are seen.

They become final only after:

1. auxiliary-Pro red-team;
2. primary-thread review;
3. commit/hash freeze before D1C targets are generated.

They must never be changed after target generation.
