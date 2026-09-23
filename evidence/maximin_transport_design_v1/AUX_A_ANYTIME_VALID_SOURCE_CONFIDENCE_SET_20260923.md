# Auxiliary A — Transport-Robust Anytime-Valid Source Confidence Set

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Status: KEEP FOR FORMAL / EMPIRICAL FALSIFICATION

## 1. Problem

Gas-source declaration is a distinct and under-developed part of GSL.

Ojeda, Monroy and Gonzalez-Jimenez (ISOEN 2022) explicitly note that many GSL works use arbitrary or undocumented termination criteria. Fixed posterior-probability, entropy, variance, stability and distance-style criteria are environment/parameter dependent and do not provide a time-uniform false-declaration guarantee.

PMFS itself has a discrete adaptive source-candidate representation, which makes this problem particularly suitable for sequential inference.

The target is NOT a better hand-tuned stopping threshold.

The target is:

**an anytime-valid confidence set over source candidates that stays statistically valid while the robot chooses sensing locations adaptively and stops at a data-dependent time.**

## 2. Remote parent idea

Recent anytime-valid sequential inference provides tests/e-processes that can be monitored continuously without invalidating error control under optional stopping.

Relevant recent anchors:

- Koning & van Meer, "Anytime validity is free: inducing sequential tests", JRSS-B, 2026, DOI 10.1093/jrsssb/qkag050.
- Lindon & Kallus, "Anytime-Valid A/B Testing of Counting Processes", AISTATS 2025.
- The general e-process / confidence-sequence literature supplies the test-inversion principle used below.

A June 2026 preprint, "Sim-to-Real Betting on the E-Process: Bringing simulators to anytime-valid confidence sequences", shows that e-process ideas are also beginning to enter robot/simulator certification. It is a novelty boundary, not a direct GSL collision.

## 3. GSL novelty audit

Searches performed on 2026-09-23 included:

- "e-process" gas source localization / odor source localization;
- "anytime-valid" source localization robot;
- "confidence sequence" source localization robot;
- sequential probability ratio test + gas source localization;
- martingale + odor source localization.

No direct GSL/olfactory-search work using e-process inversion to build an anytime-valid source-location confidence set was found in this search.

Do NOT claim absolute firstness without a broader final literature review.

Older GSL source declaration and sequential tests in other localization/robotics fields remain prior art.

## 4. Setup

Let S be the finite PMFS candidate-source set.

At time t:

- history is F_{t-1};
- robot chooses action / sensing location x_t using any predictable policy measurable with respect to F_{t-1};
- observation is Y_t (start with binary hit/miss);
- transport uncertainty is represented by an ambiguity set U_t derived from the same transport-robust framework as M1.

For a fixed candidate source s, define the composite point-source null

\[
H_s:
\text{source}=s,\qquad Q_t\in\mathcal U_t .
\]

The nuisance Q_t represents admissible forward-transport misspecification.

## 5. A robust e-factor for each candidate source

For candidate s, let the null conditional observation family be

\[
\mathcal P_{s,t}
=
\{
p_Q(\cdot\mid s,x_t,\mathcal F_{t-1}):
Q\in\mathcal U_t
\}.
\]

Choose any predictable alternative predictive law

\[
q_{s,t}(y\mid\mathcal F_{t-1},x_t)
\]

that is fixed before observing Y_t.

A practical choice is the current mixture prediction over candidate sources other than s. It may use the complete past and the current robust source belief, but never Y_t before the e-factor is fixed.

Define

\[
\boxed{
e_{s,t}(Y_t)
=
\frac{
q_{s,t}(Y_t)
}{
\sup_{p\in\mathcal P_{s,t}} p(Y_t)
}
}.
\]

For every admissible null law p_0 in P_{s,t},

\[
\begin{aligned}
\mathbb E_{p_0}
[e_{s,t}(Y_t)\mid\mathcal F_{t-1}]
&=
\sum_y
p_0(y)
\frac{q_{s,t}(y)}
{\sup_{p\in\mathcal P_{s,t}}p(y)}
\\
&\le
\sum_y q_{s,t}(y)
=
1.
\end{aligned}
\]

Therefore

\[
\boxed{
E_{s,t}
=
\prod_{\tau=1}^{t}
e_{s,\tau}(Y_\tau)
}
\]

is a nonnegative test supermartingale / e-process for H_s.

This argument remains valid with adaptive sensing locations x_t because x_t is chosen from the past before Y_t is observed.

## 6. Invert candidate e-processes into a source confidence set

Define

\[
\boxed{
C_t(\alpha)
=
\{
s\in S:
E_{s,t}<1/\alpha
\}.
}
\]

Let s_star be the true candidate source and suppose its true conditional transport law remains inside the declared ambiguity family.

Ville's inequality gives

\[
P_{s_\star}
\left(
\sup_t E_{s_\star,t}\ge1/\alpha
\right)
\le\alpha.
\]

Hence

\[
\boxed{
P_{s_\star}
\left(
s_\star\in C_t(\alpha)
\;\text{for every }t
\right)
\ge1-\alpha.
}
\]

This is the key result.

It does NOT require Bonferroni over the number of false candidate sources because coverage fails only if the one true source candidate is falsely removed.

This is the discrete-source analogue of confidence-sequence inversion.

## 7. Source declaration rule

Do not declare merely when one posterior mass exceeds a fixed threshold.

Declare only when the anytime-valid set itself becomes spatially decisive.

Examples that preserve the coverage interpretation:

### Leaf declaration

\[
|C_t|=1.
\]

If C_t = {s}, report that source leaf.

