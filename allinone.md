# 2026 causal-theory search for PMFS CORE-M1

Search window: 2026. Queries covered adaptive interventions, sequential
decision-making, nuisance invariance, interventional contrast and causal
representation learning. The local multi-source search returned 106 unique
records (arXiv 24, OpenAlex 36, Semantic Scholar 24, Crossref 36; 14 duplicates
merged); DBLP and OpenReview returned no hits for the broad query. Semantic
Scholar repeatedly returned HTTP 429 for one query, arXiv had one SSL EOF, and
DBLP returned JSON parse errors. Manual checking against first-party publisher
pages retained the three records below; 103 clearly unrelated or non-venue
records were filtered out.

| # | Title | Date | Venue | Why retained | Source |
|---|---|---|---|---|---|
| 1 | Toward Interpretable Deep Generative Models via Causal Representation Learning | 2026-04 | JASA 121(553) | Current top-journal synthesis of intervention, latent representation and identifiability boundaries | <https://doi.org/10.1080/01621459.2026.2620154> |
| 2 | Intervening to learn and compose causally disentangled representations | 2026-04 | CLeaR 2026, PMLR 323 | Context-separated intervention mechanism plus an identifiability result | <https://proceedings.mlr.press/v323/markham26a.html> |
| 3 | Partial Causal Structure Learning for Valid Selective Conformal Inference under Interventions | 2026-08 | UAI 2026, PMLR 337 | Learns only task-relevant intervention-target relations and quantifies invariance-set errors | <https://proceedings.mlr.press/v337/asiaee26b.html> |

## Overview

The relevant 2026 literature does not provide a ready-made gas-localization
estimator. It consistently requires explicit interventions, explicit invariance
or context assumptions, and a sharply bounded identifiability claim.

## Trends

The shift is from attaching causal language to predictive robustness toward
finite-sample, intervention-indexed claims with explicit failure conditions.
Specialized causal-learning venues and top statistics journals emphasize that
heterogeneity helps only when the preserved or changed mechanisms are stated.

## Key themes

1. Interventions provide extra structure, but do not remove the need for
   assumptions (1, 2).
2. Context separation can isolate intervention-responsive factors (2).
3. Partial, downstream-specific causal structure is more defensible than a
   universal causal graph claim (3).

## Keywords frequency

| Keyword | Count |
|---|---:|
| causal | 3 |
| intervention | 2 |
| representation | 2 |
| identifiability | 2 |
| invariance/context | 2 |

## Most cited by accepted paper

Fresh 2026 citation counts are too immature and inconsistent across indexes to
rank responsibly; venue and methodological fit are used instead.

## Most cited by first author

Not reported because the 2026 citation window is incomplete and would be
misleading.

## Recommendations for reading

Read Moran and Aragam first for the claim boundary, Markham et al. for the
intervention/context construction, then Asiaee et al. for falsification of an
incorrect invariance set. CORE-M1 uses these principles but relies on its own
task-specific log-odds cancellation proposition and closed-loop validation.



---


# 2026 literature search report: single-channel source evidence

Search date: 2026-09-13. Year filter: 2026 only. Queries: spatial dither and
lock-in gradient estimation; coded excitation with sensor latency; phase-
sensitive moving-sensor source localization.

API results: arXiv 0, OpenAlex 24, DBLP 0; 24 unique records; 18 records were
filtered as clearly unrelated after title-and-abstract review. The unfiltered
records with available abstracts are in
`experiments/single_channel_worl_v1/literature/paper_search_2026_raw.json`.
Connector failures are preserved in `paper_search_errors.txt`.

