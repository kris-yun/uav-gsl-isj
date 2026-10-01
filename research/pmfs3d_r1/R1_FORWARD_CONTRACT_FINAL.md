# PMFS3D-R1 offline ranking contract

State: **FINAL / AUTHORIZED BEFORE SCIENTIFIC SCORING**.
The three-arm control and the gate below were explicitly approved by the user.

## Cases and observation support

Exactly the four historical Native cases in `CASE_AUDIT_SUMMARY.tsv`.
Use the last source-update snapshot at or before 300 s, not newly generated
measurements. Preserve its measured hit/confidence map, legal cells, quadtree
leaf ownership and per-cell prior convention. Preserve the 119-123 active
leaves per case; do not add ancestors or truth-selected points to reach 150.
Do not rebuild/refine the quadtree after changing forward models.

H01/H02 release height is fixed respectively at the historical configured
-0.3 / 0.2 m for every candidate in that House. Sensor height is 0.3 m.
This is a **known-height oracle comparison**, not joint xyz source inference.
No candidate receives truth xy or a truth-neighborhood sampling privilege.
The H02 truth owner is a 5x1 leaf; exact-point identification within it is
unresolved and must not be claimed from a leaf-level result.

## Three arms

1. Native: exact frozen 2D PMFS with its recorded GMRF wind grid. Reconstructed
   forward maps must match the archived alignment probabilities before proceeding.
2. Oracle-2D: the same frozen PMFS kernel, replacing only wind vectors by the
   nearest-CFD values at each original 2D cell center and sensor height; w ignored.
3. Oracle-3D: xyz filament states, uvw CFD values, and original OccupancyGrid3D.
   Horizontal wind queries use the **same original 2D cell centers** as Oracle-2D,
   with the filament's current z. This prevents adding finer xy wind sampling
   only to the experimental arm.

Both oracle arms use the **same raw CFD CSV state0**. This is the exact static
minimum-state rule in the archived `/wind_value` service. It is not an
event-aligned or multi-state ensemble oracle, and does not claim the actual
history-wide wind realization is known.

Unchanged Native settings: dt=0.2 s, 200 recording steps, warmup min1/max3,
5 filaments released per step, horizontal noise stdev0.5, blur0, discrimination
power1, and per-filament within-leaf source sampling.
Native `configureNativeDeterminism` reads `seed` (default0), while the launcher
provided `random_seed`; actual source-point draws and complete Native forward
parity verify effective seed0 for all four cases. Preserve this historical
forward key: `(0, update5, replica0, 0x4E4154495645504D)`.
Do not substitute the run label seed1 as a new forward seed.

3D extension details, fixed without target-based tuning:

- Isotropic extension: z noise stdev0.5, a separate deterministic substream
  `native_substream XOR 0x33565F4E4F495345`; x/y retain Native's stream.
- Original 3D voxel grid for collision and exits. Collision steps are at most
  half an original 3D voxel; a blocked filament stays at its last valid point.
- Source draws falling in a blocked 3D voxel are not re-drawn or moved to a
  nearby valid point; the sampled emission is rejected. Candidate support
  and prior remain unchanged. Report this geometry constraint as part of
  the 3D forward operator, not exclusively as a vertical-advection effect.
- A hit occurs if a filament occupies the original xy PMFS cell and the same
  original 3D voxel z-layer as the sensor; at most one hit per cell per step.
- Outside-volume/grid filaments exit. The original 2D kernel is called intact
  for both 2D arms; therefore its wall handling differs from voxel-based 3D
  wall handling. R1 compares specified complete forward operators, not a
  perfectly isolated ablation of w alone.
- No Gaussian concentration footprint, amplitude likelihood, gain correction,
  density calibration, model training or tuned sensor-slab width is introduced.

These details define a first 3D PMFS **point-filament oracle prototype**, not
the full GADEN concentration simulator. A positive/negative result applies to
this frozen operator, not to all possible 3D observation models.

## Scoring and ranking

Unchanged Native single-cell factor and product on the same legal cells.
Use logs to avoid numerical underflow; do not clip, floor or use SSE softmax.
Normalize repeated leaf scores over free cells with the same uniform cell prior.
Retain full sourceProbability maps and per-cell entropy.

Primary truth rank is active-leaf **midrank** of the truth-owning leaf,
ordered by Native log likelihood (larger is better). Also report free-cell
midrank, tie count and exact-cell ambiguity. Recall@1 requires a unique
top leaf. Recall@5 is conservative: pessimistic tied rank must be <=5.

Margin = truth-owner log likelihood minus largest log likelihood of any
other active leaf. Primary delta = Oracle-3D margin minus Oracle-2D margin.
Native comparisons are separate secondary reports and cannot rescue the gate.

PASS requires all four conditions: median delta margin >0; at least3/4
positive delta margins; median Oracle-3D rank <= median Oracle-2D rank;
and no more than one case with worse Oracle-3D rank.
If the margin gate passes but rank noninferiority or anti-regression fails,
report PMFS3D_R1_HOLD_RANK_NONINFERIORITY. If the margin gate fails,
report PMFS3D_R1_NO_GO. Otherwise report PMFS3D_R1_ORACLE_RANKING_PASS.
Entropy difference H2D-H3D is descriptive only and cannot rescue any gate.
Lower entropy alone does not establish more accurate inference. A HOLD does
not establish the cause of a failed rank gate or authorize probability fusion.

Four historical cases do not establish new-realization confirmation, full xyz
inference, deployment superiority, or paper-level main-innovation acceptance.

## Required integrity gates and STOP

Historical input hash parity; exact Native forward parity; matching candidate
support; software zero-wind embedding and vertical-hit checks; CFD/occupancy
provenance; committed final contract and executable hash; full deterministic
repeat of forward maps, scores and evaluation.
No new GADEN, H03, confirmation, closed loop or training. No result-based
parameter/candidate/scorer repair. Preserve failures and stop after R1.
