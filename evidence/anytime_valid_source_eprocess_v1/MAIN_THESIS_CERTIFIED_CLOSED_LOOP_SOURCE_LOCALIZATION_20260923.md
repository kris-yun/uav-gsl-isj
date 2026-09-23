# MAIN THESIS CANDIDATE — Certified Closed-Loop Source Localization via e-Processes

Date: 2026-09-23  
Branch: \`research/anytime-valid-source-eprocess-v1\`  
Status: **current lead main-scientific-theme candidate**

## 1. Big scientific idea

The mother idea is **safe / anytime-valid inference**.

The paper-level question is:

> How can a mobile robot make a source-location declaration whose error interpretation remains valid even though the robot continuously monitors data, changes where it measures based on past observations, and stops when the evidence looks sufficient?

This is different from:
- improving the plume model;
- replacing PMFS's acquisition reward;
- posterior-temperature calibration;
- classical fixed-sample confidence;
- old controlled-sensing likelihood-ratio tests.

Proposed scientific framing:

**Certified Closed-Loop Gas-Source Localization**

or

**Anytime-Valid Source Confidence Mapping**

## 2. Why this is a real gap in the PMFS-style pipeline

Official PMFS repeatedly:

1. collects gas measurements;
2. updates a hit-probability map;
3. updates source probability;
4. chooses the next location from current data;
5. checks a declaration condition after repeated adaptive updates.

Its source declaration computes the spatial variance of the source-probability map:

\[
V_t
=
\sum_x p_t(x)\|x-\mathbb E_{p_t}[X]\|^2,
\]

and declares success when

\[
V_t < \texttt{convergence\_thr}.
\]

This is a concentration heuristic.

It is not a statement of the form:

\[
P(\text{declared source is wrong})\le\alpha
\]

and it does not have a time-uniform interpretation under continuous monitoring / adaptive stopping.

The broader GSL literature commonly uses:
- posterior entropy thresholds;
- posterior concentration;
- fixed iteration budgets;
- heuristic source-vicinity rules.

The novelty target is therefore not "having a stopping rule."

It is **certifying the source declaration along the closed-loop adaptive trajectory that generated the evidence.**

## 3. Candidate-wise safe evidence

For every candidate source/region \(s\), maintain an e-process

\[
E_t(s).
\]

Candidate \(s\) remains in the anytime-valid source confidence set while

\[
E_t(s)<1/\alpha.
\]

Define

\[
\boxed{
\mathcal C_t^\alpha
=
\{s:E_t(s)<1/\alpha\}.
}
\]

If the true source candidate \(s^\star\) satisfies its composite predictive null,

\[
\boxed{
P(
s^\star\in \mathcal C_t^\alpha
\ \text{for all }t
)
\ge1-\alpha.
}
\]

This remains valid for data-dependent stopping because the candidate evidence is an e-process.

## 4. Convert a candidate confidence set into a spatial certificate

PMFS candidates are spatial regions, not only labels.

Let \(R_s\subset\mathbb R^2\) be candidate source region \(s\).

The surviving spatial source set is

\[
\boxed{
\mathcal U_t^\alpha
=
\bigcup_{s\in\mathcal C_t^\alpha}R_s.
}
\]

Under the true-source null family,

\[
P(
x^\star\in\mathcal U_t^\alpha
\ \text{for all }t
)
\ge1-\alpha.
\]

This gives an anytime-valid **confidence map/support**, not merely a scalar confidence number.

## 5. Safe spatial declaration theorem

At any data-dependent stopping time \(\tau\), choose a declaration point \(\hat x_\tau\).

Suppose the robot stops only when

\[
\sup_{x\in\mathcal U_\tau^\alpha}
\|x-\hat x_\tau\|
\le\varepsilon.
\]

Then

\[
\boxed{
P(
\|\hat x_\tau-x^\star\|>\varepsilon
)
\le\alpha.
}
\]

Reason:
with probability at least \(1-\alpha\), the true source remains inside \(\mathcal U_t^\alpha\) at every time. On that event, the stopping geometry itself guarantees distance at most \(\varepsilon\).

Thus the confidence set converts safe sequential evidence into a physically interpretable localization certificate.

### Practical declaration point

Use a source-blind geometric center of the surviving set, e.g.:
- minimum enclosing-circle center;
- Chebyshev center under obstacle-compatible geometry;
- PMFS posterior mean **only if** its worst-case distance to the surviving support is checked.

The certificate radius is

\[
r_t
=
\inf_z
\sup_{x\in\mathcal U_t^\alpha}
\|x-z\|.
\]

Stop when \(r_t\le\varepsilon\).

No posterior entropy threshold is required for the certificate.

## 6. Natural fit to the benchmark

If the experimental definition of successful localization uses a distance tolerance, e.g. 0.5 m, set

\[
\varepsilon=0.5\text{ m}
\]

**before** the run.

Then source declaration has the directly relevant interpretation:

> the probability that an anytime/data-dependent declaration lies farther than the benchmark tolerance from the true source is controlled by \(\alpha\),

subject to validity of the composite source model.

Do not tune \(\varepsilon\) from performance results.

## 7. Why adaptive movement does not invalidate the core guarantee

At time \(t\), the robot's next measurement location \(x_t\) is allowed to depend on the entire past filtration \(\mathcal F_{t-1}\).

The alternative/betting choice \(q_t\), source interval \(I_{s,t}\), and action \(x_t\) must all be predictable before observing \(Y_t\).

If the one-step e-factor satisfies

\[
\mathbb E[
e_{s,t}
\mid
\mathcal F_{t-1}
]
\le1
\]

under candidate \(s\), then

\[
E_t(s)=\prod_{\tau\le t}e_{s,\tau}
\]

remains a test supermartingale along that adaptive trajectory.

This is the key conceptual upgrade over a fixed-data certificate.

## 8. Main / auxiliary architecture if data support it

### Main innovation — Anytime-Valid Source Confidence Map
- candidate-wise e-process evidence;
- time-uniform surviving source support;
- spatial confidence set;
- certified source declaration.

### Auxiliary A — Safe Composite Forward Null
Model each candidate as a family of conditional hit probabilities rather than a brittle point prediction.

Goal:
- absorb source-cell extent;
- simulator stochasticity;
- predeclared transport uncertainty;
- without truth-tuned widening.

This is the main calibration bottleneck.

### Auxiliary B — Evidence-Growth Active Sensing
After the inference layer is proven useful, choose robot measurements to accelerate elimination by maximizing expected safe log-evidence growth against surviving candidates.

The path is optimized for **certificate contraction**, not generic posterior entropy.

The main validity guarantee must remain true under this adaptive policy.

## 9. Novelty boundaries

### Old / not claimable
- sequential hypothesis testing;
- SPRT;
- Chernoff information;
- controlled sensing;
- active multihypothesis testing;
- adaptive stopping in general;
- e-processes in robotics in general;
- simulator-assisted e-processes in general.

### 2026 robotics near-neighbor
Chen & Weng, *Sim-to-Real Betting on the E-Process*, arXiv:2606.24038.

They use simulators to improve anytime-valid confidence sequences for robot-performance/mean certification.

Therefore "simulator + robot + e-process" is not new.

### Current narrow target
What remains distinct is the joint object:

> **candidate-wise anytime-valid spatial source confidence mapping and safe declaration under an adaptively controlled mobile sensing trajectory.**

Do not use "first" until the final literature audit is complete.

## 10. Hard falsification logic

The theorem is mathematically easy.

The method is scientifically useful only if the confidence map has power.

The main empirical bottleneck is:

> can a source-blind composite null remain honest enough to protect the true source while narrow enough that wrong source regions accumulate e-evidence and are eliminated within the search budget?

Therefore:
- SAFE-F0 passing is necessary but weak;
- SAFE-B0/B1 power and truth retention are the real gates.

## 11. Current status

\`LEAD MAIN-THESIS CANDIDATE — PENDING SAFE-B0/B1\`.
