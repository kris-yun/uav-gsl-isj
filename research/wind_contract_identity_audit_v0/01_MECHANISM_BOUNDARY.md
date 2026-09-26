# Mechanism boundary

## Facts already frozen

House01 / seed0 / Native R1, source update 1:

- 20 completed measurement blocks;
- four robot sites;
- one hit and 19 misses;
- Native forward field came from `/wind_value`;
- 626/626 PMFS internal vectors matched `/wind_value` responses after float32
  storage conversion.

The VGR adapter audit established that the VGR bridge publishes the flow-vector
direction `atan2(v,u)` in `map`. Therefore the event direction and the
`/wind_value` `(u,v)` field can be compared as flow directions; a blanket pi
correction is not authorized.

## Why this audit is necessary

Even the final measurement block at site D has a wind direction and magnitude
very different from the source-update `/wind_value` field at the same x/y.
Possible causes include:

1. genuine temporal wind-state change;
2. different wind-state indexing in VGR sensor and `/wind_value`;
3. different z-plane / coordinate sampling;
4. sensor averaging/noise;
5. the two adapters reading different physical assets.

Only case (1), or a known combination of (1)+(4), licenses a time-aligned
candidate-forward experiment.

## Required distinction from old failed routes

This is **not**:
- JTD temporal-memory modeling;
- Source-Lineage/Lagrangian reconstruction;
- M4 source×wind factorization;
- a new score.

It is a contract identity check: did observation and candidate forward consume
the same physical wind process?
