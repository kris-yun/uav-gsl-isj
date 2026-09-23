# G1 Hard Gate — Low-Data Physics-Foundation Transfer

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Purpose

G1 decides whether M6 is genuinely a **physics foundation-model transfer** rather than simply another gas surrogate based on Transolver.

The key causal variable is:

[
	ext{pretrained cross-physics representation}
]

not architecture class.

## 1. Required comparison arms

All arms must use exactly the same plume training/evaluation split.

### A — Native PMFS
No learned correction.

### B — gas model from scratch
Same GeoPT/Transolver downstream architecture but **randomly initialized**.

This is the most important control.

### C — pretrained GeoPT
Load `GeoPT_8layers.pt`; replace only the task/output head and add the predeclared source adapter.

### D — small gas-specific baseline
A deliberately small task-specific model trained from scratch.

Examples:
- shallow MLP/operator;
- small CNN/UNet where appropriate.

Purpose:
- ensure any gain is not merely because Transolver is overpowered.

### Optional E — PHOENIX-style gas baseline
Only on the PHOENIX public sandbox where its data representation is available.

Do not force PHOENIX architecture onto PMFS House data if input contracts differ materially.

## 2. Fixed source adapter

Do not tune source-conditioning architecture separately per data fraction.

Initial adapter:

[
r_s(x)
=
[
x-s,|x-s|,Q_s(x)
].
]

Map 5 source-relative scalars to hidden dimension 256 through a tiny two-layer MLP.

Inject after GeoPT input embedding by addition or one fixed FiLM rule.

Select one rule **before** truth-source evaluation.

The adapter must remain <1% of backbone parameters.

## 3. Data fractions

Freeze one pilot multi-source GADEN dataset.

Train with source-blind nested subsets:

- 2.5%;
- 5%;
- 10%;
- 25%;
- 50%;
- 100%.

Use a deterministic sampling seed fixed before model evaluation.

The held-out source/wind/seed evaluation set is never changed across fractions.

## 4. What counts as foundation-transfer signal

### G1-A — optimization/data-efficiency signal

Pretrained GeoPT should achieve the same held-out field error as random-init using materially less plume data.

Report a data-efficiency ratio:

[
R_{m data}
=
rac{
N_{m scratch}(epsilon)
}{
N_{m pretrained}(epsilon)
}.
]

Do not cherry-pick (epsilon).

Use predeclared validation-error targets or compare full scaling curves.

### G1-B — source-generalization signal

On an unseen source position:

pretrained GeoPT must outperform random-init at matched data fraction.

### G1-C — wind/generalization signal

On unseen wind condition / plume realization:

pretrained must retain an advantage.

### G1-D — source-identity signal — HARD GATE

Freeze the learned forward models.

For each held-out source-localization replay:

1. use exactly the same PMFS source candidates;
2. generate each candidate forward field with each arm;
3. apply one frozen inference/update contract;
4. evaluate truth-containing source-candidate rank.

The main innovation is not advanced unless C beats B in truth-source rank on independent realizations.

## 5. Primary statistical object

For each case compute paired rank change:

[
Delta r
=
r_{m scratch}
-
r_{m pretrained}.
]

Positive means pretraining improves the truth-source rank.

Report:
- every case;
- median/mean only as secondary summaries;
- number of improved/tied/worsened cases.

No averaging can hide a catastrophic House failure.

## 6. External PHOENIX sandbox

The public PHOENIX dataset is approximately 14.7 GB and contains ~4000 steady-state gas-dispersion cases.

It can provide a preliminary transfer test before a larger GADEN pilot.

### Important limitation

The public representation contains:
- concentration fields;
- meteorological vectors;
- source conditions;
- building geometry / Gaussian plume prior.

Current public documentation does not establish availability of the full obstacle-resolved local wind vector field.

Therefore the external test is:

`P-S0 = GLOBAL-WIND-PROMPT TRANSFER SANDBOX`

not a local-wind physics validation.

Use:

[
v(x)
=
[
cos	heta,
sin	heta,
0,
U
]
]

repeated across free-space points.

The purpose is only:

> does GeoPT cross-physics pretraining help gas-field learning under scarce data?

## 7. PHOENIX novelty boundary

PHOENIX-UNet already demonstrates:
- obstacle-aware learned gas dispersion;
- physics prior + source + meteorology conditioning;
- unseen source/wind generalization;
- seconds-level surrogate prediction.

Therefore M6 cannot claim any of those broadly.

M6 survives only if **cross-physics pretraining** provides a meaningful low-data / source-localization advantage.

## 8. Pretraining-null controls

### N1 — random init
Mandatory.

### N2 — shuffled checkpoint
If useful, independently permute or randomize pretrained weights while preserving tensor scales.

### N3 — frozen random features
Compare against frozen random backbone + trainable head.

### N4 — wind prompt shuffle
Shuffle wind conditions across cases.

A physically meaningful pretrained advantage should drop.

### N5 — geometry corruption
Permute SDF/boundary-direction fields while preserving marginal distributions.

Cross-geometry advantage should drop.

## 9. Fine-tuning ladder

To identify where useful transferred information lives, use a fixed ladder:

1. frozen backbone + output/source head only;
2. unfreeze last 2 blocks;
3. full fine-tune.

Run the same ladder for random-init controls where meaningful.

Interpretation:

- frozen positive signal = very strong foundation representation evidence;
- only full fine-tuning positive = weaker transfer evidence;
- no advantage over random init = M6 NO-GO.

## 10. Hard M6 decision rule

### ADVANCE
Only if:

1. actual official checkpoint loads at high internal-layer coverage;
2. pretrained model beats same architecture from scratch in low-data regime;
3. advantage persists on unseen source/wind/realization;
4. it improves truth-source candidate rank on multiple independent GADEN cases;
5. wind/geometry destructive nulls reduce the gain.

### HOLD
If field/data-efficiency improves but source rank is still untested.

### NO-GO
If:
- pretrained ~= random-init;
- advantage disappears at first held-out source;
- only field MSE improves, not source identity;
- input/backbone must be heavily rebuilt;
- direct prior art is found.

## 11. No rescue by architecture inflation

If M6 fails, do not:
- increase model size repeatedly;
- add OFM/stochastic generation;
- add M4 causal modules;
- add planner changes

to rescue the same experiment.

Record NO-GO and return to main-innovation search.

## 12. Current status

`READY FOR G0.5-B ACTUAL CHECKPOINT LOAD + G1 PILOT`.
