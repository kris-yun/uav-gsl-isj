# Sparse-path freeze

Use only:
- frozen House03 occupancy/navigation map;
- the 30 already-verified House03 E1 probes;
- frozen robot start `(2.00, 0.00)`;
- frozen navigation-speed configuration.

No source identity or gas field may enter path construction.

## Feasibility graph

For the robot start and all 30 probes, compute obstacle-aware shortest-path
geodesic distances in the navigation grid.

Observation interval is the existing 50 s snapshot spacing.
Reserve 3 s dwell at each observation.
A transition is feasible only when

`geodesic_distance / frozen_nominal_speed <= 47 s`.

If the nominal speed cannot be recovered from the frozen navigation contract,
STOP:
`AOD_H03_F0_HOLD_NAV_SPEED`.

## Deterministic paths

Construct two paths, A then B, each containing exactly 10 distinct probes.

Path A:
1. first probe = feasible probe with minimum geodesic distance from robot start;
   tie by `probe_rank`;
2. repeatedly choose among not-yet-used probes that are feasible from the
   current probe the candidate maximizing its minimum Euclidean distance to the
   probes already in the path; tie by `probe_rank`.

Path B:
same algorithm, but first prefer probes not used by A. If fewer than 10 form a
feasible path, allow overlap only after all unused feasible candidates are
exhausted; log every overlap.

Both paths must:
- contain 10 samples;
- be feasible under every segment timing check;
- use only the frozen 30 probe centers;
- be fixed before any fresh plume.

Report:
- ordered probe ranks and xyz;
- per-segment geodesic distance/travel time;
- total route distance;
- overlap count A vs B;
- occupancy/map hashes.

If either path cannot be built deterministically, STOP:
`AOD_H03_F0_HOLD_PATH_GEOMETRY`.
