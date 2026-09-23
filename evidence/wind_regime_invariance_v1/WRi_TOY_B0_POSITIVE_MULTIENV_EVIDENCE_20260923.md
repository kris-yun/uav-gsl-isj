# WRi-TOY-B0 — Positive multi-environment mechanism evidence

Date: 2026-09-23  
Branch: \`research/wind-regime-invariance-v1\`  
Status: **POSITIVE MECHANISM SIGNAL; still not House validation**

## 1. Experiment design

Purpose:
test only the source-inference consequence of preserving wind environments.

All compared methods receive:
- exactly the same source candidates;
- the same measurement locations;
- the same generated observations;
- the same true source;
- no trajectory difference.

Five candidate source positions are used, and every candidate is used as truth.

For each truth source:
- 200 independent observation seeds;
- 8 source-blind measurement locations;
- the same 8 locations are revisited once in each of two wind environments;
- 30 Bernoulli hit trials per stop.

Total:
- 1000 independent trials per wind-switch magnitude.

Toy plume physics:
- PMFS-like stochastic drift-diffusion age mixture;
- planner/source model receives wind vector;
- hit probability is obtained from filament occupancy statistics.

This is a controlled mechanism unit test, not a claim about House performance.

---

## 2. Compared inference semantics

### A — collapse-current

Use all historical observations, but explain all of them with the **final/current wind forward model**.

This deliberately represents the hypothesized PMFS temporal mismatch:

\[
\text{multi-environment historical evidence}
\quad\rightarrow\quad
\text{single current-environment forward}.
\]

### B — average-wind

Use all historical observations and one forward model generated at the temporal average wind.

This is an important simple-fix baseline.

### C — recent-only

Discard the old environment; infer the source only from the final/current environment.

This represents recency/sliding-window logic.

### D — regime-all

For each environment \(e\), use the corresponding forward prediction and combine evidence for the same source:

\[
\log L(s)
=
\sum_e
\log p(D_e|s,W_e).
\]

### E — regime-equal

Equal-data-count control against recent-only.

Only 8 total stops are retained:
- 4 spatial locations from environment 1;
- the complementary 4 locations from environment 2.

Thus it uses the same number of stops as recent-only and covers the same total set of 8 unique measurement locations.

### F — label-swap null

The environment labels are deliberately swapped:
- observations from environment 1 are scored with environment 2's forward map;
- observations from environment 2 are scored with environment 1's map.

This preserves data volume and the set of forward models but destroys the correct environment/evidence correspondence.

---

## 3. Stationary sanity check

When both environments are identical:

- collapse-current and regime-all are mathematically the same model;
- in the completed earlier 100-seed/source check both achieved top-1 = 99.8%.

This is the required zero-regime-change reduction.

---

## 4. Cross-wind switch gradient

The wind switches from

\[
w_1=w_0+(0,+m)
\]

to

\[
w_2=w_0+(0,-m).
\]

### \(m=0.08\) m/s

| Method | Mean truth rank | Top-1 | Top-2 |
|---|---:|---:|---:|
| collapse-current | 1.052 | 0.948 | 1.000 |
| average-wind | 1.008 | 0.992 | 1.000 |
| recent-only | 1.058 | 0.946 | 0.997 |
| regime-all | **1.001** | **0.999** | **1.000** |
| regime-equal | 1.040 | 0.966 | 0.997 |
| label-swap null | 1.035 | 0.965 | 1.000 |

### \(m=0.12\) m/s

| Method | Mean truth rank | Top-1 | Top-2 |
|---|---:|---:|---:|
| collapse-current | 1.105 | 0.895 | 1.000 |
| average-wind | 1.008 | 0.992 | 1.000 |
| recent-only | 1.071 | 0.932 | 0.998 |
| regime-all | **1.000** | **1.000** | **1.000** |
| regime-equal | 1.032 | 0.974 | 0.997 |
| label-swap null | 1.074 | 0.926 | 1.000 |

### \(m=0.18\) m/s

| Method | Mean truth rank | Top-1 | Top-2 |
|---|---:|---:|---:|
| collapse-current | 1.310 | 0.692 | 0.998 |
| average-wind | 1.022 | 0.979 | 0.999 |
| recent-only | 1.074 | 0.927 | 0.999 |
| regime-all | **1.001** | **0.999** | **1.000** |
| regime-equal | 1.035 | 0.969 | 0.997 |
| label-swap null | 1.283 | 0.724 | 0.994 |

### \(m=0.25\) m/s

| Method | Mean truth rank | Top-1 | Top-2 |
|---|---:|---:|---:|
| collapse-current | 1.560 | 0.472 | 0.972 |
| average-wind | 1.102 | 0.903 | 0.996 |
| recent-only | 1.056 | 0.944 | 1.000 |
| regime-all | **1.001** | **0.999** | **1.000** |
| regime-equal | **1.063** | **0.941** | 0.997 |
| label-swap null | 1.931 | 0.265 | 0.832 |

Important interpretation at \(m=0.25\):

- regime-all uses both environments and is almost perfect;
- average-wind uses all observations but reaches only 90.3% top-1;
- regime-equal uses only **half as many total stops as regime-all** and the same number of stops as recent-only, yet retains 94.1% top-1;
- the wrong environment assignment collapses to 26.5% top-1.

Therefore the effect is not explained solely by:
- more samples;
- averaging the wind;
- a generic regularization from multiple forward models.

Correct environment/evidence matching carries source-identification information.

---

## 5. Mechanism interpretation

The source is invariant but the plume is environment-dependent.

For true source \(s^\star\),

\[
D_e
\sim
P(\cdot|s^\star,W_e).
\]

A current-wind collapse incorrectly approximates

\[
\prod_e P(D_e|s,W_E),
\]

whereas regime factorization uses

\[
\boxed{
\prod_e P(D_e|s,W_e)
}.
\]

A mean-wind approximation instead uses

\[
\prod_e P(D_e|s,\bar W).
\]

Because the plume forward operator is nonlinear,

\[
F_s(\mathbb E[W])
\neq
\mathbb E[F_s(W)]
\]

in general, and neither expression preserves which observations arose under which transport condition.

The multi-environment representation retains this correspondence.

---

## 6. Why this is not just recency

At large regime changes:
- recent-only is much better than current-wind collapse;
- however it throws away a physically valid old view of the same invariant source.

Regime-all uses both environments correctly and outperforms recent-only.

The equal-count control shows that even without a larger measurement count, distributing observations across distinct correctly modeled wind environments can retain very strong source identity.

This supports the intended statement:

> old measurements can be stale for reconstructing the **current plume** yet remain informative for identifying the **time-invariant source**.

---

## 7. Why the average-wind baseline matters

For small/moderate symmetric changes, the mean wind can perform extremely well.

Therefore the paper cannot claim that regime factorization is always needed.

The next tests must identify when the environment mixture is sufficiently nonlinear/multimodal that

\[
F(\bar W)
\]

ceases to approximate the multi-regime evidence.

This becomes a testable regime-diversity / noncommutativity condition rather than a universal claim.

---

## 8. Current decision

### PASS TO NEXT STAGE

WRi-PMFS has passed the controlled mechanism gate more convincingly than the preceding transport-orthogonal candidate.

Positive evidence includes:
- correct stationary reduction;
- monotonic degradation of current-wind collapse with cross-wind regime separation;
- advantage over recent-only;
- strong equal-count result;
- strong destructive environment-label null;
- advantage over average-wind at large regime separation.

### NOT YET ACCEPTED AS MAIN INNOVATION

Remaining required tests:

1. asymmetric regime changes;
2. direction-change vs speed-change controls;
3. three or more environments;
4. continuous drifting wind rather than oracle discrete labels;
5. source-blind regime discovery;
6. direct novelty audit against multi-wind GSL/source inversion;
7. repaired Native House truth-source-rank test.

