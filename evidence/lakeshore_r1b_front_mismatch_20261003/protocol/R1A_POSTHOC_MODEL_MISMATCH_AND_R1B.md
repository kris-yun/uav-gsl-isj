# R1A 深度复核：由“垂直抬升”转向“湖风锋空间失配/源距离压缩”候选机制
日期：2026-10-03

## 1. 冻结结论

原判定保持：
- `R1_HOLD_WEAK_OR_UNSTABLE`
- `R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION`

明确 STOP：
- “湖风锋垂直抬升是30 m源信息层的必要机制”
- “source-x -> R30 是湖风锋专属规律”
- 原 `R1_1_ELEVATED_LAYER_FOLLOWUP`
- 原 R2 垂直主动探测

这些结果不再作为主线候选。

## 2. R1A 的核心因果拆解

r=10, z=30 m:

| scene | Top1 | median Brier margin |
|---|---:|---:|
| C06 uniform slow | 100% | 0.12665 |
| C08 uniform slow | 100% | 0.09045 |
| S06 path-profile matched | 100% | 0.12646 |
| S08 path-profile matched | 100% | 0.09132 |
| H1 exact F1 horizontal field, w=0 | 100% | 0.07739 |
| H2 exact F2 horizontal field, w=0 | 100% | 0.04049 |
| F1 full | 100% | 0.06774 |
| F2 full | 100% | 0.04512 |

F1-C06 paired mean margin increment = -0.02256; 95% seed-cluster bootstrap [-0.02792,-0.01686].
F2-C08 = -0.06892; [-0.07540,-0.06239].
F1-H1 = -0.00543; [-0.00661,-0.00441].
F2-H2 = +0.00055; [-0.00144,+0.00255].

Interpretation:
- slow residence / existing GADEN gas physics alone is sufficient for 30 m source information;
- vertical w does not provide necessary source-identifiability gain;
- full front often reduces margin relative to matched slow uniform controls.

## 3. Two additional limitations

### 3.1 Current task uses methane
Current frozen config uses methane. Slow advection gives the native gas model more time for its built-in filament spreading/random motion and gas-specific vertical physics to act. Therefore elevated information cannot be generalized to VOC/hazardous gas without gas-species sensitivity.

### 3.2 Current M4 is close to an oracle-scene classifier
The original M4 score:
- builds source templates and tests held-out seeds within the same environment;
- evaluates each release level separately.

Therefore it asks:
“if the exact environment family and release level are known, are source fingerprints separable?”

It does **not** directly ask:
“if a conventional model does not know the lake-front spatial structure or release rate, will it mislocalize?”

This explains why many 10 m/30 m Top1 values saturate at 100%.

## 4. Post-hoc exploratory rescoring of the delivered 1,944 realizations

The following was not preregistered and MUST NOT be used to retroactively change R1/R1A decisions.

New score:
- truth = full F1/F2 observation;
- nuisance release = unknown, templates pooled over r=5/10/20;
- paired seed excluded from the template;
- compare three model families:
  1. matched-speed uniform C06/C08;
  2. exact horizontal-field diagnostic H1/H2;
  3. oracle full F1/F2.

### 4.1 10 m, 300 s, threshold 0.001 ppm

| truth | inference model | Top1 | mean candidate error |
|---|---|---:|---:|
| F1 | oracle F1 | 100% | 0 m |
| F1 | H1 horizontal field | 100% | 0 m |
| F1 | uniform C06 | 82.41% | 5.28 m |
| F2 | oracle F2 | 100% | 0 m |
| F2 | H2 horizontal field | 100% | 0 m |
| F2 | uniform C08 | 70.83% | 8.75 m |

Candidate x spacing is 30 m, so nonzero mean error is caused by a subset of systematic one-cell mislocalizations rather than small continuous deviations.

### 4.2 30 m, 300 s

| truth | inference model | Top1 | mean candidate error |
|---|---|---:|---:|
| F1 | oracle F1 | 100% | 0 m |
| F1 | H1 | 93.98% | 1.81 m |
| F1 | uniform C06 | 69.44% | 9.17 m |
| F2 | oracle F2 | 92.13% | 2.36 m |
| F2 | H2 | 74.07% | 7.78 m |
| F2 | uniform C08 | 69.44% | 9.17 m |

30 m remains secondary because gas-species/residence effects are confounded.

### 4.3 Threshold robustness of the 10 m mismatch

F1 truth scored with C06:
- 0.5x threshold: Top1 78.70%, mean error 6.39 m
- 1.0x: 82.41%, 5.28 m
- 2.0x: 81.02%, 5.69 m

F2 truth scored with C08:
- 0.5x: 70.37%, 8.89 m
- 1.0x: 70.83%, 8.75 m
- 2.0x: 75.00%, 7.50 m

The exploratory mismatch is not a single-threshold artifact.

### 4.4 Source-specific systematic bias

At z=10 m with pooled release:

F2 truth, C08 inference:
- true source x=20 -> inferred x=50 in 87.5% of trials;
- true x=50 -> x=50 in 100%;
- true x=80 -> x=80 in 100%.

F1 truth, C06 inference:
- true x=20 -> inferred x=50 in 52.8%;
- x=50 and x=80 remain correct.

