# V7 独立审计：PMFS 源判别缺口、流体语义与数据资格

冻结日期：2026-10-23。审计视角：B（机器人概率定位及 PMFS 源码）、C（流体、低空气象、传感器与数据资格）、G（建设性反例）。本文件的底层诊断先从原失败记录、官方源码及既有物理资产产生，未读取本轮新附件或其他候选报告。末节的第二轮物理裁决仅响应主代理随后告知的机制候选，不把候选名称当成物理证据。

## 结论先行

最值得计算的缺口是：**候选传播模型在地图上互不相同，不等于机器人在有限观测时间内能获得足以区分源的证据。** 当前执行版 PMFS 的主动评分使用候选地图的加权方差与未观测置信度；它没有显式描述有限驻留时间、共同传输扰动、传感器滤波和可观测空间尺度怎样改变两源可分性。这个缺口可以由源码与反例证明；它是否为 B4 错误收敛的主要物理原因，仍须实验，不能先下结论。

数据侧有一项实质恢复：已从固定仓库提交取回并核验 **OCB-R2 / X00 的两源 × 四独立 seed，共 8 个既有物理导出**，每件有 10 张同钟空间浓度切片。它支持二维切片上的同步空间辨别和按整条 plume realization 留出的开发评估。快照相隔约 50 秒，不能支持高速时间差、动态边界速度、连续观测窗口或原生主动闭环的主结论。原 House01 occupancy 字节尚未恢复，所以释放点合法性与任意移动可达性继续 HOLD。

## 1. 第一轮：从失败与原始函数独立提出缺口

### 1a. 不可回避的失败事实与完整计算链

**B4 的小方差是停止条件满足，不是定位正确。** 原记录末次源更新的 variance 为 0.3290678238，MAP 误差为 5.0316647345 m，均值误差 5.0988983923 m，真源 1 m 区域质量约 0.00041262。原 `PMFS_utils.cpp::checkSourceFound` 第 21–52 行，特别是第 42、45–48 行，以源分布方差阈值判成功；第 33–39 行的真值距离只用于另外记录导航时间。因此 `success=true` 与 5 m 误差并不矛盾。[F1、S1]

原错误候选 W 与真源代表 T 的原始兼容分数分别约 7.71713e-6 与 5.18813e-10，W/T = 14874.5987。统一候选释放面积为相同 1×1 单元后，两个已执行控制仍为 17547.0359 与 20180.7108。更窄的 DIRECT10 单元控制仍偏 W，约 8.1535 与 8.3833。故不能把主缺口缩为面积归一化错误，也不能假定只删除传播得到的地图单元就会恢复正确排序。[F2、F3]

官方源码固定提交为 `MAPIRlab/GasSourceLocalization@4e141e162551e674f2f30ddb8859136c72139aac`；本地逐文件 SHA256 与行数在 `SOURCE_RUNTIME_RECEIPT.json`。关键执行链如下。

| 阶段 | 具体文件、函数、行号 | 实际语义与因果含义 |
|---|---|---|
| 有限观测 | `StopAndMeasureState.cpp` 第 10、13–40、44–90 行 | 停止时收集数据，默认 2 s 后平均浓度、风速与圆周风向。先做有限时段平均。 |
| 二值化与调度 | `PMFS.cpp::processGasAndWindMeasurements` 第 129–189 行；第 136–147 行阈值化，第 153–157 行刷新风，第 161–175 行调源更新，第 178 行移动 | 实际观测是“有限窗口浓度平均超过阈值”，不是直接看到长期 hit frequency。 |
| 地图反演 | `PMFSLib.cpp::EstimateHitProbabilities` 第 19–88 行；第 30–38 行 wind kernel，第 80 行 log-odds 加法，第 84–86 行 confidence 更新 | 一次 hit/no-hit 经局部可见区域及第 90–176 行传播影响多个格点；这些格点不能当作同样数量的独立原始传感器观测。confidence 主要随空间距离累计，并不等同有效独立时间样本数。 |
| 候选模拟 | `Simulations.cpp::simulateSourceInPosition` 第 285–380 行；`moveFilament` 第 271–276 行 | 二维风加高斯速度扰动；第 350–360 行按每步某格是否有 filament 记录二值占据，第 374–378 行取占据频率。它与有限窗口阈值化浓度均值的观测算子不同。 |
| 源评分 | `sourceProbFromMaps` 第 231–245 行；`probabilityFromSingleCell` 第 248–263 行；`probabilitySingleFrequency` 第 266–269 行 | `total=1` 后重新乘各自由格的相容因子；当前编译分支为 `1-c_i D |p_i-h_i(s)|`。它不是按原始时间窗标定的完整测量似然。 |
| 更新 | `updateSourceProbability` 第 82–197 行；第 189–194 行归一化 | 重算并覆写源分数。不是每轮把旧源 posterior 又乘一次。历史依赖在累计地图和当前模型评分中，而非上述错误描述。 |
| 主动选点 | `MovingStatePMFS.cpp::chooseGoalAndMove` 第 27–118 行；`explorationValue` 第 264–279 行；`informationValue` 第 281–297 行 | 按当前地图、模拟结果与可达目标主动选点，不是固定航线。实际 informationValue 第 291 行采用 `varianceOfHitProb(i,j)*(1-confidence(i,j))`。 |
| 停止 | `PMFS_utils.cpp::checkSourceFound` 第 21–52 行 | 源分布尖锐可触发成功，即使该尖峰落在错误源附近。 |

