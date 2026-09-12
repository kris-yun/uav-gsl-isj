# PMFS M1R three-arm mechanism audit — 2026-09-12

`HISTORICAL_REPLAY_SUFFICIENCY = FAIL`

`THREE_ARM_RESULT = THREE_ARM_EXACT_REPLAY_NOT_IDENTIFIABLE_FROM_CURRENT_ARTIFACTS`

`EVENT_ACCOUNTING_REPLAY_IDENTIFIABLE = NO`

`EVENT_ACCOUNTING_CAUSAL_EFFECT_NOT_IDENTIFIABLE_FROM_CURRENT_REPLAY`

The recorded histories contain sensor, robot pose, navigation action, MAP
estimate, entropy and run-status traces.  They do not contain the full candidate
posterior, candidate/event `p_sim`, event `p_context`, candidate/event log-score
increments, true-source rank/mass, or the random forward identity at each
candidate update.  Those omissions prevent a strict same-history M0/M1/M2
calculation and prevent an empirical comparison between per-block and
per-physical-stop evidence accounting.

No approximate reconstruction was substituted.  In particular, the existing
A0/M1R/M1M2R closed-loop comparison is not the requested three-arm observation
replay: its arms followed different histories and M1M2R changes transport
replication rather than isolating the absolute-source term.

The machine-readable field audit is in
`evidence/m1r_mechanism/HISTORICAL_REPLAY_SUFFICIENCY.json`; the terminal
three-arm record is in `evidence/m1r_mechanism/M1R_THREE_ARM_REPLAY.json`.

An instrumented rerun would necessarily be a
`NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION`, not historical exact replay,
because the original manifest binds an uncommitted source tree and only a
binary digest, while the corresponding binary bytes are unavailable.  It was
not used to overwrite this historical-identifiability verdict.

That single allowed replication was completed for H01/H02/H03 at seed 12 with
the frozen 240 s controller contract.  All three runs reached
`time_budget_timeout`; their final errors were respectively `3.344084 m`,
`1.471047 m`, and `8.879846 m`.  Its passive shadow scorer evaluated, on each
new run's identical observation history, M0 rolling-block persistence, M1
persistence plus absolute-source evidence, and M2 persistence plus
source/context contrast.

In H03, M2 minus M1 true-source log score was `+9.456873` after 32 blocks and
`+122.737148` after 104 blocks.  The first half of the first update was
`-2.052640`, however, and M2 released an 85-candidate update with the nearest
true-source candidate ranked 79 versus M1 rank 22.  Later net contrast was
positive and the M2 rank recovered to 29, but its final true-versus-top-false
margin remained `-386.562401`.  Thus the observed problem is not persistently
wrong-sign late contrast; it is evidence release while the source remains
non-identifiable.

The replication is not trajectory-equivalent to the historical M1R runs.  Its
sensor/pose sequences first diverge at rows 102, 97, and 98 for H01/H02/H03;
update clocks, source records, and algorithm hashes also differ.  The terminal
timeout status agrees, but that is insufficient for historical equivalence.
The full scores and comparison are in
`M1R_INSTRUMENTED_THREE_ARM_RESULT.json` and
`M1R_HISTORICAL_REPLICATION_COMPARISON.json` beside the historical replay
record.