| # | Title | Venue | Why retained | Source |
|---:|---|---|---|---|
| 1 | Accurate hazardous gas detection under uncertain disturbing environment with multi-fusion model combined with artificial olfactory system | Journal of Safety Science and Resilience | 2026 gas sensing under environmental interference; requires multi-sensor learning and is therefore a boundary, not a deployable module | https://doi.org/10.1016/j.jnlssr.2026.100296 |
| 2 | Artificial intelligence-enabled MOS gas sensors: Towards Selective and intelligent detection in complex environments | Sensors and Actuators A: Physical | 2026 gas-sensor review; abstract absent in API record, retained under the when-unsure-keep rule | https://doi.org/10.1016/j.sna.2026.117502 |
| 3 | Pre-Ignition Source Localization using a 3D Network of Semiconducting Metal Oxide Gas Sensors | SSRN Electronic Journal | source localization, but simultaneous sensor network violates the one-UAV contract | https://doi.org/10.2139/ssrn.6137229 |
| 4 | Event-Triggered Multivariable Newton-based Extremum Seeking | SSRN Electronic Journal | relevant collision for dither/extremum-seeking; abstract absent in API record | https://doi.org/10.2139/ssrn.6160080 |
| 5 | Prescribed-Time Newton Extremum Seeking Using Delays and Time-Periodic Gains | IEEE Transactions on Automatic Control | confirms perturbation/dither plus delay compensation is an established control direction, so spatial dither cannot be claimed broadly | https://doi.org/10.1109/TAC.2026.3660191 |
| 6 | Active-Sonar Navigation Enhanced by Delay-compensated Sliding Window Without In-Situ Sound Speed Measurement | IEEE Transactions on Instrumentation and Measurement | distant-field analogue for jointly profiling propagation delay in a local trajectory window | https://doi.org/10.1109/TIM.2026.3655926 |

Primary-page verification added four higher-signal papers missed or incompletely
described by the API query:

| # | Title | Venue | Transfer used here | Primary page |
|---:|---|---|---|---|
| 7 | Calibration-Free Gas Source Localization with Mobile Robots: Source Term Estimation Based on Concentration Measurement Ranking | ICRA 2026 | empirical ranks remove unknown positive monotone sensor calibration; exact global EDF is a comparator | https://arxiv.org/abs/2605.13208 |
| 8 | Advanced electronic noses for future robotic olfaction | npj Robotics 4:11 | explicitly model gas-sensor hysteresis/recovery and synchronize sensor time with motion | https://www.nature.com/articles/s44182-025-00071-y |
| 9 | Revisiting Optimal Coding for I-ToF under Practical Sensor Constraints | CVPR 2026 | constrain inference by actual hardware bandwidth and timing before optimization | https://openaccess.thecvf.com/content/CVPR2026/html/Luo_Revisiting_Optimal_Coding_for_I-ToF_under_Practical_Sensor_Constraints_CVPR_2026_paper.html |
| 10 | A flexible and room-temperature operatable gas sensor for robotic olfaction: selective detection of formic acid via UV excitation | npj Robotics 2026 | confirms active temporal modulation can create discriminative response structure, but requires different sensor hardware | https://www.nature.com/articles/s44182-026-00104-0 |

## Overview

The relevant 2026 corpus separates into three ideas: calibration-invariant
ordinal features; explicit sensor/propagation timing; and controlled excitation.
Only the first two fit the purchased diffusion-sampling, 1 Hz, single-VOC device.

## Trends

Robotic olfaction is moving toward explicit temporal models and real-world
sensor constraints. Control work treats dither and delay compensation as mature
tools. The strongest direct 2026 GSL result uses ranks to avoid calibration,
while the strongest distant-field analogue jointly estimates timing nuisance in
a sliding window.

## Key themes

1. **Monotone-invariant measurement features**: rank observations rather than
   trust absolute concentration (paper 7).
2. **Timing as a modeled nuisance**: slow sensor response and propagation delay
   must be aligned to platform motion (papers 6 and 8).
3. **Controlled excitation**: modulation can expose hidden properties, but the
   current detector has no intake actuator and spatial dither is prior art
   (papers 4, 5, 9 and 10).
4. **Extra hardware/data channels**: multi-sensor fusion can improve robustness
   but violates the frozen single-channel contract (papers 1 and 3).

## Keyword frequency in retained titles

| Keyword | Count |
|---|---:|
| sensor/sensing | 6 |
| source/localization | 3 |
| gas/olfaction | 5 |
| delay/time | 3 |
| active | 3 |

## Most cited accepted papers

Fresh 2026 records have incomplete citation counts; the API returned zero or
missing counts for the retained set. A numeric top-five table would invent a
ranking and is therefore omitted.

## Most cited first authors

The same missing 2026 citation metadata prevents a defensible author ranking.

