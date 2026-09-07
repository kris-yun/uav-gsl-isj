# Physical-prior asset diagnostic — 2026-09-07

This is a truth-conditioned forward-adequacy diagnostic, deliberately not a
formal M2 gate. It uses the evaluator-only source coordinate to ask whether the
declared finite-volume/FOPDT prior can assign useful likelihood to an archived
future route trace. Runtime source truth is never passed to the online bridge,
no predictive bank is queried, and no controller is run.

The corrected House-aware three-House sample (`diagnostic_houseaware_max3.json`)
contains three routes per House. H01 retains source-conditioned NLLs `22.4455`,
`19.7305`, and `19.1259`; H02 is `33.6013`, `19.8999`, and `22.0088`; H03 is
`20.8382`, `20.8382`, and `20.8382` (rounded). Context-minus-source increments
are effectively zero throughout. This means the current nominal physical prior
does not yet carry useful source-conditioned evidence, so it is not a reason to
launch a closed loop. The source-rate ensemble was fixed at `[0.5, 1.0, 2.0]`;
it was not tuned on these outcomes.

The earlier H02/H03 map/route errors came from the same complete-manifest
filtering bug as the trajectory audit. The corrected diagnostic filters each
case by its authoritative `house`; all nine sampled cases now bind to the
corresponding map. The larger pre-fix exploratory files remain preserved as
negative evidence and are not used to authorize anything.

An opt-in prefix-only amplitude experiment is recorded in
`diagnostic_assimilated_h01_max3.json` plus one first case for H02/H03. It
reduces H03's context-minus-source NLL gap by about `0.893` in that first case,
while H01/H02 remain effectively null. This confirms that causal
source-strength assimilation is wired, but it is not broad enough for a
predictive M2 gate or a closed-loop run.

Code identities at capture:

- `physical_prior.py` SHA-256:
  `82827d6d0cace774a5373df8203eb7bea8d4683258c82ff4ac33d983ee421d7b`
- diagnostic script SHA-256:
  `20be8931456fa451f917898167c432fe75cd30cc5dc7d5676a39f8ee59e4397c`
