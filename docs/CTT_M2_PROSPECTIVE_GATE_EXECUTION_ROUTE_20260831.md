# CTT M2 prospective fixed-U transport Gate execution route

Date: 2026-08-31
Status: frozen before physical materialization or outcome read

## Scientific purpose

This Gate asks one narrow question before any runtime or closed-loop work:

> With legal placement fixed exactly at `U0`, does retaining one native
> stochastic forward realization across completed stops improve true-source
> ordering relative to independently redrawing that realization at each stop?

It does not test PMFS improvement, a calibrated M3 likelihood, placement
marginalization, planner behavior or cross-House generalization.

## Frozen design

- House: H01; wind context: 0.
- Fixed measurement designs: routes 4004 and 4005. They are not called held
  out and are not inference units.
- Source support: all 210 persistent carriers.
- Placement: exact member-0 coordinate `U0` for every generated world.
- Predictive realizations: seeds `101,211,307,401,503,601`.
- Prospective observation realizations: seven SHA-256-derived seeds recorded in
  `CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_PREREGISTRATION_20260831.json`.
- Independent inference unit: each of the seven prospective observation
  realizations. The 210 source ranks and two routes are averaged within it.
- Exact one-sided sign test: all 7 realization-level effects must be positive,
  giving `p=1/128=0.0078125`.
- Candidate, stop-association and predictive-K destruction maps are frozen in
  `CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V2.json`.

## Execution phases and hard stops

1. **Preflight only.** Verify JSON, Python syntax/selftests, git SHA, binary,
   source, manifests, schedules, environment and null-map hashes. Any mismatch
   is `INVALID`; do not regenerate with a substitute asset.
2. **P0 sentinel.** Regenerate all 210 predictive-seed-101 worlds with the
   locked single-thread environment. Every shard must be byte-identical to the
   frozen context-0/member-0 bank. One mismatch stops the run before other
   seeds are generated.
3. **Factorial materialization.** Generate the remaining 2520 worlds at the
   same `U0`, atomically validate all streams, and freeze the 2730-row hash
   manifest.
4. **Pre-score freeze.** Freeze evaluator SHA, preregistration SHA, bank SHA,
   null-map SHA and schedules before loading concentration sequences.
5. **Gate evaluation.** Compute the frozen coherent/redraw ranks, seven
   transport-unit effects, exact sign test, three destruction controls,
   route non-reversal and numerical invariances.
6. **Terminal interpretation.** `PASS` supports only the prospective H01
   simulator-internal M2 premise. `NO_GO` rejects M2 as the main innovation in
   its present form. Neither state directly authorizes closed loop.

## Conditional route toward the user's final objective

Only after M2 premise PASS:

1. calibrate M3 with source-independent sensor/noise data and proper scores;
2. marginalize legal placement `U` rather than lift carrier mass uniformly;
3. implement one source-channel replacement, single-consumption ledger,
   online=batch identity and complete planner-consumer closure;
4. run one revealed 300 s infrastructure/mechanism smoke without tuning;
5. freeze and run H01/H02/H03 paired 300 s OFF/ON development;
6. if pooled improvement is at least 10% with no House-level catastrophic
   reversal, run unseen-seed confirmation and require the preregistered lower
   confidence-bound criterion.

The old 43.60% G0 shadow remains terminal negative evidence and is never reused
as a performance claim.
