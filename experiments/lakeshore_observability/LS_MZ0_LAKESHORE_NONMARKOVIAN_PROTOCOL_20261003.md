# LS-MZ0: 湖岸泄漏非马尔可夫传播记忆最小验证协议
Date: 2026-10-03

## 0. 纠偏与边界

本协议只服务于“复杂湖岸环境下无人机气体源定位”主线。

House01/02/03/VGR 不再作为主机制筛选数据；它们最多在湖岸主线 PASS 之后作为非湖岸外部对照。不得用 House03 结果替代湖岸证据。

冻结结论：
- R1 = R1_HOLD_WEAK_OR_UNSTABLE
- R1A = R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION
- R1B = R1B_HOLD_MISMATCH_NOT_FRONT_LOCKED
- REAL_SCENE_FEATURE_GATE_NOT_ESTABLISHED
- T0 = T0_FAIL_TASK_SUFFICIENCY_MAINLINE

不得回溯改判。

## 1. 新科学假设

不再假设“某一个固定湖风锋机制必然导致定位失效”。

研究假设改为：

水陆热力差异、背景风和近岸地表共同造成非平稳、空间非均匀的低空输运。UAV 只能观测局部气体、局部风和位姿，完整三维输运自由度被消元后，候选源证据可能表现为有限时间的非马尔可夫记忆。若该记忆携带源特异性的传播信息，则显式建模 source-conditioned transport memory 应在困难湖岸定位任务中优于瞬时/Markov 证据和普通时序网络。

Mori–Zwanzig 仅作为“未解析自由度 -> memory + stochastic residual”的母理论，不宣称精确恢复 MZ kernel。

## 2. 湖岸物理锚点

真实数据只约束“参数范围/场景真实性”，不用于伪造泄漏真值：
- WiscoDISCO-21：低空温度/湿度/3-D wind 与 0–120 m UAS 垂直结构，证明近岸低层状态可显著变化；
- Allouche et al. 2025：非稳态水陆热差 + 背景压力梯度 LES，证明 mean flow / turbulence / thermal forcing 可长期非平衡并存在显著时间滞后；
- Welch et al. 2024 FastEddy：湖风锋微尺度结构参考。

这些来源用于冻结 CFD/边界条件 envelope；不把任一单事件写成普适 GSL 失效机制。

## 3. 先做 runtime audit，不直接生成

Codex 必须先确认：
1. 当前 VM 是否安装 OpenFOAM/其他热力 CFD；
2. 版本和可用的 transient buoyant/Boussinesq solver；
3. 当前 GADEN 3.0 能否读取时间序列 3-D wind snapshots；
4. wind snapshot 时间间隔、坐标、单位和 preprocessing 入口；
5. CPU/GPU/内存与单场 CFD 粗网格成本。

不得先假定 solver 名称，不得升级现有 GADEN 环境。

输出：LS_MZ0_RUNTIME_AUDIT.md

若无可用热力 CFD：STOP，报告环境缺口；不要退回手画参数化 front 作为主证据。

## 4. 湖岸热力 CFD 场景：只生成少量环境，大量随机羽流由 GADEN 产生

### 4.1 几何
第一阶段平坦岸线，无建筑：
- shoreline x=0
- water x<0
- land x>0
- CFD domain 建议 x=-200..400 m, y=-150..150 m, z=0..150 m
- GSL evaluation ROI x=0..250 m, y=-80..80 m, z=0..80 m

几何和网格可按 runtime 调整，但先冻结后再运行。

### 4.2 热力边界
不要人工规定 front 的 u/w 形状。通过 water/land surface thermal forcing、background wind、roughness/boundary conditions 让低空 circulation/thermal layer 自发形成。

第一阶段只做 4 个 flow contexts：
- L0: near-neutral / weak thermal contrast
- L1: moderate lake-to-land thermal contrast + weak background wind
- L2: stronger thermal contrast + weak/moderate background wind
- L3: transition case with time-varying surface thermal forcing

参数范围从 Wisco/Allouche/FastEddy 文献和已审计真实数据中取合理 envelope；不得为了定位结果调参数。

### 4.3 CFD QC
每个 context 输出：3-D U,V,W,T；continuity/divergence QC；10/30/60/100 m profiles；cross-shore temperature gradient；characteristic advection time；integral/autocorrelation time；near-shore flow visualizations。

只要 CFD 物理/数值不合格就 STOP，不进入气体模拟。

## 5. GADEN 湖岸泄漏 benchmark

