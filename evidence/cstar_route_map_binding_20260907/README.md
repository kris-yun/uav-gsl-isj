# Route/map binding audit — 2026-09-07

This audit adds a missing prerequisite to the earlier environment preflight:
every measured-history pose and every frozen planned-route point must be in the
same House map frame and land on a free map cell. It performs no snapping,
translation, or House-specific repair.

Result: **CSTAR_ROUTE_MAP_BINDING_PASS** (`AUDIT.json`). The audit is
House-aware: each complete LOHO manifest is filtered by the row's own
physical `house` before checking that House's map. The earlier apparent
failures were a validator bug that replayed all three Houses against each map.
The corrected counts are:

| House | free | solid | outside grid |
|---|---:|---:|---:|
| H01 | 2,412 | 0 | 0 |
| H02 | 2,405 | 0 | 0 |
| H03 | 2,174 | 0 | 0 |

The manifests remain complete LOHO files: the same set of realization IDs is
present in each fold file, but each row carries its authoritative House and is
now checked against that House only. No coordinate repair, snapping, or
translation was needed.

This corrected audit is preserved alongside the earlier environment PASS. No
route was changed and no new simulator data was generated.
