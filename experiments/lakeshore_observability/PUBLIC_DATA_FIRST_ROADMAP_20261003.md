# PUBLIC-DATA-FIRST ROADMAP AFTER REAL_LAGOON_HOLD
Date: 2026-10-03

## 0. Frozen interpretation

`REAL_LAGOON_HOLD` is a metadata/contract HOLD, not a dataset failure.
The 2024 Lagoon Pingo merged file is scientifically promising: 94 variables, 13 flight rows, synchronized-grid structure, CH4, UAV position, wind variables, and 7 explicit independent source/evasion coordinates in the validation workbook. But corrected wind is stored on `flight_frec` while CH4/position are on `flight`, and the publisher mapping/coordinate/time-correction contract is not yet verified. No temporal-lag or shoreline-mechanism inference is permitted until this is resolved.

Do not abandon the dataset. Do not force the mapping.

## 1. Thesis data strategy

Use public real datasets as the main evidence chain; use GADEN only for controlled ablation/replication after a real-data scientific problem is identified.

Roles:
1. `Lagoon Pingo 2024` — target-domain natural waterside methane / distributed-source and transport validation.
2. `Mackenzie Channel Seep 2 2025/2026` — natural point source in river-delta/wetland environment, known source coordinate, UAV CH4 + UAV wind + two ground wind references; real point-source localization/transport benchmark.
3. `van Hove et al. 2025/2026 Svalbard borehole` — direct UAV source-inference predecessor, known source, lawnmower flight, CH4 1 Hz + motion-corrected 3-D wind 20 Hz; direct GSL baseline/data/code.
4. `Alaska rich fen 2026` — natural wetland CH4 + UAV 3-D wind + tower/chambers; transport/footprint validation, not primary point-source localization.

## 2. Dataset qualification matrix (must be completed before algorithm design)

For every dataset report:
- source truth type: exact point / source zone / independent flux evidence / none
- natural vs controlled source
- scene: waterside/wetland/industrial/open
- number of independent flights
- route design and whether source location was known when route was designed
- gas species and sampling rate
- UAV position and altitude convention
- local UAV wind; correction status; frame; units
- fixed/ground/background wind and measurement height
- time synchronization contract
- independent repeats
- license and exact download DOI
- whether localization error can be computed without circular ground truth
- whether plume shape/path can be evaluated

Output: `PUBLIC_DATASET_QUALIFICATION_MATRIX.csv` and `PUBLIC_DATASET_QUALIFICATION_REPORT_zh.md`.

## 3. Track A — unlock Lagoon Pingo

Do not run Stage C/D yet.

Actions:
1. Inspect full Zenodo record metadata and all listed files for processing notebooks/scripts/readmes that explain `flight` vs `flight_frec`.
2. Search the authors' publication/supplement/repositories for the exact processing code referenced by the record.
3. Search for explicit definitions of U/V/W vs ucorr/vcorr/wcorr, units, ENU/NED/body frame, yaw/motion correction, sensor delay and timezone.
4. If an authoritative mapping is found, record it verbatim in a provenance file and re-run the audit.
5. Only after the wind contract is proven, download the 2024 georeferenced imagery and build the water/shore/land mask.

Allowed outcome:
- `REAL_LAGOON_UNLOCKED`
- or keep `REAL_LAGOON_HOLD_METADATA_CONTRACT`.

No ordinal row matching without evidence.

## 4. Track B — Mackenzie natural point-source audit

Paper/data DOI: 10.5281/zenodo.20019779; source = Channel Seep 2 at 69.319583 N, 135.477520 W.

Important limitation: all four UAV curtain flights were intentionally positioned ~80 m and ~150 m downwind of the already-known seep. Therefore this dataset is NOT a source-blind autonomous-search benchmark.