### Region declaration

Let R_t be the smallest spatial region / PMFS quadtree node containing C_t.

Declare when

\[
\operatorname{diam}(R_t)\le r_{\rm declare},
\]

where r_declare is a task-resolution requirement fixed independently of source truth.

On the event that the confidence set covers the true source at all times, the declared region contains the true source.

This separates:
- statistical confidence level alpha;
- physically meaningful localization resolution r_declare.

Neither is a posterior-probability tuning knob.

## 8. Why the construction is compatible with the main innovation

M1 asks:

> where should the UAV measure so source identity remains distinguishable under admissible transport error?

Auxiliary A asks:

> when has the accumulated evidence reduced the set of transport-compatible sources enough to declare?

They share the same transport ambiguity set.

Thus the closed-loop story becomes coherent:

\[
\text{transport posterior}
\to
\text{worst-case source-information action}
\to
\text{new observation}
\to
\text{robust candidate e-processes}
\to
\text{anytime-valid source confidence set}.
\]

No unrelated deep network or independent calibration model is inserted.

## 9. Important caveat: validity is only as good as the ambiguity coverage

Anytime validity does not magically repair an uncertainty set that excludes the true transport law.

The formal guarantee is conditional on the actual observation law for the true source lying in the null ambiguity family at every step.

Therefore the paper must separate:

1. **statistical sequential validity given transport-set coverage**;
2. **empirical adequacy / calibration of the transport ambiguity set**.

Do not claim unconditional real-world 95% source coverage unless transport-set calibration justifies it.

## 10. Candidate alternative q_{s,t}

The e-process remains valid for any predictable numerator distribution q_{s,t}; q controls power, not Type-I validity.

Initial low-complexity options:

A. nominal posterior mixture over candidates other than s;

B. robust mixture over candidates other than s using least-favorable predictions;

C. one-step betting distribution optimized to maximize expected log e-growth under the current alternative belief.

Start with A.

Do not add a learned betting network before simple predictive mixtures are tested.

## 11. Relation to posterior probability

The e-process is not another renormalized PMFS posterior score.

A posterior probability answers a Bayesian belief question under a specified model/prior.

The e-process confidence set supplies a repeated/sequential error guarantee under optional stopping, conditional on the null model class.

Both can coexist:

- PMFS / M1 belief drives movement;
- e-process inversion certifies when candidate locations can be rejected / when the remaining spatial set is sufficiently small.

## 12. Hard falsification plan

### A0 — algebra / simulation validity

On a finite binary model where the null law is exactly known:

- run adaptive action selection;
- monitor all candidate e-processes;
- repeatedly stop at arbitrary data-dependent times;
- verify empirical probability that the true candidate is ever removed is <= alpha.

Use enough Monte Carlo trials to resolve alpha.

Failure => implementation / derivation bug; stop.

### A1 — ambiguity-set validity

Under controlled wind perturbations sampled inside the declared ambiguity set:

- test time-uniform true-source coverage;
- vary stopping policy aggressively;
- require empirical miscoverage to remain compatible with alpha.

If the true-source e-process is anti-conservative, kill or enlarge/rebuild the ambiguity set.

### A2 — declaration efficiency

On independent repaired Native PMFS / plume realizations, compare:

- official/current PMFS fixed declaration threshold;
- posterior max-probability threshold;
- entropy threshold;
- anytime-valid confidence-set declaration.

Report jointly:

- false declaration rate;
- declaration success rate;
- time / path length to declaration;
- final source error / source-containing rank;
- no-declaration rate by 300 s.

A method that achieves validity only by almost never declaring is not useful.

### A3 — model mismatch stress test

Introduce predeclared transport mismatch levels.

Required qualitative signature:

- naive posterior thresholds become overconfident / miscalibrated sooner;
- transport-robust confidence set preserves false-declaration control more gracefully;
- the set shrinks faster again as mismatch -> 0 or wind uncertainty decreases.

### A4 — destructive null

Break the relation between source-conditioned hit maps and observations while preserving marginal hit frequency.

The confidence set should stop shrinking or declarations should become rare.

If it continues to confidently declare, the construction is exploiting a spurious marginal/geometry effect.

## 13. Metrics and anti-tuning rules

Primary validity metric:

\[
P(\exists t:\;s_\star\notin C_t)
\]

over independent realizations.

Primary utility metrics:
- declaration time;
- final spatial diameter of C_t;
- no-declaration rate.

Do not:
- tune alpha to source error;
- choose alpha per House;
- choose r_declare after seeing truth;
- reset/restart e-processes opportunistically after bad evidence;
- remove inconvenient candidates using information not represented in the null family.

Predeclare alpha (for example 0.05) and physical resolution.

## 14. Novelty boundary

Do NOT claim as new:
- e-values/e-processes;
- Ville's inequality;
- confidence sequences;
- optional-stopping-safe sequential tests;
- source declaration itself;
- SPRT in robotics.

The candidate domain contribution would be:

**transport-robust e-process inversion for an anytime-valid spatial source confidence set inside adaptive robotic gas-source localization.**

Its value is strongest if it reuses the same physics-shaped transport ambiguity as M1.

## 15. Current verdict

**KEEP as Auxiliary A**, conditional on empirical validity after the repaired baseline returns.

It is preferable to adding conformal prediction at this stage because:
- it uses the sequential nature of GSL directly;
- it remains valid under adaptive stopping/action selection by construction;
- it needs no separate labeled calibration data for the basic construction;
- it solves a documented GSL weakness rather than decorating the main method.

Do not elevate it to the paper's main innovation unless M1 fails.
