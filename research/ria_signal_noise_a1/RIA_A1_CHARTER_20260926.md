# RIA-A1 — Signal-Separation vs Within-Source Variability Decomposition

Date: 2026-09-26

Status: **ZERO-PLUME / EXACT DECOMPOSITION AUDIT — NOT A NEW METHOD TEST**

Frozen upstream facts:
- JTD STOP remains final.
- NPG STOP remains final.
- RPO-G0 STOP remains final.
- RIA-A0 = `RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED` remains valid.

## 1. Purpose

RIA-A0 established a model-independent-ish observation-level identifiability target.

RIA-A1 asks what part of that target changes when the probe protocol changes:

1. source-separation signal increases/decreases;
2. within-source stochastic variability increases/decreases;
3. both.

This decomposition is required before assigning a new biological/physics mother theory.

## 2. Data scope

Use only the frozen House02 `3,5-1_slow` CENTRAL 84 source pairs and the two SPX/RIA probe protocols.

Use the exact same four 12-reference folds from RIA-A0.

Use RIA-A0 heldout Delta_A and Delta_B only as bounded operational validation.

0 new plume.
No H01 DEV.
No House03.
No H02 W2.

## 3. Exact CNR decomposition

For every pair i, protocol P, fold f:

`S_iPf = ||mu_a - mu_b||_2^2`

`W_iPf = 0.5 * [mean ||x_a-mu_a||^2 + mean ||x_b-mu_b||^2]`

`D_CNR_iPf = S_iPf / (W_iPf + eps)`

using the exact frozen RIA formulas and eps.

For each pair/fold define probe-switch components:

`signal_i,f = log(S_E2 + epsS) - log(S_G1A + epsS)`

`noise_i,f = -[log(W_E2 + epsW) - log(W_G1A + epsW)]`

`total_i,f = signal_i,f + noise_i,f`.

Choose epsS/epsW exactly as the RIA numerical convention:
`1e-12 * max(1, corresponding scale)`.

Verify numerically that:
`total_i,f = log(D_CNR_E2) - log(D_CNR_G1A)`
to <= 1e-10 absolute wherever both D values are positive.

Pair-level `signal`, `noise`, `total` are arithmetic means over four folds.

## 4. Energy-distance decomposition

For every pair/protocol/fold compute separately:
- mean between-source Euclidean distance `B`;
- within-source distance contribution `W_E` exactly as RIA;
- raw energy-distance numerator `ED = 2B - W_a - W_b`;
- normalized `D_ED = ED/(W_E+eps)`.

Probe-switch changes:
- `Delta_Between = B_E2-B_G1A`;
- `Delta_WithinED = W_E_E2-W_E_G1A`;
- `Delta_EDnum = ED_E2-ED_G1A`;
- `Delta_D_ED` frozen RIA target.

This is confirmatory because D_ED may be negative and has no exact log-additive decomposition.

## 5. Frozen diagnostics

### A1-Q1 — Which CNR component carries the RIA signal?

Across 84 pairs compute Spearman correlations of pair-level `signal` and `noise` with:
- frozen Delta_A;
- frozen Delta_B;
- frozen Delta_D_CNR;
- frozen Delta_D_ED.

Use 10,000 pair bootstrap for 95% intervals.

### A1-Q2 — Relative contribution magnitude

For every pair:
`share_signal = |signal| / (|signal| + |noise| + 1e-12)`.

Report median, q25, q75 and fraction with share_signal > 0.5.

### A1-Q3 — Directional agreement

Report sign agreement of:
- signal vs total;
- noise vs total;
- signal vs Delta_A;
- signal vs Delta_B;
- noise vs Delta_A;
- noise vs Delta_B.

Exact ties <1e-10 are excluded only from sign counts.

### A1-Q4 — Energy-distance consistency

Report Spearman of Delta_Between and -Delta_WithinED with Delta_D_ED, Delta_A and Delta_B.

## 6. Frozen diagnostic labels

Return exactly one:

`RIA_A1_SIGNAL_SEPARATION_DOMINANT`
if ALL are true:
- signal Spearman with Delta_A and Delta_B > 0 with bootstrap 95% lower bound >0;
- noise Spearman with Delta_A and Delta_B has bootstrap interval including 0 OR absolute point estimate <0.15;
- median share_signal >=0.65;
- fraction share_signal>0.5 >=0.70;
- Delta_Between association with Delta_D_ED has the same positive direction.

`RIA_A1_WITHIN_VARIABILITY_DOMINANT`
if the symmetric conditions hold with noise replacing signal and `-Delta_WithinED` supporting Delta_D_ED.

`RIA_A1_MIXED_SIGNAL_AND_VARIABILITY`
for all other cases.

These are mechanism diagnostics, not method GO/HOLD/STOP.

## 7. Consequence

If `SIGNAL_SEPARATION_DOMINANT`:
- do NOT elevate RIA into a temporal/noise-coding main innovation;
- treat the result primarily as observation-layout-induced source-signature separation;
- prior active-observability/sensor-layout literature becomes the primary novelty collision;
- any new mainline must demonstrate something beyond ordinary observation geometry.

If `WITHIN_VARIABILITY_DOMINANT`:
- a sensory noise-correlation / robust-coding mother theory may be worth a new independent candidate audit.

If `MIXED`:
- do not choose a single mother theory yet.

RIA-A1 never restores JTD, NPG or RPO.