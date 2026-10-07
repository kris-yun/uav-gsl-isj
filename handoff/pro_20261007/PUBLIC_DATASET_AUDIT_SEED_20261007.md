# Public dataset audit — seed list for Pro

This is a preliminary qualification list, not the final dataset review.

## 1. Lagoon Pingo / Svalbard atmospheric drone data — strongest lakeshore/water-adjacent mechanism candidate

Zenodo: **Lagoon Pingo atmospheric drone measurements and validation data** (2026)

Contains:
- drone methane concentration (Aeris Mira Strato);
- corrected 3D wind components (Trisonica Sphere);
- DJI M300 RTK flight log;
- processed merged/synchronized data;
- water-body methane / flux-chamber validation;
- public processing code.

Role:
- valuable external evidence for UAV methane + 3D wind + water-associated source environment;
- can validate transport/met observation chain.

Limitation:
- natural/open-system pingo/lake emissions, not a clean blind controlled point-source localization benchmark.
- do not use as the sole source-coordinate localization ground truth without a source-geometry contract.

Status: **MECHANISM/OBSERVATION VALIDATION — HOLD for strict GSL benchmark.**

## 2. WiscoDISCO / Lake Michigan shoreline campaigns

Public UAS/lidar datasets include:
- RAAVEN temperature/humidity/3D winds;
- DJI M210 temperature/humidity/ozone profiles;
- Doppler lidar wind profiler;
- shoreline lake-breeze episodes.

Role:
- strong lakeshore meteorological/vertical-structure evidence;
- useful to bound controlled FSR forcing and validate physical plausibility.

Limitation:
- ozone/lake-breeze campaign, no controlled unknown point gas source for GSL.

Status: **LAKESHORE METEOROLOGY VALIDATION ONLY.**

## 3. Blackpool controlled methane release UAV campaign

Zenodo 3708518.

Contains:
- controlled methane release;
- two UAV sampling platforms;
- UAV position;
- methane mole fraction;
- onboard/stationary wind;
- temperature/pressure/RH;
- derived wind-height profiles.

Role:
- high-value public external UAV methane release dataset.

Limitation:
- not a lakeshore environment.

Status: **EXTERNAL GSL / SOURCE-TERM VALIDATION CANDIDATE, NON-LAKESHORE.**

## 4. UC Merced Vernal Pools controlled methane localization dataset

Dryad DOI: 10.5061/dryad.cnp5hqcgx (published 2025, experiment 2017)

Contains:
- controlled point source with published coordinates;
- 27 sUAS flights;
- onboard open-path methane observations;
- stationary anemometer wind;
- varied source rates.

Role:
- very useful public source-localization/quantification benchmark.

Limitation:
- grassland reserve, not lakeshore;
- mostly local wind rather than dense 3D flow.

Status: **PUBLIC UAV GSL BENCHMARK CANDIDATE, NON-LAKESHORE.**

## 5. PG&E Livermore controlled-release sUAS dataset

Dryad DOI: 10.5061/dryad.h44j0zpxh (published 2025, experiment 2017)

Contains:
- sUAS trajectory;
- methane concentration;
- local wind speed/direction;
- controlled source configurations, including blind/shared experiments;
- complex facility/building setting.

Role:
- strong cross-scene external benchmark for source determination.

Limitation:
- not lakeshore;
- source configuration may need recovery from thesis/book metadata.

Status: **PUBLIC COMPLEX-SCENE UAV GSL BENCHMARK CANDIDATE.**

## Interim dataset strategy

Do not wait for a perfect public lakeshore leak dataset.

Use a three-level evidence structure:

1. **FSR** — main paper-specific lakeshore benchmark:
   real-site geometry + controlled physically-supported forcing + known source truth.

2. **Public controlled-release UAV dataset** — real GSL external validation:
   Merced / PG&E / Blackpool candidates.

3. **Public shoreline atmospheric dataset** — physical realism / mechanism validation:
   WiscoDISCO and/or Lagoon Pingo.

This is stronger than forcing one dataset to satisfy every role.

## Pro follow-up
For every dataset, verify:
- exact license;
- source coordinate quality;
- synchronized timestamp contract;
- wind measurement location/height;
- raw vs processed data;
- flight paths;
- source rate/time;
- missing values;
- whether source labels are visible to the original flight team;
- whether it is suitable for fair algorithm comparison.
