# M1R 固定源位置与区域证据边缘化：推导、代码对应和两臂初筛边界

日期：2026-09-12。状态：`SOURCE_SEMANTICS_REPAIR_TWO_ARM_SCREEN_SPECIFIED_NOT_RESULT`。

本文件由本轮已读取的源码、旧研究文件和跨域文献核验报告整理。没有新增文献检索，没有访问 VM、读取 bank payload、运行 forward 或实验。文献启发、数学推导、历史实测和本轮拟实施方案分别陈述；本文件不提供定位成功、因果识别或新颖性背书。

**结论：将每气丝重抽源位置，改为每次完整模拟固定一个源位置、完成全前缀事件评分后再对位置边缘化，修复了 M1R 内部“固定未知点源”的表示语义。它不是新的 2026 因果理论，未修复全部输运及观测失配，也不能预先保证 H03 收益。** 本轮只做 `BASELINE legacy1` 与 `FIXED_SOURCE` 两臂完整修复初筛；不包含中心点臂或算力匹配臂。

## 1. 源码事实与三个不同概率对象

历史 `runSimulation` 使用 `SimulationSource(node, metadata, rng)`。`simulateSourceInPosition` 在 warmup 和 recording 的每一次气丝释放时调用 `source.getPoint()`；quadtree 模式下 `getPoint()` 每次递增 `pointDrawIndex`，重新从矩形区域均匀抽一个坐标。`firstSampledSourcePoint` 仅记录第一个抽样，不会使随后抽样固定。

| 对象 | 源位置机制 | 正确解释 |
|---|---|---|
| 旧区域发射 | 每个气丝独立抽 `U_j ~ pi_R` | 区域内分布式释放，不是固定未知点源的证据边缘化 |
| 固定位置后边缘化 | 一次抽/选 `U`，整个模拟和被评分前缀共享它，再对 `U` 混合 | 固定未知点源的有限混合近似 |
| 代表中心点 | `pi_R = delta(center_R)` | 单点近似，丢弃区域内位置不确定性；不能称完整区域边缘化 |

源码位置：[Simulations.cpp](../../ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp)，函数 `runSimulation`、`simulateSourceInPosition`、`SimulationSource::getPoint`；类型定义见 [Simulations.hpp](../../ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp) 的 `SimulationSource`。改动前本轮读取的行号分别为 830、6933/6964、7001–7033；这是修改前定位，最终行号可能变化。`Point` 构造函数原已存在，并被 shadow、旧 PC-ACI 和 point replay 使用，因此固定点 forward 不是新增底层能力。

“完整模拟”在这里仅指一次 native warmup + recording。native forward 仍输出时段聚合 hit map，随后在记录位置上读取该图；它没有因此变成观测真实时钟上的完整物理浓度轨迹。

## 2. 两个可手算的反例

### 2.1 每气丝重抽与固定未知源的 occupancy 不同

这是说明性玩具模型，不是 House 数据：区域有两等面积部分 A、B。来自 A 的一个气丝在考察时刻必命中目标格，来自 B 的一个气丝必不命中。同一时刻释放 5 个气丝，观测统计为“至少一个气丝命中”。

- 每气丝独立重抽位置：5 个气丝全部来自 B 的概率为 `(1/2)^5`，所以命中概率是 `1 - (1/2)^5 = 31/32 = 0.96875`。
- 整次释放共享一个固定未知位置：`U in A` 时全部命中，`U in B` 时全部不命中，所以混合命中概率是 `1/2`。

更一般地，若给定 U 的气丝命中概率为 q(U)，且玩具模型中气丝在给定 U 后独立，则两者分别是 `1 - (1 - E[q(U)])^N` 与 `E[1 - (1 - q(U))^N]`。二者通常不等；这个关系不能不加条件地当作真实湍流的定量公式。它足以证明“每气丝重抽”与“固定源边缘化”是不同的生成对象。

### 2.2 证据乘积与位置期望不能交换

另一个说明性模型：U 等概率取 a、b，两个已观测事件都是 hit。给定 a，事件概率为 `(0.9, 0.1)`；给定 b，为 `(0.1, 0.9)`。则

