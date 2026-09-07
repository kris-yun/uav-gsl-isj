# Physical-prior asset diagnostic — 2026-09-07

This is a truth-conditioned forward-adequacy diagnostic, deliberately not a
formal M2 gate. It uses the evaluator-only source coordinate to ask whether the
declared finite-volume/FOPDT prior can assign useful likelihood to an archived
future route trace. Runtime source truth is never passed to the online bridge,
no predictive bank is queried, and no controller is run.

The H01 three-route sample (`H01_3.json`) shows source-conditioned NLLs
`22.4455`, `19.7305`, and `19.1259`, with context-minus-source increments
`0.00029`, `0.00021`, and `0.0`. This is effectively no source evidence under
the current nominal physical prior, so it is not a reason to launch a closed
loop. The source-rate ensemble was fixed at `[0.5, 1.0, 2.0]`; it was not
tuned on these outcomes.

The same diagnostic exposed two map/route binding failures before prediction:

- H02: `CSTAR_M2_PRIOR_POINT_IN_SOLID` (`H02_one.json`);
- H03: `CSTAR_M2_PRIOR_POINT_OUTSIDE_GRID` (`H03_one.json`).

The larger exploratory files are retained as negative evidence; they are not
used to authorize anything. These failures must be resolved as environment
identity/alignment issues before a House-level physical gate.

Code identities at capture:

- `physical_prior.py` SHA-256:
  `eca38b755c247372a0bd7b5df40faa4eb3bc534b55a872831f15c2b30f7fa663`
- diagnostic script SHA-256:
  `4d662a3c01ab302f85b727c06241a87d9a27dec6e19099c7cf848fbc811ae21d`
