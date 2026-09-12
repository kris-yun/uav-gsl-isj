# H03 distributed paired-intervention result

Date: 2026-09-13

## Frozen verdict

```text
AT_LEAST_TWO_PHYSICAL_ACTIVE_STATIONS_EVERY_WORLD=FAIL
PHYSICAL_SOURCE_OVER_TRANSPORT_CAPACITY=PASS
HELDOUT_PROVIDER_DIRECTION=FAIL
ALL_SOURCES_ALL_TRANSPORTS_UNIQUE_FULL_SUPPORT_RANK1=FAIL
PAIRED_CONTRAST_NON_DEGRADE_SAME_ENDPOINT_RAW=FAIL
PAIRED_CONTRAST_STRICTLY_LOAD_BEARING=PASS
SHARED_SOURCE_ACROSS_STATIONS_LOAD_BEARING=FAIL
NO_GO_NO_CLOSED_LOOP_DISTRIBUTED_OPERATOR
```

The frozen evaluator ran once after all four H03 physical worlds completed.  No
PMFS, posterior, planner or closed-loop arm ran.

## What survived

The nine-dimensional physical SA-minus-HF contrast remained consistent across
the existing transport interventions:

- fast/slow cosine: `0.963078`;
- source main-effect norm: `0.087482`;
- source-by-transport interaction norm: `0.033385`.

This independently confirms the narrower result from the one-station rank-2
probe: executed position actions produce a real source-dependent response, and
that coarse response is more stable than the source-by-transport interaction.

Paired contrasts strictly improved the truth rank over the same-endpoint raw
comparator in at least one world.  The contrast operation therefore contains
some useful information; this is not enough to establish source localization.

## Decisive failures

The source-blind map-spread stations did not yield the preregistered minimum of
two physical hit stations per world:

| physical world | active stations | distributed paired truth rank | same-endpoint raw truth rank | best-source error |
|---|---:|---:|---:|---:|
| SA fast | station 2 | 416--820 | 630 | 13.727 m |
| SA slow | none | 1--820 tie | 1--820 tie | 2.426 m |
| HF fast | station 2 | 169 | 416 | 8.321 m |
| HF slow | station 2 | 85--820 | 80 | 7.447 m |

Station identifiers above are one-based.  Every nonzero physical hit occurred
at station 2 near `(12.8, 6.087)`; stations 1 and 3 stayed below the native
0.1 ppm threshold.  SA-slow peaked at only `0.012423 ppm` over all station
endpoints.  Thus the continuous plume did not provide the multiple associated
spatial events required by the HARPA-inspired shared-source construction.

The H01+H02-selected provider had observed/predicted source-difference cosine
`0.117351` in fast transport and `-0.000776` in slow transport.  Distributing
the action fixed neither the provider's held-out spatial response shape nor its
slow-transport direction.  The paired operator also degraded the raw comparator
for HF-slow, so the action contrast was not uniformly safe.

## Scientific decision

DPISC is frozen `NO_GO`.  It will not be rescued by lowering the 0.1 ppm
threshold, selecting stations from observed gas, removing SA-slow, allowing one
station, changing the station scale contract, or accepting a broad rank tie.

The tested 2026 distant-field chain is now resolved under the current benchmark:

- task-related changes can carry information, but the earlier temporal
  `Delta log1p` transfer failed and the spatial paired contrast is not
  uniformly source-identifying;
- independent physical measurement directions create source contrast, but one
  station lacked global support and three distributed stations lacked repeated
  plume hits;
- controlled position inputs do not repair a misspecified held-out provider;
- a shared-source multi-observation constraint cannot operate when the single
  UAV does not observe multiple associated active stations;
- the two-chemical differential strategy cannot be instantiated from one gas
  channel without inventing a measurement.

Therefore the current single-UAV, single-gas causal measurement line remains a
valid audit and experiment-design result, not a supported cross-dataset main
localization innovation.

## Operational provenance

The first remote launch generated the first gas world but stopped before
history extraction because an obsolete sensor-root path was supplied.  No gas
value or gate output was read.  Only this newly created failed temporary output
was removed.  The complete rerun used the same frozen commit, archive, route,
worlds and RNG seed; the sole correction was the deployment path to the already
frozen sensor asset.  All four complete-world files are represented in the raw
manifest and independently verified after transfer.