```
E_U[product_e p(hit_e | U)] = (0.9*0.1 + 0.1*0.9)/2 = 0.09
product_e E_U[p(hit_e | U)] = 0.5*0.5 = 0.25
```

第一式要求一个固定 U 解释两个事件；第二式允许每个事件重新混合位置。这与 2.1 是两个不同层次的问题：native 每气丝重抽先改变 forward；即使得到正确的固定点 forward，若先平均概率再乘事件，仍会破坏共享 U 的证据语义。`E[product] != product E` 的方向并不固定；不能从玩具例推断修复必然提高真实源分数。

## 3. 本轮实际冻结的两臂方案

每个 quadtree 自由区域 R 的物理矩形端点为 `a_R, b_R`。固定四个相对位置：

```
F = {(.25,.25), (.25,.75), (.75,.25), (.75,.75)}
u_R,j = a_R + F_j * (b_R - a_R),  j=1..4
pi_R,j = 1/4
```

坐标逐轴运算。它们是事先固定的矩形四分点积分规则，不由真源、气体记录、House 成绩或运行后的排名选择；不是精确连续区域积分，也不是“真源一定被四点命中”的保证。四点须有限、位于区域内且映射到合法自由格；不合法时报告实现/支持失败，不改成靠近真源的点。连续位置先验的四点近似误差本轮没有保证。

| 臂 | 源评分 forward | planner 使用的 hit map | 每叶、K=1 的 forward 次数 |
|---|---|---|---|
| `BASELINE legacy1` | 原每气丝重抽区域源；一个 transport replica | 原 `result.hitMap` | 1 |
| `FIXED_SOURCE` | 四个固定点各做完整模拟，分别全前缀评分后等权混合 | 另行保留同规则生成的原 `result.hitMap` | 5 = 1 legacy + 4 fixed-point |

两臂使用历史 M1R 的 rolling persistence、事件定义、clipping、transport 数和原 controller 配置；不开启 sequential assimilation、FOPDT、新的 transport pooling 或额外规划目标。U 与 K 分层保存：每个 U 下保留 K 个 transport maps，本次 K=1，不能把四个 U 伪称为四种输运环境。

本轮读取的实现块已在 `runSimulation` 内生成上述四点，类型为 `SourcePointComponent`，设置独立的 `sourcePointComponents`；对每个 U 使用 `SimulationSource(component.point, ...)`。同一 source-update/transport member key 复用于四点，U 不加入 transport random key。候选共享随机 key 是数值对照安排，不是外生风干预，也不是候选间完整物理噪声路径对应的识别保证。

**算力不匹配。** 固定源臂每叶 5 次 forward，对照每叶 1 次；实际总耗时还受自适应细化和闭环路线影响，不应直接假定整次实验恰为 5 倍。本轮两臂只能评估完整修复包的快速开发收益，不能单独分离固定源身份、四点相对中心点的几何覆盖、多次模拟、context 改变等因素。没有中心点臂、等算力 legacy 臂或积分点数消融，不能据此报告这些因素各自的因果效应。

## 4. 当前 context 条件下的全前缀工作证据

令 v 为本次源更新，`H_v` 为目前可用的完整观测记录，`R_v^0` 为本次更新的有效首层区域集合（`resultsFirstLevel`），`C_v` 包含本次估计风、地图、该首层集合和 forward 配置。对过去事件 e 的位置 `x_e`，从当前更新生成的固定点 hit map 中读取

`p_v(R,u,k,e) = hitMap_v(R,u,k)[cell(x_e)]`。

本轮保留历史 M1R 的算术候选 context。固定源臂先在区域内混合原始 hit 概率，再按本次更新的有效首层区域等权平均：

```
bar_p_v(R,k,e) = sum_u pi_R(u) * p_v(R,u,k,e)
c_v(k,e) = (1 / |R_v^0|) * sum_{R in R_v^0} bar_p_v(R,k,e)
```

