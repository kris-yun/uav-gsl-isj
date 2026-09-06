# Controlled data qualification, 2026-09-07

Status: **CONTROLLED DATA QUALIFICATION PASS; M1/M2 UTILITY NOT EVALUATED**.

- Truth-blind route freeze: `d3fa825a2da06a308af6bb6398d5f5a43e5b701a`.
- Actual extraction source: `7f45cee` (full SHA in EXTRACTION_START.json).
- Corrected H01 live ROS source: `ccdf0558173104681b6620d1cf303937bf1ab94c`.
- VM independent trace / frozen-fold / destructive audit: `a72c784`.
- All mandatory reference/model/environment/provenance/review selftests passed.

## Delivered data

All 12 existing raw realizations were used, not selected by performance:
3 Houses x 2 exact sources x 2 provenance-qualified fast/slow interventions.
Seed 12 only; no new simulator realization, seed or predictive bank was built.
One geometry-only 60 s coverage history per realization produced 3,600 frames
and 180 preregistered causal prefixes. Seven decisions per history each have
three precommitted 4 s routes: 252 cases and 5,040 future frames. Each branch
inherits its exact prefix and complete sensor memory. Independent full-prefix
FOPDT recomputation agrees to <= 4.62e-14 ppm. All 8,640 extracted query frames
agree exactly with the numeric wind file selected by the original gas header.

Each of three LOHO manifests contains 8 training and 4 held-out parents.
Prefix/history/outcome roles cannot cross that parent boundary. Eight destructive
controls reject fake interventions, role overrides, wrong provenance, truth
inputs, forged route locks, missing parents, cross-parent outcomes and adaptive
retrospective routes. Model-input history files contain only time, pose,
measured gas and local wind. Raw gas and future observations are evaluator-only.

Offline route coordinate commands have zero command deviation. GADEN's float32
point conversion adds at most 4.7305e-7 m quantization; this is not a Nav2 tracking
or acceleration qualification. Full free-cell candidate support is unchanged.

## Important wind correction

Before any controlled histories were extracted, the first adapter attempt
failed against H02/H03 ROS frames. The historical raw helper lexically ordered
wind files as 0,1,10,2,...; numeric gas-header indices therefore picked the wrong
wind file. This also invalidates a full-physical-wind interpretation of the old
H01 probe, which had only checked bridge-to-ingress consistency.

The old helper/evidence remain untouched. A separately built numeric-order
helper was checked against independent original wind-file values, and then used
in a targeted real H01 ROS probe. Live wind error <= 1.63e-9 m/s; gas error <=
8.68e-19 ppm. WIND_INDEX_CORRECTION_AUDIT.json is now mandatory in asset manifests.
H02/H03 archived player frames match the corrected helper. Raw provenance,
routes, source positions, release identities and frozen splits did not change.
The rejected attempt is preserved in sibling cstar_controlled_assets_20260907.

## Scientific warning before training

This is a data gate, not a scientific success. Across 84 shared contexts,
69 have different future concentration sequences across routes, but only **5/84**
have different first-hit labels at the frozen 0.1 ppm threshold / 4 s horizon.
Of 252 cases, 173 hit, 79 do not hit, and 168 hit at the first future frame.
A no-route/no-source persistence diagnostic (predict first-frame hit if current
measured gas > 0.1 ppm, otherwise no hit) gets **247/252 = 98.02% exact labels**.
This is post-extraction diagnosis, not a preregistered model-performance gate.

Thus a high first-passage prediction score alone could reflect current sensor
state, not learned route effects. Do not expand seeds or rescue-tune threshold,
routes, split or horizon after seeing this. Next: M1 controlled causal-screen
implementation; for M2, explicitly compare route/source-free persistence and
the required frozen physics/FOPDT controls before interpreting a learned gain.
Changing M2's target requires a separate scientific revision, not silent tuning.

No PICR/CPO training, production cstar_v1 run, or 12-run campaign was executed.
Raw realizations have historical exposure: LOHO here is development evaluation,
not virgin confirmation. Equal release mechanism is not equal stochastic draws.

## Portable verification

From the extracted bundle root (Python with NumPy; no ROS or VM needed):

```text
python -B tools/cstar_reverify_controlled_bundle.py
```

It checks package hashes, recomputes sensor/branch alignment, verifies all frozen
fold manifests and destructive controls without changing archived files. It does
not regenerate the gas field or reread the external ~1 GB original wind inputs.