必须特别区分 **有互信息函数、函数被计算、其结果真正被决策使用** 三件事：

- `chooseGoalAndMove` 第 65 行计算 `calculateMutualInformationGas()`；该函数第 129–239 行确有候选频率桶、条件熵计算。
- 其注释第 120–125 行明确假想得到某一点 hit frequency 的完美知识；第 193 行把假想测量点 confidence 置 1。五桶频率分布见 `HitProbability.hpp` 第 30–43 行，是置信度调节的启发式，不是有限时窗经验分布。
- 但是实际 `informationValue` 的第 290 行互信息读取已注释，第 291 行执行方差代理。邻域循环只改变距离权重，方差索引保持中心 `(i,j)`。因此应审计执行的方差代理，不能把未使用的 MI 公式当成运行结果。
- 第 96 行计算距离惩罚后的 `evaluation`，第 98 行插入集合的却是 `interest`。此固定提交中距离惩罚没有进入排序。可作为基线缺陷修复与敏感性分析，不能包装成研究主创新。

**初始独立假说 H1：** 一份由少量相关观测传播成的地图，经过很多兼容因子相乘后会很尖锐；主动行为又偏好当前模型认为分歧大的区域。在模型或观测算子失配时，“尖锐”和“当前模型的分歧大”都可能与真实源辨别脱节。这解释一种可发生的错误闭环，但不构成 B4 物理原因已经归属的证明。

### 1b. 建设性反例：为何预测更好、地图方差更大仍可能不辨源

反例采用两个等先验源以及两个可选观测动作。仅用于数学否证，不是新 plume 仿真。

| 动作 | 两源预测均值 | 窗口内扰动标准差 | 源间均值方差 | 精确测量互信息，nats |
|---|---:|---:|---:|
| A | −2、+2 | 10 | 4 | 0.01961017 |
| B | −0.5、+0.5 | 0.2 | 0.25 | 0.67594258 |

若两处未观测 confidence 和可见范围相同，按源间均值方差将选 A；有限观测真正提供的信息却在 B 高约 34.5 倍。结果由 160 点 Gauss–Hermite 积分计算，收据为 `FINITE_WINDOW_COUNTEREXAMPLE.json`。反例没有证明 PMFS 必在某个物理世界失败；它证明该方差代理不能普遍替代有限测量源信息。

第二个反例是共模改善：设两源观测为 `m(t)+δ_s(t)+ε(t)`。一个新预测器把大的共同项 `m(t)` 预测得更准，会显著降低整体浓度 MSE；若小的源差异 `δ_s(t)` 未改善、被平滑掉或与扰动混淆，定位仍不改善。这与已有 M4/RK “预测改善但不辨源”的失败结构相容，但不把所有具体失败都归为同一原因。

第三个反例约束修复：降低相关因子的重复计权可使分布变宽，却未必改变 W/T 的符号。B4 DIRECT10 控制已说明仍存在偏错的直接观测相容性。只做相关性折扣、概率温度或归一化不足以宣称修好了源判别。

## 2. 第二轮：收紧计算问题与可证伪门槛

### 2a. 修正后的独立命题

将目标表述为 **给定有限预算与读出算子，哪些可执行观测能排除仍相容的源假说？** 把源身份、传输扰动和观测算子分开建模，但模型可以很低阶，无需预定网络结构或双机配置。

