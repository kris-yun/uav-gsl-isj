# TAORL literature trace and transfer boundary

Date checked: 2026-09-13

## Direct 2026 anchor

Jin, Duranceau, Erünsal and Martinoli, **Calibration-Free Gas Source
Localization with Mobile Robots: Source Term Estimation Based on Concentration
Measurement Ranking**, ICRA 2026.

- Primary record: https://arxiv.org/abs/2605.13208
- Full HTML: https://arxiv.org/html/2605.13208
- Accepted-venue corroboration: https://www.epfl.ch/labs/disal/publications/year/
- Transfer: replace absolute concentration matching by empirical ranks.  This is
  invariant to an unknown positive monotone sensor calibration curve.
- Boundary: global EDF ranking itself belongs to Jin et al. and is implemented
  only as arm `ICRA2026_GLOBAL_EDF`.  TAORL cannot claim rank likelihood alone.
- Mismatch relevant here: their setting assumes a sufficiently developed
  steady plume and uses a 10 Hz MOX sensor; our purchased detector outputs 1 Hz
  and the H03 plume/trajectory is nonstationary.

## 2026 robotic-olfaction constraint

Zhang et al., **Advanced electronic noses for future robotic olfaction**,
npj Robotics 4, 11 (2026).

- Primary record: https://www.nature.com/articles/s44182-025-00071-y
- Transfer: mobile gas sensing needs an explicit timing layer for hysteresis,
  recovery and motion synchronization; sensing bandwidth must be co-designed
  with control and plume intermittency.
- Boundary: the article does not provide TAORL and does not establish source
  identifiability from a passive single channel.

## 2026 distant-field timing analogue

**Active-Sonar Navigation Enhanced by Delay-compensated Sliding Window Without
In-Situ Sound Speed Measurement**, IEEE Transactions on Instrumentation and
Measurement (2026), DOI 10.1109/TIM.2026.3655926.

- Primary record: https://doi.org/10.1109/TIM.2026.3655926
- Transfer: treat propagation/timing error as a nuisance jointly estimated in a
  sliding window instead of assuming a perfectly timed point observation.
- Boundary: acoustic two-way travel time, depth constraints and B-splines are
  not transferred.  TAORL transfers only the bounded delay/dynamics nuisance
  and local-window principle.

## 2026 hardware-constrained inference analogue

Luo et al., **Revisiting Optimal Coding for I-ToF under Practical Sensor
Constraints**, CVPR 2026, pp. 12501-12510.

- Primary record: https://openaccess.thecvf.com/content/CVPR2026/html/Luo_Revisiting_Optimal_Coding_for_I-ToF_under_Practical_Sensor_Constraints_CVPR_2026_paper.html
- Transfer: define the feasible inference family from measured hardware limits
  before optimizing the estimator.  TAORL therefore fixes its 1 Hz cadence and
  upper time constant from the FKT contract before H03 scoring.
- Boundary: illumination modulation and ToF demodulation are not transferred.

## Collision and novelty decision

Spatial dithering, gradient following, crosswind casting and extremum seeking
are established robot-source-search ideas; the project's paired-position and
distributed DPISC probes also failed on H03.  The proposed route therefore does
not claim UAV oscillation or gradient search.  Its candidate delta is narrower:

1. ordinal evidence is computed inside hardware-sized time windows;
2. a bounded first-order sensor timescale is profiled as a source-coupled
   nuisance;
3. the same candidate evidence is recomputed with an anti-causal filter;
4. the forward time arrow must beat that negative control before any causal
   language is allowed.

This delta is a hypothesis, not established novelty.  A H03 failure retires it
without tuning.

## Search audit

The installed `paper-search` CLI did not implement its documented `--json`
option.  A wrapper called the same search function and persisted the returned
abstracts.  arXiv returned HTTP 429/timeouts, DBLP returned invalid JSON, and
OpenAlex returned 24 records.  `paper_search_2026_raw.json` is the unfiltered
machine record.  Manual primary-page verification supplied the four anchors
above.  No unverified title is used as theory evidence.
