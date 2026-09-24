# Project Handoff for Second Pro — 2026-09-24

Repository: `kris-yun/uav-gsl-isj`

Coordination branch for reading/planning only:
`research/pro6-sync-handoff-20260924`

This branch was created from:
`27087e158fe709c905c22eb9e65280223d68fb7d`

The active scientific execution branch is:
`research/path-action-source-inference-v0`

**Do not push to the active PASI branch while Codex is executing the fresh S3 gate.**

---

## 1. Research objective

The project is UAV gas source localization (GSL) with GADEN simulation first and real-flight validation later.

The paper target is one publishable main scientific innovation plus two auxiliary innovations.

Hard requirements:

- preserve the PMFS-style **source-location probability map** as the final representation/output;
- internal inference may be radically redesigned;
- main innovation must come from a clearly identifiable far-domain scientific mother theory, preferably 2025/2026;
- avoid small engineering patches;
- avoid generic Bayesian/statistical tuning, SBI, and ordinary experimental-design contributions;
- first prove an offline source-identification mechanism;
- only then derive the second-order innovation and code;
- only after offline confirmation authorize Codex closed-loop experiments;
- require cross-source and cross-environment evidence;
- record STOP/HOLD/NO-GO explicitly and never rescue a failed frozen gate by post-hoc tuning.

The current bottleneck is no longer “make the plume forward model more accurate.”

The accumulated evidence says that **stochastic plume realization variability is strongly source/location conditioned**, so a representation that is robust for one source can destroy useful information for another.

---

## 2. Frozen data / benchmark facts

Primary simulator: GADEN.

Houses:
- House01 / H01
- House02 / H02
- House03 / H03

Common search budget: 300 s.

House02 frozen W2:
- wind name: `3,5-1_slow`
- GADEN binary SHA256:
  `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`
- occupancy SHA256:
  `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`
- W2 wind_iteration_1 SHA256:
  `54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8`
- extractor SHA256:
  `206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91`

Frozen House02 arbitrary-source bank:
- 630 free PMFS support cells;
- prediction seeds:
  - C = `2026092401`
  - D = `2026092402`
- 10 frozen times;
- 30 frozen pooled probes;
- exact source→sensor predictions already exist and are reusable infrastructure.

Important contract:
historical HCMC House02 replays used W1=`3,5-1_fast`; they are **not** valid W2 plume evidence. Their candidate manifest may be reused for geometry only.

---

## 3. The key empirical discovery that should guide all future work

Across all 630 source hypotheses, independent C/D plume-realization variability is strongly source dependent.

Approximate relative C/D discrepancy distribution:
- minimum ~1.5%
- 25th percentile ~9.3%
- median ~15.3%
- 75th percentile ~24.4%
- 90th percentile ~34.5%
- maximum ~57.5%

Relative variability is negatively associated with mean observed plume mass:
Spearman approximately `-0.50`.

Two important source regimes already exposed:

### S1
`(-2.242730141, -2.200880051, 0.20)`

Low stochastic variability:
- target A/B raw relative L2 ~8.1%
- raw exact-forward ranks were 1/1.

Absolute concentration was useful source information.

### S2
`(-4.342730045, 2.899120331, 0.20)`

More stochastic:
- target A/B raw relative L2 ~21.2%
- Gate1A exact-forward ranks A/B = 1/7.

Here absolute amplitude behaved much more like realization nuisance.

Therefore:

> There is no globally valid rule saying “absolute plume mass is signal” or “absolute plume mass is nuisance.”

The next successful method must model **source-conditioned stochastic uncertainty**, not delete one observable component globally.

---

## 4. Current active candidate: PASI

Working name:
**Source-Conditioned Stochastic Path Action / Path-Action Source Inference (PASI)**.

Mother-theory direction:
nonequilibrium statistical physics / stochastic path probability / Onsager–Machlup and large-deviation action ideas.

Core shift:

Instead of:
`source -> one mean plume -> distance to observation`

use:
`source -> source-conditioned stochastic path distribution -> probability/action of the entire observed path`.

Frozen exploratory proxy for candidate source (s):

[
\mu_{s,k}=\frac{x^C_{s,k}+x^D_{s,k}}{2}
]

[
v^{local}_{s,k}=\frac{(x^C_{s,k}-x^D_{s,k})^2}{2}
]

[
\bar v_k=\frac{1}{N}\sum_s v^{local}_{s,k}
]

[
v_{s,k}=v^{local}_{s,k}+\bar v_k
]

[
A(s;y)=\sum_k
\left[
\frac{(y_k-\mu_{s,k})^2}{v_{s,k}+10^{-12}}
+\log(v_{s,k}+10^{-12})
\right].
]

No mass normalization is used.

