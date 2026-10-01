# Scene figure and output contract

Date: 2026-10-01

The revised scene figure should no longer show only "one UAV + unknown source".

## Required visual objects

Draw one lakeshore ROI with:
- lake / shoreline;
- facility / industrial equipment;
- vegetation and obstacles;
- unknown leak source s*;
- 3-D wind vectors / lake-breeze front;
- an evolving, patchy plume with at least three time slices t, t+Delta, t+2Delta;
- concentration contours / transparent volumetric plume;
- current effective region Omega_theta(t);
- forecast region Omega_hat_theta(t+tau);
- plume centerline and centroid;
- plume boundary / front;
- 3 to 5 UAVs at distinct functional positions.

## UAV placements to show

Suggested schematic:
- UAV-A near the high-probability source / upwind core;
- UAV-B on the plume centerline;
- UAV-C and UAV-D near two high-uncertainty boundary points;
- UAV-E ahead of the predicted plume front.

Arrows should show dynamic role re-allocation as the plume shifts.

## Input panel

Meteorology:
- wind speed/direction;
- vertical shear;
- temperature / lake-land thermal contrast;
- turbulence / stability.

Mobile observations:
- VOC concentration;
- local wind;
- UAV pose;
- time.

Environment:
- shoreline;
- buildings / vegetation / terrain;
- no-fly / safety regions.

## Output panel

Localization:
- source position / posterior;
- source uncertainty.

Current situation:
- plume centroid;
- principal spread;
- centerline;
- effective region;
- concentration / risk boundary.

Forecast:
- t+tau plume region;
- predicted boundary / front;
- uncertainty.

Swarm:
- key sensing points;
- role assignment;
- cooperative trajectories.

## One-sentence caption logic

"Multiple UAVs sparsely observe a meteorology-driven, time-varying gas plume in a complex
lakeshore environment; the system jointly estimates the leak source and current plume state,
forecasts its short-term evolution, and reallocates the UAV swarm to source, centerline,
boundary and forecast-front sensing tasks."
