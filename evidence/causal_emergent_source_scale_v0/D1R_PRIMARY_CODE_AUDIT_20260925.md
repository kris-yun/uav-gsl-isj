# CESS D1R Primary-Thread Code and Scientific Audit

Date: 2026-09-25

Status:
**D1R DATA GENERATION AUTHORIZED AFTER THIS AUDIT**

## 1. Governing scientific revision

The current mainline is controlled by:

`01_idea/CESS_POST_PRO_REVIEW_MAINLINE_REVISION_20260925.md`

The older D1/D1A macro-EI PASS/STOP tasks are superseded as scientific
confirmation gates.

Reason:

- a deterministic macrostate has fewer labels and a changed intervention
  distribution;
- a larger macro EI / accuracy by itself does not establish that localization
  on the original microcell state space improved;
- the eventual confirmation endpoint must compare models on the **same
  microcell outcome support and same source prior** using locked fresh targets
  and a proper score.

Therefore D1R is reference construction only.

## 2. D1R frozen data object

D1R generates:

- 168 geometry-selected 0.30 m source cells;
- PMFS rectangle i=1..24, j=12..18;
- House02 / W2;
- 16 independent fresh realizations/source;
- 2688 GADEN realizations total;
- 10 times ×30 pooled probes;
- seed `2026105000 + 16*panel_index + replicate`.

Replicates 1..16 are reference data only.

Replicate 17/18 or any other final-target seed range must NOT be generated in
D1R.

## 3. Input integrity audit

The runner now hard-pins:

- GADEN binary SHA:
  `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`
- occupancy SHA:
  `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`
- W2 iteration1 SHA:
  `54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8`
- extractor SHA:
  `206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91`
- Gate1A source-bank SHA:
  `0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb`
- Gate1A observation-contract SHA:
  `68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334`

A path with 630 rows but a different bank is not accepted.

## 4. Resume-safety audit

A cached source/replicate is reused only when all are valid:

- concentration cube shape = 10×83×119;
- pooled array shape = 10×30;
- finite / nonnegative;
- panel index;
- source id;
- replicate;
- RNG seed;
- House02;
- W2;
- binary SHA;
- occupancy SHA;
- W2 SHA;
- extractor SHA;
- source-bank SHA;
- Gate1A contract SHA.

Any missing/mismatched provenance invalidates the cache and forces regeneration.

This prevents historical GADEN outputs from silently contaminating D1R.

## 5. Allowed D1R analysis

Allowed:

- completeness;
- numerical validity;
- mass / zero-fraction summaries;
- first8 versus last8 encounter-profile cosine / relative error.

Forbidden before the reference package is independently reviewed:

- final partition selection;
- final macro count / radius;
- model-selection threshold;
- fresh confirmation targets;
- mainline PASS/HOLD/STOP;
- PMFS closed loop.

## 6. Review-package audit

The review archive must contain:

- D1R protocol;
- current runner;
- 168-source panel;
- D1R inventory / summary / frozen SHA list;
- consolidated 168×16×10×30 pooled tensor;
- exact Gate1A source bank;
- exact Gate1A observation contract;
- current mainline revision;
- Codex D1R handoff;
- package Git state;
- internal SHA256SUMS.

This is sufficient for the primary thread to recompute D1R independently
without the full 2688 concentration cubes.

## 7. What happens after D1R

After D1R returns:

1. primary thread verifies the archive and recomputes the reference statistics;
2. only the 16 reference realizations may be used to develop/freeze the
   partition/risk objective;
3. reference-only cross-fitting must compare:
   - identity micro model;
   - candidate multiscale model;
   - all-in-one negative control;
   - size-matched random partitions;
   - geometry-only connected partition;
   - ordinary profile clustering;
   - ordinary pooling/shrinkage;
4. partition stability, fidelity loss and micro-support predictive risk are
   frozen;
5. **only then** is D1C target generation authorized.

The D1C primary endpoint must remain on the same 168-cell micro source support
and the same source prior.

D1R is therefore infrastructure/data evidence, not a positive innovation
result.