It IS valuable for fixed-trajectory inverse localization and plume-transport evaluation because:
- exact natural point-source coordinate is known;
- 2 UAV platforms sample CH4;
- both UAV wind measurements are motion corrected;
- two fixed ground wind sensors near the seep are available (~1.5 m and ~2.7 m AGL);
- repeated near/far curtains permit source-receptor consistency checks.

Audit tasks:
- download full Zenodo dataset/code;
- reproduce paper figures/coordinate transform first;
- inventory CP-1/CP-2/OP-1/OP-2;
- identify raw and corrected wind variables;
- reconstruct plume enhancement coordinates relative to source;
- quantify how localization/back-projection changes when using: ground wind only, UAV local wind only, flight-mean wind, height-dependent wind;
- do not use source coordinate as input to the inversion; use it only for evaluation.

Metrics:
- source localization error from fixed curtain observations;
- uncertainty area / posterior rank where candidate grid is used;
- near-vs-far consistency;
- inferred plume centerline error;
- sensitivity to wind representation.

Decision:
`MACKENZIE_GO_REAL_POINT_SOURCE` if source can be reconstructed from public measurements/code without hidden information and results are stable across multiple flights/platforms.

## 5. Track C — van Hove direct GSL field-data audit

Paper: Environmental Data Science 2026, `Actively inferring methane sources with drones`.
Code: `https://github.com/AlouetteUiO/active`, including `drone_data`.

Field data:
- known Svalbard borehole source;
- DJI M300 RTK;
- Aeris methane 1 Hz;
- Trisonica 3-D wind 20 Hz, motion corrected;
- lawnmower over ~150 x 200 m at ~2/4/6 m AGL.

Audit goals:
- determine whether the public `drone_data` contains enough field measurements to run independent source-location inversion, not merely calibrate their synthetic nature run;
- reproduce their field-data preprocessing;
- run their Bayesian STE or the closest published fixed-path inference on the real field observations if technically valid;
- inventory exact priors and any source-dependent route design.

This dataset is the most direct predecessor and should become a mandatory baseline if usable.

## 6. Track D — Alaska rich-fen audit (secondary)

Use only for plume/footprint and source-region evidence.
Do not force point-source localization if source truth is distributed.

Primary questions:
- relation between UAV CH4, 3-D wind and footprint;
- what fixed tower wind/flux adds beyond UAV local measurements;
- whether spatial source-region evidence can validate plume/transport outputs.

## 7. Scientific-question selection gate

Do not choose the first-paper mother theory before Tracks A-C are audited.

After the audits, select ONE failure mechanism that appears in at least two independent real datasets.

Candidate mechanisms to test, not assume:
A. local/mean wind representation causes systematic source-location bias;
B. source location is stable but plume centerline/support varies strongly across flights;
C. finite history improves source evidence beyond instantaneous measurements;
D. vertical/height-dependent wind changes inferred source-receptor geometry;
E. sensor response/background selection dominates plume/source inference.

The first-paper scientific problem must be supported by >=2 real datasets OR 1 real dataset + one controlled GADEN confirmation.

## 8. Public-data-first first-paper benchmark

Primary task: source localization.
Secondary tasks: plume centerline/path, effective support/shape, future concentration/hit where ground truth permits.

Primary real-data test set, if qualification passes:
- van Hove Svalbard borehole — direct GSL;
- Mackenzie natural seep — fixed-path point-source inversion;
- Lagoon Pingo — target-domain waterside external validation/source-zone consistency;
- GADEN — controlled repeated seeds and ablations only.

Do not claim all datasets measure the same endpoint. Report dataset-specific valid endpoints.

## 9. Immediate execution order

1. Keep Lagoon on HOLD and try only to unlock metadata/processing provenance.
2. In parallel download and audit Mackenzie.
3. In parallel audit `AlouetteUiO/active/drone_data` and reproduce the direct predecessor.
4. Build the qualification matrix.
5. Only after those results, decide the main scientific mechanism and algorithm.
6. Then update the opening report.

Do not start new CFD, large GADEN generation, PMFS closed loop, or multi-UAV experiments before step 5.