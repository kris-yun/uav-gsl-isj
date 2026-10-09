# 2026-10-09 related-work boundary: PMFS history-vs-forward consistency

**Prior art != new contribution.** Before promoting the possible source-receptor evidence consistency issue to a novel method, compare at least:

1. Original PMFS (Ojeda et al., IEEE TRO 2024; DOI 10.1109/TRO.2024.3426368). Its code `PMFSLib.cpp` accumulates `cell.logOdds += ...`, and `cell.omega += ...` for each measurement. `PMFS.cpp` updates the wind grid on measuring and calls `updateSourceProbability()` at selected steps. `Simulations.cpp` computes a candidate score by multiplying per-cell factors `1 - confidence*abs(measured_hit-sim_hit)*D`. **Code fact:** saved hit map is accumulated history while forward candidate scoring consumes the wind grid at that update. **Unverified inference:** changing wind or observation-time misalignment systematically damages source localization.
2. Piro et al., *Journal of Turbulence* 2025, "Many wrong models approach to localise an odour source in turbulence with static sensors," DOI 10.1080/14685248.2025.2492711. Uses multiple approximate models and model-weighted Bayesian inversion; therefore adding weighted BMA alone is not new.
3. *Exploration and Gas Source Localization in Advection–Diffusion Processes with Potential-Field-Controlled Robotic Swarms* (2023), https://pmc.ncbi.nlm.nih.gov/articles/PMC10674467/. Incorporates time-varying wind and aging/forgetting measurements; naive time-decay/forgetting is not original.
4. "基于时间加权最大似然估计的室内气体源定位方法" (2025), https://cnki.istiz.org.cn/kcms/detail/detail.aspx?dbcode=CJFQ&dbname=CJFD2025&filename=YQXB202502008 . Time-weighted measurement window in gas localization is also not new; full-text independent checking is needed.
5. Ando et al., ISOEN 2026, "Evaluation of Robotic Gas-Source Localization in Simulations Under Outdoor Wind Fluctuations", DOI 10.1109/isoen68725.2026.11665201. Examines changes in outdoor wind and MOX sensor lag; demonstrates that wind/latency mismatch is already an investigated problem (conference paper).
6. Scheel et al., AMT 2026, "Dynamic quantification of methane emissions at facility scale using laser tomography" DOI 10.5194/amt-19-2343-2026. Uses time-indexed wind and Bayesian dynamic inversion; not UAV GSL but shows source inversion/time-varying wind isn't novel.

## Current intellectually honest problem definition
**研究问题候选（尚未在真实原生PMFS上证明）**：在非均匀、时变风场与传感器响应滞后下，二维累计气体命中证据与候选源当前传播预测存在时间/模型条件不一致时，怎样识别仍可用于区分源位置的可靠证据，而不把真实源错误排除，同时保留 PMFS 二维源概率图输出？

**A narrower, potentially contributory method rather than recycled forgetting/BMA:** reconstruct observation-event source-receptor *conditional* evidence with physically consistent wind history and sensor response kernel; account for correlated exposure windows; produce a 2D source probability map and uncertainty reliability diagnostic. This remains a **proposed mechanism**, not a validated innovation. Domain-specific novelty must be judged against direct published methods and data, not against strawman baselines.

## The decisive falsification
- Freeze source coordinates/height, plume realizations and observation path independently from source truth. Compare native PMFS to an offline physically time-aligned source-receptor predictor under **the same inputs and candidate source space**; ablate wind history vs stale hit-map only when all ground truth and clocks are legal.
- If correct time alignment does **not** reduce predictive mismatch or improve nontrivial source ranking/calibration across independent source/wind/realization, STOP this route.
- If the apparent benefit is entirely due to correcting a wind-direction adapter, compilation flag, playback modulo, source support or sensor lag, classify as engineering repair, not theoretical novelty.
- Baselines in evaluation: original native PMFS, correctly matched static source-receptor likelihood, naive rolling-window/forgetting and weighted-multiple-model method when available.
- Report no gains on saturated two-candidate tasks as no evidence, not a win.

**Status:** prior-art screening only, no new original PMFS test or claim of 2026 theoretical superiority. Previous M0/AOD/TNQC/M4 STOP/HOLD retain original verdicts.
