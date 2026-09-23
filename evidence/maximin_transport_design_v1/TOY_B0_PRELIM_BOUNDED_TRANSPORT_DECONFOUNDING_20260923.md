# TOY-B0 preliminary evidence — controlled transport confounding

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`  
Status: **preliminary mechanism evidence; not House evidence**

## 1. Purpose

Test the proposed transport-deconfounding mechanism without relying on the old R2 baseline and without waiting for the repaired Native PMFS runs.

The toy is deliberately PMFS-like rather than a generic classifier:

- discrete candidate source set;
- nominal wind used by the planner;
- stochastic drift-diffusion / filament-age mixture produces candidate hit probabilities;
- the observation generator uses a different true wind;
- all acquisition methods use the same posterior update and same measurement budget;
- two fixed initial exploration measurements are shared by all methods;
- only subsequent measurement-location selection changes.

Primary metric:
- rank of the true source candidate.

This is a mechanism stress test only. It cannot validate the method for the paper.

## 2. Toy transport model

A filament of age \(k\) is approximated as

\[
X_k
\sim
\mathcal N(
s+w\Delta t k,\;
(\Delta t\,\sigma_v)^2 k I
).
\]

Candidate hit probability at a measurement cell is obtained by:
- evaluating cell occupancy probability for multiple filament ages;
- composing multiple filaments per age;
- averaging across the recording ages.

Planner:
- uses nominal \(w_0\).

Observation generator:
- uses \(w_{\rm true}=w_0+\delta w\).

Transport sensitivity:
- common-random-structure central finite differences in \(\delta u,\delta v\).

## 3. Methods

### Native

At each adaptive step choose the unvisited cell with largest posterior-weighted candidate hit-map variance.

### TO-inf

V5 unbounded transport-orthogonal sequential criterion:

\[
D^\perp_{sr}(B)
=
\min_{a\in\mathbb R^d}
\|d_{sr,B}+J_{sr,B}a\|^2.
\]

### Random

Uniform random unvisited cell.

### BTD-r — bounded transport deconfounding

After the negative TO-inf result, introduce the physically necessary finite ambiguity budget:

\[
\boxed{
D^{(r)}_{sr}(B)
=
\min_{\|a\|_2\le r}
\|d_{sr,B}+J_{sr,B}a\|^2
}
\]

and posterior-weighted accumulated score

\[
\mathcal I_r(B)
=
\frac12
\sum_{s,r}
\pi_s\pi_r
D^{(r)}_{sr}(B).
\]

Next-cell value is the marginal gain.

Reduction limits:

- \(r=0\): exactly native accumulated candidate variance;
- \(r\rightarrow\infty\): unbounded V5 transport-orthogonal criterion.

Thus BTD-r continuously interpolates between Native PMFS and the failed unlimited projection.

## 4. Completed unbounded test — NEGATIVE

Completed panel:

- 5 candidate sources;
- all candidate sources used as truth across repeated realizations;
- 2 fixed initial exploration measurements;
- 5 adaptive measurements;
- 30 Bernoulli samples per measurement stop;
- 25 independent seeds per truth source for the completed panel below.

### Results

#### Matched wind \(\delta w=(0,0)\)

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.016 | 0.984 |
| TO-inf | 1.040 | 0.976 |
| Random | 1.072 | 0.928 |

#### Cross-wind mismatch \(\delta w=(0,+0.10)\) m/s

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.016 | 0.984 |
| TO-inf | 1.216 | 0.856 |
| Random | 1.208 | 0.800 |

#### Cross-wind mismatch \(\delta w=(0,+0.18)\) m/s

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.040 | 0.960 |
| TO-inf | 1.656 | 0.576 |
| Random | 1.504 | 0.616 |

#### Cross-wind mismatch \(\delta w=(0,+0.25)\) m/s

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.096 | 0.904 |
| TO-inf | 1.872 | 0.456 |
| Random | 1.768 | 0.488 |

#### Along-wind mismatch \(\delta w=(+0.15,0)\) m/s

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.016 | 0.984 |
| TO-inf | 1.096 | 0.968 |
| Random | 1.112 | 0.896 |

## 5. Interpretation — hard correction to V5

The unbounded V5 criterion is **not retained as the main acquisition rule**.

In the deliberately confounded geometry, lateral source displacement and cross-wind bias are strongly aligned. The unlimited nuisance optimizer is allowed to explain arbitrarily large source differences as transport nuisance and therefore discards useful source information.

This is over-conservative and physically wrong because real transport error has finite amplitude.

Reclassification:

- V4/V5 unbounded orthogonalization: **diagnostic / limiting case only**;
- finite-radius shared transport ambiguity: **new lead formulation**.

Do not hide or overwrite this negative result.

## 6. Preliminary bounded-radius panel

A first completed small panel used the predeclared radius set

\[
r\in\{0.05,0.10,0.20,0.30\}\;{\rm m/s}.
\]

No radius was selected after truth reveal.

For 12 independent seeds per source, the bounded variants produced weak positive signals in some cross-wind mismatch settings, while TO-inf remained poor.

Example: \(\delta w=(0,+0.18)\) m/s:

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.0500 | 0.9500 |
| BTD-0.05 | 1.0833 | 0.9667 |
| BTD-0.10 | 1.1000 | 0.9500 |
| BTD-0.20 | 1.0500 | 0.9500 |
| BTD-0.30 | 1.0333 | 0.9833 |
| TO-inf | 1.6667 | 0.5167 |
| Random | 1.5000 | 0.6167 |

At stronger cross-wind mismatch \(\delta w=(0,+0.25)\) m/s:

| method | mean truth rank | top-1 |
|---|---:|---:|
| Native | 1.1000 | 0.9000 |
| BTD-0.05 | 1.1000 | 0.9500 |
| BTD-0.10 | 1.1167 | 0.9333 |
| BTD-0.20 | 1.0833 | 0.9167 |
| BTD-0.30 | 1.1833 | 0.8833 |
| TO-inf | 1.9667 | 0.4000 |
| Random | 1.8833 | 0.4333 |

These are **not enough to pass** the candidate:
- sample is still small;
- radius ordering is not stable;
- a source-blind radius calibration rule is not yet fixed.

## 7. Current decision

### KILL
Unbounded transport-orthogonal acquisition as the primary planner.

### KEEP
The underlying scientific mechanism:
- source-vs-transport confounding exists as a meaningful object;
- the nuisance must be physically bounded;
- shared transport perturbation is preferable to independent source-wise envelopes.

### NEW LEAD
**Bounded Transport Deconfounding (BTD)**

\[
D^{(r)}_{sr}(B)
=
\min_{\|a\|\le r}
\|d_{sr,B}+J_{sr,B}a\|^2.
\]

The next hard problem is not to find a post-hoc best \(r\), but to derive or estimate \(r\) source-blind from transport evidence.

## 8. Next gates

1. optimize the batched 2-D trust-region solver so larger panels finish reliably;
2. test both signs of cross-wind mismatch and an along-wind control;
3. test radius misspecification explicitly;
4. derive a source-blind radius from measured-vs-forward wind residuals / wind uncertainty;
5. run destructive sensitivity shuffles;
6. only then test BTD on repaired Native House data.