这一步均值只用于构造候选共同 context，不用于代替各 U 的事件证据。首层区域仍各计一次，不能将四点展开后错误改变区域权重。`BASELINE` 的 context 按原区域发射 hit maps 同样跨有效首层区域取算术平均；因此固定源臂的 context 数值也可能改变，这属于本次修复包。`initializeContrastiveEventContext(resultsFirstLevel)` 每次源更新只调用一次；随后所有自适应细化子叶沿用同一个 `c_v`，不按每层候选集合重新估计 context。当前源码定位为第 590 行初始化、第 698 行仅评分细化结果。每个细化子叶仍独立生成其自身四点 maps 和位置混合似然。

令 `clip(p)` 截到 `[1e-4, 1-1e-4]`，`sigmoid` 为 logistic 函数。历史 persistence 记为

`a_e = 0.5*erfc((log1p(threshold_e) - log1p(previous_recorded_concentration_e))/sqrt(2))`。

首次记录的 previous concentration 为 0，随后按已记录块滚动。固定点工作概率为

```
q_v(R,u,k,e) = clip(sigmoid(logit(clip(a_e))
                          + logit(clip(p_v(R,u,k,e)))
                          - logit(clip(c_v(k,e)))))
ell_v(R,u,k) = sum_e [h_e*log(q_v(R,u,k,e))
                     + (1-h_e)*log(1-q_v(R,u,k,e))]
L_v(R) = sum_u pi_R(u) * sum_k rho_k * exp(ell_v(R,u,k))
```

本轮 `rho_1=1`、四个 `pi=1/4`。实现先完成每个 `(R,u,k)` 的整个事件 log 累加，再以普通算术混合边缘化。不能用几何均值、最优点、最大似然点或按结果重估四点权重代替。

数值边界与数学公式分开：本次核查到的 `sourceProbFromContrastiveEvents` 使用 `long double` 的 `std::exp(logLikelihood)`，再做 K 混合及外层 U 混合；没有指数下限钳制或 log-sum-exp 实现。已有 `[1e-4,1-1e-4]` 是单事件工作概率的 clipping，不是指数的 numerical floor。指数下溢至 0 会由 `CER_RATIO_LIKELIHOOD_INVALID` 显式拒绝；因此上式并非无限长前缀上的机器精确保证。如最终冻结另外引入 `expLongDouble`/指数 numerical floor，须按真实 helper 的下限与钳制位置同步本段及实现绑定，不能把尚不存在的 floor 写成当前已实现机制。

这里对 `C_v` 和当前前缀条件化：所有旧事件在同一当前 forward/context 下重新评分；不保存历史各时刻完整 plume，不维护一个跨更新的物理 plume state，也不保存并递推历史 `P(U|R,H)`。全前缀重评分继续替换当前源权重，不再乘入由同前缀产生的旧后验。若将来改增量评分，必须另行维护 U 的条件权重/状态及一次消费语义；那不是本轮方案。

在源更新时使用当前已经获得的风信息是在线可得的，但它可能晚于旧事件 e。因此这些因子不是每个历史时刻仅用当时信息产生的 prequential 预测。当前候选集合/风估计又可受历史数据影响，故 `L_v` 在这里是冻结 context 下的 M1R 工作证据，不能不加证明地当作完整 SCM 的联合观测似然、校准贝叶斯因子、真实 `p(H_v | do(S in R))` 或 full-generative 因果模型。

## 5. 与源权重和 planner 的接口

`result.hitMap` 保留 legacy 区域发射 forward 的生成及原 blur 流程。固定点 maps 进入源评分和其 candidate-common context；它们不直接替换 planner 的 hit map。

但源权重 `result.sourceProb` 按新 `L_v(R)` 更新，随后自然进入原 `weighted_incremental_variance(result.hitMap[cell], result.sourceProb, ...)` 计算。因而 planner 方差和选择的路径可能改变；不能写成“planner 输出不变”或“变化只发生在离线打分”。保持的是原方差公式、原候选 hit-map 通道及原 controller，而非冻结权重后的决策。

