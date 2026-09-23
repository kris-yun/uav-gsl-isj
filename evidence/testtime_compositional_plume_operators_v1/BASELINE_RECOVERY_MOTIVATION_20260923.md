# Baseline-Recovery Motivation for M7 Mechanism Composition

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## 1. Relevant corrected R1 result

Recovered baseline R1 uses:
- the same 20 observations;
- the same 87 candidate-source regions.

Corrected truth-source ranks:

- A: frozen R2 source + GMRF wind + R2 parameters -> **48/87**
- B: frozen R2 source + GADEN ground-truth wind + R2 parameters -> **18/87**
- C: official PMFS source + GADEN ground-truth wind + official parameters -> **47/87**

This is one frozen House01 snapshot only.

It is not a 300-s performance conclusion.

## 2. Mechanism-level reading

### A -> B: wind/advection intervention

A and B keep:
- R2 source implementation;
- R2 PMFS forward/hit-map parameters;
- observations;
- candidate set.

The declared forward change is the wind path.

Truth-source rank changes:

\[
48 \rightarrow 18.
\]

This shows that the **advection/wind mechanism alone can strongly alter source identity**.

### B -> C: non-wind forward-contract intervention

B and C both use ground-truth wind.

C additionally changes the PMFS source/forward/hit-map contract back toward official settings.

Truth-source rank changes:

\[
18 \rightarrow 47.
\]

Therefore a good wind mechanism alone does not determine the final source evidence.

Other mechanisms/settings can erase or reorganize that gain.

## 3. Why this motivates modular forward modeling

The R1 pattern is compatible with:

> the source-localization forward model is a coupled composition of mechanisms whose errors can compensate, amplify, or cancel each other.

A monolithic surrogate can reproduce this entanglement without explaining it.

M7 instead asks whether the forward model should be represented as reusable mechanisms:

\[
\mathcal J_S,\quad
\mathcal A_W,\quad
\mathcal D,\quad
\mathcal B_O
\]

so that each mechanism can be:
- validated separately;
- reused across candidates/environments;
- replaced or adapted without relearning the entire forward law.

## 4. Important limitation

R1 does **not** prove M7.

It does not show:
- that a neural operator library is needed;
- that operator splitting improves candidate rank;
- that test-time composition works;
- that the true mechanism decomposition is exactly J/A/D/B.

It only supplies a concrete motivation for avoiding an opaque monolithic forward correction.

## 5. Hard interpretation rule

M7 only becomes scientifically stronger than native PMFS if:

1. a learned/reusable mechanism block improves held-out dynamics;
2. the same block transfers across source/wind/realization without retraining;
3. test-time composition beats an equal-capacity monolithic learned forward model;
4. truth-source rank improves on independent realizations.

If only the analytical PMFS/GADEN decomposition helps, that is a baseline/physics result, not the paper-level novelty.

Status:

\`MOTIVATION POSITIVE — METHOD UNVALIDATED\`.
