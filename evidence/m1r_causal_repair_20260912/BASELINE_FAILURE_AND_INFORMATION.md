# PMFS 底座失败与可利用信息：只读结论（2026-09-12）

核查起点：`3b0957d3f7280404bfdffc5bee7b4e68722d77fd`。只读代码、小型摘要和已有开发运行记录；未进入原始大 bank、访问 VM、训练或修改旧证据。结论是：**PMFS 已经利用局部气体、局部风和地图，M1R 主要更换证据形成方式；现有证据支持观测/forward 表示的失配与区分力不足，不能把问题缩写成“早期过度自信”，再仅用证据降权解决。**

## A0 实际看见什么，在哪里丢失信息

1. `PMFS.cpp:384–400` 把当前浓度压成 `concentration > thresholdGas` 的 hit/no-hit，并连同当前局部风向、风速和机器人格点交给 `EstimateHitProbabilities`。`PMFSLib.cpp:19–86` 用随风椭圆核、地图可见性和传播形成整图 hit probability；各格累积 log-odds，空间距离累积 confidence。这是经传播的气体命中图，不是各格独立实测浓度。
2. 原生 forward 用估计风场加高斯运动噪声推动二维气丝；每步每格只记录“至少一个气丝中心在格内”，再除以步数得到 hit frequency（`Simulations.cpp:6882–6998`）。没有气丝质量/尺度浓度核或 ppm 转换，聚合结果没有抵达时刻、事件持续时间或浓度振幅。候选为 quadtree 区域时，每个新气丝从区域重新采样释放点（`7001–7033`），不能直接解释为“一个固定未知点源在该区域内”的概率边缘化。
3. A0 源分数是所有自由格的乘积：
   `L_A0(s) = product_i [1 - confidence_i * sourceDiscriminationPower * abs(p_measured_i - p_sim(s,i))]`。
   这是实际 `lerp` 与绝对差公式的展开，不是完整时序观测似然（`6823–6837`, `6859–6879`）。H03 保存的 A0/M1R launch 都是 `sourceDiscriminationPower=1`、`useWindGroundTruth=false`。

因此，底座不是“没有因果/物理信息”；它把有时序的局部观测和粗略输运压成了匹配两个空间命中图的问题。代码能证明这种信息压缩和模型语义，不能单凭代码分配每项对 A0 闭环误差的因果贡献。

## M1R 的真实新增量与历史结果

历史 M1R 使用每个内部测量块的 hit、浓度、位置、阈值和顺序，计算

`p_s,e = expit(logit(p_persist,e) + logit(p_sim(s,e)) - logit(mean_s p_sim(s,e)))`，

随后对所有已记录块取 Bernoulli 因子乘积，替换第一层候选源分数，再进入普通 PMFS refinement/controller。历史 persistence 是以 `log1p(previousConcentration)` 为中心、单位标准差的正态尾概率；previousConcentration 每块更新，每次候选评分从零重建。它是上一记录块启发式，不是完整 FOPDT 状态，也不是已经校准的共享输运潜变量。历史 M1R 本身一个 transport member；三成员属于 M1M2R。历史实现绑定仅 `PASS_WITH_PROVENANCE_LIMIT`，不能用当前默认分支行为覆盖历史滚动项。

| House | A0 最后源 MAP 误差 | M1R 最后源 MAP 误差 | M1R 终点改善 | 源误差 AUC 改善 |
|---|---:|---:|---:|---:|
| H01 | 4.116 m | 2.851 m | +1.265 m | +50.632 m·s |
| H02 | 3.483 m | 1.471 m | +2.012 m | +103.477 m·s |
| H03 | 7.647 m | 8.710 m | −1.063 m | +14.301 m·s |

“2/3 改善”是 **`source_estimate_trace.csv` 中 `POSTERIOR_MAP` 的源定位误差**，不是机器人距离。评价器 `tools/cstar_evaluate_cer_house123.py:12–29` 直接对 `estimate_x/y` 与真源求欧氏距离；AUC 同样是源误差积分，而且积分范围是首末有效记录，并未外推补齐 0–240 s。三例 M1R 均为预算超时，不是宣布找源成功。开发门槛对 M1R 的局部 `pass=true` 不改变完整包 `NO_GO_NO_MULTISEED`，更不构成独立验证。

## 已有反证对下一机制的限制

