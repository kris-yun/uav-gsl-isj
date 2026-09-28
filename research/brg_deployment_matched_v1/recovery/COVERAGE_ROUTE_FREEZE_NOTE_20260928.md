# BRG V1 OPEN coverage collection route

The first pure-geometry candidate was the existing VGR `reversal` profile.
Its complete 300 s path was legal, but it visited only 4–5 Native legal cells.
No coverage-policy VGR run had started. We therefore replaced that candidate
before reading any coverage observation with the frozen V2 graph route.
`COVERAGE_GEOMETRY_FREEZE_V1_SUPERSEDED.json` preserves the earlier check.

V2 uses only the fixed Native legal-cell map and the already frozen initial
pose in House01/House02. A deterministic four-neighbor BFS chooses the most
distant unvisited legal cell, using cell ID to resolve ties. Adjacent cell
centers are joined with 3.4 s minimum-jerk segments. This construction never
reads source truth, plume concentration, source scores, or House03.

The three per-environment routes each contain 1,501 positions over 300 s.
House01 visits 57 distinct legal cells over 26.16 m; both House02 winds share
the same geometric path, visiting 58 legal cells over 26.18 m. All sampled
positions are on Native legal support. Speed, acceleration, and jerk stay
within the existing VGR envelope. Exact route file hashes, bank fingerprints,
and kinematic maxima are in `COVERAGE_ROUTE_FREEZE_V2.json`.

Only training/development collection selects this path. Native and later
learned-arm closed loops keep their own planner-driven motion. The VGR route
loader is opt-in and rejects files outside the three frozen route names.
