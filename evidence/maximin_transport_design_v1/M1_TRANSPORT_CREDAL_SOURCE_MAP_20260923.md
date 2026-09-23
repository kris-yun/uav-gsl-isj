# M1 Completion — Transport-Credal Source Map

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Status: theoretical completion of M1; empirical validation pending repaired Native baseline

## 1. Why M1 needs this component

If transport ambiguity only changes the next-action acquisition score, M1 can still be criticized as a robust path planner wrapped around an unchanged single-model PMFS belief update.

The same ambiguity set should also change what the source map means.

PMFS currently maintains a single source-probability map under one forward model.

M1 should instead expose:

**which source probabilities remain possible across the admissible transport family.**

This yields a set-valued / credal source map.

Credal / imprecise probability theory itself is old and is NOT a novelty claim. The contribution is the transport-derived likelihood set inside PMFS.

## 2. Likelihood interval induced by transport ambiguity

At sensing cell x_t, candidate source s has a nominal binary hit probability

\[
h_{s,t}=P(Y_t=1\mid s,x_t).
\]

Transport ambiguity induces

\[
q_{s,t}\in[L_{s,t},U_{s,t}].
\]

After observing y_t in {0,1}, the admissible likelihood interval is

\[
[\ell^-_{s,t},\ell^+_{s,t}]
=
\begin{cases}
[L_{s,t},U_{s,t}], & y_t=1,\\
[1-U_{s,t},1-L_{s,t}], & y_t=0.
\end{cases}
\]

These bounds come from the same transport model used by robust planning.

## 3. Cumulative source evidence interval

Let pi_0(s) be the initial source prior.

Under a rectangular sequential relaxation of transport ambiguity, the cumulative likelihood for candidate s lies in

\[
\mathcal L_{s,1:t}
\in
[
\mathcal L^-_{s,t},
\mathcal L^+_{s,t}
],
\]

where

\[
\log\mathcal L^-_{s,t}
=
\sum_{\tau=1}^{t}\log\ell^-_{s,\tau},
\]

\[
\log\mathcal L^+_{s,t}
=
\sum_{\tau=1}^{t}\log\ell^+_{s,\tau}.
\]

Use log space numerically.

The rectangular relaxation is conservative: it allows the transport adversary to choose likelihood extremes independently across time/candidates even if not every such combination corresponds to one globally coherent wind field.

Therefore this is the cheap first version, not automatically the final physical set.

## 4. Exact coordinate-wise posterior bounds under the rectangular relaxation

For any admissible cumulative likelihood vector L,

\[
\pi_t(s;L)
=
\frac{
\pi_0(s)L_s
}{
\sum_r\pi_0(r)L_r
}.
\]

The lower posterior probability of source s is obtained by making its own evidence minimal and every competitor's evidence maximal:

\[
\boxed{
\underline\pi_t(s)
=
\frac{
\pi_0(s)\mathcal L^-_{s,t}
}{
\pi_0(s)\mathcal L^-_{s,t}
+
\sum_{r\neq s}
\pi_0(r)\mathcal L^+_{r,t}
}.
}
\]

The upper posterior is

\[
\boxed{
\overline\pi_t(s)
=
\frac{
\pi_0(s)\mathcal L^+_{s,t}
}{
\pi_0(s)\mathcal L^+_{s,t}
+
\sum_{r\neq s}
\pi_0(r)\mathcal L^-_{r,t}
}.
}
\]

The intervals do not need to sum to one; they are coordinate projections of a set of admissible posterior distributions.

## 5. Robust source identity

A nominal MAP source can be highly model-dependent.

Define candidate s as pairwise robustly dominant over r only if

\[
\underline\pi_t(s)>\overline\pi_t(r).
\]

Define the robust-MAP possibility set

\[
\boxed{
M_t
=
\left\{
s:
\overline\pi_t(s)
\ge
\max_r\underline\pi_t(r)
\right\}.
}
\]

Every source outside M_t cannot be MAP under the rectangular posterior set.