设 `s` 为候选释放位置，`η` 为传输、强度和传感器 nuisance，`a` 为位置或短路径连同持续时间 `τ`，真实可采数据为

`Y_a = H_sensor({c(x(t),t;s,η)}_{t∈[t0,t0+τ]}) + ε`。

研究对象应是不同 `s` 在 nuisance 变化后仍保留的可区分部分，以及在给定 `τ` 后能够实际获得多少这类证据。需要检验的是源对比、反证与误判稳定性，而不是只检验总体场预测误差。关于“先排除错误假说”的候选想法，数据可支持后再比较；不因名称接近上述命题便提前选定。

可复用 PMFS 的占据栅格、可达性、风估计和候选传播骨架；必须明确新证据由哪些原始观测产生，预测与实际读出是否相同，以及它的置信度怎样受观测时长和共模变化约束。普通读出纠正是必要基础，不单独作为主创新。

### 2b. 对本轮候选的物理 Red Team 与最小可实施修正

1. **双侧差分不自动是双机机制。** 同时两点差值可去掉严格共模项；若传输扰动只在局部相关，两点变远后它会变成额外噪声。若两点都处在同一平台或同一扰流区，传感器误差又可相关。先比较同预算单点、同平台双点、异步顺序两点、同步两点，再讨论飞行器数量。
2. **动态边界返回向量需要连续边界运动、物理时钟和足够传感器带宽。** 50 秒切片不能通过线性插值获得这些新事实。空间边缘与局部浓度梯度可作本轮静态对照，但不得标作动态返回矢量。
3. **反后验锁定可以是动作设计假说，仍要接受可辨性约束。** 当前 posterior 很小的源若在所有合法观测下与领先源等价，重复挑战它只是浪费预算；若仅在昂贵或不可达区域可分，必须记真实成本。分歧应落在观测空间并有有限窗噪声尺度，不能仅取模型内部方差。
4. **未知源高度不能在配对时藏进 XY 定位成绩。** X00 两源分别为 `(-0.6,1.95,0.4)` 与 `(-0.4,-2.9,-0.3)` m。两者同时改了 XY 与 z；数据只能支撑“两三维释放位置在 z=0.2 m 观测切片上的判别”。若主张纯 XY 定位，需要固定或明确边缘化源高度的合法世界。
5. **最小证伪端点：** 先报告跨整条独立 seed 的两源误判、源对似然比方向、随读出预算的变化；共同增益/基线扰动、未观测高度、局部风漂移作为单独压力条件。不得把同一世界的 10 帧当作 10 个独立实验。只有八条世界，结果是开发门，不是最终统计确认。

## 3. 本轮实际恢复的 OCB-R2 物理字节

固定仓库为 `kris-yun/uav-gsl-isj`，提交 `005ba6a34d95fdfe340050df96fe30a688fa71bf`。精确路径、Git blob SHA 和逐件 SHA256 见 `ocb_r2/REMOTE_FETCH_RECEIPTS.json` 及 `ocb_r2/RETRIEVAL_VERIFICATION.json`。原始下载仅保留在本轮 `v7_work`；最终交付包仅应包含获授权的最小 manifest、读取/核验脚本和结果，不重新分发全部原物理文件。

