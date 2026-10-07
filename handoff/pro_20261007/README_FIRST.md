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
