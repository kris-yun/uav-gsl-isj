# Dual-UAV two-point theory and geometry freeze

Date: 2026-09-13

## Scientific object

The candidate mechanism is a simultaneous two-receiver spatial increment,

\[
\delta_{\mathbf b}z(t)=z(x+\mathbf b/2,t)-z(x-\mathbf b/2,t),
\]

with the two receivers queried from the same plume frame. The added physical
information would come from the second simultaneous receiver. The difference
is only a physics-guided representation of the same two-channel data.

The required future comparator remains:

```text
D2-STRUCTURE > same-data ORDINARY-D2
```

This task does not call the mechanism causal and does not modify PMFS.

## Frozen source-blind choices

- Center route: lexicographically first existing frozen route, `T_diag_A`
- Route selection inputs: filename inventory only; no gas, source rank, or localization error
- Primary orientation: cross-wind direction from the median nonzero deployable wind vectors
- Wind fields used by the geometry program: `raw_wind_u` and `raw_wind_v` only
- Gas columns in those replay files: never read
- Gas grid spacing: 0.1 m
- Large-UAV separation lower bound: 2.0 m
- Practical formation cap: 5.0 m
- Free-corridor check spacing: at most 0.05 m

The 2.0 m lower bound is optimistic for two large rotorcraft. Increasing it can
only strengthen the geometry failure below.

## Pre-gas geometry result

The existing House02 map and route fail before any plume value is queried.

- `T_diag_A` has 750 samples; 480 are free and 270 lie in blocked occupancy cells.
- Under `W_fast`, the largest cross-wind symmetric corridor found anywhere on
  the route is 1.8 m and there are zero samples supporting a 2.0 m corridor.
- Under `W_slow` and `W_altfast`, the optimistic maximum is 2.2 m, but only 14
  and 13 of 750 samples respectively support 2.0 m.
- The cross-wind span common to all three winds is therefore 1.8 m.

Thus:

```text
r_min = 2.0 m
r_max = 1.8 m
r_max <= r_min
FORMATION = STOP_RMAX_NOT_GREATER_THAN_RMIN
```

The uploaded execution contract explicitly requires stopping at this point.
No logarithmic baseline scales were created and no source-dependent gas query
was run.
