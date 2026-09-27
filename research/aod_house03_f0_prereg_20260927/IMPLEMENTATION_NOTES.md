# F0 implementation choices fixed without gas

The full House03 source bank is the 624-source set already defined by the E1
occupancy, seed-invariant pruned PMFS geometry and source eligibility rule.
E1 serialized six selected anchors, while retaining the complete source-set
definition and count. F0 materializes all 624 rows from those hash-verified
inputs, with the unchanged E1 grid-center and clearance definitions. It does
not substitute a House02 source table or use response data. The supplied
`select_house03_pairs.py` is run unchanged.

The source IDs within a pair are sorted by the supplied selector. Its
`anchor` and `partner` role labels therefore follow lexicographic order;
membership of all three E1 anchor pairs is unchanged.

Paths use the frozen pruned PMFS mask. The graph has eight neighbouring
cells, metric axial and diagonal costs, and no diagonal corner cutting.
Within-cell endpoint links preserve the exact start and probe coordinates.
Dijkstra gives metric shortest paths, with the result independently checked
using SciPy's graph implementation. This freezes geometry and timing; it
does not execute or claim equivalence to a live UAV navigation controller.
Path ties differing only below 1e-12 m are resolved by probe rank.

The frozen launch command fixes start (2,0) and simulator dt 0.2 s.
The archived pre-navigation VGR source and current source both specify
step_size 0.3 m and max_uav_speed 1.5 m/s, with no launch override.
Thus min(1.5, 0.3/0.2) = 1.5 m/s supplies the nominal path speed.

F0 freezes 50-second observation slots and 3-second dwell exactly as supplied.
The historical E2 extraction configuration separately uses snapshot indices
100,150,...,550, a results_time_step setting of 0.5 s, and a 300 s simulation.
Those file indices must not be silently interpreted as physical seconds.
The F0 path schedule is relative physical time 50,100,...,500 s; F1 must bind
this schedule to explicit simulator timestamps and sufficient generation
duration before execution. F0 does not change the historical generator or
authorize those future numerical settings. The two paths are already feasible
under the stated F0 47-second travel budget.

The only robustness condition is the state0 subset of the same future
1056-forward bank. Nominal averaging is 1/11 over wind states and 1/8 over
replicas. Both amplitude arms use the archived B2 score and identical forwards.

Future seeds are positive signed-31-bit integers derived from the complete
SHA256 key recorded per row. The GADEN and PMFS labels are separate domains;
all 1152 resulting seeds are distinct. Manifests carry F1-signature-required
status and contain no execution commands.

Infrastructure repairs affected only audit tools: UTF8 BOM-aware source
parsing, the correct E2 source location, literal TIMES resolution in the AST,
and use of bundled pandas with Python -s. E1's original CRLF table hashes and
their LF-normalized historical hashes both match. No scientific input bytes
were changed. Collection attempts are retained in VM temporary directories.