- 历史 9 月 8 日结果缺完整候选逐事件概率，无法精确重放 M0 persistence-only、M1 absolute-source、M2 source/context 三臂归因。9 月 12 日仪器化复现的观测、轨迹、二进制和时间戳均与历史不同；其结果必须单列为开发复现。
- 仪器化 H03 最后更新的真源所在叶，在 70 个正块中有 66 个原始 `p_sim=0`；其候选叶虽然包含真源，forward 不是该真源物理响应。最终 M1R 在线真源叶质量约 `3.28e-168`、源 MAP 误差约 `8.880 m`。这使“源后验已经基本正确、只需改 planner”缺乏支持。
- `ONE_NEXT_MECHANISM.json` 用“晚期真实候选加分”支持可识别性控制，但绝对加分不等于对错源胜出。更新 4 的固定 M2 最强错源对比中，晚半段真源叶−错源仍为 **−223.488 nats**，最新块段仍 **−48.935 nats**；不能据此断言只要忘掉早期证据便能恢复。
- 已有独立验证的重加权上界：固定现有 score、候选支持和轨迹，只允许候选共同非负事件权重时，H01/H02 各 4 次更新都不能严格唯一辨识真源叶；H03 4 次仅是使用真源标签的 oracle 可行，未得到可部署选择器。这不证明改善坐标误差不可能，也不排除换观测/forward，但排除了将共同降权/弃权本身宣称为已解决跨 House 源区分。
- 新 Python 物理 provider 修复了浓度与时序语义，却在同代码 H01 两源实验仍只排对 1/2；真 SA 预测尾过长、振幅过大，普通工作分数反而偏好 SB 零响应。此反证要求先证明新增表示确有相对源证据收益，不能把“更物理”自动视为因果创新成功。

## 可部署信息清单与不能假定的信息

| 可利用的信息 | 当前状态与边界 |
|---|---|
| 本机至当前的连续气体读数、阈值、时间戳 | 传感/记录接口已有；A0 源分数主要保留 hit 图，M1R 仅用当前 hit 与上一块浓度。可进一步利用振幅、上升/衰减、抵达与持续时间，但观测规律尚需校准。 |
| 本机过去的位姿、已执行移动/停止及测量块 | 已有；可区分同一次物理 stop 内的相关块、不同位置/时间的观测。动作由既有策略选择，不能未经假设便当随机干预或忽略选择偏差。 |
| 本机过去的局部风观测、严格过去时刻的 GMRF 场 | 已有接口与导出；局部 prequential 风误差已检验。离开已访问位置的风、跨域输运误差和风到浓度的误差传播尚未校准。 |
| 占据地图、可见性、自由区候选及其区域边界 | 已有；可约束输运/路径与候选，但区域代表响应不等同精确真源响应。 |
| 候选 forward 与候选间共享随机数 | 可计算；共享 nuisance 的物理含义、分布与源无关性须明确。随机数配对本身不能校正错误 forward 或产生缺失浓度信息。 |
| 连续浓度、持久传感状态的新物理模型 | Python 诊断实现已有，尚非经验证的在线 PMFS M1；需要同输入普通贝叶斯对照，不能假定已可部署。 |

不可使用真源标签选权重、真实全场风/气体、未来观测、未访问区域的真值或按 House 校准参数。现有证据不能判断：真实未知点源的完整响应是否在当前候选族内、共享输运分布能否跨 House 校准、哪种新时序统计可稳定区分来源、以及任何修复的闭环净收益。

**最小下一机制的必要条件：**新增模块必须明确拿回底座丢失、而部署时可得到的信息，并在 Bayesian accumulation 前改变真实候选与主要错源的相对证据；源干预、共享 nuisance 和识别假设必须能区别于同 provider 普通生成式 Bayes。仅做 posterior 展宽、旧分数重加权、置信拒判、sensor-only 修补零输入、或搬动 planner 不能满足这个条件。这是由现有失败得到的设计约束，不是已选定或已验证的新因果理论。

证据入口：`docs/PMFS_M1R_IMPLEMENTATION_FREEZE_20260912.md`；`docs/PMFS_M1_GPT_REVIEW_START_HERE_20260912.md`；`docs/PMFS_M1_OBSERVATION_CONTRACT_FINDING_20260910.md`；`evidence/cstar_cer_ratio_house123_seed12_20260908/CSTAR_CER_RATIO_HOUSE123_SEED12_GATE.json`；`evidence/m1r_mechanism/M1R_THREE_ARM_REPLAY.json`；`evidence/m1r_mechanism/M1R_HISTORICAL_REPLICATION_COMPARISON.json`；本目录 `PAIRWISE_PREMISE.json`、`REWEIGHTING_CEILING.json`、`VERIFICATION.json`。所有具体结论均由本次 checkout 读取验证。
