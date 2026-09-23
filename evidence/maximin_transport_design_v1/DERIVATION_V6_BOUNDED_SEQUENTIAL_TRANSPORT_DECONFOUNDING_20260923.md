# M1 derivation v6 — Bounded Sequential Transport Deconfounding

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`  
Status: **current preferred main-formulation before repaired-House falsification**

## 0. Current decision

### Main line retained

Use a **finite**, physically admissible, shared transport perturbation:

\[
D^{(r)}_{sr}(B)
=
\min_{\|a\|_2\le r_t}
\|d_{sr,B}+J_{sr,B}a\|_2^2.
\]

The acquisition score is the posterior-weighted marginal gain in this quantity.

### Demoted

The unbounded nuisance projection

\[
\min_a\|d+Ja\|^2
\]

is no longer the preferred movement rule. Controlled toy stress tests showed it can be over-conservative and lose to Native PMFS.

Retain unbounded projection / confounding ratio only as a diagnostic.

---

## 1. Finite shared-adversary pairwise geometry

For candidate sources \(s,r\) and measurement history \(B=\{x_1,\ldots,x_m\}\),

\[
d_{sr,B}[k]
=
h_s(x_k)-h_r(x_k),
\]

\[
J_{sr,B}[k,:]
=
g_s(x_k)-g_r(x_k),
\]

where \(g_s(x)\) is the response of the candidate hit probability to a common low-dimensional transport perturbation.

The true source-pair discrepancy under nuisance \(a\) is locally

\[
d_{sr,B}+J_{sr,B}a.
\]

The finite robust separation is

\[
\boxed{
D^{(r)}_{sr}(B)
=
\min_{\|a\|_2\le r_t}
\|d_{sr,B}+J_{sr,B}a\|_2^2
}
\]

and the posterior-weighted accumulated source identifiability is

\[
\boxed{
\mathcal I_r(B)
=
\frac12
\sum_{s,r}
\pi_s\pi_r
D^{(r)}_{sr}(B).
}
\]

The next measurement is scored by

\[
\boxed{
U_r(x|B)
=
\mathcal I_r(B\cup\{x\})-\mathcal I_r(B).
}
\]

No separate entropy family is required.

---

## 2. Exact trust-region solution

For one source pair,

\[
A=J^TJ,\qquad
b=J^Td,\qquad
c=d^Td.
\]

Then

\[
D^{(r)}
=
\min_{\|a\|\le r}
a^TAa+2b^Ta+c.
\]

If the minimum-norm unconstrained solution

\[
a_0=-A^\dagger b
\]

satisfies \(\|a_0\|\le r\), then

\[
D^{(r)}=c-b^TA^\dagger b.
\]

Otherwise,

\[
a^\star=-(A+\lambda I)^{-1}b
\]

for the unique \(\lambda>0\) satisfying

\[
\|a^\star\|=r.
\]

For the first probe \(a=[\delta u,\delta v]\), so the inner optimization is 2-D plus a scalar root solve.

---

## 3. Exact native-PMFS reduction

At \(r=0\),

\[
D^{(0)}_{sr}(B)=\|d_{sr,B}\|^2.
\]

Therefore the marginal contribution of a new cell is

\[
D^{(0)}_{sr}(B\cup\{x\})-D^{(0)}_{sr}(B)
=
(h_s(x)-h_r(x))^2.
\]

Using

\[
\operatorname{Var}_\pi(h)
=
\frac12\sum_{s,r}\pi_s\pi_r(h_s-h_r)^2,
\]

we get

\[
\boxed{
U_0(x|B)
=
V_{\rm PMFS}(x).
}
\]

Thus bounded transport deconfounding is an exact conservative extension of the statistic the official PMFS Search state already uses.

---

## 4. Monotonicity

For fixed \(r\),

\[
D^{(r)}_{sr}(B\cup\{x\})
=
\min_{\|a\|\le r}
\left(
\|d_{sr,B}+J_{sr,B}a\|^2
+
[\Delta h_{sr}(x)+\Delta g_{sr}(x)^Ta]^2
\right)
\]

is at least

\[
D^{(r)}_{sr}(B).
\]

Therefore

\[
\boxed{
U_r(x|B)\ge 0.
}
\]

Do not claim submodularity without proof.

---

## 5. Physical scale of \(r\)

Official PMFS free-space filament dynamics use

\[
X_{k+1}
=
X_k+\Delta t[w(X_k)+\epsilon_k],
\quad
\epsilon_k\sim N(0,\sigma^2I).
\]

For a common drift error \(a\), the local transition KL divergence is

\[
D_{\rm KL}(P_{w+a}\Vert P_w)
=
\frac{\|a\|^2}{2\sigma^2}.
\]

So

\[
\boxed{
r
=
\sigma\sqrt{2\eta}.
}
\]

This provides units and a direct relation to PMFS's own stochastic transport scale.

It does **not**, by itself, choose the correct radius.

---

## 6. Source-blind radius evidence already available in the official stack

Two official-source facts matter.

### 6.1 PMFS repeatedly queries the whole wind grid

In \`PMFS::processGasAndWindMeasurements()\`, after every gas/wind measurement PMFS calls

\`PMFSLib::EstimateWind(...)\`

over the grid.

When \`useWindGroundTruth=true\`, that function queries GADEN's \`/wind_value\` service and writes the returned current field into \`estimatedWindVectors\`.

### 6.2 GADEN advances its wind scene over time

In GADEN's \`gaden_player/src/simulation_player.cpp\`:

- \`GetWindValue_srv()\` returns \`Scene->SampleWind(...)\`;
- the player repeatedly calls \`Scene->AdvanceTimestep()\` according to \`player_freq\`.

Therefore the Native simulation stack naturally exposes a source-independent time sequence

\[
W_1,W_2,\ldots,W_t
\]

of transport fields.

This can be logged without knowing or using the gas-source location.

---

## 7. Candidate auxiliary A1 — online transport ambiguity calibration

### Core observable

Define temporal wind innovations

\[
R_t=W_t-W_{t-1}.
\]

For the first global-bias nuisance model, project the field innovation onto the global drift basis:

\[
a_t
=
\arg\min_a
\|R_t-Ba\|_M^2.
\]

For a spatially constant 2-D bias basis, \(a_t\) is essentially an appropriately weighted mean wind-vector change across the chosen free-space region.

This yields a stream of source-blind transport perturbation samples

\[
a_2,\ldots,a_t.
\]

### Minimal first calibration

Before importing any conformal machinery, test whether simple predeclared statistics of this stream predict the amount of robustness needed:

- rolling empirical norm distribution;
- trailing high quantile;
- maximum over a fixed physical history window;
- covariance ellipsoid of \(a_t\).

The window must be tied to PMFS/GADEN timing, not optimized using truth-source rank.

### Why not immediately claim conformal guarantees

Standard conformal calibration relies on exchangeability or related assumptions, while consecutive wind fields are temporally dependent.

2026 Anytime-Valid Conformal Risk Control gives sequential high-probability risk-control machinery and discusses growing calibration sets / distribution shift, but it does not automatically validate arbitrary dependent GADEN wind residuals.

2026 ICML Inverse Conformal Risk Control explicitly addresses calibration of robustness levels in robust optimization, but the published reference implementation currently demonstrates offline calibration for robust linear programs and lists online/sequential extensions as future work.

Therefore:

> conformal/ICRC is a promising **parent idea**, not a guarantee we may simply inherit.

A1 becomes a real auxiliary innovation only if its assumptions and calibration target are made valid for our wind-residual process.

---

## 8. Stronger future A1 option: empirical transport set instead of scalar radius

If a scalar radius is inadequate, retain the actual source-blind transport samples.

For a low-dimensional basis:

\[
\mathcal A_t
=
\operatorname{conv}
\{a_{\tau}:\tau\le t\}
\]

or an uncertainty ellipsoid fit to the residual stream.

Then use

\[
D^{(\mathcal A_t)}_{sr}(B)
=
\min_{a\in\mathcal A_t}
\|d_{sr,B}+J_{sr,B}a\|^2.
\]

This preserves the key shared-adversary geometry and avoids pretending wind error is isotropic.

Do not adopt this richer version unless the 2-D ball fails for identifiable physical reasons.

---

## 9. What repaired Native artifacts must log

Ask the baseline-recovery output to preserve, if available:

- timestamp of each full wind-grid query;
- \`u,v\` at all free cells for each query or a lossless saved grid;
- GADEN player timestep / iteration if exposed;
- PMFS source-update timestamp;
- exact wind grid used for each candidate simulation;
- robot measurement locations and timestamps.

These are sufficient to test A1 without source truth.

If the Codex recovery run does not currently save the historical wind grids, add instrumentation in a separate commit after baseline parity is proven. Instrumentation must not change algorithm state.

---

## 10. Immediate falsification when data arrive

### R-CAL0

Compute the time series of projected wind innovations \(a_t\).

Required:
- nonzero temporal variability;
- stable units / no coordinate-frame sign jumps;
- distribution not dominated by service failures.

If GADEN wind is effectively static in the recovered scenarios, kill temporal self-calibration for those experiments.

### R-CAL1

For each source update, compare a source-blind radius estimate from *past only* with the retrospectively observed next wind-field change.

Do not use source truth.

### R-CAL2

Freeze the radius rule, then compare:
- Native \(r=0\);
- fixed physically predeclared radius panel;
- source-blind adaptive \(r_t\).

Only after those are frozen reveal truth-source ranks.

A1 survives only if adaptive \(r_t\) preserves or improves the finite-radius mechanism without source-truth tuning.

---

## 11. Current module hierarchy

### Main candidate

**Bounded Sequential Transport Deconfounding**

Core claim:
PMFS's nominal candidate variance can contain transport-confounded source information. Select complementary measurements whose candidate-source differences remain separated under a single bounded shared transport perturbation.

### Diagnostic only

- unbounded nuisance projection;
- transport-confounding ratio;
- independent hit-probability intervals.

### Auxiliary candidate A1

**Source-blind online transport ambiguity calibration from the wind-field stream**, potentially upgraded with modern conformal risk-control ideas only if assumptions can be justified.

No second auxiliary is frozen yet.