| 项目 | 已核验事实 |
|---|---|
| 选择 | 已开放 DISCOVERY 的第一个上下文 X00；先冻结选择再解码数值；未打开 H01/H02 confirmation 或 H03 动态目标。 |
| 八条 run | `ocb_r2_cfg00_r01`–`r04` 与 `ocb_r2_s2x_x00_r01`–`r04`。 |
| 两源 | A=`House01_configured_1`, `(-0.6,1.95,0.4)`；B=`House01_configured_2`, `(-0.4,-2.9,-0.3)`。源真值仅作离线 discovery 标签。 |
| 独立实现 | A seed `2026900001`–`2026900004`；B seed `2026910001`–`2026910004`。八个不同 master seed，不把同 r 编号当共同随机数配对。 |
| 上下文固定 | House01；gas type 13；wind `1,3-2,4_fast`；相同 occupancy、风场 bundle、时间线与生成器 hash。不是两个源同时释放的混合场。 |
| 浓度导出 | 每条 `cube.npy` 为 `(10,87,114)`、float32，轴为 `(time,x,y)`；每条 `pooled.npy` 为 `(10,30)`、float64。共 16 个 NPY，3,195,008 bytes。 |
| 空间 | metadata 指定 `min_x=-7.55`, `min_y=-7.88`, cell=0.1 m, z=0.20 m。单元中心公式 `x=-7.55+0.1(ix+0.5)`, `y=-7.88+0.1(iy+0.5)` 与原 2×2 probe 中心合同一致；原 C++ extractor 的内部落点代码尚未取回，所以此单格公式仍保留该限制。 |
| 池化 | 原 30 probes 的每个读数是指定 2×2 native cells 的 float64 平均。八件均重算 bit-exact，不能误称理想数学点浓度。 |
| 实际物理时刻 | `[50.2998047,100.099045,149.799942,199.802994,249.806046,299.809082,349.812134,399.815186,449.818237,499.821289]` s。来自原 native sidecar，不能用文件编号当时间。 |
| 对应 record | `[92,175,265,365,465,565,665,765,865,965]`；wind index `[8,3,10,10,10,10,10,10,10,10]`。 |
| 时空资格 | 同一帧两个空间点确实同一物理时刻；跨帧间隔 49.700897–50.003052 s。连续窗口与高速时差资格为 NO。 |
| 风资格 | 有 native wind index 和原 wind bundle hash；没有本轮可调用的局地 `(u,v,w)` 字节。hash 相同不等于已拿到局地风。 |
| 读出 | GADEN filament 导出的 molar ppm，未加入真实传感器延迟/噪声/饱和/旋翼扰动。三维传播的二维切片，不是完整三维状态。 |
| 划分 | 每源 r01/r02 可作训练、r03/r04 可作开发；必须整条实现分组，不随机拆快照。所有这些均为历史已开 discovery，无新的盲确认资格。 |

原池化脚本 `research/aod_r2_transfer/extract_f0_targets_vm.py` 的第 71–80 行读取 occupancy 原点与维度后传入原 native extractor，第 83–94 行检查 cube 和计算 pooling。该脚本 Git blob 为 `bdf38820cadb8872eea33e967e160aff84755db0`，原 extractor 可执行文件 SHA 为 `206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91`。[D1]

**源点合法性仍 HOLD。** 原 House01 occupancy SHA 为 `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb`，原位置 `/mnt/hgfs/workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv`。现有 S1 审计只核 hash/文件存在；S2X 冻结脚本只核坐标变更及相同上下文，没有查询源位置所在体素是否 free。`scientific_sanity_pass` 也不是该条件的替代。负 z 仅是坐标，不能据此断言地下或无效；但未见 occupancy 字节也不能断言合法。完整文件、源体素及出生扰动邻域 free-cell 收据是补数合同第一项。

**64 条与八条不能混写。** 原 F0 time mapping/extraction/comparability 元数据证明曾有 8 contexts × 2 sources × 4 seeds = 64 个 discovery 导出；本次真正读出和核验的是 X00 的 8 条。完整 1803 帧原世界位于既有归档 `C:/GADEN_OCB_R2_ARCHIVE/s2_discovery/{run}` 或 `.../s2x_matched_source/{run}`，旧 VM `/home/zyc/ocb_r2_s2_discovery/`、`/home/zyc/ocb_r2_s2x_matched_source/`。仓库有原 hash 清单，但未找到可直接下载的完整原世界 release，不能把文字清单计成已持有世界。[D2]

## 4. 所有现有资产的逐能力裁决

