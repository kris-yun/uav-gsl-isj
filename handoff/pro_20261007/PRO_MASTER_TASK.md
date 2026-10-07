# Pro master task

## Mission
Reconstruct the first-paper scientific problem and the full master's research plan for:
**复杂湖岸环境下无人机气体源定位方法研究**

Act as a committee combining:
- UAV gas-source-localization expert;
- atmospheric boundary-layer / CFD expert;
- robotics/UAV expert;
- ML expert;
- SCI Q2 / ISG-style reviewer;
- experiment-design auditor;
- supervisor-group style reviewer.

## Highest constraint
The research object is UAV GSL.
Wind reconstruction, CFD, PMFS, world models, PINN/GNN/RL etc. are tools only.
The first paper must ultimately establish value on source localization under fair evaluation.

## Phase 1 — literature/problem audit
Systematically audit recent 2024–2026 work plus critical classics:
- UAV/robot gas source localization;
- odor source localization;
- source-term estimation / inverse dispersion;
- PMFS/probabilistic mapping + forward simulation;
- information-driven and RL search;
- terrain/wind-aware learned GSL;
- sparse 3D wind reconstruction in complex terrain/urban/low-altitude settings;
- lakeshore/coastal breeze and pollutant transport;
- CFD/GADEN/GADEN-RT.

Answer:
A. How does modern GSL actually use wind?
B. What objective do wind-reconstruction papers optimize?
C. Has anyone already closed the chain:
sparse UAV/ground meteorology → complex/lakeshore 3D wind → plume transport → source posterior/localization?
D. What limitations/future-work statements from prior papers naturally motivate a new problem?

Do not manufacture novelty by saying “few studies”.

## Phase 2 — public dataset audit
Search for public lakeshore/reservoir/coastal gas-release or pollutant-transport datasets.
Audit each for:
- known source coordinates;
- source timing/rate;
- UAV/mobile concentration measurements;
- synchronized wind;
- vertical wind structure;
- timestamps and coordinate systems;
- downloadable raw data;
- suitability for GSL.

If a dataset lacks strict source labels, it may validate transport/met mechanisms only, not source-localization accuracy.

## Phase 3 — candidate competition
Generate 3–5 candidate first-paper scientific questions.
For each give:
- research object;
- real scene conflict;
- broken assumption of existing methods;
- genuine literature gap;
- why lakeshore UAV GSL needs it;
- candidate backbone family;
- exact innovation relative to that backbone;
- minimal falsifiable experiment;
- STOP condition;
- compute/data cost;
- likely reviewer attack;
- publication strength.

Compare at least:
- PMFS / probabilistic map + online forward simulation;
- Bayesian/source-term inversion;
- Gaussian/CFD inverse modeling;
- information-driven GSL;
- learning-based spatiotemporal GSL;
- terrain/wind-aware methods;
- RL/search approaches;
- physics-probabilistic hybrids.

Decide whether PMFS is a backbone or only a strong baseline.

## Phase 4 — explicitly attack current wind→GSL candidate
Test the hypothesis:
**global wind-field accuracy may not equal GSL utility**.

Design a zero/minimal-new-simulation phenomenon gate:
construct controlled wind perturbations with similar global RMSE but different spatial/structural errors (source region, shoreline, main transport corridor, vertical shear, local recirculation, missing w component, direction bias, etc.).
Test whether they cause materially different:
wind error → plume/path/sensor-response error → source likelihood/posterior/localization error.

If that phenomenon does not survive strict controls, STOP the task-oriented wind route before inventing an algorithm.

## Phase 5 — FSR benchmark design
Treat FSR as the main self-built lakeshore benchmark.
Respect the current geometry-only PASS boundary.
Design the shortest publishable generation contract:
- execution preflight;
- CFD necessity/model choice;
- controlled forcing matrix;
- source locations;
- realizations;
- UAV trajectories and sparse met/gas sensing;
- GADEN/GADEN-RT interface;
- strong baselines;
- storage and compute budget;
- lineage/hashes;
- validation gates.

## Phase 6 — choose exactly one first-paper line
Return:
- `PRIMARY_GO`: one main scientific problem/method direction;
- `BACKUP`: one fallback;
- all others explicitly STOP.

Success means a new UAV-GSL method has stable, interpretable advantage over multiple representative baselines under fair source/wind/realization/cross-scene evaluation.
It does not have to be a PMFS modification.

## Phase 7 — rebuild thesis plan
Three connected research contents:
1. strongest first-paper GSL innovation;
2. weaker but coherent multi-UAV monitoring / key-point deployment / task allocation or active resampling that uses part 1 outputs;
3. GADEN-RT + real UAV observation chain + controlled flight validation.

Target chain:
**localization/inversion → multi-UAV dynamic monitoring → closed-loop flight validation**.

## Phase 8 — only then revise the opening report
Use the private Library file:
`开题报告_原格式_任务充分定位_多无人机协同更新版.docx`.

Keep:
- school template;
- cover;
- section order;
- tables and overall formatting.

Rewrite the science where necessary.
Delete claims tied to experimentally stopped world-model assumptions.
Verify all references online.
Distinguish explicitly:
verified evidence / experimental indication / literature support / hypothesis / proposed validation.

## Required final deliverables
1. 第一主创新决策报告.
2. 文献与前人不足矩阵.
3. 公开湖岸/滨水数据集资格审计.
4. FSR-FB1主benchmark生成合同.
5. 第一篇SCI最小验证→完整实验计划 with GO/HOLD/STOP.
6. 三研究内容与总体技术路线.
7. revised full opening-report DOCX, preserving template.
8. standalone 后续研究规划书.
9. reviewer attack test from GSL, CFD/ABL, robotics/UAV, and ML perspectives.

For every important conclusion report:
evidence, alternative explanation, whether excluded, scope of validity, and non-generalizable boundary.