### 5.1 sources
先用 12 个 source positions，必须覆盖多个岸距：
- x = {30, 70, 110, 150} m
- y = {-30, 0, 30} m
- z = 1 m

### 5.2 plume realizations
每个 flow context × source：8 independent plume seeds；primary release = one frozen medium rate。

第一阶段 gas tasks：4 contexts × 12 sources × 8 seeds = 384 realizations。

### 5.3 route
固定、源盲、所有方法共享。使用 cross-shore + crosswind mixed route，至少覆盖 x=40..200 m、y=-60..60 m；primary altitude 10–20 m；1 Hz；budgets 30/60/120/300 s。路线必须在看任何定位结果之前冻结。

### 5.4 observation tensor
仅允许 UAV 实际可获得或合理安装的量：time、UAV xyz、gas concentration/hit、local wind U,V,W、optional T/RH、map/shoreline distance。

不得把完整 CFD flow field、front position、source truth 输入定位器。

## 6. 候选源评分形式

避免固定 12 类分类器。对每个候选源 s 构造 source-relative features：q_t-s、along/cross-wind displacement、shoreline-relative geometry、gas/wind history。模型输出 candidate score/log-likelihood，再归一化得到 p_t(s)。

## 7. 四个冻结对比臂

A. MARKOV：当前 observation + source-relative geometry，无历史。

B. HAND_MEMORY：gas mean/std/max、hit/intermittency、time since last hit、whiff duration、blank duration、integrated along/cross-wind travel。

C. GENERIC_MEMORY：小型 GRU/LSTM，与 D 同量级，不显式 source-conditioned kernel。

D. LS_MZ_CLOSURE：Markov base candidate evidence + source-conditioned finite-memory kernel + wind-relative transport displacement + stochastic residual scale；kernel 随 lag 衰减或有限支撑；不重建 dense 3-D plume。

统一候选先验、路线、观测预算和 train/test split。

## 8. 物理形式

概念式：
ell_t(s) = ell_0(o_t,s) + sum_k M_k(s; o_{t-k:t}, delta_q, u) + eps_t

其中 ell_0 是当前局部证据，M_k 是未解析传播自由度投影产生的有限记忆贡献，eps_t 是未解析随机湍流残差。

## 9. 数据划分

禁止随机拆 1 Hz 样本。Primary 按完整 plume realization/seed 留出；robustness 再做 held-out source-x band 和 held-out flow context。test seed 不得参与标准化、选 K 或超参搜索。

## 10. 主指标

第一篇主终点：
1. localization error (m)
2. true-source rank
3. Top-1
4. Top-3 / Success@distance

Secondary：source posterior NLL/Brier；future 10/30 s hit Brier/NLL；30/60/120/300 s rank-vs-time。

不以 future prediction 单独判 GO。

## 11. 机制指标

必须输出 learned memory contribution vs lag、empirical gas autocorrelation time、whiff/blank duration、effective memory horizon、no-memory ablation、no wind-relative geometry ablation、no stochastic residual ablation。

关键问题：learned memory horizon 是否与真实 plume temporal scales 对应，而不是任意网络记忆。

## 12. 冻结判定

LS_MZ0_PASS_LAKESHORE_NONMARKOVIAN_SOURCE_SIGNAL 仅当：
1. D 的 median true-source rank 优于 B 和 C；
2. >=3/4 lake flow contexts 非劣，至少2/4明显改善；
3. localization error/Top1 至少一项同向改善；
4. 不是单一 source 或 seed 驱动；
5. memory ablation 明显损失 source-rank benefit；
6. learned effective lag >0 且跨 seeds 稳定；
7. held-out flow context 不崩溃。

LS_MZ0_HOLD_MEMORY_SIGNAL_NOT_SOURCE_SPECIFIC：future prediction 改善但 source localization 不改善，或只优于 generic memory、不优于 hand memory。

LS_MZ0_FAIL_NONMARKOVIAN_LAKESHORE_MAINLINE：D 不优于 B/C，或 source gain 不稳定，或 memory scale 无物理解释。

## 13. 后续边界

只有 LS_MZ0 PASS 才加建筑/植被、第二气体物性、PMFS 完整闭环直接比较、多无人机/主动补测。

若 FAIL，不再以 MZ/非马尔可夫记忆作为第一篇主创新，继续换母理论。

House/VGR 只允许在 LS_MZ0 PASS 后做非湖岸外部对照，不能替代上述主实验。