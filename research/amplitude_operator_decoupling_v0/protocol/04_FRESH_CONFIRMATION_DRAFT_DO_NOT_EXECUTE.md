# Draft fresh confirmation — DO NOT EXECUTE YET

Only after the implementation-only task reproduces the OPEN four-arm results
should the main thread freeze a fresh experiment.

Provisional design:

## Environment
- House03 only.
- one wind family selected from metadata before gas results are generated/read.

## Sources
- 12 true sources = 6 geometry-selected 0.30 m neighboring pairs.
- source pairs selected without using gas/plume outcomes.
- include off-PMFS-grid-center or nontrivial probe geometry where possible, so
  the result cannot be explained only by current grid alignment.

## Fresh plumes
- 8 independent realizations/source = 96 fresh GADEN realizations.
- This is a budget proposal; perform an OPEN variance/power audit before
  signing the final number.

## Observation protocol
- two fixed feasible 10-step single-UAV-like paths.
- one spatial sample/time.
- paths fixed before fresh plumes are read.
- same target observations used by every method.

## Primary causal comparison

Keep the score EXACTLY the same (B2).

Compare only the observation operator:

C0: `u` (native extra-blurred amplitude template)
C1: `rawu` projected by the frozen sampling operator

Thus a fresh difference is attributable to amplitude observation-operator
decoupling, not to a new score.

## Required secondary baselines
- native binary hit B0;
- ICRA-2026 ranking baseline;
- ordinary calibrated/value comparator if legally available under the same
  observation contract.

## Primary endpoint
For true source s and predeclared paired neighbor k, lower SSE is better.
Define candidate margin:

`M_arm = SSE_arm(k) - SSE_arm(s)`.

Define improvement:

`Delta = M_rawu - M_u`.

Aggregate first over the two paths / realizations within source, then over the
6 source pairs. Source pair is the main spatial generalization unit.

The final numeric PASS gate must be signed BEFORE generating/reading fresh
targets. Do not copy an effect threshold from the current OPEN improvement.

## Robustness requirement
Because blur was originally used for robustness, fresh confirmation must also
include ONE predeclared transport-model-mismatch condition (not a parameter
sweep). The mismatch must be chosen from deployment-plausible wind/model error
before plume outcomes are read.

If rawu wins only under matched/GT conditions but becomes worse under the
predeclared mismatch, the scientific conclusion is a resolution-robustness
trade-off, not a universal replacement of blur.
