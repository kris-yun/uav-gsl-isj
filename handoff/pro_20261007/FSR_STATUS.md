# FSR / 枫树岭 benchmark status

## Intended role
FSR is the project's **main self-built lakeshore benchmark**, not just an auxiliary external scene.
House H01/H02 are cross-scene stress tests.

## What has actually passed
Latest geometry decision:
`FSR_FB1_GEOMETRY_PASS_LOCAL_RELATIVE_FRAME`

The current static base includes:
- real-site shoreline proxy constrained from remote-sensing products;
- DEM-based terrain;
- local relative vertical frame;
- water/land geometric conditioning;
- reproducible geometry contracts and hashes.

## Critical boundary
This does **not** mean the scientific benchmark is finished.
At the latest R8 checkpoint:
- CFD scientific cases run: 0
- GADEN scientific cases run: 0
- PMFS scientific cases run: 0
- full execution preflight still pending.

Therefore use the wording:
**“real-site-geometry-constrained controlled lakeshore simulation benchmark base”**
not
“measured FSR wind/plume dataset”.

## Accepted modeling stance
For the first paper it is acceptable to use:
- real FSR geometry;
- controlled meteorological forcing within literature-supported ranges;
- clearly labeled oracle CFD/GADEN truth.

Possible controlled factors include:
- water–land thermal contrast;
- water/land roughness difference;
- background wind direction/speed;
- cross-shore vs along-shore flow;
- atmospheric stability;
- vertical shear;
- day/night-like direction changes if physically supported.

Every variable must be labeled as one of:
measured/remote-sensed geometry, literature-supported physical range, controlled factor, or oracle simulation truth.

## Pro task
Design the shortest path from current geometry PASS to a publishable UAV-GSL benchmark:
preflight → CFD cases → GADEN → source/realization design → UAV sampling → strong baselines → storage/compute budget.
