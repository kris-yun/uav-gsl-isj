# Route/map binding audit — 2026-09-07

This audit adds a missing prerequisite to the earlier environment preflight:
every measured-history pose and every frozen planned-route point must be in the
same House map frame and land on a free map cell. It performs no snapping,
translation, or House-specific repair.

Result: **CSTAR_ROUTE_MAP_BINDING_NO_GO** (`AUDIT.json`). The counts are:

| House | free | solid | outside grid |
|---|---:|---:|---:|
| H01 | 7,236 | 392 | 1,264 |
| H02 | 7,216 | 60 | 1,616 |
| H03 | 6,492 | 0 | 2,400 |

The failures are not a M1/M2 model result. They show that the currently
packaged controlled histories/routes and the per-House navigation slices are
not jointly aligned. In particular, the same archived episode IDs/source
coordinates are present in all three House manifests although their candidate
map extents differ. Launching a physical-prior or closed-loop gate on this
package would confound algorithm failure with coordinate identity.

This negative audit is preserved alongside the earlier environment PASS; the
earlier certificate checked map/candidate identity and live wind but did not
check all trajectory poses. No route was changed and no new simulator data was
generated.
