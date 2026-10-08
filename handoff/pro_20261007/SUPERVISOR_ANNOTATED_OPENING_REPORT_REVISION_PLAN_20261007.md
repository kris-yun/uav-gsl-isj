# 2026-10-07 Supervisor-marked opening-report revision plan

## Scope and provenance
Base annotated document is the user's private Word `开题报告(4).docx` (school template, about 31 rendered pages). It has yellow-highlighted advisor remarks. Do **not** upload this private Word to the public repository.

The thesis title remains provisionally:
**复杂湖岸环境下无人机气体源定位方法研究**.

This is a **proposal/revision plan**, not a completed new method, accepted SCI paper, or completed CFD benchmark.

## Yellow remarks — exact categories and actionable responses

| Annotated location | Supervisor request | Planned revision |
|---|---|---|
| Fig 1, approx p.4 | Label study region, which key points have UAVs, gas-diffusion shape, source coordinates, path/concentration/shape change, relation to UAV deployment, explicit localization and prediction outputs | Redraw one physically meaningful 2.5D lakeshore scene: shoreline/water/terrain/facilities/source; real-site vs modeled annotations; plume core/center/path/front/side boundaries; gas/wind/UAV trajectories; source probability and bounded short-horizon plume-state outputs; roles of different UAVs |
| Research status, approx p.5 | “太简单了，写作方面，一个研究现状一页” | Reorganize by broad methodological streams, enlarge critical comparisons with genuine recent verified papers; explicitly contrast gas mapping, source localization, inverse dispersion, wind-field errors, multisensor/multi-UAV dynamic monitoring; do not pad text |
| Fig 2, approx p.9 | “不好看在设计” | Rebuild readable 4-stream evidence/gap figure with uniform year notation, Chinese/English typography, consistent alignment and sources |
| Research contents, approx p.12 | “定位源/形状和扩散的途径，受气象要素的影响” | First content must make source position + transport path/shape/concentration + meteorological forcing relation explicit, without overstating prediction skill |
| Research contents, approx p.12 | “无人机集群怎么动态跟踪和监测…多个无人机” | Replace old second standalone source-identifiability/reliability chapter with multi-UAV dynamic key-point tracking/monitoring; carry identifiability and calibration into content 1 as a method-evaluation layer |
| Research contents, approx p.12 | “从问题角度出发” | Order chapter as scene contradiction → broken prior assumption → testable scientific problem → proposed solution family → evidence gate; do not title by algorithm fad |
| Technical route, approx p.16 | “技术路线一个研究内容配图” | Preserve total route chart plus individual methods figures for each of the three contents; separate common benchmark construction, first-paper GSL inference, second multi-UAV plume monitoring, third simulation-real validation |
| Fig 4, approx p.18 | “图难看” | Rebuild method figure with wind/geometry/sparse observation → transport-conditioned source likelihood/posterior → source map, plume-related outputs and uncertainty; do not imply an unvalidated world-model algorithm is finalized |

## Research change from previous draft
Annotated draft is organized:
1. candidate-source probabilistic localization;
2. source identifiability/reliability;
3. closed-loop and field validation.

New provisional structure:
1. **复杂湖岸三维输运约束下的无人机气体源概率反演方法** — first/main SCI contribution, final method family still evidence-gated;
2. **面向羽流态势变化的多无人机动态协同监测方法** — key-point extraction, roles, constrained assignment/redeployment;
3. **复杂湖岸环境下无人机气体溯源闭环与受控实飞验证** — device timing/calibration/rotor influence, GADEN-RT, single then multi UAV.

**Do not make the first paper a wind reconstruction paper.** GSL remains the measured primary objective.
**Do not force the main method to be PMFS derivative.** PMFS is a strong reproducible comparator/backbone candidate, not a constraint on novelty.

## Provisional scientific gap — conditionally framed
Under heterogeneous 3D lakeshore flow, sparse UAV gas+wind samples may support different source hypotheses depending on transport conditions. A candidate issue is that global wind-field accuracy and source-posterior utility are not equivalent. This remains a hypothesis, not demonstrated mechanistic novelty. Candidate solution family: source-task-aware transport uncertainty / physics-probabilistic source inversion.