## Recommended reading path

1. Jin et al. (ICRA 2026): closest deployable baseline and exact ownership
   boundary for global EDF ranking.
2. Zhang et al. (npj Robotics 2026): gas-specific timing and synchronization
   requirements.
3. Active-sonar delay-compensated sliding window (IEEE TIM 2026): distant-field
   nuisance-profiling analogue.
4. Luo et al. (CVPR 2026): hardware-constrained inference-design principle.

The resulting one-mechanism hypothesis is TAORL: within-window ordinal source
evidence, a hardware-bounded sensor time constant, and a reverse-time negative
control. It is preregistered for one H03 run; failure retires the route.

---

# TROQL external-dataset search, 2010–2026

Date: 2026-09-14

## Search protocol

Three queries targeting public gas-source-localization datasets, known source
geometry, repeated experiments, and wind/transport variation were run across
Semantic Scholar, OpenAlex, arXiv, OpenReview, Crossref, and DBLP. The raw merged
response is preserved in `paper_search_troql_external_dataset_2010_2026.json`.
OpenAlex returned 24 records, Crossref 24, and arXiv 8; Semantic Scholar was
rate-limited, DBLP encountered TLS errors, and OpenReview returned no records.

## Ranked relevant records and datasets

1. Burgués et al., *Gas distribution mapping and source localization using a 3D
   grid of metal oxide semiconductor sensors* (2019/2020), DOI
   <https://doi.org/10.1016/j.snb.2019.127309>. Public Orebro3DSEN real-sensor
   data; selected and scored under frozen V1/V2 gates.
2. Ojeda et al., *Robotic Gas Source Localization With Probabilistic Mapping and
   Online Dispersion Simulation* (2024), DOI
   <https://doi.org/10.1109/TRO.2024.3426368>. Closest online-PMFS context, but
   not a fresh external run-level confirmation asset.
3. Ojeda et al., *VGR Dataset* (2023), DOI
   <https://doi.org/10.1007/s10846-023-02012-z>. Public and large, but simulated
   and adjacent to the project evidence lineage.
4. Burgués et al., *Exploration and localization of a gas source with MOX gas
   sensors on a mobile robot* (2017), DOI
   <https://doi.org/10.1109/ISOEN.2017.7968898>. Relevant real-sensor study; no
   newly identified factorial raw asset.
5. Wada et al., *Collecting a Database for Studying Gas Distribution Mapping and
   Gas Source Localization with Mobile Robots* (2010), DOI
   <https://doi.org/10.1299/jsmeicam.2010.5.183>. No current auditable download
   satisfying the factor contract was located.
6. Vergara et al., turbulent wind-tunnel gas-sensor dataset (2015), DOI
   <https://doi.org/10.1016/j.dib.2015.02.014>. The two source positions emit
   different gases, confounding position with analyte identity.
7. GSL-Bench (2024), DOI
   <https://doi.org/10.1109/ICRA57147.2024.10610755>. High-fidelity simulation,
   not untouched real-sensor confirmation.
8. Gongora et al., human gas-source-localization dataset (2017), DOI
   <https://doi.org/10.1109/ISOEN.2017.7968899>. Simulator-derived and its original
   dataset URL is no longer available.
9. Hinsen et al., *Red:Vapor* (2026),
   <https://zenodo.org/records/18299926>. Real transport repeats but one fixed
   physical source; input-contract NO-GO.
10. France et al., *Chasing Ghosts* (2026),
    <https://arxiv.org/abs/2602.19577>. Reports two rooms and five real runs per
    room, but current public repository lacks the raw flight sensor logs.
11. Jin et al., *Towards Efficient Gas Leak Detection in Built Environments*
    (2023), DOI <https://doi.org/10.1109/ICRA48891.2023.10160816>. Reports 24 real
    experiments; no public run-level raw series was located.

## Search conclusion

Orebro3DSEN was the only located, currently downloadable real-sensor dataset
supporting both a strong same-source nuisance control and a different-source edge
without analyte confounding. Its untouched V2 confirmation failed one frozen
per-direction effect-size requirement. No second certifiably untouched public
asset satisfying the full factor contract was found. This is a data and
identification boundary, not evidence of universal mechanism success or failure.

