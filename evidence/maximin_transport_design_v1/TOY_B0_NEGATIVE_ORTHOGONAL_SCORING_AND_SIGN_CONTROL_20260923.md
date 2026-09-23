# TOY-B0 update — transport-orthogonal scoring also fails

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`

## Purpose

After the unbounded acquisition failure and the direction-sensitive bounded-acquisition result, test whether the real problem was only that observations were still fed into the nominal PMFS likelihood.

To isolate inference from planning:

1. generate one measurement trajectory using **Native candidate-variance acquisition**;
2. use exactly the same selected cells and exactly the same observations for both source-ranking rules;
3. compare:
   - Native nominal binomial posterior;
   - a semiparametric-style transport-orthogonal profile residual.

No acquisition advantage is involved in this comparison.

## Orthogonal profile score

For source candidate \(s\), over the observed measurement history \(B\),

\[
y_B
\approx
h_s(B)+G_s(B)a+\epsilon
\]

where \(a\) is a shared low-dimensional transport perturbation.

Define the candidate residual after profiling the local transport nuisance:

\[
R_s^\perp
=
\min_a
\|y_B-h_s(B)-G_s(B)a\|_2^2.
\]

Equivalently,

\[
R_s^\perp
=
\|
P^\perp_{G_s}
(y_B-h_s(B))
\|_2^2.
\]

Candidates are ranked by smaller \(R_s^\perp\).

This is an observation-conditioned nuisance projection, unlike the V5 acquisition criterion that projected candidate differences before observing data.

## Completed controlled results

Configuration:

- 5 candidate sources;
- every candidate used as truth;
- 50 independent observation seeds per truth source;
- same Native-selected trajectory for both scoring methods;
- two fixed initial exploration measurements + five Native adaptive measurements;
- 30 Bernoulli hit trials per stop.

### Matched wind

| score | mean truth rank | top-1 | top-2 |
|---|---:|---:|---:|
| Native | 1.032 | 0.980 | 0.996 |
| Orthogonal profile | 1.112 | 0.932 | 0.968 |

### Cross-wind +0.18 m/s

| score | mean truth rank | top-1 | top-2 |
|---|---:|---:|---:|
| Native | 1.076 | 0.948 | 0.992 |
| Orthogonal profile | 1.168 | 0.908 | 0.948 |

### Cross-wind -0.18 m/s

| score | mean truth rank | top-1 | top-2 |
|---|---:|---:|---:|
| Native | 1.056 | 0.964 | 0.984 |
| Orthogonal profile | 1.136 | 0.904 | 0.972 |

### Cross-wind +0.25 m/s

| score | mean truth rank | top-1 | top-2 |
|---|---:|---:|---:|
| Native | 1.140 | 0.884 | 0.992 |
| Orthogonal profile | 1.268 | 0.848 | 0.900 |

### Along-wind +0.18 m/s

| score | mean truth rank | top-1 | top-2 |
|---|---:|---:|---:|
| Native | 1.048 | 0.972 | 0.992 |
| Orthogonal profile | 1.108 | 0.936 | 0.968 |

## Additional sign-control result for bounded acquisition

A completed 25-seed-per-source test at reverse cross-wind mismatch

\[
\delta w=(0,-0.18)\ {\rm m/s}
\]

gave:

| method | mean truth rank | top-1 | top-2 |
|---|---:|---:|---:|
| Native | 1.048 | 0.968 | 0.984 |
| BTD-0.05 | 1.088 | 0.936 | 0.984 |
| BTD-0.10 | 1.096 | 0.928 | 0.984 |
| BTD-0.20 | 1.112 | 0.936 | 0.952 |
| BTD-0.30 | 1.136 | 0.936 | 0.944 |
| TO-inf | 1.568 | 0.600 | 0.840 |
| Random | 1.472 | 0.632 | 0.920 |

The bounded positive signal seen for the opposite cross-wind direction is therefore not sign/geometry robust.

## Decision

Do **not** tune:
- ridge penalties;
- nuisance radius;
- finite-difference epsilon;
- history length;
- candidate truncation

against these truth outcomes to rescue the line.

Current classification:

### V4/V5 unbounded transport orthogonalization
**NO-GO as main algorithm.**

### Bounded Transport Deconfounding acquisition
**HOLD, not positive.**  
A small positive signal in one mismatch direction failed the reverse-direction control.

### Orthogonal profile source score
**NO-GO in current form.**

### Overall transport-confounding line
**HOLD as a scientific diagnostic / backup only.**

One repaired-Native House recheck is justified because the real PMFS geometry and mismatch can differ materially from this toy. But no more method complexity should be added before that evidence arrives.

This branch must preserve the negative evidence rather than optimize around it.
