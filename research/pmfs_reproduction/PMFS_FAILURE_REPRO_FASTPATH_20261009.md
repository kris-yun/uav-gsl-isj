# PMFS 原生复现和真正可改进机制筛选：最短路线（2026-10-09）

## 当前结论 / evidence labels
1. 2026-10-09 `PMFS_H02_FAILURE_ROOT_CAUSE_R1`：`UNRESOLVED_CONTRACT_HOLD`。两例含真源叶的硬零因子数学复核通过，但风/时钟/编译参数/源叶采样模型仍不闭合。H02 第2例当前读数 NOTHING，累计地图保存历史证据；不可描述成“当前强检出与当前预测矛盾”。
2. H02 历史适配配置 `sourceDiscriminationPower=1`；官方示例 `0.3`，但 PMFS 源码默认值为 `1`，不能说 1 非法。改 0.3 的 frozen score-only 回放使真源非零，但并未恢复正确定位；不能用作创新成绩。
3. R1 恢复旧诊断曾取得：87 源叶、20次观测、同数据单次评分，R2风约 47/87，GT风+R2参数约 14/87，GT风+官方参数约 47/87（结果因归档版本有修正，须以严格 ref/hash 与单一冻结报表绑定）。非 300s endpoint，也不能推导风修正通常有效。
4. `M0_STOP`：40/40 合格解析风机制箱的双候选后验饱和，风改变羽流但没有可重复源后验损伤。不能重开该已冻结箱。
5. `S2X` 仅有每背景×两源×四气体独立实现，两个候选近满分；不等于原生 PMFS 连续源网格后验。
6. 原始官方论文实验在 GitHub `MAPIRlab/GasSourceLocalization` → `Environment_config/PMFS/scenarios/[A-E]/` 配置，B1↔House01、C1↔House02。**官方 repo 存在 YAML 和部分风场文件，不等于已提供精确原作者气体随机实现。**

## G0：0 新仿真的复现资格与因果辨识准备
- 固定官方 Git commit；首先比对 2024 PMFS 对应源码/场景文件哈希，与现用 humble 版本及已审 2026 历史 zip 的差异。
- 对官方 `B1` 和 `C1` 从 3 处解析最终合同：`scenarios/{B,C}/simulations/{B1,C1}.yaml`、`params/{gaden,preproc}_params.yaml`、`launch/main_simbot_launch.py` 及 `basicSim/{B1,C1}.yaml`。输出一行一字段的 `RESOLVED_CONTRACT.csv`；不得根据未绑定 launch 变量臆测生效。
- **静态先核实本地资产存在性**：源 CAD、_occupancy/OccupancyGrid3D、官方风快照序列、匹配源的气体帧、播放器/index/time metadata、机器人初始位姿/TF；按 SHA256 列 PASS/MISSING/MISMATCH。不把其它 VGR House 工况标作作者 B1/C1。
- 核验 `USE_GADEN` 编译与 `useWindGroundTruth` 实际分支，风向 from/to、风数据单位，GMRF 收敛与 fallback。查实源/机器人高度坐标和传感器应答/气体帧 clock 对齐。
- 审核已有一个恢复 R1-C 源更新的 87叶/20观测，源真值后验排名约47；无需新模拟，先做 **候选区域几何 vs 评分支持 vs 观测信息** 的定量分解，确定可识别性。不从这个单例推出模型缺陷。
- 若原作者 B1/C1 精确输入缺失，G0 `DATA_MISSING` 停止，给出最小原生 GADEN 重生成成本/参数，无须重新下载VGR大盘。

## G1：只准一次新官方 C1 完整运行（须另行获用户批准）
满足 G0 之后，以原生 PMFS/GADEN/ROS2 Humble 启动一个 **完整预算** C1 程序（1源、1 seed，允许官方提前停止）；选 C1 因此前 H02 历史零分异常需要独立的干净合同，不能用旧 H02 洗白新实验。
- 保存原生代码/有效参数/ELF/启动输入 sha256；真实风路径及全部 WindPosition 查询，采样 sensor pose/height / frame ID / timestamp。
- 只加被动日志：每一次 source update 的候选叶、真源包含、quadtree sample 位置+RNG、完整 hit-map，原始 logOdds/confidence，评分零因子/概率图及逐次 MAP/credible mass。验证日志旁路不改变 RNG/运行。
- 路线/总观测预算/物理时间证据合法；源真值只供事后评价。
- 只报告一例是否正常复现；不得宣称跨 House 稳健或将一次源 rank 作为 SCI 结果。
- G1 结束分诊：`RUNTIME_OR_DATA_MISMATCH` / `CANDIDATE_SUPPORT_FAILURE` / `INSUFFICIENT_OBSERVABILITY` / `QUALIFIED_FORWARD_EVIDENCE_MISMATCH` / `UNRESOLVED`。
- 若 G1 FAIL/HOLD，先汇报，不追加 seed / 选择有利场景。

## G2：只在 G1 合格后指定科学机制（不要先写新算法）
**优先问题（待证伪）：在同一可信气体观测下，低维候选源前向响应和累积观测证据冲突时，是否出现可重复的源后验排除/失真？**

预声明三种竞争解释，并尽量用同一记录零成本辨识：
A：**观测不足**（原生/更精确的前向均不能区分源；典型可分性/expected evidence 近零）；
B：**前向模型失配**（受控 GADEN 观测和原生 PMFS 模拟在真实源/高度/时钟/风一致下具有显著不同的检测响应；更忠实的受体预测可解释冲突）；
C：**证据聚合失配**（同样的匹配预测，独立新近/累积历史证据的权重分配导致错误支持剔除）。

仅 B/C 在 **独立源、独立随机实现、至少两种物理条件** 重复、且非零源支持、稳定原生时钟/风/传感器合同下，才可申请主创新。可借鉴鲁棒贝叶斯 / generalized Bayes / 大气 source-receptor footprint / distribution shift，但这些原理已有先例，需检索直接竞争与二次物理创新；不能简单夹概率底噪自称创新。

## 输出与停止
- G0：`RESOLVED_CONTRACT.csv`、`ASSET_LINEAGE.json`、`R1C_EVIDENCE_DECOMPOSITION.md`、`GO_NOGO.md`，保留旧 R1、H02 R1、M0 STOP 不改。
- 先结束 G0，用户批准 G1，再执行 G1；G2 需要合格统计支持。
- 开题科研方向可以先陈述“复杂气体传播条件下的源—受体证据一致性与可靠概率定位”作为**待验证研究问题**，而不是宣称成功。
