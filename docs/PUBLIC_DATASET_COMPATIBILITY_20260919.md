# Public-Dataset Compatibility Audit — Remote-Paradigm Loop

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: DATA-INTERFACE QUALIFICATION, NOT PERFORMANCE EVIDENCE

## Purpose

A candidate innovation is rejected if it can only be defined on the private House01–03 setup.
The target method must accept sparse/trajectory measurements and return a source-location probability map on at least three physically different data regimes.

## D1 — VGR / GADEN

Verified public source:
- MAPIR VGR Olfaction Dataset.
- 30 detailed 3-D models of real houses.
- 120 CFD/gas-dispersion simulations (4 configurations per environment).
- GADEN / ROS integration, OpenFOAM outputs, geometry and configuration assets.

Use:
- training/development of sparse-trajectory encoder;
- cross-house and cross-wind splits;
- source map in each house's free-space grid.

Candidate compatibility:
- Predictive latent M1: PASS.
- Extreme-event M2: PASS.
- Structured source-region M3: PASS.

## D2 — TURB-Smoke 2026

Verified peer-reviewed source:
- Scientific Data 13, 428 (2026).
- fully resolved 3-D Navier–Stokes DNS.
- hundreds of millions of Lagrangian pollutant particles.
- five distinct point sources.
- turbulence with and without mean wind.
- particle positions + local flow velocities.
- coarse-grained 3-D and quasi-2-D concentration fields.

Scientific value:
- independent transport generator, not GADEN/OpenFOAM house CFD.
- source labels and concentration fields allow synthetic mobile-robot trajectories to be sampled without modifying the underlying DNS.
- ideal test of whether representation learns source evidence rather than VGR/GADEN fingerprints.

Candidate interface:
- sample fixed, preregistered trajectory families through the concentration field;
- local velocity can play the role of measured wind where required;
- source-map target = the five source positions embedded in the accessible plane/domain.

Compatibility:
- Predictive latent M1: PASS.
- Extreme-event M2: PASS; sparse/infrequent cue detection is an explicit dataset motivation.
- Structured region M3: PASS.

## D3 — ICASSP 2025 GSL Grand Challenge

Verified public challenge:
- DLR + TUM.
- real-world high-spatial-resolution in-situ concentration and wind measurements.
- controlled wind-tunnel setting.
- train / validation challenge data distributed through IEEE DataPort.

Use:
- independent real-measurement localization benchmark;
- no CFD simulator semantics required by the model interface.

Compatibility caveat:
- exact trajectory/time-series packaging must be audited before fixing the training protocol.
- if measurements are spatial scans rather than online robot histories, construct source-blind ordered paths only from provided measurement coordinates and acquisition time; do not invent unrecorded temporal dynamics.

## D4 — Red:Vapor / High-Resolution Wind-Tunnel Dataset 2026

Verified peer-reviewed source:
- Scientific Data 2026, *High-Resolution Wind Tunnel Dataset of Gas Sensor Responses to Vapor Plumes in Scale Model Landscapes*.
- 39 experimental runs listed in the repository overview.
- Sampling Experiments and Fly-Through Experiments are explicitly separated.
- records include wind speed, sampling time and setup metadata.
- repository contains dedicated fly-through experiments.

Use:
- primary simulator-to-real robustness test for trajectory-compatible inputs.
- especially suitable for M2 because real gas-sensor plume intermittency is retained rather than reconstructed from CFD.

Candidate compatibility:
- Predictive latent M1: PASS for fly-through sequences.
- M2: PASS.
- M3: PASS.
- static/sampling experiments can be auxiliary but must not be mixed with fly-through sequence semantics.

## 2026 direct collision that changes the novelty claim

Advanced Materials 2026:
- Zhang et al., *Receptor-Mimetic Stereo Olfaction for Simultaneous Odor Recognition and Spatial Localization* (AROMA).
- spatially separated receptor-mimetic sensors;
- time-varying onset/rise/amplitude plume dynamics;
- multi-task Transformer;
- unified latent representation;
- simultaneous mixture recognition and 3-D source localization;
- mobile-robot indoor demonstration under natural airflow.

Therefore the following are NOT novel enough:
- “use temporal plume dynamics”;
- “learn a latent representation for odor source localization”;
- “use a Transformer on plume sequences”.

The active candidate must be defended through:
1. source-blind predictive/self-supervised objective rather than supervised latent decoding;
2. a separately load-bearing extreme-event-aware constraint;
3. PMFS-compatible source probability field rather than direct coordinate regression;
4. heterogeneous VGR -> DNS -> real-wind-tunnel transfer;
5. destructive mechanism controls.

## Frozen cross-dataset interface

To avoid dataset-specific architecture changes, the proposed model interface is frozen at:

Per observation:
- timestamp or relative time;
- robot/sensor position;
- gas measurement;
- optional local wind (maskable if absent);
- optional sensor metadata.

Per environment:
- candidate/source-map coordinates or a free-space query set;
- optional occupancy/geometry context if consistently available.

Output:
- probability/logit at arbitrary source query coordinates;
- normalized source probability map;
- M3 calibrated spatial source region.

No module may require at deployment:
- full 3-D CFD field;
- future wind;
- simulator filament IDs;
- source truth;
- source-specific route selection.

## Decision

The current Predictive + Extreme-Event + Structured-Region 1+2 candidate is definable on all four verified data families.

Public-data compatibility is therefore NOT a current blocker.

Remaining blocker is mechanism novelty:
- M1 must beat direct/reconstruction/context-parroting baselines;
- M2 must add beyond ordinary intermittency features;
- M3 must retain nontrivial region size under real distribution shift.