| 资产 | 同钟两空间点 | 连续窗/物理钟 | 局地风 | 多源与独立 plume | 主动移动 | 本轮准入 |
|---|---|---|---|---|---|---|
| OCB-R2 X00 八条已恢复 | 是，同帧切片；pooling 明确 | 钟是；连续窗否，约 50 s 间隔 | 仅 index/hash | 两替代三维源 × 四独立 seed；不是同时两源 | 离线选栅格可，飞行/碰撞/闭环未资格 | 同步空间二类开发；不做动态主结论 |
| House02 18×16 旧导出 | 只可在已定义 pooled record 内对比 | `record_index` 未验证物理秒，不能造真实时差 | 全历史风缺失 | 18 源、16历史实现；训练/开发/原留出按原 scope | 固定探针离线数据 | 离线 source discrimination；原 test 响应禁作在线库 |
| O24 六世界 | 固定脚本查询；须依原 tick 绑定 | 48 unique frames/240 queries，名义 .5 s绑定；旧世界 | 个别记录可用，不升级未取回内容 | 六世界，不是新 seeds | scripted route，不等于新策略反事实 | 机制筛查，不增独立样本量 |
| Cross-house H07/H14 FAST/SLOW | 依原日志 | 有原时间与局地风追踪 | 有原记录 | 四任务，非四独立seed | 原脚本回放 | H14 两任务可用；H07 receptor domain 故障仅作错误检测 |
| B4 原轨迹 | 原单移动传感器日志 | 有原停止测量及更新；非任意双点连续场 | 原轨迹观测/估计 | 一个 episode、一个真源 | 实际 PMFS 主动动作 | 已知失败归因，不作训练分布 |
| CH4 S2 DAY/NIGHT T0 | 是，同 tick 可查询任意合法空间点 | .1 s tick，20 s短窗 | 三维局地风可读 | 固定单源；DAY/NIGHT不同风，不是多源或独立seed | 轨迹读出可，完整飞行/nav/旋翼无 | 读出/时钟/短窗 smoke；不能升级源泛化资格 |

House02 的具体限制见 `source_evidence_recovery_v2/src/gsl_recovery/data/house_v2.py` 第 154–157、179、191、209 行与原 `ARCHIVE_DATA_SCOPE.json`：四 native-cell 空间均值、十 records，物理时钟/风/完整三维资格没有给出。禁止以 record_index 相邻就构建 `Δt=1 s`，也禁止把 test 真源响应当候选的在线模板。

CH4 S2 的 Python 读出在 `.../NIGHT_RELEASE_ONLY_COLDQA/code/ch4_world.py` 第 15–19、33–54 行限制 .1 s step、加载 tick puff，输出浓度与局地风。其完整 Gaussian + voxel LOS 读出是有记录的扩展；数值 cold QA 合格不等于气象、独立源或全搜索资格。既有风场诊断 DAY/NIGHT RMSE 为 .0231489/.0285114，高于 .02 gate；20 s、单源、固定诊断风均不变。旧 OCB 的阶段名 S2/S2X 与这一 CH4 S2 不是同一数据集。

## 5. 原生 GADEN-RT：能复用什么、当前机器能运行什么

本地有 upstream core `1a20e35cd5f174ae9675a2ae3c796137a05c4ee5`，位于 `v6_work/data/s2_review/FSR_S2_CH4_DAY_NIGHT_PRO_REVIEW_20261022/evidence/04_native_upstream/core/`。它有可直接链接的 C++ core，不必先搭 ROS。`RunningSimulation.hpp` 第 13–33 行定义单个 GasSource、dt、wind dt、输出选项；第 42、44 行推进与读钟。`RunningSimulation.cpp` 第 78–104 行有移动、保存和 float 时钟推进，第 111–115 行取局地风，第 183–204 行三维输运。[N1]

需要守住的实现语义：

- 原 `Simulation.cpp` 第 35–49 行 Gaussian sum 有 3σ 截断与 LOS；第 73–85 行越界浓度返回零。适配器必须区分 invalid 与观测到零，不得默默把越界视为无气体。
- `RunningSimulation.cpp` 第 125–139 行出生位置检查 bounds，不能由此推导所有出生点都在 free voxel；要补源体素/出生邻域校验。
- 保存顺序与浮点时间累加使 iteration 不能简单等同 `n*0.1`；本地 clock 审计记录 2 s 约为 2.0000002384，20 s 约为 20.00004005。应输出物理 tick sidecar。
- Public playback 接口可重放当前保存状态；没有完整随机数未来恢复保证，不能宣称同一 checkpoint 未来字节级可继续。
- 构造函数第 50–55 行在 saveResults 时会 remove_all 输出目录；真正执行时必须新建专属输出路径，不能指向现有资产。

**本轮实际 runtime probe 结果：** 有 g++、libgomp、zlib、OpenCL loader；缺 cmake、fmt、yaml-cpp、libbsc、已装 gaden、ROS；OpenCL 平台枚举为零（−1001）。因此目前 Python 现有状态读出可运行，但 native generator 未编译就绪。CPU 构建可行，GPU 不是必要前提；不应为本轮数据门大规模新造世界。

OCB-R2 八条不是上述 1a20 版本新生成：其冻结 generator core 提交 `9e93c36ae1af74f6a62c42f1c9d7b813153222ed`，有保存的 dirty patches，binary SHA 为 `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`。原 A/B/C 资格实验 1803 files/条，同 seed A/C 全相同，异 seed 有 1802/1803 不同。可引用这一既有资格，不能抹掉 generator 版本与补丁差异。[D3]

