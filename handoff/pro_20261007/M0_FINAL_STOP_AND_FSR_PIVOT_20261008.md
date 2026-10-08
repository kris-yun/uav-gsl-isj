# Final M0_STOP review and transition to FSR mainline

Date: 2026-10-08

## Frozen decision
**M0_STOP. No rescue experiment.** Main evidence branch `codex/m0-e3-final-20261007`, commit `bfca3344c553ddb1f9f05852a83f7b4ed7d883dc`.

Independent reinspection of uploaded `M0_STOP_ALL40_FULL_EVIDENCE_20261007.zip`:
- outer ZIP CRC PASS, contains `FINAL_DECISION.json`, full frozen contract and the 40-run original bank;
- `FINAL_DECISION.json` states 40/40 legally qualified, 28 E3 additions, unchanged R0/E1/E2, BMA excluded from primary gate, STOP;
- `INDEPENDENT_FINAL_VERIFICATION.json`: 39 R0 frozen files, 14,779 native files verified, two source models and all matched RMSE checks; independent verdict STOP;
- `LINUX_FINAL_REPLAY_VERIFICATION.json`: fresh replay PASS and STOP, no native simulation added;
- `PAIRED_EFFECTS_ALL_SOURCES_SEEDS.csv` has exactly 16 rows (2 pairs × 2 sources × 4 seed blocks);
- `ALL40_SOURCE_POSTERIORS.csv` has 96 rows (2 likelihood families × 6 wind/BMA models × 2 sources × 4 realizations), Top1 correct in every evaluated arm, source MAP error zero for the frozen two candidate positions.

Primary indicators from the sealed report:
- Pair A maximum |ΔD_F|=0.462346508, maximum |ΔD_Y|=0.351838181;
- Pair B maximum |ΔD_F|=0.271911749, maximum |ΔD_Y|=0.151390561;
- maximum |ΔBrier|: HIT_FORWARD 8.84506939e-08 for A and 3.82605025e-13 for B; LOG_GAUSSIAN 0 for both;
- required material |ΔBrier|≥0.10, same-direction same-master-seed intersection per source ≥3/4; achieved 0/4 for both sources and both directions.
- p_true min across all single-wind HIT arm ~0.9997026, LOG_GAUSSIAN numerical p_true=1; the two-candidate source task is already highly separable / posterior-saturated.

## Allowed inference
- Structural wind differences in this controlled analytic box changed plume and fixed-route sensor samples but caused no predeclared, reproducible **source-posterior damage**.
- A transferable main-paper claim that global wind RMSE fails to predict source localization utility has **not** been established.
- The frozen candidate mechanism is STOP; previous W0-PRE/PRE2 screening was exploratory and boundary-confounded.
- Two-source task saturation is a limitation of M0, **not** a reason to retroactively broaden its source set, thresholds, wind perturbations or model to manufacture PASS.
- The result does **not** prove wind or lake-breeze irrelevance to all source-inversion problems, nor is it PMFS comparison or real lakeshore evidence.

## Scientific program changes
1. Retire `task-sensitive wind error anisotropy under matched RMSE` as a selected FIRST PAPER innovation. It can be cited as tested and unsupported in its frozen idealized box only.
2. Do not reinstate the previously STOP/HOLD world-model (P0 0/21), vertical-spread (R0C 2/4), generic multi-model blending (prior art), AOD or other branches without independent new scene-derived evidence.
3. The FSR real-terrain lake benchmark remains the mainline independently of M0.
4. The supervisor's thesis proposal should no longer present task-sensitive wind uncertainty correction as the method already chosen or proven. Retain the real scientific target: industrial-facility hypothetical leaks, source posterior map/coordinate primary, path/shape/concentration plus dynamic multi-UAV monitoring as downstream work.
5. Benchmark requirements should prevent trivial two-candidate saturation without designing a benchmark to force a method's failure:
   - physically legal, verified source locations including lake-adjacent hypothetical industrial point sources;
   - transparent 2D source-prior / candidate grid with truth support;
   - source-held-out as well as independent stochastic/wind conditions where meaningful;
   - source-blind fixed sampling trajectories plus later active sampling;
   - realistic diversity in wind/stability/thermal surface contrast, including same background wind neutral vs nonneutral conditions;
   - physical transport support of full CFD/GADEN domain, no boundary artefacts;
   - difficulty/identifiability diagnostics *before* choosing an innovation based on one lucky scene.
6. Strong comparators first: native PMFS, physically parameterized inverse dispersion/Gaussian Bayesian source inversion, qualified learned GSL if replicable; multiple wrong transport models as relevant prior-art baseline.
7. Select first-paper failure mechanism only once FSR physical wind, plume and source-localization data have passed qualification and the failure appears across independent sources/wind/realizations. No task-specific winds or novel modules should be promised before this.

## Immediate Codex task, separate from the frozen M0
- Stop M0 forever under `M0_STOP`; do not run 41st M0 sim or alter any of 39 R0 frozen files.
- Preserve raw evidence, write result in STOP register and relevant thesis research notes.
- Advance FSR **F0** based on latest R9.3 verdict:
  - R9.3 alternative B local S2 mesh PASS, S4 has four determinant failures; S2 local pass is not full-domain fitness.
  - Original 250k mesh budget conflicts with native full near-surface field: ~1.47–1.63 million cells at 29 vertical layers and 19.4 GiB minimum field snapshots for four cases, ignoring solver overhead. Do not silently expand RAM/disk caps or downgrade vertical resolution.
  - Define a scientifically meaningful **contiguous local lakeshore pilot** with genuine water, shoreline, land slope, hypothetical industrial emission source, UAV ROI, transport guard, credible buoyant flow model, separate complete simulation domain. Preserve R8 coordinate provenance. Do not choose only smooth/easy shore after seeing algorithm outcomes.
  - Independently qualify full pilot mesh quality, shoreline and vertical AGL geometry, thermal/momentum boundaries and resource budget. If original numerical quality threshold or 250k cap requires change, freeze a new *explicit* pilot contract with user approval; do not override old R9 failures.
  - Once pilot qualification PASS, request approval for the FIRST CFD **wind** dry-run; no mass production or GADEN until wind physical/numerical checks PASS.
- When FSR scientific cases begin, neutral-vs-controlled land-water temperature contrast is one **forcing factor**, not a claim that lake-breeze reversal necessarily occurs.
- M0 STOP must never be described as stopping FSR data generation.

## Supervisor-facing one paragraph
前期已对 PMFS/GADEN 和不同风场条件开展对照。一个受控等误差风场机理实验完成40组重复计算，虽然风场变化引起了羽流差异，但没有带来可重复的源定位损伤，因此我们没有把这条假设直接写成新算法。当前重点仍是枫树岭真实地形约束下的湖岸数据集，计划先完成可靠的三维热力风场和泄漏扩散仿真，再比较源反演方法，确定具有跨源、跨风况证据的研究问题。
