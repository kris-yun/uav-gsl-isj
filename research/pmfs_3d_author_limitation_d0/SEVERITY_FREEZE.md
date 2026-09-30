# PMFS author-limitation 3D D0: severity definitions

Frozen before reading new oracle localization outcomes, 2026-09-30.

Only the eight H01/H02 S2 contexts and their S2X crossed sources are admitted.
No confirmation or House03 wind/concentration assets are read. All eleven
canonical wind states are audited; these are shared prescribed wind states,
not independent stochastic wind realizations.

Occupancy is the original 0.1 m 3D voxel file. Free means value 0. Coordinates
are voxel centres, with x fastest, then y, then z. The parser must verify
the z-slice count, y-row count, x-column count and binary wind header 999.
All input SHA256 values must equal S1 frozen asset metadata.

Per state, over free voxels in each region, epsilon = 1e-12:

* Rz = mean(abs(w)/sqrt(u*u+v*v+w*w + epsilon*epsilon)).
* Vertical/horizontal ratio = mean(abs(w)/(hypot(u,v)+epsilon)).
* RMS vertical/horizontal ratio = sqrt(mean(w*w)/(mean(u*u+v*v)+epsilon)).
* Angular discrepancy = mean(atan2(abs(w),hypot(u,v))) in degrees.
* Vertical shear = mean(norm(U[z+1]-U[z])/0.1) over adjacent free voxel pairs
  whose two endpoints are in the same region. This is a vertical derivative
  of the full vector field, not a temporal turbulence measure.

Geometry-only regions:

* DOMAIN: all free 3D voxels.
* SOURCE: sphere of radius 1.0 m around the original configured source xyz.
* PROBES: union of spheres of radius 0.30 m around the thirty frozen E1
  probe centres at z=0.20 m.
* CORRIDOR: union of tubes of radius 0.30 m around straight 3D segments
  from this source to those probe centres. This is a geometric corridor
  proxy, not a flow-derived transport path or a claim of obstacle visibility.

Aggregate each metric by equal averaging over states 0..10. Group severity
for the oracle gate is CORRIDOR Rz. Report all 16 source x context groups,
eight contexts and both Houses. Copy the same geometry/state severity to
each group's four realization records, explicitly treating those copies as
non-independent. A given GADEN seed does not have a distinct wind field.

If a region or its adjacent free voxel pairs is empty, report missing and
retain that limitation; do not redefine the region after seeing outcomes.
The high/low severity gate and oracle implementation/scoring contract are
separate pre-outcome freezes. This document does not authorize target scoring.