Interpretation:
- low-noise source/path component -> deviations penalized strongly;
- high-noise component -> deviations discounted appropriately;
- the log-variance term prevents the model from winning by assigning arbitrarily large uncertainty.

Exploratory discovery data only:
S1_A, S1_B, S2_A, S2_B all had path-action truth rank 1.
This is **not confirmation**, because the formula was discovered after inspecting those cases.

---

## 5. Current fresh confirmation gate — S3

S3 was selected before generating new target data.

Selection rule:
- exclude source candidates within 2 m of S1 or S2;
- among remaining candidates select the one closest to the 630-source median in both:
  - C/D relative realization discrepancy;
  - log mean plume mass.

Frozen S3:

- source id: `pmfs_3_12`
- xyz: `(-4.342730045, -3.700880051, 0.20)`
- C/D relative discrepancy ~15.39%
- global median ~15.27%
- distance from S1 ~2.58 m
- distance from S2 6.60 m

Fresh targets:
- S3_W2_E seed `2026092403`
- S3_W2_F seed `2026092404`

Active branch:
`research/path-action-source-inference-v0`

Frozen execution handoff:
`CODEX_PASI_D0_S3_HANDOFF_20260924.md`

Theory/contract freeze:
`01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md`

Scorer:
`research/path_action_source_inference_v0/score_pasi_d0_s3.py`

Runner:
`research/path_action_source_inference_v0/run_pasi_d0_s3_w2_vm.sh`

Package script:
`research/path_action_source_inference_v0/package_pasi_d0_s3_review.sh`

At the time this handoff was written, Codex is already executing this fresh S3 gate.

**Do not duplicate S3 or change its formula.**

Frozen outcomes:

PASS:
`PASI_D0_PASS_FRESH_S3_PATH_ACTION_SIGNAL`

FAIL:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

No rescue after result reveal.

---

## 6. What the second Pro should do now

While Codex runs S3, do **not** run a competing scientific experiment on the same gate.

Use the second Pro for independent work that cannot contaminate S3:

1. audit the PASI scientific argument;
2. search 2025/2026 far-domain literature for path-action / path-space inference / state-dependent stochasticity / large-deviation source-conditioned likelihood;
3. establish a precise prior-art boundary versus:
   - ordinary heteroscedastic Gaussian likelihood;
   - generalized least squares;
   - Mahalanobis scoring;
   - Gaussian processes;
   - stochastic plume ensemble likelihood;
   - Onsager–Machlup parameter inference;
   - source localization work that already uses ensemble uncertainty;
4. challenge whether the current diagonal action proxy is genuinely a second-order adaptation of a big theory or only a standard heteroscedastic NLL;
5. derive what a **real paper-level PASI** would need if S3 passes:
   - path-level temporal dependence, not just diagonal features;
   - source-conditioned stochastic geometry;
   - online approximation compatible with PMFS;
   - an auxiliary module architecture;
6. formulate the next frozen gate, but do not execute it before S3 is independently reviewed;
7. if S3 fails, propose the next far-domain route using the hard empirical constraint:
   **source-conditioned heteroscedastic stochastic path distributions**.

The second Pro must not restart old routes from scratch.

---

## 7. Immediate decision tree

### If S3 FAILS

Freeze:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`.

Do not:
- tune the global noise floor;
- change local variance;
- mix raw and normalized scores;
- pick another S3-like source to rescue the formula;
- train a neural model to fit the failed score.

Then use the 630-source heteroscedasticity result as the new scientific constraint and search the next mother theory.

### If S3 PASSES

First:
- independently recompute result from review package;
- verify package/target hashes;
- verify no contract drift.

Then authorize a D1 **second fresh source** chosen before target generation and deliberately in a different stochastic regime (e.g. low- or high-variability quantile), while keeping the path-action formula frozen.

Only after second-source confirmation:
- cross-wind or cross-House offline gate;
- then derive practical online approximation;
- only then PMFS closed loop.

A House02-only S3 PASS is not enough for a main-innovation claim.

---

## 8. Publication architecture if PASI ultimately survives

Tentative only:

### Main innovation
Source-conditioned stochastic path-action inference for PMFS source probability maps.

### Auxiliary innovation A
Efficient estimation / regularization of source-conditioned stochastic path geometry from sparse forward realizations.

### Auxiliary innovation B
Memory- or uncertainty-aware active observation/planning derived from the path-action geometry.

Do not build auxiliary modules before the main offline mechanism survives cross-environment testing.

---

## 9. Non-negotiable process rules

- sequential scientific gates;
- no result-driven tuning;
- no closed loop before offline confirmation;
- no old idea relabeling;
- every claimed innovation must have explicit theoretical ancestry;
- every route must end in PASS/HOLD/STOP/NO-GO;
- freeze code + formulas + data provenance + commit hashes;
- preserve negative results;
- keep PMFS probability-map output.