## 6. 最小合法补数合同：先提取现有世界，不重跑传播

优先在已开放 X00 原归档提取 **两源 × 两 seed** 的连续短窗，若已有四 seed 则保持本轮四 seed 的整条训练/开发划分。窗口范围在看浓度前按物理时钟预注册，例如选一个已有 50 s anchor 附近 20 s，按原原生保存步长导出；不能筛选对拟议机制最有利的羽流片段。

必须一并交付：

1. 原 House01 occupancy 字节/hash、坐标原点/分辨率、释放点体素值、出生扰动支持范围内合法性；声明负 z 对应什么本地坐标。
2. 每帧原 filename、iteration、actual_time、wind_index、内容 SHA；clock 误差容忍和保存前/后状态语义。
3. 该窗的原 `(u,v,w)` 风场或合法空间点的同步局地风；明确风场保持/循环方式，不能用全局平均冒充局地风。
4. 原 filament state 或空间 ROI 浓度序列；给原 extractor 源码/可执行 SHA、点值或 pooling、z、LOS、截断、边界合法性、ppm 定义。
5. 若欲辨快速运动，先证明 native保存与传感器带宽能解析目标变化；插值不提供新时间信息。原 .5 s 保存无法评估更快线索时，换有足够原生分辨率的公开物理数据，或另行批准最小生成任务。
6. 源 truth 与 seed 只供评价；适配器与算法不得拿待测世界完整场、真源标签、未来帧或未授权 test 模板。manifest 标出 discovery/confirmation scope、读取权限及许可；H03 与原 confirmation 保持封存。

补充实验不得从“同一个连续窗切成多块”虚增独立 plume 数。若最终必须重新生成，先完成 native build/one-step smoke 和记录时钟、RNG、源合法性，明确它是新增世界；本轮不靠新生成绕过已有数据的不足。

## 7. 可复用的公开物理数据：已查官方入口，尚未冒充本地可用

| 官方来源 | 独特能力 | 严格限制与当前取得状态 |
|---|---|---|
| MAPIR Virtual Gas Research / GADEN | 与现有 House 世界同源，优先补原 geometry/wind/filament | `https://mapir.isa.uma.es/olfaction-dataset/` 本次打开显示暂时停服；不能声称已下载完整世界。已恢复 OCB 字节优先。 |
| TURB-Smoke DNS | 官方论文描述粒子位置/速度、二维/三维浓度和多个释放位置；适合连续传输和源差异机制 | 理想均匀各向同性湍流，非低空建筑/湖风。部分 dt/10 产品为插值；必须用 native timestamps。入口 SMART-Turb 本次未验证下载。论文 `https://arxiv.org/html/2507.22749v1`。 |
| High-speed e-nose + PLIF | 10 次风洞实验，四空间区域与八 MOX 通道，能校准有限窗和传感器滤波 | PLIF native 20 Hz；1 kHz 对齐浓度是 PCHIP 插值并有标记，不是 1 kHz 原生真值。部分通道饱和。论文 `https://arxiv.org/html/2604.19626v1`；ETH dataset handle `20.500.11850/782611` 本次未成功打开。 |
| RED:VAPOR，DLR / Zenodo | 风洞中四个相隔 24 cm 的垂直传感层，PID/MOX 与局地 3D 风共同采样；真实传感器与空间同步的有用对照 | 39 次实验中的 raster 是长时间顺序扫描，不能当整三维场瞬时同步；有 flythrough/purge，气体/雾混合非甲烷。论文 `https://www.nature.com/articles/s41597-026-06927-8`；Zenodo `https://zenodo.org/records/16414473` 已实际打开，有 3.9 kB overview、82.9 kB header spec、840.9 MB CSV archive。尚未下载大型文件，页面有更新版本提示，应读取最新 metadata 后再选最小记录。 |

这些外部数据可各自补机制门：DNS 检验连续传输、PLIF 检验时间带宽与读出、RED:VAPOR 检验真实同步多点与局地风。没有任何单个入口已经证明本任务的低空室外甲烷双机定位有效。

## 8. 双 UAV 的物理准入条件与必要基线

