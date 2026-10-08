# PRO HANDOFF — READ THIS FIRST

This branch is a sanitized research handoff for the next Pro session.

## Core scope
The research object is **UAV gas source localization (UAV GSL)** in a complex lakeshore setting.
Wind reconstruction, CFD, PMFS, Bayesian inversion, world models, PINN/GNN/RL etc. are tools only.
The first paper must ultimately show value on **source localization** metrics, not only wind/plume RMSE.

## User-fixed decisions
1. The thesis title may remain: **复杂湖岸环境下无人机气体源定位方法研究**.
2. FSR / 枫树岭 is intended as the **main, self-built lakeshore benchmark** tailored to the paper.
3. House H01/H02 are cross-scene / cross-geometry stress tests, not the lakeshore main benchmark.
4. Real FSR geometry + controlled, literature-supported meteorological forcing is acceptable; do not mislabel controlled CFD forcing as measured weather.
5. The new method does **not** have to be an improvement of PMFS. PMFS is a strong reproducible baseline/backbone candidate because it has public code and outputs a source probability map.
6. The first paper must outperform a fair set of representative classical/strong baselines on UAV GSL, but need not beat every baseline on every case.
7. Pro is allowed to overturn the current wind-oriented hypothesis if a stronger scientific problem is found.
8. A public lakeshore dataset without strict source labels may be used only for transport/met mechanism validation, not falsely as a source-localization benchmark.

## Private files available in ChatGPT Library
Search the Library by exact names/paths:
- `开题报告_原格式_任务充分定位_多无人机协同更新版.docx`
- folder: `/UAV_GSL_PRO_HANDOFF_20261007/`
  - `课题组10篇无人机论文_20261005.zip`
  - `DYNAMIC_SUFFICIENCY_R0_EVIDENCE.zip`
  - `R0C_ANALYSIS_EVIDENCE.zip`
  - `R0D_ANALYSIS_EVIDENCE.zip`
  - `P0_ANALYSIS_EVIDENCE.zip`
  - `R0C_REPORT_zh.md`
  - `R0D_REPORT_zh.md`
- FSR R8 report is also in Library as `REPORT_zh(8).md`

Do not ask the user to re-upload these before first searching the Library.

## Order of work
1. Read CURRENT_STATE.md and STOP_HOLD_REGISTER.md.
2. Read the latest opening report and evidence packages from Library.
3. Read the 10 group papers as examples of how the supervisor's group forms scientific questions from real failure mechanisms.
4. Audit literature and datasets.
5. Compete 3–5 candidate first-paper scientific questions.
6. Pick exactly one PRIMARY_GO and one BACKUP; STOP the rest.
7. Only then redesign FSR benchmark and revise the opening report.


## Interim analysis completed before Pro upgrade
Read these next:
- `INTERIM_PRIMARY_INNOVATION_ANALYSIS_20261007.md`
- `LITERATURE_GAP_MATRIX_20261007.md`
- `W0_TASK_SENSITIVE_WIND_TO_GSL_GATE.md`
- `PUBLIC_DATASET_AUDIT_SEED_20261007.md`

Important: these are **provisional analyses**, not final PRIMARY_GO decisions. The wind→GSL route remains phenomenon-gated and may still be STOPped.


## W0C Stage-0 update — 2026-10-07
Latest verdict: `W0C_STAGE0_NO_CLEAN_BASE_HOLD`.
The matched-error causal hypothesis was **not tested** because no existing House baseline cell passed the frozen 4/4 all-side transport-support gate.

Read:
- `W0C_STAGE0_HOLD_REVIEW_20261007.md`
- `M0_CLEAN_SUPPORT_MECHANISM_DRAFT.md`

Private evidence is in ChatGPT Library:
- `/UAV_GSL_PRO_HANDOFF_20261007/W0C_STAGE0_NO_CLEAN_BASE_HOLD_20261007.zip`
- `/UAV_GSL_PRO_HANDOFF_20261007/W0C_STAGE0_REPORT_zh.md`

Do not relax the old House gate. The recommended next step is a clean-support mechanism benchmark, followed by FSR lakeshore confirmation only if the mechanism survives.


## M0 R0 design review — 2026-10-07
The frozen M0 design has been reviewed and is accepted for **staged execution only**.

Read:
- `M0_R0_DESIGN_REVIEW_20261007.md`

Current authorization recommendation:
1. E0 runtime qualification, 0 scientific runs;
2. E1 only the 8 U0 baseline runs;
3. stop and review before any wrong-wind intervention runs;
4. if E1 passes, use four already-budgeted intervention rows as a CRN sentinel before launching the remaining 28.

Private frozen package is in ChatGPT Library:
- `/UAV_GSL_PRO_HANDOFF_20261007/M0_CLEAN_SUPPORT_DESIGN_R0_FROZEN_20261007.zip`
- `/UAV_GSL_PRO_HANDOFF_20261007/M0_SCIENTIFIC_CONTRACT.md`

## Supervisor's 2026-10-07 annotated opening-report update
Read `SUPERVISOR_ANNOTATED_OPENING_REPORT_REVISION_PLAN_20261007.md` before revising any Word document. The annotated 31-page original contains explicit yellow feedback about the lakeshore scene diagram, literature depth, plume path/shape/concentration and forecast outputs, dynamic multi-UAV tracking, and three content-specific route figures. The private annotated Word must not be committed into this public repo.

## M0 E0/E1 verification, 2026-10-07
E0 and eight U0 baseline simulations are **QUALIFIED**. The full evidence bundle was independently replayed in a separate environment: 39 frozen R0 files, 2,551 native files, 8 U0 baseline runs, 0 wrong-wind runs. Matched-error causal conclusion is still **NOT_TESTED**.
Review and exactly-four-run E2 sentinel plan: `M0_E0_E1_REVIEW_AND_E2_SENTINEL_AUTHORIZATION_PLAN_20261007.md`.
Private archive: `/UAV_GSL_PRO_HANDOFF_20261007/M0_E0_E1_BASELINE_QUALIFIED_FULL_EVIDENCE_20261007.zip`.
No remaining 28 wrong-wind rows are authorized by this review document.

## Next-stage priority decision (FSR mainline / M0 bounded, 2026-10-07)
See `FSR_MAINLINE_AND_M0_BOUND_EXECUTION_20261007.md`. It directly incorporates FSR R9.3 local S2 PASS/S4 determinant HOLD and the 250k-vs-1.5M cell budget conflict. First approve a real-geography local shoreline pilot with physics and resource qualification; M0 only four E2 CRN sentinel runs, stopping afterwards. No automatic CFD, GADEN or the 28 other wrong-wind runs.

## M0 E2 review / E3 final 28-run plan
Independent replay of uploaded E2 evidence passed: `M0_E2_CRN_SENTINEL_QUALIFIED` (4 wrong-wind sentinel runs, 12/40 overall). The original clock-serialization false HOLD and the one-expression erratum are retained. Scientific M0 posterior-damage verdict remains `NOT_TESTED`.
Read `M0_E2_REVIEW_E3_28_RUN_CONDITIONAL_PLAN_20261007.md` for the exact final 28 run IDs, prerequisites, frozen 3/4-replication gates and conditional STOP. Private archive: `/UAV_GSL_PRO_HANDOFF_20261007/M0_E2_CRN_SENTINEL_QUALIFIED_FULL_EVIDENCE_20261007.zip`. Do not treat this memo as actual E3 simulator authorization.
