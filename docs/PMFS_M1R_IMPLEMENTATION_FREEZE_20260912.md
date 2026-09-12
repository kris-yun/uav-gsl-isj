# PMFS M1R implementation freeze — 2026-09-12

Status: `M1R_IMPLEMENTATION_BOUND = PASS_WITH_PROVENANCE_LIMIT`.

## Authority and boundary

The 8 September runtime manifests identify the executed source as
`c62a54a+cer-ratio-working-tree` and the binary only by SHA-256
`62df6d257bda7123dea67c3142b877fc3b8a8d8550012c18bfd3f456925ee533`.
Commit `8dd5977` is the first repository snapshot that preserves both that
`cer_ratio_m1` implementation and the nine run folders.  It is therefore the
best source-level binding, but the historical binary bytes are absent, so a
byte-for-byte source-to-binary proof is not available.  The complete file/blob
ledger is in `evidence/m1r_freeze/M1R_IMPLEMENTATION_MANIFEST.json`.

## Actual observation computation

For each current first-level candidate and each recorded internal measurement
block, the preserved implementation computes a Bernoulli probability from

`logit(p_persist) + logit(p_sim(candidate,event)) - logit(p_context(event))`.

`p_context` is the arithmetic mean hit-map probability at the event cell over
the current valid first-level candidate set.  Candidate probability is clipped
to `[1e-4, 1-1e-4]`.  The candidate likelihood is the product across all
recorded blocks and replaces the candidate's native first-level leaf score
before ordinary PMFS refinement and controller use.

The historical persistence term is the unit-scale normal tail at
`log1p(threshold)`, centred on `log1p(previousConcentration)`.  Contrary to the
earlier V4.1 review, `previousConcentration` is updated after every recorded
block.  It is not permanently zero.  It is nevertheless not a complete FOPDT
latent sensor state: it has no fitted time constant or persistent latent state
beyond the immediately preceding recorded concentration, and it is reset to
zero for every candidate evaluation.

## Code–document contradictions

1. The old report says each completed `StopAndMeasure` enters once.  Historical
   code records on every internal measurement block whenever event evidence is
   enabled; there is no physical-stop filter in `cer_ratio_m1`.
2. Logs show cumulative counts `32, 56, 80, 104` in every House, consistent
   with repeated internal blocks rather than one factor per physical stop.
3. The old report's notation `p(y_i | y_(i-1))` is acceptable only as a narrow
   previous-recorded-block heuristic.  Calling it a full persistent FOPDT state
   is false.
4. The later `c41fdb3` source changed this persistence path to reuse a window
   boundary concentration.  That later behavior must not be projected backward
   onto the 8 September binary.

Controller parameters, seed 12, 240 s horizon, House-specific geometry, action
runner, and `pfdi_mode=cer_ratio_m1` are bound by the per-run formal manifests
and preserved launch parameter files.  No controller modification or new score
was introduced in this audit.

