# Minimal vertical-transport oracle probe

This is a minimal offline vertical-transport lift of the frozen AOD-R2 F0
PMFS candidate kernel, not a replacement GADEN simulator or a validated full
3D PMFS implementation. The production ROS2/GADEN installation is untouched.

## Paired inputs

Reuse F0's exact 3,168 candidate/state/key rows, legal masks, selected candidate
neighbourhoods, source coordinates (including z=0.20 m), wind states, keys
1..8, simulation settings and blur. Candidate neighbourhoods were frozen
before F0 observations; no new source coordinates or neighbourhood are chosen.
Original configured truth xyz remains unchanged in all target metadata. Native
H01 configured source 1 is outside its coarse legal support, so this probe
cannot claim exact-source, full-map or arbitrary-height source coverage.

Arm A executes the existing Native 2D simulation code unchanged, instrumented
only to export multiplicity. All four map channels p/u/rawp/rawu must reproduce
the existing F0 bank exactly on the parity sample before proceeding.

Arm B adds a filament z coordinate, initially 0.20 m, and samples U/V/W from
the canonical 3D field at the same coarse XY cell centre and current z. It
adds w*deltaTime to z, using the identical XY Gaussian noise calls with no
additional z noise. XY collision handling is still the exact Native routine.
Vertical motion into a non-free 3D voxel is blocked; exit through the vertical
domain boundary removes the filament. Thus this probe restores vertical
advection, vertical shear and vertical boundary effects; it does not restore
arbitrary horizontal 3D obstacle bypass, buoyancy, Gaussian filament growth or
continuous-concentration physics. Gas metadata is matched but this Native
kernel does not model gas-specific buoyancy in either arm.

Observation lifting: the Native 0.30 m XY counting cell becomes a 0.30 m tall
voxel centred on the frozen observation plane z=0.20 m. Counts are recorded
only when abs(z-0.20)<0.15 m, then the unchanged Native 2D blur and occupancy
correction are applied. Arm A's degenerate z=0.20 filaments obey the same
lifted sampling rule automatically and exactly reproduce Native counts.
This voxel support is a declared proxy, not a Gaussian concentration sensor
model. The target remains the existing E1 2x2-voxel concentration average,
binarized by concentration>0; neither arm changes target extraction.

All fixed state banks are averaged equally over 11 states x 8 keys, following
the original F0 static-bank contract. The same 30 footprint samples are used
at every one of the ten frozen time slots. This does not introduce a new
event-aligned wind-state mixture in one arm, and is not a claim of historical
wind-state reconstruction. The target time mapping is retained exactly.

Randomness: identical process seeds and the same Native 2,500-entry Gaussian
table construction. Transport changes particle lifetimes, so identical seeds
do not imply identical disturbance assignment to every surviving filament.
No new RNG stream or stochastic parameter is introduced. This is paired seed
replay, not a claim of exact common-random-number filament matching.

## Verification before target outcomes

1. Arm A map-byte parity against the historical F0 frozen bank.
2. B-flat diagnostic: zero vertical wind, z-invariant Native XY wind, and no
   vertical barriers must reproduce A map bytes exactly.
3. No amplitude observer consumes RNG or changes hit counts.
4. Every primary B wind/occupancy file SHA256 equals frozen S1 metadata.
5. Arm A and B use the identical source/support/state/key/settings and blur.
6. Completed forward banks are hashed before evaluating target tensors.

## Scoring

User amendment: primary mean Brier mismatch on the existing binary 10x30
observations. Smaller is better. Source discrimination margin is alternative
Brier minus truth Brier. For each original configured source, average the
probability templates of its exact pre-frozen F0 candidate neighbourhood,
equally, in both arms. The two resulting source hypotheses are the same in
A/B. Unique Top1 requires strictly smaller Brier; exact ties are not success.
This is a two-source mechanism comparison, not full legal-map localization.

Amplitude diagnostic keeps original nonnegative gain-profile B2 SSE and does
not compare count-proxy self-residuals with ppm residuals as calibrated units.

Primary improvements: A truth Brier minus B truth Brier; B discrimination
margin minus A margin. Average over four independent target realizations
within each source/context before group and House comparisons. Repeated
slots and probe cells are not scientific repetitions.

The user-requested severity/concentration gate remains pending its separate
pre-outcome numerical amendment. No target scoring is authorized by this file
alone. Native parity failure stops the probe; it is not a scientific NO_GO.
