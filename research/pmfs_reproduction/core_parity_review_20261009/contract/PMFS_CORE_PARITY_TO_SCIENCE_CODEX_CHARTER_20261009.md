# PMFS 原生基线复现与科学问题定向筛选：统一执行合同（2026-10-09）

> 给 Codex 的唯一下一轮任务。开题报告已冻结，不更改 Word。本轮不寻找新数据集，不训练新的网络。先证明哪一层是原生 PMFS，哪一层只是适配。

## 0. 需要先纠正的表述

Codex 当前说法：「调用公开 PMFS 的核心概率更新与扩散推断代码，但使用自定义离线适配器和参数，不能称为完整、未经改动的原生导航流程。」该表述合理。请进一步划分：

- **A 历史自定义离线适配版（ADAPTED-OFFLINE）**：官方核心 API 可能被调用，但数据、参数、ROS 消息、风估计、候选源/时间和导航不完全一致。旧 H02 为 `UNRESOLVED_CONTRACT_HOLD`。
- **B 官方算法核心严格回放版（CORE-PARITY-REPLAY）**：使用逐字段匹配的官方有效参数和合法且完全同一组观测/源候选、风场、时间轴；验证原生在线与离线同一步更新的数值一致性。可验证科学归因及离线算法，不宣称复现原论文导航结果。
- **C 官方系统闭环版（PAPER-CONFIG-FULL-PIPELINE）**：`Environment_config/PMFS` 的场景、GADEN/ROS、实际风场、传感器、机器人导航/运动策略、停止规则及输出，按固定 commit 和运行时合同复现，才能称“官方配置下完整系统复现”。与作者当年完全相同的随机实现若未保存，不可声称逐数字复现论文实验。

明确每项结论到底由 A/B/C 哪一级支持；不给 B 写成 C，也不因为缺 C 否认 B 的有效方法级实验。

## 1. 官方锚点与旧审计（必须复用）
- 官方仓库 https://github.com/MAPIRlab/GasSourceLocalization，先固定具体 commit；2024 论文对应版本与现用 `humble` 当前 HEAD 的差异需审计，不能仅写“官方最新版”。
- 官方源码：`gsl_server/src/gsl_server/algorithms/PMFS/{PMFS.cpp,PMFSLib.cpp,MovingStatePMFS.cpp,internal/Simulations.cpp}`，以及 `gsl_server/CMakeLists.txt`。
- 官方场景 `Environment_config/PMFS/scenarios/B/simulations/B1.yaml` (House01) 和 `C/simulations/C1.yaml` (House02)，`basicSim` 起点、`params/gaden_params.yaml` 和 `launch/main_simbot_launch.py`。
- 2026-09-23 旧 `research/native-pmfs-baseline-recovery-v1`：已有参数差异136行、27个核心文件字节比对、R0 21次 ground-truth wind service PASS、R1同一观测快照87叶三臂回放。勿重复已经合格的静态审计，但要注明尚未逐字节对齐归档的旧 R2 可执行文件。
- H02 R1 2026-10-09 `UNRESOLVED_CONTRACT_HOLD`：历史累积饱和概率图、第二例更新前 NOTH​ING、近零 GMRF 风、未收敛；不要描述成原生 PMFS 的真实物理失效。
- 旧 `M0_STOP` 等其他 STOP 原样保留。

