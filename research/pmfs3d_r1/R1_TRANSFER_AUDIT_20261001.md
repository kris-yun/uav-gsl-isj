# PMFS3D-R1 transfer audit

Status: `PMFS3D_R1_PRE_FORWARD_CONTRACT_HOLD`.
This is an asset and Native parity audit, not a scientific R1 result.
Branch: `research/pmfs3d-r1-oracle-ranking-20261001`.
Base: `810489aad56f755bb22c8cbe2ac6ba4a8f695437`.

## Frozen cases recovered

The four requested Native cases were recovered from the authoritative historical
TNQC archive, not substituted with newer cases or with fused-method outputs.
Each selected input was checked against the archive's `SHA256SUMS.json`.
The historical execution commit is `b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`.
The exact frozen PMFS source is retained under `evidence/pmfs3d_r1_oracle_ranking_20261001/frozen_code`.

| Case | Last update <=300 s | Time (s) | Evaluated leaves incl. ancestors | Active leaves | Free cells | Native posterior max absolute error |
|---|---:|---:|---:|---:|---:|---:|
| House01 seed0 | 5 | 275.8 | 152 | 123 | 626 | 1.8318679906315083e-15 |
| House01 seed1 | 5 | 279.6 | 148 | 121 | 626 | 2.9976021664879227e-15 |
| House02 seed0 | 5 | 274.2 | 148 | 123 | 631 | 4.551914400963142e-15 |
| House02 seed1 | 5 | 275.6 | 144 | 119 | 631 | 2.1094237467877974e-15 |

Native reconstruction uses the unchanged single-cell formula
`1 - confidence * abs(measured_hit_probability - predicted_hit_probability) * sourceDiscriminationPower`,
product over free cells, and the historical active quadtree partition.
Log-space evaluation reproduces the existing normalized source map to floating-point accuracy.
Missing standalone candidate `.f32` files do not prevent this parity: the frozen
alignment CSV contains the required predicted probabilities on cells with positive confidence.
Cells with zero confidence contribute exactly one.

No new forward simulation or scientific source-rank comparison has been performed.

## Wind knowledge is a confound in the proposed two-arm design

All four resolved runtime files contain **`useWindGroundTruth: false`**.
In the exact frozen `PMFSLib.cpp`, `EstimateWind` takes the GMRF service branch
when `useGroundTruth` is false (lines 371-404). Historical `estimated_wind.csv`
is the 2D wind grid actually used by the forward model.

Therefore `Native estimated-wind 2D` versus `CFD oracle-wind 3D` changes both
wind information and transport dimensionality. Its improvement could not be
attributed uniquely to restoring 3D information.

The proposed minimal correction is:

| Arm | Wind | Transport | Role |
|---|---|---|---|
| Native | Historical frozen GMRF | Historical 2D | Original baseline anchor |
| Oracle-2D | Same CFD assets/state as Oracle-3D; fixed sensor-height uv projection, w=0 | 2D | Control for oracle wind knowledge |
| Oracle-3D | Same CFD assets/state, full uvw | 3D | Experimental forward operator |

Primary dimensional comparison is Oracle-3D minus Oracle-2D;
comparisons to Native are reported separately. The user **approved the three-arm
control in the current conversation**. Oracle scientific forward/scoring has
not started. The correction adds no GADEN plume or observation.

## Candidate and observation semantics

Use the original complete active quadtree support for each case (119-123 leaves),
including all original free cells. The suggested 150-candidate count is not
available as 150 distinct active leaves; historical ancestor leaves cannot be
treated as additional independent source-map candidates.
This complete support avoids selecting candidates using truth or historical rank.
All arms must use identical candidate ordering, cell ownership, and prior/mass
convention. A quadtree leaf must retain Native per-filament within-leaf source
sampling; its recorded first sampled point is not a persistent source center.

The terminal measured hit/confidence map is already computed from the same
historical trajectory. Reusing this frozen map preserves the observation side
and isolates the final source-update forward comparison. This is an offline
ranking experiment, not a new 300 s closed loop.

H01 truth height is -0.3 m; H02 truth height is 0.2 m; the robot sensor height is
0.3 m. These are different from O0's fixed 0.2 m contract and cannot silently
be replaced with O0 settings. Any 3D source-height prior, sensor projection,
wind state/time mapping, collision semantics and RNG contract must be frozen
before R1 forward scores are produced.
The labels seed0/seed1 are historical run/replay/sensor seeds; they are not
evidence of two newly independent GADEN plume realizations.

All truth coordinates lie on original legal cells. H01 truth owner is the 1x1
leaf `quadtree_23_16_1_1`; H02 truth owner is the 5x1 leaf
`quadtree_16_21_5_1`. A leaf-level result cannot resolve the latter's five cells.

The effective Native forward RNG seed is0 in all four runs: the launcher supplied
`random_seed`, while frozen `configureNativeDeterminism` reads `seed` with default0.
The isolated replay using key `(0,5,0,0x4E4154495645504D)` has now reproduced
**all 130,853 archived alignment probabilities with exactly zero error**.
Do not silently change its seed to the run's seed1 label.

The copied historical wind service hash is
`e94becb2d72f82b9e040bb7a12d2b7132dc85283176cf0ee0b309b4804347116`,
matching the historical runtime hash registry. It always selects minimum CSV
iteration; both contexts have state0. Oracle assets are hashed in
`ORACLE_ASSET_HASHES.json`.

## Gates and evidence limits

The user's detailed three-condition gate requires >=3/4 positive margin changes,
positive median margin change, and strictly smaller median truth rank.
The final short handoff says non-worsening rank instead. Both wordings are
recorded; no result-dependent choice between them is permitted.
Margin-only improvement cannot be silently promoted to the strict three-condition PASS.
Truth ownership and leaf/cell tie handling must be frozen before scoring.

O0 established a Hellinger-based spatial-fingerprint margin effect in its small
panel. It did not estimate mutual information or prove a strict information
inequality. Four historical development cases likewise cannot establish a
paper-level main innovation, calibrated posterior, or general deployment benefit.

## Resource and protection status

Read-only VM check: root available 440 MiB; hgfs available about 5.6 GiB.
No ROS source/build/install directory was changed, no GADEN input was changed,
and no original raw dataset was deleted. New small audit outputs were written
to shared storage. No H03 or confirmation observations were opened.

## Implementation and software checks

`oracle_forward.cpp` compiled as an isolated executable, reusing frozen Native
libraries read-only. Native and Oracle-2D call the exact library kernel.
All protected library/source hashes remained unchanged.

- Four-case Native forward parity: all PASS, maximum hit-map error0.
- Synthetic zero-wind 2D embedding: Native=Oracle-2D=Oracle-3D exactly.
- Synthetic vertical transport: without w, below-sensor emissions produce no
  sensor-plane hit; with w, sensor-plane hits appear.
- Comma-containing CFD path CSV parsing tested.
- Asset/parity audit repeated with identical output SHA256
  `59db8fa7ac644ba0ac6020093bcda7706d3709bedbddad63148843a63da05c6e`.

These are implementation checks, not evidence of R1 improvement. Four Native
reconstruction forwards and five synthetic forwards ran; zero Oracle forwards
on historical cases and zero new GADEN plume ran.

## Next step

Resolve the remaining gate definition before scientific forward
execution. Then freeze the complete transport/observation contract, hashes and
candidate ownership, implement shared 2D/3D replay, verify parity/projection
tests, score all four cases once, repeat deterministically, report and STOP.
