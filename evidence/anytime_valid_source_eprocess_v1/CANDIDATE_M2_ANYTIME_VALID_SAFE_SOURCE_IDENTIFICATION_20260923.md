# Candidate M2 — Anytime-Valid Safe Source Identification with e-Processes

Date: 2026-09-23  
Branch: \`research/anytime-valid-source-eprocess-v1\`  
Status: **KEEP FOR HARD FALSIFICATION — new main-thesis candidate**

## 1. Mother idea

The candidate transfers the modern **e-value / e-process / safe-testing** paradigm into mobile gas-source localization.

The main scientific claim is NOT:
- sequential hypothesis testing;
- active hypothesis testing;
- Chernoff information;
- a likelihood-ratio planner.

Those ideas are old.

The 2024–2026 parent idea is:

> inference should remain statistically valid under adaptive data collection, continuous monitoring, optional continuation, and data-dependent stopping.

Recent parent anchors:

1. Grünwald, de Heide & Koolen, *Safe testing*, JRSS-B 86(5), 2024.
   - e-values;
   - e-processes / optional continuation;
   - composite nulls and nuisance parameters;
   - growth-rate optimal safe evidence.

2. Lindon & Kallus, *Anytime-Valid A/B Testing of Counting Processes*, AISTATS 2025.
   - anytime-valid confidence processes / e-processes with time-uniform error guarantees.

3. Adusumilli, *Continuous time asymptotic representations for adaptive experiments*, 2026.
   - e-processes for adaptive experiments;
   - “any-time and any-experiment valid” inference.

4. NeurIPS 2026 workshop *E-Values: From Statistics to ML*.
   - evidence that the paradigm is moving from statistics into modern ML systems.

## 2. Why PMFS is a natural interface

Official PMFS already produces the required event stream.

For every gas measurement event:

\`\`\`cpp
if (concentration > thresholdGas)
    ... true ...   // GAS HIT
else
    ... false ...  // NOTHING
\`\`\`

Therefore each raw observation is naturally

\[
Y_t\in\{0,1\}.
\]

For each candidate source \(s\), PMFS filament simulation provides a predicted hit probability at the selected measurement position:

\[
h_{s,t}(x_t).
\]

Thus PMFS already contains:
- finite/discrete source hypotheses;
- online adaptive sensing locations;
- Bernoulli hit/miss observations;
- candidate-specific predictive probabilities;
- a data-dependent stopping/declaration process.

The current PMFS source score, however, is a heuristic map-compatibility product rather than an anytime-valid sequential evidence process.

## 3. Critical novelty boundary

Do NOT claim “first active sequential hypothesis testing.”

Controlled sensing / active multihypothesis testing dates at least to:

- Nitinawarat, Atia & Veeravalli, ICASSP/ISIT 2012;
- Nitinawarat, Atia & Veeravalli, IEEE TAC 2013.

Those works already jointly design:
- sensing/control actions;
- stopping rules;
- multihypothesis decisions;
- likelihood/Chernoff-information-driven evidence.

The candidate survives only if its contribution is specifically:

> **safe anytime-valid source evidence under adaptively chosen robot measurements and composite forward-model uncertainty**, integrated with PMFS’s filament-generated hit predictions.

## 4. Composite source hypothesis

A point prediction \(h_s(x)\) is too brittle under transport/model mismatch.

Instead candidate source \(s\) defines a **composite null**:

\[
H_s:
p_t
=
P(Y_t=1\mid\mathcal F_{t-1},x_t,s)
\in
I_{s,t}(x_t)
=
[\ell_{s,t}(x_t),u_{s,t}(x_t)]
\quad\forall t.
\]

The interval is allowed to include:
- stochastic forward uncertainty;
- source-cell extent;
- predeclared transport/wind ambiguity;
- other source-blind simulator uncertainty.

How to construct a non-vacuous, scientifically defensible interval is an empirical bottleneck and a hard falsification gate.

## 5. One-step safe evidence factor

Before observing \(Y_t\), choose a predictable alternative hit probability

\[
q_{s,t}\in(0,1)
\]

using only past information.

Project it onto the source candidate’s composite null interval:

\[
p^\*_{s,t}
=
\operatorname{clip}
(q_{s,t},\ell_{s,t},u_{s,t}).
\]

Define

\[
\boxed{
e_{s,t}
=
\frac{
q_{s,t}^{Y_t}
(1-q_{s,t})^{1-Y_t}
}{
(p^\*_{s,t})^{Y_t}
(1-p^\*_{s,t})^{1-Y_t}
}
}
\]

For every true conditional hit probability

\[
p_t\in[\ell_{s,t},u_{s,t}],
\]

\[
\mathbb E_{p_t}
[e_{s,t}\mid\mathcal F_{t-1}]
\le1.
\]

Reason:
- if \(q>u\), \(p^\*=u\) and the expectation is maximized at \(p=u\), where it equals 1;
- if \(q<\ell\), \(p^\*=\ell\) and the expectation is maximized at \(p=\ell\), where it equals 1;
- if \(q\in[\ell,u]\), \(p^\*=q\) and \(e=1\).

No i.i.d. assumption is needed beyond the conditional Bernoulli/conditional-mean null at each predictable step.

## 6. Source-candidate e-process

Accumulate evidence against source candidate \(s\):

\[
\boxed{
E_t(s)
=
\prod_{\tau=1}^{t} e_{s,\tau}
}
\]

Under \(H_s\), this is a nonnegative test supermartingale / e-process.

Therefore, for any adaptive robot policy and any data-dependent stopping time,

\[
P_{H_s}
\left(
\sup_t E_t(s)\ge\frac1{\alpha_s}
\right)
\le
\alpha_s.
\]

Interpretation:

> if candidate \(s\) is compatible with the true conditional hit process, the probability of ever falsely eliminating it is controlled.

## 7. Anytime-valid source confidence set

For a **single-source** localization problem, no Bonferroni split across the candidate grid is required to obtain confidence-set coverage.

Define

\[
\boxed{
\mathcal C_t^\alpha
=
\left\{
s:E_t(s)<1/\alpha
\right\}.
}
\]

If the true source hypothesis is \(s^\star\), coverage only requires that its own e-process does not cross the rejection threshold. Hence

\[
P_{s^\star}
\left(
s^\star\in\mathcal C_t^\alpha
\ \forall t
\right)
=
P_{s^\star}
\left(
\sup_t E_t(s^\star)<1/\alpha
\right)
\ge1-\alpha.
\]

The fact that many false candidate hypotheses are tested does not require replacing \(\alpha\) by \(\alpha/|S|\) for this inverted confidence set: only one candidate is the true null whose retention determines coverage.

This materially improves power. At \(\alpha=0.05\), the evidence threshold is \(20\), not \(20|S|\).

A multiplicity allocation may become necessary for a different inferential target, e.g. simultaneous guarantees about multiple true sources, multiple declarations, or dynamically introduced hierarchical hypotheses. Those extensions must be derived separately rather than imported into the single-source case.

This is fundamentally different from a posterior threshold:
- validity is uniform over time;
- the robot may adapt its next position based on all previous measurements;
- the robot may stop whenever the evidence is sufficient.

## 8. Growth-rate link: evidence and movement use one principle

Under an alternative Bernoulli prediction \(q\),

\[
\mathbb E_q[\log e]
=
D_{\rm KL}
\left(
\operatorname{Ber}(q)
\Vert
\operatorname{Ber}(p^\*)
\right).
\]

Thus a candidate location gives zero safe evidence against source \(s\) when the competing prediction lies inside \(s\)’s allowed interval.

It gives positive evidence only when the competing predictive law lies outside the composite null.

This provides a natural acquisition quantity:

\[
G_t(x)
=
\sum_{s\in\mathcal C_t}
w_s
D_{\rm KL}
\left[
\operatorname{Ber}(q_{s,t}(x))
\Vert
\operatorname{Ber}
(
\operatorname{clip}(q_{s,t}(x),I_{s,t}(x))
)
\right].
\]

A max-min version can target the hardest surviving source.

Important:
controlled sensing / Chernoff-style action selection is old.
The claimed role of \(G_t\) is specifically to accelerate a **composite-null e-process whose validity is preserved under the resulting adaptive path**.

## 9. Choosing the alternative q

First falsification:

\[
q_{s,t}(x)
=
\frac{
\sum_{r\in\mathcal C_t,r\ne s}
w_r h_{r,t}(x)
}{
\sum_{r\in\mathcal C_t,r\ne s}w_r
}.
\]

Weights must be predictable from past information only.

Do not optimize q using source truth.

Later, if warranted, reverse-information-projection / growth-rate-optimal constructions from Safe Testing may replace this simple mixture.

## 10. Why this may solve a real PMFS scientific weakness

PMFS:
- repeatedly observes;
- actively changes robot position based on previous observations;
- repeatedly updates candidate source scores;
- declares a source using a threshold/stopping rule.

This is exactly the setting where a fixed-time confidence interpretation can fail if reused after continuous monitoring/adaptive collection.

An e-process is designed for this data-dependent continuation/stopping regime.

The scientific thesis is:

> **gas-source localization should maintain evidence that is valid along the same adaptive trajectory that generated it, rather than treating an adaptively collected stream as if it were a fixed experiment.**

## 11. Hard risks / kill conditions

### K1 — composite interval vacuity
If physically honest source/transport intervals are so wide that almost every competing \(q\) lies inside every interval, then e-factors are almost always 1 and source elimination is powerless.

Kill or demote.

### K2 — true-candidate rejection under real mismatch
If point-null or narrow-interval e-processes rapidly eliminate the truth candidate on recovered Native/VGR data, the simulator family is not calibrated enough for safe claims.

Do not rescue by truth-tuning intervals.

### K3 — only independence makes it work
The method must be formulated in conditional/predictable form.

If the practical implementation silently relies on independent hits while PMFS collects correlated repeated measurements, NO-GO.

Possible source-blind fixes:
- one designated event per stop;
- block-level predictive law;
- wider composite intervals for conditional hit probability.

### K4 — no efficiency
If safe validity requires so much conservatism that candidate set size barely shrinks within 300 s, it cannot be the main algorithm.

### K5 — no GSL novelty
A final literature audit must find no prior robotic GSL that already maintains time-uniform e-process/confidence-sequence source sets under adaptive sensing.

## 12. Falsification sequence

### SAFE-F0 — pure algebra
Verify:
- one-step composite-null expectation ≤1 over a dense grid of \((\ell,u,q,p)\);
- predictable adaptive q preserves crossing control in Monte Carlo;
- expected log growth equals binary KL to the clipped null.

### SAFE-B0 — repaired Native frozen replay
Use raw HIT/MISS events and frozen candidate hit maps.

Three predeclared arms:
1. native PMFS source score;
2. point-null e-process \(I_s=\{h_s\}\);
3. source-blind composite-interval e-process.

Report before truth:
- number of surviving candidates vs event count;
- e-process trajectories;
- fraction of e-factors equal to 1;
- stopping time / no-stop;
- robustness to event thinning.

Reveal truth only after all paths freeze:
- whether truth candidate ever gets rejected;
- its survival margin;
- final candidate-set size.

### SAFE-B1 — independent plume realizations
Hard gate:
- truth candidate survival rate;
- candidate-set contraction;
- time to unique/small set;
- no truth-tuned interval widths.

### SAFE-B2 — closed-loop
Only if B0/B1 are positive:
- e-growth movement;
- Native movement + e-process inference;
- Native PMFS baseline.

Primary metrics:
- truth-source candidate set/rank;
- false declaration;
- declaration time;
- endpoint error secondary.

## 13. Proposed module structure if successful

### Main innovation
**Anytime-valid e-process source evidence map**
- candidate-specific safe evidence;
- time-uniform source confidence set;
- adaptive stopping/declaration guarantee.

### Auxiliary A
**Composite transport-safe null**
- source-blind PMFS hit-probability interval under forward uncertainty.

### Auxiliary B
**Growth-optimal safe sensing**
- move where expected e-capital growth against surviving candidates is largest.

These three modules share one scientific narrative rather than being unrelated patches.

## 14. Current assessment

Scientific-narrative strength: **high**.  
2024–2026 remote-field relevance: **high**.  
Direct GSL collision found so far: **none obvious**.  
Classical active-hypothesis-testing collision: **strong but explicitly bounded**.  
PMFS interface fit: **very high**.  
Training/data requirement: **low**.  
Biggest risk: **non-vacuous composite calibration under plume/model mismatch**.

Status:

\`KEEP FOR SAFE-B0 / INDEPENDENT-REALIZATION FALSIFICATION\`.
