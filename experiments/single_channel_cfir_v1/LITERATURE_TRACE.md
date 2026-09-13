# CFIR 2026 literature trace

Checked: 2026-09-13.  Links point to primary publisher, author, or institutional
records.  The literature motivates individual principles; none is represented
as evidence that CFIR will work on this dataset.

## Statistical physics: time-arrow likelihood ratio

Miguel Aguilera, Sosuke Ito and Artemy Kolchinsky, **Inferring Entropy
Production in Many-Body Systems Using Nonequilibrium Maximum Entropy**,
Physical Review Letters 136, 077101 (2026), DOI `10.1103/xgkj-dxzh`.

- Author PDF:
  https://artemyk.github.io/assets/pdf/papers/AguileraItoKolchinsky_InferringEntropyProduction_PRL_2026.pdf
- Verified principle: trajectory irreversibility is expressed by a log ratio
  between forward and reverse path probabilities.
- CFIR transfer: replace an unpaired forward score by a paired
  chronological/reversed footprint log ratio for every candidate source.
- Boundary: CFIR is not thermodynamic entropy production.

## Turbulent inverse problems: backward/adjoint domain of dependence

Rui You, Bingquan Wang and Shiyu Zhu, **Scalar Source Localization Using
Multi-Sensor Domains of Dependence in Turbulent Channel Flow**, AIAA SciTech
2026, DOI `10.2514/6.2026-2343`.

- Author institutional record:
  https://pdxscholar.library.pdx.edu/mengin_fac/549/
- Verified principle: forward-adjoint duality converts sensor measurements into
  source-space domains of dependence for scalar-source localization.
- CFIR transfer: LMBT's backward Lagrangian kernels are treated as approximate
  candidate footprints before constructing the time-arrow ratio.
- Collision/boundary: the cited method uses multiple sensors and an idealized
  time-averaged setting.  CFIR has one moving channel, finite intermittent
  observations, sensor memory, and does not claim a new adjoint solver.

## Turbulence data science: intermittency is part of the signal

Luca Biferale et al., **TURB-Smoke: a 3D Eulerian-Lagrangian database for
turbulent transport and mixing**, Scientific Data 13, 428 (2026), DOI
`10.1038/s41597-026-06774-7`.

- Publisher page: https://www.nature.com/articles/s41597-026-06774-7
- Verified principle: turbulent scalar fields consist of correlated,
  intermittent puff/filament structures with non-Gaussian statistics.
- CFIR transfer: preserve whiff chronology and spatial transport footprints
  instead of treating 1 Hz concentration samples as independent Gaussian
  source responses.

## Coarse observation: claim boundary

Udo Seifert, **Universal bounds on entropy production from fluctuating
coarse-grained trajectories**, Nature Reviews Physics 8, 493-507 (2026), DOI
`10.1038/s42254-026-00954-5`.

- Publisher page: https://www.nature.com/articles/s42254-026-00954-5
- Verified principle: hidden degrees of freedom mean coarse trajectories expose
  bounded information about irreversibility.
- CFIR boundary: a forward-over-reverse footprint win is partial directional
  evidence, not proof that the full plume mechanism or real-flight source is
  identified.

## Pre-experiment rejection of two tempting transfers

1. **Closed control-volume flux inversion** was rejected because the frozen
   H03 path does not enclose the source or form a usable closed boundary, and
   the device does not measure the diffusive, storage, or vertical flux terms.
2. **Eddy-covariance gas/wind cofluctuation** was rejected because a moving
   1 Hz channel with a response time up to about 15 s cannot resolve the
   stationary high-frequency covariance assumed by that method.  A
   source-blind H03 preflight produced inconsistent directions rather than a
   stable source intersection.

These rejections occurred before CFIR outcome evaluation and prevent further
experiments on assumptions the present hardware and trajectory cannot satisfy.

