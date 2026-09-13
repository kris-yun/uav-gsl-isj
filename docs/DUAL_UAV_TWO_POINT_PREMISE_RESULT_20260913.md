# Dual-UAV two-point premise result

Date: 2026-09-13

## Formal verdict

```text
D. RAW_CACHE_INSUFFICIENT
qualification:
RAW_FRAMES_COMPLETE_BUT_EXISTING_HOUSE02_ROUTE_AND_MAP_CANNOT_SUPPORT_THE_DECLARED_DEPLOYABLE_DUAL_LARGE_UAV_GEOMETRY
```

This verdict does not mean that the plume frame files are missing. Their audit
passed 12/12 and all 5,040 required frames were rehashed. It means that the
frozen R3B experimental asset cannot instantiate the proposed physical
two-large-UAV measurement geometry without violating the source-blind
free-space and safety contract.

## Gate results

| Gate | Result |
|---|---|
| Raw-cache inventory and hashes | PASS |
| Source-blind formation | STOP: `r_max=1.8 m <= r_min=2.0 m` |
| Same-frame gas query | NOT RUN |
| Per-wind source observability | NOT EVALUATED |
| Held-wind 4/4 source identity | NOT EVALUATED |
| Destructive controls | NOT EVALUATED |
| Ordinary-D2 comparator | NOT EVALUATED |

## Claim boundary

The current evidence neither validates nor falsifies two-point turbulent plume
sensing. It falsifies the premise that the existing indoor House02 R3B cache
can serve as a deployable two-large-UAV testbed under the supplied contract.

Reducing the separation to 0.2--1.0 m would produce a numerical experiment but
would no longer represent the user's two-large-UAV system. Selecting only the
few favorable route samples would introduce a post-hoc geometry choice. Both
repairs are rejected.

The next scientifically valid premise requires a source-blind, open-space
synchronous two-receiver asset whose geometry supports the declared UAV
separation before gas values are read. Until such an asset exists, the proposed
two-point aperture remains a candidate measurement principle rather than an
established main innovation.
