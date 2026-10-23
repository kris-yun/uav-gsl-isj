# V7 Codex 完整实验合同

日期：2026-10-23。目标：完成一次能够区分结构适配、跨领域母机制及气源二次设计收益的研发验证；不把软件跑通、构造性例子或期刊名称当作定位成果。

## 0. 仓库、入口与当前结论

- 仓库：`kris-yun/uav-gsl-isj`。
- 独立分支：`research/active-source-discrimination-v7`。实际发布 commit 以交付根目录 `DELIVERY_RECEIPT.json` 为准；此文件不预写虚构 SHA。
- 仓库内目录：`research/source_localization_v7/`。ZIP 内目录：`source_localization_v7/`。
- 主包：`gsl_discrimination`，命令：`gsl-v7`；本合同锁定依赖的复现环境为 **Python 3.12**。包元数据的 ≥3.10 是宽依赖兼容声明，不能用 Python 3.10 安装本次 NumPy/SciPy 锁定组合。
- 三模块：M1 源对覆盖镜像通道；M2 返回方向管与源响应差编队；M3 全候选成本分配、付费覆盖及新后缀审计。精确算子见 [理论](THREE_INNOVATIONS_AND_THEORY.md) 和 [架构](METHOD_ARCHITECTURE.md)。
- **当前决策：软件可进入原生资产恢复与资格化；不能直接进入论文效果确认。**71 项最终测试通过；156 个 Level 1 episode 已跑完。强基线饱和，新算法未建立独立收益。真实静态 pilot 的冻结直方图 31/40、raw-joint 40/40。完整动态 House、native PMFS/ROS、双 UAV 公平闭环及未见源泛化均未完成。

允许本地 Codex 连续执行以下已授权工作：独立工作分支、读取开放资产、实现提取器与 executor、单元及接口验证、合格训练/开发，以及有访问权限数据上的冻结评测。不更改 main，不覆盖 V1/V2 或本包已冻结负结果。**冻结协议不自动授予数据访问权；H03/confirmation 或其他原封存资产只有在获得新的明确访问授权后才可标记 final，本合同不授权解封。**

## 1. 环境与第一条执行命令

