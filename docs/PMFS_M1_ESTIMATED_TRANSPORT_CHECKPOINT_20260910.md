# Estimated-transport integration checkpoint

The M1 goal is active; no closed-loop utility PASS is claimed.

## Completed input recovery

Native aligned GMRF run in tmpfs completed all six distinct House/wind
histories. All transferred files match the native SHA256 manifest.
Each history: 240 s, 120 fields, 1200 observations accepted, zero rejected.
All estimates are finite and map-centre aligned, with 6866/6811/7258 free
cells for H01/H02/H03. Five cases report convergence at all fields; H02 slow
reports convergence at 115/120. This is NOT an all-case numerical convergence
PASS and does not measure prediction accuracy.

Preserved complete data: `evidence/cstar_m1_gmrf_aligned_complete_20260910/`.
Independent audit: `evidence/cstar_m1_aligned_wind_complete_audit_20260910.json`.
Native session 29161 completed with exit 0. Old root-disk v4 remains invalid.

## Physical integration, not another ranking claim

Added map-bound reference visibility and filament sliding/outlet handling in
`m1_causal/filament_geometry.py`, following the inspected native sampling law.
It is not exact ray casting, native float parity, or UAV collision certification.
Tests cover free/blocked LOS, wall sliding, outlet removal and outside boundary.

The H01 fast existing-data integration uses both frozen candidate locations,
the same keyed noise member, native dt=0.1, physical Gaussian concentration,
and persistent tau=1.2/dead time=0.4 sensor law. Gas observations are excluded
from the forward dynamics. Explicit approximations remain: planar extrusion
with zero vertical transport wind; initial zero wind prior; point deterministic
7/s release instead of the original variable-rate emission. Gas type 10 is
butane (specific gravity 2.0061), not archival wind-directory label 13.
The parameter values follow the existing producer script/native formulas;
the full historical binary/parameter identity is not thereby established.

The 60 s smoke completed for both candidates, but both concentration/sensor
predictions are zero. In the existing SA observations the first 60 s gas is
zero; SB maximum is 0.024827 ppm. Both candidates therefore tie on response
error: SA log1p MSE 0, SB log1p MSE 1.242102e-5. No identifiability claim.
Output: `evidence/cstar_m1_estimated_transport_h01_screen_20260910.json`.

A 240 s continuation is running in unified exec session 97603. It has already
reported SA MODEL_INPUT_FAILURE at 70.8 s. Do not treat the 60 s smoke as
superseding that failure. Wait for the saved full diagnostic (both candidates),
inspect exact error, and address the failed physical/input assumption rather
than switching candidates, seeds, or hiding missing support with zeros.
