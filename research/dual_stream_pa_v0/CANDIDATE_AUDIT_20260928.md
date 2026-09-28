# Dual-Stream Perception–Action GSL candidate audit
Date: 2026-09-28

Status: THEORY/MECHANISM CANDIDATE ONLY — NO NEW SIMULATION, NO VGR, NO TRAINING

## Why this candidate exists

The frozen D0.5 cross-attribution separates two questions that had been
confounded:

1. where to measure;
2. how to decode a source from the measurement.

On the same LF-u selected point, replacing u-B2 by rawu-B2 improves the
environment-mean true-source rank in all three OPEN environments:

- H01: 2.000 -> 1.917
- H02 W0: 1.583 -> 1.458
- H02 W2: 2.417 -> 2.250

By contrast, replacing the LF-u selector by the LF-rawu selector has
environment-dependent effects and does not establish a stable action benefit.

Therefore the current evidence does NOT support "rawu should control both
action and inference." It motivates a different scientific hypothesis:

> a representation useful for online action guidance need not be the same
> representation that is best for source identity readout.

## Mother-theory candidate

The transfer target is the neuroscience distinction between complementary
perception and action pathways ("vision-for-perception" vs
"vision-for-action"), updated by recent work emphasizing specialized but
interacting streams rather than hard isolation.

Foundational theory:
- Goodale & Milner, two visual systems / perception-action division.

Recent anchors:
- Vega-Zuniga et al., Nature Neuroscience (2025),
  "A thalamic hub-and-spoke network enables visual perception during action
  by coordinating visuomotor dynamics."
  https://www.nature.com/articles/s41593-025-01874-w
- Dima, Culham & Mohsenzadeh, Communications Biology (2026),
  "Distinct perceptual and conceptual representations of natural actions
  along the lateral and dorsal visual streams."
  https://www.nature.com/articles/s42003-026-09834-1
- Recent neuroscience also stresses interaction between dorsal and ventral
  pathways during memory-guided action rather than a simplistic total split.

## GSL transfer

Working name: **Dual-Stream PMFS (DS-PMFS)**

Action stream:
- consumes robust spatial/transport information;
- chooses measurement locations and executes navigation;
- is evaluated only by downstream action utility, not by source-readout
  sharpness.

Perception/source-identity stream:
- consumes high-resolution amplitude structure;
- AOD/rawu is the current evidence-backed representation candidate;
- is evaluated by source-identification metrics under fixed measurement
  locations.

The two streams interact only through an explicit interface; one stream is not
assumed to be a drop-in replacement for the other.

## Important negative boundary

Do NOT equate:
- "u = dorsal stream" as a proven biological mapping;
- "rawu = ventral stream" as a proven biological mapping;
- HD-PLF v0 with a validated action stream.

Current data only support task-role dissociation as a candidate mechanism and
support AOD/rawu more strongly on the readout side.

## Prior-art boundary

Dual-stream architectures already exist in robotics, e.g. semantic robotic
grasping inspired by dorsal/ventral vision. Therefore novelty cannot be
"first dual-stream robot."

The paper-level novelty, if later validated, must be narrower:

> role-specialized source-localization representations under turbulent
> transport, where action guidance and source-identity decoding are evaluated
> separately, and a high-resolution amplitude decoder is prevented from
> automatically controlling measurement geometry.

A direct GSL/robotic-olfaction prior-art audit is still required before any
first-use claim.

## Relation to stopped branches

- HD-PLF v0 remains STOP as an action proxy.
- AOD readout evidence remains KEEP.
- This is not the old path-action-source-inference D0, which used a different
  heteroscedastic/path-action scoring construction and froze
  PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE.
- This is not causal invariance and does not require environment-invariant
  source representations.

## What must be true before implementation

Do not write a neural dual-stream architecture yet.

A future D1 is licensed only if a preregistered offline test can show that
role-specialized representations provide incremental downstream value over a
single shared representation without using truth to choose the role assignment.

Until then, this remains a theory candidate, not a mainline method.