在下载 ZIP 解压后的工程目录，或上述分支的 `research/source_localization_v7/` 内执行：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install -e .
python scripts/run_tests.py --out results/local_tests
gsl-v7 --help
```

`requirements-tested.txt` 是本次已运行版本快照，不是所有平台都自动可用的承诺。Windows 使用 WSL 或相同 Python venv；不把 Linux 命令翻写成尚未验证的 ROS launch 名称。测试退出码非零先定位失败；不能删除科学资格测试让流程通过。

基础方法无需 GPU。设置单机线程和内存上限：

```bash
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4
export GSL_V7_MAX_CALIBRATION_MB=512
```

上述 4 线程上限用于 Python/BLAS 开发计算。**历史 OCB 生成器复现须恢复其原冻结设置 `OMP_NUM_THREADS=1`**；新原生实验可以另定线程数并保存 provenance，不能把改变线程后的同 seed 运行称作原运行的字节级复现。

代码对所选数据先估算解压大小，超过标定预算即停止。估算并非进程 RSS 的硬限制；容器/调度器另设 4–8 GB 内存与单任务运行限制。一次只运行一个原生 GADEN 世界，不并发占满 GPU/CPU。没有足够 RAM 时按世界提取可复核窗口，不能静默截断观测或候选。若新原生后端确实使用 GPU，须记录设备、显存峰值和 OOM，禁止自动缩小实验集合。

## 2. 资产发现与权限

### 2.1 先恢复已存在的八个开放世界

```bash
python scripts/fetch_ocb_assets.py --output local_assets/ocb_x00
python scripts/check_native_assets.py --root local_assets/ocb_x00 --out results/ocb_input_audit.json
gsl-v7 qualify-ocb --root local_assets/ocb_x00 --out results/ocb_qualification.json
```

下载 pin 为 `005ba6a34d95fdfe340050df96fe30a688fa71bf`，仅八个开放 discovery 世界、16 个固定文件，逐件核对字节数、Git blob 和 SHA256。私有仓库使用本地已有凭证或 `GITHUB_TOKEN`，日志不打印凭证。不能递归下载封存世界。ZIP 不重复分发这些物理数组。

已知原生归档优先路径：

```bash
python scripts/discover_native_assets.py --root /mnt/c/GADEN_OCB_R2_ARCHIVE/s2_discovery --root /mnt/c/GADEN_OCB_R2_ARCHIVE/s2x_matched_source --root /mnt/hgfs/workspace/GADEN_files/scenarios/House01 --out results/native_asset_inventory.json
```

若本地使用 Linux VM，附加已存在的 `/home/zyc/ocb_r2_s2_discovery` 与 `/home/zyc/ocb_r2_s2x_matched_source`。脚本只登记允许的 run 与元数据，不通过枚举元数据宣称已经读取完整世界。路径不存在时输出缺失项；不要新建空文件伪装恢复。

### 2.2 资格门

详细字段、原哈希及原生接口见 [NATIVE_INTEGRATION_CONTRACT.md](NATIVE_INTEGRATION_CONTRACT.md)。进入动态实验须同时满足：

1. `OccupancyGrid3D.csv` 原字节、原点、轴序和坐标单位可校验。已知 House01 期待 SHA256 为 `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb`。真源体素、出生邻域、两采样端点和移动路径均合法；负 z 不能单独用来判废或判合法。
2. 同一物理时钟上的两端点原生查询，连续窗口与采样间隔可证明。约 50 秒一帧的 OCB 切片只能做静态同步空间回放；不能插值成 10 Hz 动态序列。
3. 气体读出体积/点值语义、ppm/ppb、传感器标识、响应和恢复带宽、管路滞后、两通道同步误差均有收据。没有实机传感器时清楚标为理想/仿真读出。
4. 若采用 wind-gated 边界母机制，提供因果可获得的局地风矢量和时间戳。风索引与文件 hash 不能替代局地风向量。entry-only 是明确的工程消融，不冒充完整母机制。
5. 每个世界固定 source、风配置、传播 seed/realization；不能把帧当独立世界，不能把源 B 的高度变化当纯二维位置变化。
6. 动态块和连续运动必须按执行时间取得，未来全场风、未来观测数组和真源标签留在独立 executor/evaluator 中，策略不可见。
7. 两 UAV 的最小间距、最大速度、障碍、时延和成本成立。当前未建模旋翼扰流；进入飞行实验前单独校验采样位置/下洗影响，不能默认为零。

资格文件中的 `QUALIFIED_FOR_DECLARED_USES` 需要上述证据，不是把 `HOLD` 字符串改为 PASS。当前 reader 验证结构和字节，物理判断仍由链接的审查证据承担。

## 3. 一次性恢复计划与停止边界

优先从已存在约 1803 帧的原始归档抽取连续窗口，保留原生帧时刻、两点坐标、传感器读出和局地风。提取器放在新建 `native/extract_existing_worlds.py`，executor 放在 `native/gaden_executor/`；**这两处当前是明确的后续实现位置，包中没有伪造完成的脚本。**依照合同的实际 GADEN `Simulation/PlaybackSimulation` 入口实现，记录构建与版本。

先完成八个开放 discovery 世界的最小资格窗口，不启动大规模新 CFD/GADEN 生成。若归档确实不可恢复，记录每个检索路径/文件及失败原因，然后只补一套开发用途的最小合法原生数据：两类候选源、至少两个可区分流况、每格独立传播 seed，训练与开发整世界分离。具体数量由可辨识性和置信区间精度预先确定，不能看效果后补到显著。新生成数据不能与原失败实验混称同一证据。

已有 H01/H02/H03、VGR/S2X、E3/B4、S2 DAY/NIGHT 的能力边界全部写入资格清单。S2 当前单源短序列仅作读出/接口验证，不能作为多源、多 realization 湖岸泛化集。H03 及最终 confirmation 继续封存。

## 4. 分组、冻结与允许读取的内容

当前八世界静态开发划分：每个源 r01/r02 为 TRAIN，r03/r04 为 DEV。源 A/B 合计四个开发世界，不是四十个独立测试。它们都属于已开放 discovery，不能再把其中一部分重命名为最终确认集。

原生正式清单必须显式记录 `source_id`、`wind_id`、`realization_id`、`sensor_calibration_id`、`episode_id`、House 和 split。按完整 realization 划分，同一个世界的任何片段不能跨 TRAIN/DEV/FINAL。候选域、航线、真源、阈值、时间预算与排除标准在读取开发成绩前冻结。

当前有限通道的各 source/action/nuisance 单元都需要标定。**未见 realization 不等于未见 source；有限表并未实现未见标定源的位置泛化。**Level 4 的未见源试验维持 BLOCKED，直到另有经过独立验证的源条件响应支持；不得用真源库临时补单元再称零样本泛化。未见风也不能偷偷映射到最近已知 nuisance 后宣称已经解决。

首次冻结保存 `EXPERIMENT_FREEZE.json`：分支 commit、代码 SHA、数据 manifest SHA、每个世界 ID、先验、预算、主要指标、主比较、计划排除项、统计单位、阈值与多重比较方案。开发后可以因程序错误更正一次，但须记录缺陷、旧结果、受影响范围，并重新冻结新版本。不得只保留改善版本。

## 5. 当前可直接运行的标定、回放和闭环

### 5.1 Level 1 完整链

```bash
gsl-v7 calibrate-control --variant secondary --blocks 32 --out results/local_model
gsl-v7 demo --model results/local_model --out results/local_demo --wrong-prior --budget 300
gsl-v7 control-matrix --config configs/control_matrix.yaml --out results/local_matrix
```

此处 32 是每 action/source/mechanism 标定块数，不是论文独立样本数。解析后端可做数学与接口试验，不能称湖岸传播或原生 PMFS 效果。已有冻结矩阵不需要为了提高数字而重跑或扩展。

### 5.2 真实切片的可复核静态试验

```bash
gsl-v7 static-pilot --root local_assets/ocb_x00 --out results/static_reproduction
```

固定 TRAIN 选择探针 12/17，再使用同一 pair 评估 DEV。`legacy_per_cell` 只为复现已经冻结的旧直方图结果；当前默认是固定总 Dirichlet 质量。报告静态无独立胜出，不能在该开发集继续调平滑参数直到胜过 raw-joint。

### 5.3 合格原生窗口

创建 `local_assets/native/train_dev_manifest.json`，schema 为 `gsl-native-block-manifest-1`。动作、源/机制 ID、采样合同固定；每个 `[action,source,nuisance]` 标定单元完整、均衡且至少两个块，实际论文样本量须由独立世界决定。资格合格后以下命令是真实现：

```bash
gsl-v7 calibrate-blocks --manifest local_assets/native/train_dev_manifest.json --variant secondary --out results/native_model
gsl-v7 fit-geometry --manifest local_assets/native/train_dev_manifest.json --model results/native_model
gsl-v7 replay-blocks --manifest local_assets/native/train_dev_manifest.json --model results/native_model --split dev --out results/native_dev
gsl-v7 plan-channel --model results/native_model --out results/native_next_action.json
```

M1 只读 TRAIN；M2 geometry 先验证与 M1 原训练 manifest 相同 SHA，之后才开块。`fit-geometry` 的 RBF、均值/梯度/协方差是普通结构适配，不另立创新。需非共线二维训练中心、同一合格感测高度和足够每源/中心窗口，独立 DEV 校验空间线性化及 pooled covariance 近似。

母结构和强基线使用相同训练数据、同样世界与预算：将 `--variant` 分别设为 `even`、`mother`、`fixed_two`、`raw_joint`，各自输出独立冻结目录。`mother` 是同一库 TRAIN-best 单通道，不是假装重现母论文全部滤波器训练。完整 raw-joint baseline 必须保留，且控制符号数、总先验质量与调参机会。

最终确认须同时满足协议冻结与相应数据访问授权；封存资产不得由 Codex 自行解锁。两条件满足后，才将经审查的 final 清单标为授权并显式运行：

```bash
gsl-v7 replay-blocks --manifest local_assets/native/frozen_final_manifest.json --model results/native_model --split final --out results/native_final
```

此命令存在，但当前没有合格 final 资产。训练不会打开 final 字节。final 合同不得改变原源集合、动作几何、成本、时钟或传感器参数。

### 5.4 已运行的进程桥与原生接续

```bash
gsl-v7 live --model results/local_model --bridge '["python","scripts/control_bridge_server.py","--output","results/local_bridge_backend"]' --out results/local_bridge --budget 60
```

已验证 JSONL 子进程的 `describe`/`execute`，完整行超时、固定动作合同、原始块账本、M1/M2/M3、二维图。此 server 明确是 Level 1。

本地实现并验收 `native/gaden_executor/` 后，唯一接入差异是 `--bridge` 的 argv 数组；不改变 policy 的接口、也不允许 policy 读取 evaluator 真源。`describe` 声明合法动作及成本上界，`execute` 返回实际过去区间的 NPZ、运动记录、局地风、实际成本和端状态。冻结 TRAIN `formation_predictions.npz` 提供协方差，原生后端不能用真源产生编队统计。当前原生 executor 不存在，因此不提供假的“现成 ROS 启动命令”。

### 5.5 PMFS 原生对照

官方源码固定于 `MAPIRlab/GasSourceLocalization@4e141e162551e674f2f30ddb8859136c72139aac`。先在本地复现原始 launch/config 和 B4 源码兼容评分；不得将我们的 `A_adapted_variance` 冒充官方完整方法。

从真实官方运行提取 `measured_hit[T,C]`、`confidence[T,C]`、`predicted_hit[T,S,C]`、`source_xy[S,2]`（可选 `free_mask[C]`）后可运行：

```bash
gsl-v7 pmfs-map-replay --maps local_assets/pmfs/extracted_maps.npz --out results/pmfs_operator_replay
```

这是实际评分/方差算子的离线移植；不涵盖 ROS 时钟、传播或导航。评分比不是校准物理似然比。每帧从图重算，不递归乘上一帧源后验。

## 6. 一次完整验证矩阵

### 6.1 功能和公平基线

| 层次 | 方法 | 目的与真实状态 |
|---|---|---|
| A | 官方 PMFS-1U | 原始参考；native ROS 本轮 BLOCKED |
| A′-设备 | PMFS-2U | 自建双机适配，不能称作者官方双机版；本地待实现 |
| A′-几何 | PMFS-2U 同步编队 | 分离同步/几何收益；本地待实现 |
| A′-统计 | 双机标准 raw-joint + joint EIG | Level 1 已运行；native 待资格通过 |
| A′+B | 单个母镜像算子 / 普通边界返回 / 成本 ASHT | 当前母结构适配已运行；不等于原论文全复现 |
| A′+B′ | 三模块气源设计 | Level 1 已运行，native 未验证 |

固定回放实验 A：同一真实双机轨迹、原始观测、局地风、时钟、传感器，比较兼容评分、普通联合模型、M1 母结构与二次设计；几何收益不能在固定路线中虚报。

主动实验 B：同样两架 UAV、每次 300 秒、相同速度/安全域、每源风 seed/world 对齐。统计实际移动/驻留/计算成本，不能只扣观测时间。另列等 UAV 秒和等标量采样预算比较；不能将两机对一机的收益都归于算法。

当前后验只用 dwell 块，M2 还读 travel 事件。这是公开的部分观测推断约束，不是完整历史 Bayes。原生公平主比较须让强 raw-joint 基线取得同一移动流，并使用完整合法历史；若仍只用 dwell，所有方法同样限制，单独报告 travel 使用的差异。

### 6.2 各模块 A→A′→A′+B→A′+B′

| 模块 | A | A′ | 母结构 B | 二次设计 B′ | 必要额外消融 |
|---|---|---|---|---|---|
| M1 | hit 图/前向相容比较 | 同物理块 raw-joint，正确 readout | 同库 TRAIN-best 镜像通道 | 偶部 + 源对覆盖的多个镜像通道 + 一次联合符号 | 固定等数量通道、完整 raw-window VQ、随机选择同预算、相同总平滑质量；派生证据乘积仅作为错误对照 |
| M2 | 原主动点候选 | 相同动作域/成本/同步几何 | 因果边界方向返回 | 不确定方向管 + 竞争源响应差双点几何 + 管外复测 | no-memory geometry、boundary-only、M2 off；不使用真源响应 |
| M3 | 原方差启发式 | joint EIG | 成本正确的 Chernoff/ASHT | 全源覆盖 + 付费探索 + 新后缀审计反馈 | no-coverage、no-audit、robust-EIG、软码距；各自同一联合观测模型 |

当前 `configs/control_matrix.yaml` 已落实 13 个控制变体，完整 raw-joint、best-one、fixed-two、M2 独立消融和 M3 三项对照均有真实运行。**robust-EIG、普通软码距、完整 native PMFS-2U、额外随机通道和完整 (2^3) 交互不是当前已完成项**；在合格原生固定矩阵阶段由本地 Codex 实现，不能在报告中勾选为已跑。软码距必须由冻结模型生成，禁止实际未来响应码本。

## 7. 指标、统计单位和科学验收

主要指标：逐世界最终真源 Top-1、MAP 米误差、Top-5% 米误差、真源对最强竞争源 log-margin、Brier/可靠性、原本正确案例退化率。后验校准用覆盖/可靠性与原始样本数共同报告，不能只报平均置信度。

恢复指标：先验/早期后验错误高置信的预先定义子集，恢复率、达到正确可靠度的时间、失败未恢复次数、审计触发与候选再进入。一次审计挑战触发只证明分支运行，不是恢复成功。列表 `compatible_now` 可以再进入；`not_rejected_since_start` 是不可再进入的 anytime 记录，不混用。

成本：两机累计飞行时间/距离、标量观测数、驻留块数、总 wall-clock、在线 p50/p95 运算时间、内存峰值。报告候选数和不可分源对，不以减少候选悄悄提高成功率。

统计单位为独立传播世界；主比较用同源/风/world 的配对差异，世界级 bootstrap 区间或相应配对检验。时间帧不充当独立样本。只有四个开发世界时不给精确总体概率承诺。

预设研发目标是相对强 A′ 在主要 MAP 指标达到至少 10% 的有实际意义改善，或在预先登记的非饱和主要指标达到相当收益；95% 世界级区间应支持改善，并无系统性可靠性/原正确案例伤害。若 A′ MAP 已为零，不能事后更换主指标来制造百分比；应报告饱和并为下一版开发协议选择更有辨识力的合法世界，最终封存集不变。

每项贡献成立另需：M1 在同原始观测、同容量预算下胜过强 raw-joint/母算子，或达到同精度显著降低标定/计算成本；M2 在等资源下提高源判别/恢复，不能只提高羽流命中；M3 在预先定义错误高置信场景胜过 joint/robust EIG 与无审计覆盖，真实误删率须验证。三项可以有不同收益指标，但必须事前冻结，不能从多项指标任选显著者。

## 8. 失败停止条件

立即停止对应级别：源不在合法支持、混用物理单位、时钟/同步不成立、缺 occupancy、使用真实未来风或真源挑动作、同 realization 泄漏、预算不等、代码/配置漂移、不可解释的传感器模型、内存超限或原生 executor 安全门失败。保存失败收据；其余不依赖部分可继续。

完成一轮合格固定回放后：若 M1 对强 raw-joint/母结构没有源排名或预登记效率收益，停止把它作为已证实主创新推进主动大矩阵；保留候选设计，提出针对实测失效原因的**一个**结构修订和新冻结协议，而不是无限平滑/权重搜索。若只有物理上相同的源响应，报告不可辨识，不训练网络强行分离。

若 M2 仅提高命中、M3 与普通联合 EIG 等效，分别收缩论文贡献；不为满足三模块名称而虚报创新。final 一旦打开，任何后续修改只能成为新研究版本；不能回写这次确认结论。

## 9. 证据保存与最终判决

每次运行保存命令、退出码、Python/依赖/设备、代码 commit/文件 SHA、冻结清单、模型参数及训练世界、逐世界 CSV/JSON、原始唯一块账本、预测/动作/成本、失败项与统计脚本。模型预测和真源 evaluator 日志分开保存，策略接口不包含后者。任何资格拒绝都保留完整原因。

结果目录不可覆盖：使用新的版本化目录；resume 只允许相同 config SHA。打包排除 token、未授权原始私有数据、sealed 内容、缓存与生成中间依赖。交付 `SHA256SUMS.txt` 和 `DELIVERY_RECEIPT.json`，确认源文件与安装包一致。

| 判决 | 允许写什么 |
|---|---|
| L1_IMPLEMENTED | 数学/接口测试及解析闭环可运行；当前已达到 |
| L2_QUALIFIED_DISCRIMINATION | 合格固定物理观测下的源判别独立收益；当前未达到 |
| L3_FAIR_ACTIVE_GAIN | 同双机资源的原生主动闭环收益；当前未达到 |
| L4_GENERALIZATION | 明确未见源/风/House 的独立泛化；当前未达到 |
| PAPER_READY_FOR_TARGET_REVIEW | 完整主比较、每项贡献消融、可靠性与物理限制、重复性材料全部通过；不能由“7/10”代替 |

**Codex 的下一任务是恢复与资格化已有原生连续窗口并实现受限 executor，而不是再次跑一遍饱和 L1 数字或继续维护旧 V2 蒸馏主线。**
