# AOD House03 F1 — FINAL FULL-SUPPORT SIGNOFF

Date: 2026-09-27

This package supersedes the earlier unsigned/partial-support F1 draft.

## Main-thread scientific decision

**Use the complete House03 legal PMFS candidate support: 624 candidates.**

The 12 frozen sources remain the fresh truth panel only.

Therefore F1 answers:

> across the complete legal House03 source map, does keeping the amplitude
> channel unblurred (`rawu`) improve unique source identification relative to
> reusing the native hit-map blur (`u`) under the same B2 score?

It is NOT a 12-way classification experiment.

## Approved budgets

Fresh GADEN:
- 12 true sources x 8 independent realizations = **96**.

PMFS candidate templates:
- 624 candidates x 11 wind states x 8 transport replicas =
  **54,912 forward realizations**.

Both u and rawu MUST be exported from the same realization.

The full-support PMFS seed manifest is frozen in this package.

SHA256:
`00bf64ab0d1ce55fda58303b11208019473313b97c4de11f7a2305d16143327d`

Original 1,056 rows belonging to the 12 F0 truth sources retain their original
seed keys and values exactly.

Full-support seed audit:
- 54,912/54,912 PMFS seeds unique;
- no overlap with the 96 frozen GADEN seeds;
- one newly-added PMFS key required deterministic `nonce=1` collision
  resolution; no frozen F0 seed was changed.

No fresh target may be generated/read until the full 624-candidate template
bank has been generated, audited and frozen.
