# H03 M1R failure decomposition — 2026-09-12

The reproducible historical fact is narrower than the former single-label
story: M1R worsened H03 endpoint error by `1.063361 m` while improving
whole-horizon distance AUC by `14.300730 m s`.  This is an endpoint reversal,
not evidence of uniformly worse navigation.

The historical artifacts alone leave all five requested mechanisms
`INSUFFICIENT_EVIDENCE`.  The separately labelled new instrumented development
replication resolves the mechanism choice without being projected backward as
historical exact replay.  In its H03 history, the first half of the first
source update has negative M2-minus-M1 evidence (`-2.052640`) and the released
M2 score ranks the nearest true-source candidate 79/85.  Later true-source
contrast is net positive (`+75.370918` in the final cumulative late half), and
the M2 rank can recover to 29/85.  The final margin nevertheless remains
strongly non-identifiable (`-386.562401` versus the top false candidate).

This rules against persistent cross-environment wrong-sign contrast as the
primary observed failure.  Rank recovery also gives no support for an
irreversible-bookkeeping diagnosis, while rank 29/85 is not a basically
correct posterior from which to blame only action selection.  The supported
failure label is therefore `EARLY_SOURCE_NONIDENTIFIABILITY`, with the scope
explicitly limited to the new frozen replication.

The full multi-label record is in
`evidence/m1r_h03/H03_M1R_FAILURE_DECOMPOSITION.json`.  It selects
`IDENTIFIABILITY_CONTROL` and does not implement a repair.
