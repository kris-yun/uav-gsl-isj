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