If |M_t| is large while the nominal PMFS posterior is sharply peaked, the algorithm is **nominally confident but transport-fragile**.

That diagnostic is scientifically useful even before source declaration.

## 6. Relationship to the robust action criterion

The two objects answer different questions from the same ambiguity family.

Transport-Certified Information Floor:
- prospective;
- asks which next sensing location preserves source separation under transport uncertainty.

Transport-Credal Source Map:
- retrospective;
- asks which source beliefs are still supportable after the measurements under that uncertainty.

Thus M1 becomes:

\[
\boxed{
\text{transport ambiguity}
\rightarrow
\begin{cases}
\text{robust action selection}\\
\text{robust source-belief set}
\end{cases}
}
\]

rather than only a new acquisition function.

## 7. Relationship to Auxiliary A

Do not confuse the credal map with the anytime-valid source confidence set.

Transport-credal map:
- model-based robust Bayesian object;
- represents sensitivity of source belief to admissible transport models;
- does not by itself provide repeated-frequentist coverage under optional stopping.

Auxiliary A e-process confidence set:
- sequential evidence / testing object;
- supplies an anytime-valid coverage statement, conditional on the true observation law lying in the declared null family.

They can be displayed together:
- credal interval = model-robust belief;
- e-process confidence set = declaration certificate.

Do not merge their claims.

## 8. Cheap offline falsification

No closed-loop code is needed initially.

Given repaired Native hit maps and frozen observations:

For each measurement prefix, compute:
- nominal PMFS source rank / posterior;
- lower/upper source probabilities;
- robust-MAP possibility set M_t;
- width of truth-source interval;
- whether nominal top-1 lies outside/inside M_t;
- whether the truth-containing candidate is prematurely excluded from M_t.

Compare matched transport and deliberately mismatched transport.

Expected positive signature:
- under matched transport, intervals shrink and M_t contracts;
- under mismatch, credal intervals widen / robust-MAP set stays broader before nominal PMFS becomes confidently wrong;
- truth source remains plausible more often than under the nominal rank.

## 9. Hard kill conditions

Kill the rectangular credal implementation if:
- intervals become nearly [0,1] for all candidates throughout the 300 s run;
- M_t remains almost the entire candidate space even in matched Native simulation;
- truth-source plausibility is not better protected under mismatch;
- only a truth-tuned ambiguity radius makes it informative.

If the rectangular relaxation is too conservative but structured wind-field adversarial simulation remains viable, kill only this relaxation, not M1.

## 10. Stronger structured version

Instead of independent likelihood intervals, define a global admissible wind-field set A_t.

Each W in A_t induces a coherent sequence of candidate likelihoods and a posterior

\[
\pi_t^W(s).
\]

Then the true transport-credal set is

\[
\Pi_t
=
\{
\pi_t^W:
W\in A_t
\}.
\]

Coordinate bounds become

\[
\underline\pi_t(s)=\inf_{W\in A_t}\pi_t^W(s),
\qquad
\overline\pi_t(s)=\sup_{W\in A_t}\pi_t^W(s).
\]

This is physically tighter but computationally more expensive.

Only implement it if the cheap interval version gives a positive source-rank/plausibility signal.

## 11. Novelty boundary

Searches on 2026-09-23 for:
- credal gas source localization;
- imprecise probability gas source localization;
- robust Bayesian odor source localization;
- interval probability gas source localization;
- set-valued posterior plume source localization

did not return a direct robotic GSL implementation in this audit.

Do not claim that robust Bayes, credal sets or posterior probability intervals are new.

The candidate-specific novelty remains:

**transport uncertainty derived from stochastic plume physics is propagated consistently into both active source-identifying decisions and a set-valued PMFS source belief.**

## 12. Current role in the paper architecture

This is part of M1, not Auxiliary C.

Preferred M1 internal structure:

M1-a:
physics-shaped transport ambiguity;

M1-b:
worst-case / certified source-information action selection;

M1-c:
transport-credal source-map update.

Auxiliary A remains anytime-valid source declaration.

Auxiliary B remains online conformal calibration of transport uncertainty.
