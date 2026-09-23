# C0-PRE — Existing 2×2 intervention pre-screen

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## Decision

`C0-PRE = NEGATIVE FOR SIMPLE COMPOSITIONALITY`

M4 is **demoted from first-priority main thesis** pending stronger evidence.

This result does not prove that all nonlinear causal world models must fail. It does show that the existing source×wind interventions do not exhibit a simple reusable additive mechanism in the observed concentration histories.

## 1. Existing 2×2 data are valid interventions

Historical data:
- H01/H02/H03;
- source SA/SB;
- transport fast/slow;
- 1200 matched measurements per condition;
- identical route/timing within each House.

For every House:

### Within fast
SA and SB have exactly identical:
- pose sequence;
- timestamps;
- wind_uv;
- wind_w.

### Within slow
SA and SB likewise have exactly identical:
- pose sequence;
- timestamps;
- wind_uv;
- wind_w.

### Fast vs slow is genuinely different

Wind-trace RMS differences:

- H01: 0.11335 m/s;
- H02: 0.07836 m/s;
- H03: 0.24636 m/s.

Largest component differences:

- H01: 0.47124 m/s;
- H02: 0.69076 m/s;
- H03: 0.88237 m/s.

Therefore source and transport are independently varied in this mechanism dataset.

## 2. Zero-training compositional pretest

For each House, use three corners to predict the fourth.

In a source-blind log-compressed concentration coordinate, test:

[
z(S_2,W_2)
approx
z(S_2,W_1)
+
z(S_1,W_2)
-
z(S_1,W_1).
]

The transform scale is computed only from the three training corners for each held-out fold.

Compare this compositional prediction against:

- same-source / other-wind field;
- same-wind / other-source field;
- diagonal/base corner.

## 3. Representative results

### H02 — held out SB_slow

- compositional RMSE: 4.7395;
- same-source SB_fast RMSE: 2.9970;
- same-wind SA_slow RMSE: 8.8845.

Correlation:
- compositional: 0.8232;
- same-source: 0.9351.

### H03 — held out SB_slow

- compositional RMSE: 0.6514;
- same-source SB_fast RMSE: 0.3770.

Correlation:
- compositional: 0.7133;
- same-source: 0.8832.

Across the tested folds, the simple three-corner compositional predictor generally fails to outperform the same-source other-wind baseline.

## 4. Interpretation

The source×wind interaction is not well described by a simple additive/factorized effect in the observed concentration coordinate.

This matters because M4's strongest paper-level claim was:

> source and environmental mechanisms can be learned separately and recombined in unseen combinations.

The existing data do not provide a cheap positive signal for that claim.

## 5. What this does NOT prove

It does not prove:
- causal modularity is impossible;
- a nonlinear shared transport decoder cannot generalize;
- a richer intervention model cannot work.

But a large causal architecture would now require substantial modeling effort merely to overcome a negative zero-training compositionality screen.

Under the project’s kill-fast policy, that is not sufficient to keep M4 as the first-priority main innovation.

## 6. Revised status

M4:

`DEMOTED — KEEP AS BACKUP / POSSIBLE AUXILIARY STRUCTURE`

Do not start full WM3C-style implementation now.

Priority should shift to candidates with stronger direct interface/data signals, currently M6 GeoPT physics-foundation transfer.

## 7. If revisited later

Only revisit M4 if:

- M6 or another forward-world-model line succeeds;
- intervention data are already available;
- a nonlinear mechanism factorization can be tested cheaply on top of the successful representation.

Do not generate new data solely to rescue M4 at this stage.
