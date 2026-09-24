# CESS D1R Reference-Bank Freeze — 2026-09-25

Status: **REFERENCE CONSTRUCTION ONLY — NO MAINLINE PASS/STOP**

This protocol supersedes the previously written D1A decision gate before any
D1A scientific execution.

## 1. Purpose

Construct a fair, homogeneous, fresh reference bank for dense-source
multiscale-identifiability development.

This stage does NOT:
- choose the final source partition;
- select a final macro scale;
- evaluate fresh target performance;
- claim causal emergence;
- authorize closed loop.

## 2. Frozen source panel

Use the exact same geometry-only dense-panel rule already defined for CESS D1A:

- start from the frozen 630-source Gate1A House02 bank;
- select the largest complete axis-aligned rectangle of free PMFS cells;
- expected result: PMFS i=1..24, j=12..18;
- 24 x 7 = **168 equal-area source microcells**;
- 0.30 m spacing.

Panel construction must be reproduced by:
`research/causal_emergent_source_scale_v0/build_cess_d1a_panel.py`.

No plume statistic enters source selection.

## 3. Frozen environment

- House02
- W2 = `3,5-1_slow`
- same frozen GADEN binary / occupancy / extractor contract used in R0
- same 10 frozen extraction times
- same 30 pooled probes
- preserve both:
  - raw nonnegative pooled concentration `pooled.npy`;
  - binary support derived later as `pooled > 0`.

Do not discard raw concentration, because Pro red-team correctly noted that
stable amplitude information must not be silently removed.

## 4. Fresh reference realizations

Generate exactly:

[
168	imes16=2688
]

independent reference realizations.

For panel row `i=0..167`, replicate `r=1..16`:

[
seed(i,r)=2026105000+16i+r.
]

These 16 realizations are **reference data**.

They may later be cross-fitted internally for:
- profile stability;
- partition discovery;
- model selection;
- calibration design.

They may NOT later be relabeled as untouched final confirmation targets.

## 5. No final target generation

Do not generate replicate 17 or 18.

Do not create any new target seed range.

The final confirmation target seeds will be assigned only after the primary
thread freezes:

- partition search family;
- scale-selection objective;
- microcell posterior lifting;
- baseline set;
- calibration method;
- minimum effect threshold;
- partition-stability threshold;
- fidelity-loss tolerance;
- final PASS/STOP rule.

## 6. Required stored artifacts

For every source/replicate preserve:

1. 10x83x119 extracted concentration cube;
2. 10x30 pooled concentration array;
3. run manifest with source, seed and frozen contract hashes.

The heavy raw GADEN realization directory may be removed after successful
extraction, as in R0.

## 7. Reference-bank integrity outputs

Produce:

- `CESS_D1R_PANEL_168.tsv`
- `CESS_D1R_ARTIFACT_SHA256.tsv`
- `CESS_D1R_REFERENCE_SUMMARY.json`
- `CESS_D1R_GIT_STATE.txt`
- `CESS_D1R_FROZEN_SHA256.txt`

The summary is infrastructure/statistical description only.

It may report:
- number of sources;
- realizations/source;
- total realizations;
- pooled-array shapes;
- total mass / zero-fraction descriptive ranges;
- split profile reproducibility diagnostics.

It must NOT report:
- a selected partition;
- a selected M;
- macro-vs-micro winner;
- a mainline PASS/STOP.

## 8. Optional reference-only diagnostics

Allowed:
- first8 vs last8 encounter-profile cosine per source;
- first8 vs last8 raw mean-profile relative discrepancy;
- legacy local-neighbor vs distant-source similarity descriptions.

These are bank-quality diagnostics only.

Not allowed:
- target-like ranking against held-out reps followed by model selection;
- choosing the final partition from a diagnostic and then treating the same
  held-out references as confirmation.

## 9. Exit states

Only infrastructure states:

`CESS_D1R_REFERENCE_BANK_READY`

or

`CESS_D1R_INFRA_STOP`.

There is no scientific PASS/FAIL at D1R.

## 10. After D1R

Stop.

Primary thread will independently audit the bank and, with the auxiliary Pro,
freeze the final same-prior microcell proper-score confirmation protocol before
any additional simulations are authorized.