At z=30 m:
- F2 true x=20 -> x=50 in 84.7%;
- F1 true x=50 -> x=80 in 66.7%.

This is a **directional downstream bias**, not random confusion.

## 5. New candidate mechanism

Tentative internal name only:

**Front-induced source-range compression / 湖风锋诱导的源距离压缩偏差**

Physical interpretation to test:
- a lake-breeze front creates a cross-shore, spatially nonuniform horizontal velocity structure;
- a source plume generated through that structure can resemble a nearer/downstream source when interpreted with a homogeneous or path-mean wind model;
- local/path-mean wind is therefore insufficient even when its average speed is matched;
- the result is systematic downstream source-position bias.

The key decomposition signal is:
- C/S do not contain x-dependent front structure and mislocalize;
- H contains the exact x-dependent horizontal structure and restores 10 m source identity;
- adding/removing w changes the 30 m layer but is not necessary at 10 m.

H is a nonphysical diagnostic, so it does not prove the mechanism. It only identifies the next factor that needs a physically self-consistent confirmatory test.

## 6. R1B confirmatory experiment: FRONT_SPATIAL_MISMATCH

### 6.1 Goal
Confirm whether a **physically self-consistent full front field** causes a systematic source-location bias when the inference model only knows matched local/path-mean wind, and whether that bias tracks the front position.

No new localization algorithm in this phase.

### 6.2 Truth scenes
Use only divergence-consistent full fields.

Three front locations:
- XF90
- XF120
- XF150

Two frozen strengths:
- moderate = original F1 family
- strong = original F2 family

Controls for every front:
- uniform matched-speed control;
- x-invariant path-profile matched control.

Do not use H fields as physical controls; H remains diagnostic only.

### 6.3 Source grid
Primary confirmatory grid:
- retain the existing 9 sources first, so current post-hoc effect can be independently reproduced;
- source x={20,50,80}, y={-20,0,20} m.

Do not densify before this gate.

### 6.4 Seeds and gas
- entirely new plume seeds: 32001–32008;
- release levels 5/10/20 all generated;
- inference must treat release as unknown nuisance (equal-prior marginalization unless a separately frozen prior is justified).

Primary gas may remain methane for exact replication, but before any general lake-GSL claim, repeat a compact robustness subset with at least one neutral/heavier gas supported by the frozen GADEN gas library. Do not invent gas properties manually.

### 6.5 Observation
Primary:
- z=10 m;
- 30/60/120/300 s prefixes;
- same XY path.

Secondary:
- z=30 m only.

Drop 60/100 m from primary analysis.

### 6.6 Inference arms
For each truth front scene:

A. **Uniform-matched baseline**
Uses templates from the matched uniform-speed control.

B. **Path-profile baseline**
Uses x-invariant, height-profile matched templates.

C. **Oracle-front diagnostic**
Uses correct full-front templates, leave-one-seed-out.

Optional D only after A-C:
wrong-front-location templates (e.g. truth XF90 scored with XF150) to test front-location sensitivity.

No PMFS yet.

### 6.7 Primary endpoint
At 10 m, release-marginalized:

`front mismatch penalty = Oracle Top1 - Uniform/PathProfile Top1`

and:
- candidate Euclidean error;
- fraction of nonzero errors;
- signed x bias `pred_x - true_x`;
- true-source rank;
- Brier margin.

### 6.8 PASS gate
For at least 4/6 {front location x strength} truth scenes:

1. Oracle Top1 >= 90%;
2. Uniform or path-profile baseline is >=20 percentage points worse than Oracle;
3. mean candidate error >=5 m OR >=20% trials have nonzero candidate error;
4. among errors, >=70% have the same signed x direction;
5. the source-x region most affected shifts consistently when x_front is moved 90 ->120 ->150, i.e. bias is tied to source-front relative geometry rather than absolute x alone;
6. >=6/8 new seeds show the same mismatch direction.

Negative control:
matched uniform truth scored by matched uniform model must remain >=90% Top1.

Decision:
- `R1B_PASS_FRONT_SPATIAL_MISMATCH`
- `R1B_HOLD_MISMATCH_NOT_FRONT_LOCKED`
- `R1B_FAIL_STOP_FRONT_MISMATCH`

### 6.9 Interpretation rules
PASS supports only:
“front-like spatially nonuniform flow can systematically bias source location when interpreted by homogeneous/path-mean wind assumptions, and the bias follows front-relative geometry.”

It does NOT yet support:
- quantitative real-lake error;
- vertical uplift mainline;
- active-sensing benefit;
- final method novelty.

If PASS, next step is high-fidelity thermally driven lake-front CFD/LES (not another hand-tuned parametric field) using Wisco/JGR/FastEddy-informed boundary conditions. Only after high-fidelity replication should the final inference/active-sensing method be designed.

## 7. Implication for bio-inspired active sensing

Do not use vertical probing as the default action.

If R1B passes, the biologically inspired mechanism should be reframed as:
**diagnostic cross-front / cross-shore active sensing**.

The UAV intentionally takes a short cross-shore/cross-front probe to determine whether the current odor evidence is being compressed/warped by the front before committing to a source range estimate.

This is closer to active sensing than “algorithm switching,” but it remains a candidate only after R1B and high-fidelity validation.
