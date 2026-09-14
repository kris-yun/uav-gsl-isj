# Chasing Ghosts input-contract audit for TROQL/OQIC

Date: 2026-09-14

## Verdict

`CHASING_GHOSTS_RAW_CONFIRMATION_SERIES_UNAVAILABLE`

The paper reports a promising real-world design: an approximately 200 m² course,
an ethanol diffuser placed in two rooms, and five runs per room. This satisfies
the high-level source-replication requirement better than the other newly found
candidates.

The current public repository does not, however, contain the raw real-flight
sensor time series needed to recompute candidate-relative evidence. At repository
commit `fb632d0596a9e06eee38a149654b91fabac18dab`, the tree contains code, CAD files,
model weights, and simulation assets, but no raw experimental flight-log files.
The README states that code consolidation for the paper remains in progress.

## Decision

The reported 100% task success cannot be substituted for a TROQL/OQIC replay.
No paper table, trained weight, or simulated trajectory is treated as raw
candidate-relative evidence. This candidate remains eligible only if the authors
release the run-level olfactory and navigation logs with room/source labels.

## Provenance

- Paper: <https://arxiv.org/abs/2602.19577>
- Repository: <https://github.com/KordelFranceTech/ChasingGhosts>
- Audited repository commit: `fb632d0596a9e06eee38a149654b91fabac18dab`