## 2. P0：现有“官方源码核心”到底保持了什么（只读优先、零仿真）
输出 `CORE_ADAPTER_DIFF_MATRIX.csv`，逐模块列：官方函数入口、是否原函数直接调用、源 blob/hash、本地改动、运行时适配行为及是否影响输出。至少逐项检查：
1. 连续观测/传感器事件抽取、原始测量阈值、漏检、传感器动态与模拟时间；
2. hit-map `logOdds`、confidence 更新、地图传播；
3. 真实风 `USE_GADEN` 编译开关、`useWindGroundTruth` 运行分支；GMRF wind to/from 方向、值域与收敛状态；
4. 候选源 quadtree 的生成、细分、原始源叶支持和候选叶内随机采样/RNG；
5. 单格源证据、聚合、`sourceDiscriminationPower`、归一化与来源排名；如果 `D=1` 是源码默认但官方 launcher 用 `D=0.3`，如实标注，不混淆“非法”与“非论文配置”；
6. `stepsSourceUpdate`、仿真 `deltaTime`、预热/记录步数和正态噪声；
7. robot/navigation 行为路径、停止时间300s、测量等待时间、Nav2、信息驱动采样及 `MovingStatePMFS.cpp`；
8. observation XYZ/高度与 sensor frame、场景 mesh/occupancy、保存/播放记录 timestamps；
9. 原论文 2024 commit 或发表版与当前 `humble` 代码差异。
每一项判断 EXACT / EQUIVALENT-WITH-TEST / DEVIATES / UNKNOWN，提供可审查的源码行号和哈希。不要简单用“用了原始 PMFS 核心”替代测试。

输出 `RESOLVED_PAPER_CONTRACT_B1_C1.csv` 和 `LOCAL_ASSET_MATRIX.csv`：逐字段比对官方 B1/C1 的源位置XYZ、气体参数、所有入出口、风文件、机器人起点、实际源高及占用地图。有缺失就标 MISSING，不能以相似 House 的不同配置替代。

**P0 可立即执行并完成；完成后进入 P1 的条件是同一观测快照和可信的原生状态可获得。**

## 3. P1：最短核心函数等价性测试（禁止新 CFD/GADEN）
寻找旧恢复 R1 PASS 的 87-leaf / 20-observation 快照或另一份合法的官方 B1/C1 快照，冻结同一输入。

A. 原生在线过程导出被动记录：原始传感器事件，hit-map完整 logOdds/confidence，风向/速度与2D网格，候选源集合/种子/细分树，候选模拟 hit-map 和 raw source logscore。
B. 用当前离线适配器读取 **字节相同的输入**；保持官方有效参数和 RNG，单步复算。允许固定 RNG 种子或直接注入原生候选采样序列，但不可引入 truth；必须注明 RNG 语义。
C. 逐层比较传感器事件 → hit-map → 风/地图 → 候选源 hit-map → 得分与归一化后验 → 真源rank。定位第一个分叉环节。float64/float32 区分并报告 max abs/max rel，设置数值容差于试验前（建议各精度按数据格式说明，不得根据结果调门）；候选叶ID、概率图热点及 rank 同步审计。
D. 若导航策略不一致，只能确认核心数值等价，**不升级至 C**；若核心不同，请修复或独立隔离为 adapter variant，不能改原官方源码后声称相同。
E. 同一快照的官方核心＋官方 launch 参数为主基线；R2 自定义参数保留为历史对照，需明显隔离。

**P1 verdict**: CORE_PARITY_PASS / CORE_PARITY_FAIL / CORE_PARITY_HOLD。只有 PASS 才允许用该适配器做 *方法级* 正式比较。

## 4. P2：只在资产齐备后做一次官方 C1 完整运行
- 这是系统级复现，不是重建20组/重启 M0。使用预先有合法原始气体记录及作者场景匹配的 C1；若缺匹配气体记录，只出缺失清单和单次生成资源预算，等待用户批准后生成，禁止直接批量生成。
- 使用原生编译＋ROS2/GADEN/风服务＋传感器＋原生动作选择＋导航＋原生停止判断。最大搜索时长按论文场景 resolved value，示例 `maxSearchTime=300.0`；最终使用的物理时间与帧号必须审计。
- 只被动记录每次 source update 的候选后验、MAP/rank、观察事件、实际运动/时间、compile flags、重要环境变量。任何日志修改不可改变 RNG/动作序列，需验证。
- 真实源真值只供事后评分，禁止用于选择航迹/候选/最优阈值。
- 与 P1 固定轨迹离线比较区分两种协议：同观测同航迹的算法比较可以归因于 source inference；各方法自主运动的完整闭环比较还包含策略/观测路径差异。
- 如果数据合同不合格，`FULL_PIPELINE_HOLD` 并停止。

