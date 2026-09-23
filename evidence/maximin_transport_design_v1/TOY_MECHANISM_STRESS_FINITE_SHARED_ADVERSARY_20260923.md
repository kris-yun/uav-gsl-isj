# Controlled Mechanism Stress Test — Finite Shared Transport Adversary

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`  
Status: **toy mechanism evidence only — NOT House/PMFS validation**

## Purpose

Test whether the proposed source-vs-transport deconfounding mechanism has the correct qualitative behavior before the repaired Native PMFS artifacts are available.

This test intentionally does **not** use old R2 truth-dependent evidence.

## Toy physics

A free-space stochastic advection-diffusion filament model is used, matched to the structure of PMFS's free-space update:

\[
X_{k+1}=X_k+\Delta t(w+\epsilon_k),\qquad
\epsilon_k\sim N(0,\sigma^2 I).
\]

Parameters:
- domain: x in [0,10], y in [0,8];
- nominal wind: \([0.8,0.0]\) m/s;
- \(\Delta t=0.2\);
- \(\sigma=0.5\), matching the official PMFS example noise standard deviation;
- candidate sources: 7 x 7 lattice = 49 candidates;
- action set: fixed coarse 6 x 5 spatial lattice = 30 possible measurement positions;
- fixed initial history: four predeclared spatial points;
- four additional measurement acquisitions;
- source update: same absolute-discrepancy compatibility shape as PMFS, using \(\gamma=0.3\);
- transport sensitivity: common-random-free deterministic central finite difference in global wind drift;
- no source-specific tuning.

The expected stationary filament occupancy is approximated analytically by a finite mixture of Gaussian age cohorts and transformed to a bounded hit probability.

This is a **mechanism surrogate**, not an exact PMFS implementation.

## Compared acquisition rules

### Native

Posterior-weighted candidate hit-map variance:

\[
V_{\rm native}(x)=\operatorname{Var}_{s\sim\pi}[h_s(x)].
\]

### Unbounded transport-orthogonal

Pairwise source differences are projected completely outside the transport-nuisance tangent, equivalent to allowing arbitrarily large nuisance amplitude.

### Finite shared adversary

For each source pair and accumulated measurement set \(B\),

\[
D^{r}_{sr}(B)
=
\min_{\|a\|_2\le r_w}
\|d_{sr,B}+J_{sr,B}a\|_2^2.
\]

Acquisition is the posterior-weighted marginal increase in this finite-radius pairwise separation.

The radius is set equal to the **predeclared injected transport-mismatch budget** in this controlled test. It is not selected from source truth.

## Stress test A — 25 fixed source locations, crosswind mismatch 0.20 m/s

After four added measurements:

| method | mean truth rank | median truth rank | wins / ties / losses vs Native |
|---|---:|---:|---:|
| Native variance | 11.0 | 8 | — |
| finite shared adversary, r=0.20 | **9.4** | **7** | **3 / 20 / 2** |
| unbounded orthogonal projection | 11.2 | 9 | 5 / 7 / 13 |

The same aggregate result occurred for +0.20 and -0.20 m/s crosswind perturbations because the free-space toy is symmetric.

### Decision

**Unbounded / parameter-free orthogonalization is demoted.**

It is too conservative and produces more losses than wins in this controlled test.

The finite physically bounded adversary remains alive.

## Stress test B — mismatch gradient

12 predeclared source locations, +crosswind bias, four added measurements:

| injected drift mismatch | Native mean rank | finite-robust mean rank | Native median | robust median | robust W/T/L | mean rank improvement |
|---:|---:|---:|---:|---:|---:|---:|
| 0.05 m/s | 2.17 | 2.17 | 1.0 | 1.0 | 0 / 12 / 0 | 0.00 |
| 0.10 m/s | 4.08 | 4.00 | 2.5 | 1.5 | 3 / 8 / 1 | 0.08 |
| 0.20 m/s | 13.33 | **9.67** | 10.0 | **6.0** | **3 / 9 / 0** | **3.67** |
| 0.30 m/s | 17.08 | 16.50 | 15.0 | 15.0 | 1 / 11 / 0 | 0.58 |

## Mechanistic interpretation

The qualitative pattern is encouraging:

1. **Near matched transport (0.05):** robust acquisition is identical to Native.
2. **Small mismatch (0.10):** almost no effect.
3. **Moderate mismatch (0.20):** the robust rule rescues a small number of strongly confounded cases, producing a substantial mean/median truth-rank gain.
4. **Large mismatch (0.30):** both nominal inference and robust acquisition become poor; the robust benefit shrinks.

This is the expected signature of a method that removes **transport-confounded source information** rather than a method that generically smooths or regularizes every case.

However, the win count also shows that the benefit is sparse:
- at 0.20, most cases tie;
- improvement is concentrated in cases where Native becomes badly misled.

That is scientifically plausible, but it makes independent House-level confirmation essential.

## What this test does NOT establish

It does not show:
- improvement on House01/02/03;
- improvement under obstacles;
- improvement under official PMFS hit-map generation;
- correct radius calibration in real data;
- closed-loop localization benefit;
- publication-level novelty.

It only establishes that the finite shared-adversary mechanism can produce the predicted mismatch-dependent source-rank effect in a controlled PMFS-like transport model.

## Updated candidate decision

### Demote

- unbounded NOSI / infinite nuisance projection as the main movement rule.

Keep its confounding ratio only as a diagnostic.

### Keep for repaired-baseline falsification

- finite-radius shared transport adversary;
- posterior-weighted pairwise source separation;
- sequential complementary measurement design.

### New critical bottleneck

A publishable method cannot choose \(r_w\) from source truth.

Required next step after Native recovery:
1. estimate/calibrate transport-error radius source-blind;
2. freeze it before truth reveal;
3. reproduce the mismatch-gradient signature on independent plume realizations.

Potential remote-field calibration parent:
- Zhou & Zhu, *Calibrating Decision Robustness via Inverse Conformal Risk Control*, ICML 2026.

Do not integrate conformal calibration until the Native-data finite-radius probe is positive.
