# LAGOON-PINGO REAL-DATA MECHANISM AUDIT
Date: 2026-10-03

## Goal
Use the public Lagoon Pingo 2024 field dataset to test, before any new CFD/GADEN generation, whether a real coastal water-land methane scene contains measurable transport structure that can support the thesis first-paper problem.

This is an audit, not an algorithm paper and not a source-localization claim.

Dataset:
Zenodo record 19597182, field campaign 2024-08-26 to 2024-09-01.
Primary files:
- svalbard_merged.nc (~533.9 MB)
- Dissolved_methane_floating_flux_chamber_ebullition.xlsx
Optional after audit:
- multispectral/thermal GeoTIFFs
- older Lagoon Pingo DEM/orthomosaic from DataverseNO DOI 10.18710/IMPEG8

The dataset provides synchronized DJI M300 RTK flight logs, Aeris MIRA Strato dry CH4 mole fraction, and Li-Cor TriSonica Sphere 3-D wind components.

## 1. Stage A — minimal download and schema audit
Do not download all imagery first.

Download only:
1. svalbard_merged.nc
2. Dissolved_methane_floating_flux_chamber_ebullition.xlsx
3. Zenodo metadata / checksums

Audit:
- dimensions and variables
- units
- CRS / lat-lon / altitude representation
- timestamps and timezone
- number of flights
- start/end/duration per flight
- effective sampling rates of CH4, wind and flight log
- missingness
- duplicated timestamps
- synchronization offsets if present
- wind coordinate convention and whether values are already motion-corrected
- sensor lag metadata if available

Outputs:
- DATA_SCHEMA.md
- FLIGHT_INVENTORY.csv
- VARIABLE_DICTIONARY.csv
- MISSINGNESS.csv
- SHA256SUMS.txt

STOP if merged file cannot be unambiguously split into independent flights or if wind/CH4 synchronization cannot be verified.

## 2. Stage B — spatial geometry and shoreline question

First answer whether the UAV actually samples different water-land contexts.

For each sample derive:
- projected x,y in one metric CRS
- altitude AGL if available or recoverable
- flight_id
- heading / ground velocity
- CH4 enhancement above flight-specific background
- 3-D wind U,V,W
- wind speed/direction

Build a shoreline/water mask only after confirming suitable georeferenced imagery exists.

Preferred:
- use the campaign multispectral image(s) and NDWI / visual QC
- otherwise use public Lagoon Pingo orthomosaic/DEM as a geometry reference, while documenting date mismatch

Create:
- water
- shoreline transition band
- land

and signed shore distance d_shore.

Do not claim the small lagoon creates a classical large-lake breeze. The variable d_shore is initially only a surface-context coordinate.

Outputs:
- SITE_MAP.png
- UAV_TRACKS_BY_FLIGHT.png
- SHORELINE_MASK.tif / geojson
- SAMPLE_CONTEXT.csv

Geometry gate:
- report how many independent flights actually traverse more than one context;
- report number of repeated crossings;
- report overlap of altitude/time/wind conditions across contexts.

If almost all methane flights stay in one context, STOP the “water-land transition mechanism” claim and use the dataset only as a real coastal methane validation dataset.

## 3. Stage C — real transport-structure audit

No neural network yet.

For each flight and for water / transition / land groups calculate:
- mean/median CH4 enhancement
- intermittency / hit fraction at frozen thresholds
- whiff duration distribution
- blank duration distribution
- CH4 autocorrelation time
- wind-speed variance
- wind-direction circular variance
- vertical wind W distribution
- CH4-wind lagged cross-correlation
- along-shore / cross-shore wind components if shoreline normal is reliable

All statistics must be summarized by flight/transect; do not treat 1-Hz samples as independent replicates.

Primary exploratory question:
Does the shoreline context explain changes in methane intermittency, wind variability, or temporal correlation after controlling descriptively for altitude and flight/time?

Outputs:
- CONTEXT_SUMMARY.csv
- CH4_ACF_BY_FLIGHT.csv
- WHIFF_BLANK_BY_FLIGHT.csv
- WIND_VARIABILITY_BY_FLIGHT.csv
- LAGGED_CORRELATION.csv
- figures

No causal language from this stage.

## 4. Stage D — instantaneous vs finite-history explanatory test

This is the key physics audit.

Target 1:
predict CH4 enhancement / hit at t+10 s and t+30 s.

Models use identical held-out-flight splits:

M0 CURRENT:
- current xyz
- current CH4
- current U,V,W
- d_shore / context if available

M1 HAND-HISTORY:
M0 plus fixed history summaries over 10/30/60 s:
- CH4 mean/std/max
- hit fraction
- time since last hit
- whiff/blank age
- integrated wind-relative displacement
- wind mean/variance/direction persistence

M2 SEQUENCE:
small GRU/LSTM on the same raw 60-s history.
Only run M2 after M0/M1.

Primary question:
Does finite history improve held-out-flight future CH4/hit prediction over current state alone?

Metrics:
- Brier/NLL for hit
- MAE/RMSE for log CH4 enhancement
- per-flight improvement
- bootstrap by flight, not sample

Run separately:
- all data
- water
- transition
- land

Important interpretation:
A history gain proves only that local observation dynamics are non-Markovian/predictive at the available sampling level. It does NOT prove a lake-breeze mechanism.

## 5. Stage E — independent source-evidence audit

Read the validation spreadsheet and identify whether dissolved methane, floating chamber and ebullition records include spatial coordinates.

If coordinates exist:
- map independent source/evasion evidence into the same CRS
- define source-evidence zones without using UAV CH4
- compare atmospheric CH4 enhancement/hotspots to independent source evidence

Metrics:
- distance from atmospheric hotspot/ridge to independent high-flux zones
- posterior/rank mass in source-evidence zones for any later inversion
- spatial correlation only where measurement supports are comparable

If coordinates do not exist:
do not invent source truth. Treat the dataset as transport/field validation only.

## 6. Decision

REAL_LAGOON_GO only if all are true:
1. multiple independent flights provide meaningful water/transition/land coverage OR another defensible spatial water-boundary contrast;
2. synchronized CH4 + 3-D wind are usable;
3. finite-history M1 improves future CH4/hit prediction over M0 on held-out flights, with the direction replicated across multiple flights;
4. the effect is not solely an altitude or one-flight artifact;
5. independent source/evasion evidence can be spatially related to atmospheric measurements, or the limitation is explicitly accepted as transport-only validation.

REAL_LAGOON_HOLD if:
- the dataset is scientifically usable but shoreline coverage is too weak for a water-land mechanism;
- history predicts CH4 better but no source-localization truth exists;
- effects are flight-specific.

REAL_LAGOON_FAIL if:
- synchronization/wind quality is unusable;
- there is no meaningful methane plume structure;
- history does not improve held-out prediction and no spatial source relation can be formed.

## 7. What comes after GO/HOLD

If GO:
- use Lagoon Pingo as the real target-domain dataset;
- next audit Mackenzie natural point seep as the real localization-error dataset;
- only then design the first source-localization model.

If HOLD:
- keep Lagoon Pingo as real coastal methane external validation;
- do not force a shoreline mechanism;
- move the localization-mechanism test to Mackenzie / another natural point-source dataset.

Do not launch new CFD/GADEN before this audit is complete.