## 5. P3：优先测试一个可证伪的机制（仅 P1合格；零新气体模拟优先）
假设：在时变风场下，累计历史命中地图与当前时刻候选源传播模拟使用不同的物理传播条件，可能导致源—受体证据失配。不是已证明的缺陷。典型气体观测会受源位置、过去时段的流场、释放和传感器响应联合影响。

预先分辨三种机制：
- H_a **输入/配置错误**：风向、编译开关、时钟、源高度、候选网格或适配产生损伤；只能作为工程修复；
- H_b **本来不可识别**：多个候选源在相同合法观测路线上的响应高度相似，任何方法难以定位；
- H_c **模型/证据一致性不成立**：合法时钟、风场和候选网格下，正确源的模型-观测残差异常，并导致源后验伤害。

低成本冻结对照（同场景、同候选、同传感器事件）：
1. 当前官方 PMFS 累积证据＋当前风场模拟（基线）；
2. 正确传感器/气体时钟对齐的短时观测块评分，仅作诊断；
3. 有合法逐时风历史且 P1 PASS 时，做时段条件一致的源—受体预测（试验方法），并用**风时序打乱或时间错位**作为负对照；
4. 简单遗忘或时间加权以及多错误传播模型应视为已有人研究过的对照，不得直接宣称创新。
冻结评价：前向观测误差/零因子/源排名/MAP m /真源概率与NLL/Brier；独立气体 realization 按完整 episode 评估，不能把相关时间片当成独立样本。若任务二源后验饱和则只标 UNDERPOWERED，不算正信号。
新方案必须出现清晰物理因果方向：正确时序改善、错乱时序不改善，且在真实源候选支持和至少两源两背景条件下重复；若现有数据达不到，这轮只输出 feasibility/HOLD，不加 seed 捞结果。

**P3 verdict**: ENGINEERING_ONLY / NO_IDENTIFIABILITY / PHYSICAL_EVIDENCE_SIGNAL_EXPLORATORY / UNRESOLVED。不得在这轮训练新世界模型或申请 SCI 正效果声明。

## 6. 控制预算、交付与停止
- 本轮尽可能只读、不下载新数据、不修改旧分支原始记录；GADEN重新生成必须另行授权。
- 单独新分支提交脚本、合同、参数差异和小审核包；保留任何旧冻结 STOP 和审计结果。
- **P0 + P1 作为这轮必须完成的闭环工作**；缺状态就标 P1 HOLD。
- P2 只有 P0/P1 足够且现有官方精确匹配气体记录、ROS 环境合格时才允许运行最多一条；缺任何要件只报告不新生成。
- P3 只读离线诊断在 P1 PASS 且完整物理时序数据可用时启动；所有正结果必须标 exploratory。
- 交付 `PMFS_CODE_AND_ADAPTER_DIFF_zh.md`、`CORE_ADAPTER_DIFF_MATRIX.csv`、`RESOLVED_PAPER_CONTRACT_B1_C1.csv`、`LOCAL_ASSET_MATRIX.csv`、`CORE_PARITY_RESULTS.json`、`SCIENTIFIC_MECHANISM_TRIAGE.md`、`GO_NOGO_zh.md`，以及可独立验证的 <=20MB 审核 ZIP；在 GitHub 提交检查点。
- 给出一条最终结论：①离线程序能否用于正式方法对比？②是否有合法原生 C1 完整复现？③现有数据有没有真实、非平凡、可重复的物理证据失配？④若缺证据，最小补齐是什么？
- **绝不宣称**官方原生闭环已复现、通用PMFS缺陷已证实或创新已成功，除非各级门实际通过。

## 7. 开题用语（冻结）
第一篇研究方向暂为「基于物理传播约束的湖岸无人机气体源概率定位方法研究」，内含「源—受体历史证据一致性」这一待验证方向，保留2D source posterior+3D/2.5D latent plume path/shape/concentration短时预测作为完整目标；失败机理确认前不写数值改善。