本轮读取工作树的定位：`Simulations.cpp` 第 863–915 行为四点生成块，第 870–873 行明确保留 legacy `result.hitMap`；第 878–879 行是四点；第 899–905 行是 key 与固定点模拟；第 910–911 行构建用于 context 的位置均值。第 599–601 行将 `result.hitMap` 与更新后 `result.sourceProb` 送入原加权方差，第 617 行除以权重和。旧 `sourceProbFromContrastiveEvents` 先按事件求 log likelihood、后对 transport member 算术混合；本轮位置层必须在该完整事件评分之外再混合。

这些行号属于正在实施中的工作树读数，只用于追踪对应关系，不代表全实现、编译、测试或二进制绑定已通过。读取时仓库 HEAD 为 `5bbdba64266283e6a8392237c34948c49a32a508`，但新四点改动尚不能归属于该 HEAD。最终代码、理论、配置、runner 和二进制以主任务冻结 manifest/哈希为准；本文件不代替该绑定。

## 6. 明确的旧用史与 NO-GO 的作用范围

1. [PF_DEI_FINAL_METHOD_FREEZE_V3_REGION_LATENT_20260828.md](../../docs/PF_DEI_FINAL_METHOD_FREEZE_V3_REGION_LATENT_20260828.md)：第 39–51 行已经定义全程固定区域 S、区域内位置 U、输运 Z 与传感状态；第 89–108 行定义几何位置分布和积分点；第 141 行要求每个 carrier/member 以固定 placement 生成完整物理实现。这证明固定 U 后区域边缘化已在项目中提出，不能包装成 2026 新概念。该旧方案的训练/3D/native GADEN 路线不等于本次 M1R 在线两臂实现。

2. [PF_DEI_FULL_RECONSTRUCTION_FAILURES_AND_FINAL_METHOD_20260829.md](../../docs/PF_DEI_FULL_RECONSTRUCTION_FAILURES_AND_FINAL_METHOD_20260829.md)：第 52–69 行记录 region/U 的生成链和代表点不等于区域；第 88 行要求 coherent trajectory 后边缘化；第 90–92 行明确 nuisance marginalization 等已有项目历史。其 V6-A 第 40 行报告频率证据即使移除组件碎裂仍为 0/30 continuous predictive PASS；不能将更好的积分算术视作消除全部 representation mismatch。

3. [CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_NO_GO_20260831.md](../../docs/CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_NO_GO_20260831.md)：真实终止判决为 `CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_NO_GO`。H01 固定 U0，210 carriers，6 个 predictive K、7 个 prospective observation K；比较跨 stop 保持同一 transport realization 与逐 stop redraw/marginalize K。排名增量为 `-7.16075904e-05`，3 胜 4 负。它否定该 K-coherence 主创新增益，**没有比较每气丝重抽源位置 U 与固定 U**，因此不能直接说本次 U 修复已经被该实验否定；同样不能用此次 U 修复重新启动/改名该已失败 K 机制。相关旧 evaluator 为 [evaluate_ctt_h01_fixed_u_transport_gate.py](../../experiments/cg_pc_ctt/ctt_final_hazard_20260830/evaluate_ctt_h01_fixed_u_transport_gate.py)，本轮未运行。

4. [PMFS_M1_OBSERVATION_CONTRACT_FINDING_20260910.md](../../docs/PMFS_M1_OBSERVATION_CONTRACT_FINDING_20260910.md)：第 35–39 行已经识别每气丝区域采样与固定未知源的区别；第 60–63 行要求 fixed-source hypotheses 的区域边缘化。因此此次修复落实已知问题，不是首次发现。

5. [PMFS_M1_GPT_REVIEW_START_HERE_20260912.md](../../docs/PMFS_M1_GPT_REVIEW_START_HERE_20260912.md)：第 19 行列出已实现的固定候选源、时序气丝、物理 ppm、持续 FOPDT、严格过去估计风读取；同实现 H01 真实 SA/SB 两例源排序仅 1/2 正确，V3 oracle 参考半径两例均弃权。源坐标固定的校验见 [filament_observation.py](../../experiments/ctpi_cstar/m1_causal/filament_observation.py) 第 73–91 行。旧失败表明“固定源 + full temporal + FOPDT”本身没有解决失配；本次差别仅是保留在线历史 M1R 其余机制，替换区域发射/位置积分语义，并观察 H03 快速闭环初筛。