Existing negative evidence:
- R0C1 vertical-spread signal passed only 2/4 contexts -> STOP.
- R0D wind/gas factor dependence local, no universal repeatable mechanism -> HOLD.
- P0 fixed transfer dynamics audit 0/21 accepted target/horizon -> STOP for that frozen world-model direction, not a universal statement that plume forecasting is impossible.
- W0C Stage0: 64 House baselines, 0/16 full four-realization cells pass a conservative all-side edge-support screen -> prerequisite HOLD, 0 new causal runs.
- M0: 40-run **design** frozen, 8 U0 baseline + 32 potential wind perturbations; no new simulations yet. Experimental results are not PASS.
M0 scientific purpose: test matched global wind errors with different spatial/structural impacts on plume/source inference; the non-lakeshore box is only a mechanism pre-screen.

## Why FSR / 枫树岭 self-built benchmark is necessary
Existing House experiments are not lakeshore and suffer finite transport-domain support risks. Off-the-shelf field measurements rarely provide complete, synchronized true source / full 3D wind / UAV gas / repeatable counterfactual conditions. The planned FSR benchmark is for:
1. real reservoir shoreline/terrain/water-land masks;
2. physics-labeled controlled lake/land thermal contrast, surface roughness, stability and background wind;
3. CFD 3D wind + GADEN gas releases, known source locations/times;
4. paired source/gas/wind/realization/route tests, all-side simulation-domain guard, full lineage;
5. source-localization comparisons and short-horizon plume-state evaluation.

**Truth-status contract**:
real remote-sensed terrain ≠ real observed meteorology.
Water/land temperature difference used as a controlled boundary parameter cannot be described as measured FSR weather.

Current status:
- R8 real-site geometry/local relative vertical-frame PASS;
- latest R9 mesh-quality/open-face/AGL initialization HOLD; no scientific CFD/GADEN result can yet be claimed.
FSR is intended as the MAIN lakeshore benchmark; H01/H02 are cross-scene/geometry stress tests, not external real-data proof.

Public data role:
- controlled UAV gas-release datasets (Merced / PG&E / Blackpool) may support real external localization validation, after qualification;
- Lagoon Pingo / WiscoDISCO support water-adjacent meteorological/plume physical plausibility, not necessarily blind-source GSL metrics.

## Outputs and division among papers
Content 1 primary output:
- 2D source posterior/probability map + coordinate;
- error/rank/Success@k/probability scoring;
- auxiliary plume center/path, effective footprint/core/front/boundary, concentration trend and uncertainty, only at validated forecast horizon.

Content 2 outputs:
- dynamic monitoring key points;
- UAV source-check / plume-core / boundary/front / wind-complementary roles;
- assignment and rolling re-deployment with safety/time/energy/communication constraints;
- comparison on plume coverage/front tracking/total time/energy.

Content 3 outputs:
- closed-loop simulation and bounded field validation;
- sensor response/recovery, wind/gas/flight synchronization, rotor/interference effects;
- source error, stability, task completion, failed/abstained cases.

## Immediate teacher-facing positioning
Do not promise the new main algorithm already works.
Say:
“We have reproduced and stress-tested PMFS/GADEN, found substantial sensitivity to 3D transport context but also negative results for multiple candidate dynamic features. We are therefore restructuring around a physically explicit lakeshore GSL failure problem. We are building a reproducible FSR simulation benchmark with actual shoreline/terrain and controlled, clearly labeled meteorological forcing. The proposed first-paper mechanism is under a minimal causal experiment gate; following that, the second study addresses multi-UAV monitoring driven by dynamic plume situation, and the third handles closed-loop flight verification.”

## Submission strategy
For an imminent supervisor deadline, provide a **revision draft / planned research**. It is legitimate for a thesis proposal to state intended tests and contingency paths. Do not present a false empirical `PRIMARY_GO`.
Revise the exact school Word template in place, retain section/header/table hierarchy and styles.
Remove yellow instruction lines from clean teacher copy; retain a separate change log.
Rework figures rather than keeping ugly previous graphics under unchanged scientific claims.
References must be verified; keep accurate prior text until an actual verified source replaces it.
