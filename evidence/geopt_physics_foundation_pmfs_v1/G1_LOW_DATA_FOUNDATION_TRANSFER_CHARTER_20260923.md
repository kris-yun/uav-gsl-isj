> **CRITICAL INTERFACE CORRECTION (2026-09-23):** GeoPT uses separate `pos3` plus `fx11`; the pretrained `preprocess` layer therefore receives 14 dimensions. See `CRITICAL_INTERFACE_CORRECTION_POS3_PLUS_FX11_20260923.md`. Any wording below that calls 11 dimensions the *total* input is superseded. The correct gas mapping preserves `space_dim=3`, `fun_dim=11` exactly.\n\n# M6 G1 Charter — Low-Data Foundation Transfer and Source-Rank Falsification

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## 0. Purpose

G1 must answer one question:

> Does the pretrained GeoPT geometry–dynamics representation provide **source-identification value** under scarce high-fidelity gas data, beyond the same architecture trained from scratch?

Do not optimize full closed-loop navigation yet.

## 1. Required model family

### A — Native PMFS
Recovered Native PMFS forward baseline.

### B — Scratch Transolver
Exact same 8-layer Transolver geometry as M6, initialized randomly.

Input:
- 11-D geometry+wind features.

Source:
- same source-injection adapter used by M6.

### C — GeoPT Foundation Transfer
Official `GeoPT_8layers.pt`.

Freeze or minimally fine-tune according to the predeclared sub-stage.

Use the same source-injection adapter and output head as B.

### Optional D — tiny non-foundation residual/surrogate
Only if cheap. Used to show that gains are not merely architecture scale.

## 2. Source Injection Adapter v1

Do not change the raw 11-D GeoPT input.

For candidate source (s) and query point (x), define a physically localized injection feature:

[
Q_s(x)
=
exp
left(
-rac{|x-s|^2}{2sigma_s^2}
ight)
]

with (sigma_s) fixed from grid/source-cell scale, not truth tuned.

Build:

[
r_s(x)
=
[
Q_s(x),
Q_s(x)(x-s)_x,
Q_s(x)(x-s)_y,
Q_s(x)(x-s)_z
].
]

Encode:

[
a_s(x)
=
A_phi(r_s(x))inmathbb R^{256}.
]

After GeoPT's pretrained input projection:

[
h_0(x)
=
h_{m env}(x)+a_s(x).
]

Then pass through the pretrained Transolver blocks.

Why this form:
- source effect is spatially localized;
- relative direction is available near the injection region;
- pretrained raw input projection is untouched;
- adapter is tiny relative to the backbone.

## 3. Target field

First G1 target should remain PMFS-compatible.

Preferred target:

[
H_s^{m GADEN}(x)
=
P(
C(x,t)>	au
mid s,W,O
)
]

estimated as time-averaged hit frequency over a predeclared recording window and multiple plume seeds.

This maps directly onto PMFS candidate hit maps.

Do not start with full transient concentration forecasting.

## 4. Pilot data generation

Use **one House first**.

Preferred House:
- House02, because it is hit-bearing / informative in existing evidence.

Hold fixed:
- geometry;
- one ground-truth wind configuration;
- source release settings;
- sensor height;
- gas threshold;
- time window.

Generate a source-blind space-filling set of source positions.

Suggested pilot:
- 12 source positions;
- 2 independent plume seeds each.

Split fixed before field generation:
- 8 train source positions;
- 2 validation source positions;
- 2 completely unseen test source positions.

Do not move positions after looking at model/source-rank results.

## 5. Low-data scaling curve

Using the fixed 8 training sources, create nested source subsets:

- 2 sources;
- 4 sources;
- 8 sources.

For each subset train B and C with:
- same data;
- same adapter;
- same output head;
- same optimizer budget;
- same early-stopping criterion.

Primary transfer question:

> Does C reach better held-out source prediction / source rank than B at 2–4 training sources?

If benefit exists only with full data, the foundation-data-efficiency narrative is weak.

## 6. Training stages

### G1a — frozen backbone
C:
- freeze GeoPT backbone;
- train only source adapter + output head.

B:
- use a randomly initialized frozen backbone with trainable adapter/head only.

This is a strict representation probe.

### G1b — parameter-efficient adaptation
Only if G1a shows signal.

Allow:
- LayerNorm;
- small LoRA/adapters;
- final 1–2 blocks.

Keep most foundation parameters frozen.

### G1c — full fine-tune
Only if needed and justified.

If full fine-tuning is required from the start, the foundation-transfer claim is weaker.

## 7. Field metrics — secondary gate

On held-out source positions:
- hit-map BCE / cross-entropy;
- Brier score;
- spatial correlation;
- calibration;
- obstacle-region error;
- downwind/upwind error.

These are diagnostics only.

## 8. HARD source-rank replay

After all models and thresholds freeze:

For each held-out truth source:

1. take the same sparse observation set from an independent GADEN plume realization;
2. query every PMFS source candidate using each forward arm;
3. compute source evidence using one fixed source-update rule;
4. rank all candidates.

Primary metric:

[
oxed{
	ext{truth-containing source-candidate rank}
}
]

Compare:
- Native PMFS;
- Scratch Transolver;
- GeoPT transfer;
- optional tiny surrogate.

No endpoint-only rescue.

## 9. Candidate-set fairness

Use exactly the same:
- candidate source geometry;
- observation locations;
- measurement budget;
- gas threshold;
- source update rule

for all forward models.

The only changed object is the candidate forward map.

## 10. Destructive controls

### N1 — random pretrained backbone
Same architecture, no GeoPT weights.

Already provided by B.

### N2 — wind shuffle
Pair geometry/source with the wrong wind field.

Foundation-transfer advantage should drop if dynamics prompt matters.

### N3 — source injection shuffle
Shuffle candidate source adapter labels.

Source-rank advantage must collapse.

### N4 — geometry destruction
Permute wall/SDF directions while preserving marginal distributions.

Cross-source field quality should deteriorate.

## 11. G1 advance criteria

Advance M6 only if all hold:

1. actual official checkpoint loads at high internal-block coverage;
2. GeoPT transfer beats scratch in the scarce-data regime;
3. benefit appears on unseen source positions;
4. truth-source candidate rank improves on independent plume realizations;
5. wind/source destructive controls remove the gain;
6. no truth-dependent hyperparameter selection.

## 12. Kill conditions

M6 is NO-GO as main if:

- checkpoint cannot transfer without rebuilding major internal layers;
- frozen/pretrained features provide no advantage over scratch;
- field error improves but truth-source rank does not;
- only full fine-tuning with large GADEN data works;
- gain survives wind/source shuffles;
- benefit only occurs on source positions seen during training;
- the IROS 2026 gas-PINO turns out to contain an equivalent pretrained/foundation transfer mechanism.

## 13. Compute discipline

Do not generate a large dataset before:
- checkpoint load verification;
- one-source GADEN generation cost benchmark;
- one frozen-backbone train/inference smoke test.

Every stage commits immediately.

Status:

`G1 READY AFTER G0.5 CHECKPOINT LOAD COMPLETES`.