6. [PMFS_M1R_CAUSAL_GOAL_AND_SHORTEST_PATH_20260912.md](../../docs/PMFS_M1R_CAUSAL_GOAL_AND_SHORTEST_PATH_20260912.md)：第 58–59 行指出含真源叶绑定通过不等于精确物理真源点响应；H03 叶为 5×3 单元，代表中心距真源约 0.71 m。这是不能用中心替区域的证据，不证明本次四点恰好修复了 H03，也不允许按这个真源距离挑积分点。

另有区域位置混合的真实参考代码 [m3_phs/phs.py](../../experiments/ctpi_cstar/m3_phs/phs.py) 的 `marginalize_region_laws`；它处理给定 route/outcome laws 的位置混合，并非本轮 M1R forward 已验证成功。

## 7. 正式 2026 文献：借鉴与不能移植的部分

Cheng Shi et al., **High-rate phase association with travel time neural fields**, Nature Communications **17, 8140 (2026)**。正式 DOI：**10.1038/s41467-026-74092-y**；[期刊全文](https://www.nature.com/articles/s41467-026-74092-y)。本轮先前核验记录见 [GEOSCIENCE_2026.md](GEOSCIENCE_2026.md) 第 11、18–26 行。本文件整理阶段没有再次搜索；此前尝试直接重开网页收到 Nature 身份跳转错误，故这里的原文方法摘要依赖同一工作区内已完成的核验报告，不声称本次再次完整读取成功。

HARPA 的多台站到时关系 `t_ij=T_c(s_j;r_i)+tau_j` 与共同低维介质 latent code，使多个接收位置/事件受共同源与介质约束。可借鉴的科学思想是：本应共同的物理原因不能在每个观测中任意独立重选，否则会放宽错误解释。

不可移植之处：单 UAV 的持续湍流气源没有自动提供多台站同一地震事件的关联到时、共同发震时刻或 P/S 两种传播相位；HARPA 的神经 travel-time field 和联合优化也不是本次算法。本次四点区域混合的公式来自普通潜变量概率边缘化，不来自 HARPA 的新识别定理。HARPA 不为 PMFS 的几何、输运、hit surrogate 或四点积分提供一致性/唯一性/跨 House 保证。

因此文献只能作为跨域结构启发和问题审视依据；项目已有 8 月 U/Z 推导，不能用新论文年份改写旧算法的新颖性。新主创新仍需额外、此前未有的源辨识信息与不可由普通生成式贝叶斯解释的独立贡献；本轮初筛没有预先满足这些条件。

## 8. H03 seed12 初筛能回答什么

本轮只回答：在冻结的 H03 seed12 设置下，把在线 M1R 的区域发射语义和位置证据混合整体替换，同时保留原 hit-map/planner 通道，是否得到可复核的源证据与定位结果变化。源权重变化引起的路径反馈属于闭环结果的一部分。

必须并列保留两臂完整运行状态、代码/配置/输入身份、实际 forward 次数与耗时、最终定位误差和已有过程指标；单 seed 的改进仍是开发初筛，不是跨 House、未见种子或主创新确认。若出现完全相同的固定点候选响应，任意位置混合都不能凭空制造身份信息；若四点/原生输运不能解释真源观测，语义更一致也可能更差。

不预设改善方向；不把全部弃权、更多计算、更换候选支持或事后选择积分点算作机制成功。两臂不能隔离中心位置、几何覆盖、采样数等贡献，也不能推翻旧 full-temporal/FOPDT 或固定 U 条件下 K-coherence 的失败记录。

本文件由理论子任务新增；未修改运行算法、旧判决或实验结果。正式实现与实验执行状态须由主任务另行绑定。