当前数据不含机体、旋翼、进气管或飞行控制作用，不能把两个数学查询点直接等同两架 UAV 的收益。要把空间对抗线索落实到 UAV，至少要报告：传感器进气口相对机体位置、两机几何和风向、旋翼开启/关闭对局地浓度与风的影响、采样/泵送延迟与同步误差、碰撞/墙面/高度约束、总时间与航程预算。

间距不应由算法任意固定一个“最佳米数”。作为量纲约束，差分的空间尺度需与可测梯度和局地相关长度相容；平流过基线的时间约 `d/|u|`，应与读出/时钟误差和目标时间尺度比较。基线过短会让真实差异淹没在传感器噪声与共同扰流中；过长会降低共模消除并引入不同输运路径。上述是设计约束，不是已测出的最佳间距。

最低对照应覆盖：同总样本/时间的单机主动策略；单机顺序两点；固定几何同步两点；单平台可实现的双传感布局（若几何允许）；在相同调度和总预算下的自适应几何。同步优势、额外传感器优势、额外移动自由度与新判别算法优势应分别有消融。若动态边界机制没有通过真实时钟与传感带宽门，应保留为空间静态判别实验，不能用仿真的漂亮轨迹补上缺失物理。

## 证据索引

- S1：本地 `research_work/v3_pmfs_source/`，官方源码 pin 及 URL 见 `source_index.json`；本轮 `SOURCE_RUNTIME_RECEIPT.json` 保存内容 SHA。
- F1：`source_evidence_recovery_v2/examples/native_b4/B4_OBSERVATION_AND_POSTERIOR_AUDIT.csv`、`TOP5_SNAPSHOT_ESTIMATOR_REVIEW.json`；原终止判决：`https://github.com/kris-yun/uav-gsl-isj/blob/c2aacbac7fb2ef7be4be3c9c7dcfce20c11f823c/research/pmfs_reproduction/b4_official_terminal_resumed_20261010/B4_OFFICIAL_TERMINAL_DECISION_zh.md`。
- F2：原 B4 M0 归因 `https://github.com/kris-yun/uav-gsl-isj/blob/17c48958f9d7eda98dd61b8e656a8c52205cb7d7/research/pmfs_reproduction/b4_m0_offline_attribution_20261010/B4_M0_EVIDENCE_ATTRIBUTION_zh.md`；本地原 receipts `research_work/project_evidence_receipts.json`。
- F3：M1 统一面积原提交 `a41c611b25b276ad86d1baf887153f26bb153df7`，`research/pmfs_reproduction/b4_m1_source_representation_20261010/review/M1_A_RESULT.json`，blob `8e3d91e340449de96fbf1bce22af6cb9fbd14bb7`；本地 `research_work/v2_project_evidence_receipts.json`。
- D1：OCB 固定提交 `005ba6a34d95fdfe340050df96fe30a688fa71bf`，路径 `evidence/ocb_r2/aod_r2_f0/targets/{run}.cube.npy` 及 `.pooled.npy`；34 项恢复收据在 `ocb_r2/REMOTE_FETCH_RECEIPTS.json`。
- D2：同提交 `evidence/ocb_r2/aod_r2_f0/AOD_R2_F0_TIME_MAPPING.tsv`，blob `6b6fd1d08c891a18b9f5a87c7c403e75e316c785`；`targets/AOD_R2_F0_TARGET_EXTRACTION.json`，blob `ef9e23e97e77ab03629bf47aa71d5a60324e6877`；`AOD_R2_F0_D0A_COMPARABILITY.json`，blob `547f5c9e9dcddf0e6c1cd895819838d0db27b670`。
- D3：同提交 `evidence/ocb_r2/BUILD_PROVENANCE.md`，blob `deed3877267f5cf1833837594e8e95f69a690e06`；`OCB_R2_GENERATOR_QUALIFICATION_RESULT.md`，blob `3af08cc71ccb72fef566940168aa2ecc4387ab17`。
- N1：本地上游 GADEN core 与既有 `audit/CLOCK_SEMANTICS_SOURCE_RECOMPUTE.json`、`audit/NATIVE_CURRENT_STATE_PLAYBACK_VERDICT.json`；本轮未执行新生成。

冻结裁决：**PMFS 底层研究问题通过；OCB 八条空间判别开发数据通过；高速动态机制、全源泛化、完整主动双机与完整物理源合法性仍未通过。** 本文件不选定神经网络、蒸馏教师或双机架构，也不以读出纠正取代机制贡献。
