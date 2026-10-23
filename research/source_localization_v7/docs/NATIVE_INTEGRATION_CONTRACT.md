# V7 原生接入与物理资格合同

审查日期：2026-10-23。范围：现有归档恢复、有限同步观测块、TRAIN 标定、固定轨迹回放、JSONL 主动接口与最小 GADEN executor。本文不授予新的留出数据访问权限，不把软件测试通过解释为流体或飞行资格。

## 1. 当前裁决

**已有可执行软件链：标准 NPZ/CSV 块 → 冻结联合通道 → 固定轨迹回放；以及 JSONL 进程接口 → M1/M2/M3 → 下一动作。已有真实 OCB 字节只支持同步空间静态开发；完整原生动态与 UAV 实验仍未 qualified。**

`navigation/bridge.py` 已有实际进程通信，不是空接口。`results/bridge_demo/BRIDGE_RESULT.json` 记录 6 步、57 s、`CONTROLLED_LEVEL1`，证实分析构造环境下的进程与三模块联通；该收据明确写着没有物理或飞行资格。`evaluation/block_pipeline.py` 的首轮接口修正经独立复核，集成测试当轮 10/10 通过；本次追加复核的 `tests/test_pipeline_integration.py` 为 **13/13 passed，1.12 s**，包括单位误用、同 episode 换世界、半行响应 deadline 等反例。它们支持工程可运行性，不证明 GADEN、ROS、真实传感器或旋翼流场已接通。[C1–C4]

| 能力 | 当前可用证据 | 当前裁决 |
|---|---|---|
| 同一物理时刻两个空间读出 | 8 个 OCB DISCOVERY 世界的原生切片；同帧不同格点 | 可用于静态空间线索开发；原 pooling 必须保留 |
| 连续有限时窗及真实时钟 | 10 个切片有实际秒值，间隔约 50 s；完整世界时钟仅有清单与 hash | 切片不能用于高速动态线索；须恢复连续原生记录 |
| 两个备择源、独立实现 | 两个三维释放位置 × 4 seeds；每个世界只有一个源 | 是备择源判别开发，不是同时多源定位；不是新的独立确认集 |
| 源点与查询点占据合法性 | 原 occupancy 路径及 SHA256 已知，完整字节未恢复 | **HOLD**，包括 source B 的负 z 坐标 |
| 局地风与观测时钟联通 | 风文件清单、原 bundle hash、风状态序列 hash | 不是局地风向量；须恢复并按原时钟、位置查询 |
| M1 原生联合观测律 | 标准接口和 TRAIN 标定代码存在 | 缺 qualified 原生窗口，尚无对应实测通道 |
| M2 训练响应几何 | 新增 `fit-geometry`，可生成 `formation_predictions.npz` | 结构适配 A′；真实梯度、线性近似与协方差仍须独立验证 |
| 主动策略影响未来采样位置 | 分析 L1 JSONL 闭环已跑通 | 原生 GADEN executor 未提供；不能声称真实飞行闭环 |
| 双 UAV / 旋翼扰流 | 无当前合格证据 | 不作性能或可部署性主张 |

`calibrate-blocks` 本身不生成 M2 几何 NPZ。新加的 `fit-geometry` 填补了“从合格训练块写出该文件”的软件步骤，但没有填补真实训练数据、传感器校准、源合法性和梯度验证的物理缺口。禁止复制 `calibrate-control` 的分析几何文件到原生模型目录以绕过缺件检查。[C2,C5]

## 2. 优先恢复现有归档，保留精确来源

### 2.1 已访问的 DISCOVERY 范围

仓库：`kris-yun/uav-gsl-isj`，读取 pin：`005ba6a34d95fdfe340050df96fe30a688fa71bf`。原公开切片路径为 `evidence/ocb_r2/aod_r2_f0/targets/{run_id}.{cube,pooled}.npy`。本地原始字节和收据在 `evidence/discovery/ocb_r2/`；逐文件 SHA256 见 `evidence/discovery/data_qualification_v7.json`。64 个世界的目录/提取元数据，不等于本轮持有 64 个完整世界。实际已打开核验的是下列 8 件；H03/confirmation 保持封存。[D1,D2]

| 释放位置 | 世界 | master seeds | 已冻结用途 |
|---|---|---|---|
| A：`(-0.60, 1.95, 0.40)` m | `ocb_r2_cfg00_r01` 至 `r04` | `2026900001` 至 `2026900004` | r01/r02 TRAIN，r03/r04 DEV |
| B：`(-0.40, -2.90, -0.30)` m | `ocb_r2_s2x_x00_r01` 至 `r04` | `2026910001` 至 `2026910004` | r01/r02 TRAIN，r03/r04 DEV |

共同上下文为 House01、`1,3-2,4_fast` 风场、`gas_type=13`。A/B 的高度也不同，因此科学对象应写成“两个已知高度条件下的三维释放位置，其二维投影判别”。当前数据不能把差异全部归因于 XY 改变。不同 seed 的 A/B 也不是同一个随机羽流平移后的严格配对反事实。

每个 `cube` 为 float32 `[time,x,y]=(10,87,114)`，切片 z=0.20 m，cell=0.10 m。现有坐标合同为 `x=-7.55+0.1(ix+0.5)`、`y=-7.88+0.1(iy+0.5)`；与历史 probe 合同一致，但原 C++ extractor 的格点实现尚未取回。`pooled` 为 float64 `[10,30]`，是指定 2×2 原生格点的空间均值，8 件均重算 bit-exact；不能称为无体积的理想点传感器。[D1,D3]

10 个实际时间（秒）为：

```text
50.2998047, 100.099045, 149.799942, 199.802994, 249.806046,
299.809082, 349.812134, 399.815186, 449.818237, 499.821289
```

它们对应 record indices `92,175,265,365,465,565,665,765,865,965`，相邻时间差约 49.7009–50.0031 s。`record_index` 是记录标识，不是秒，也不是通用固定步长时钟。House02 旧池化记录没有补足这一点；S2 短单源文件也不能把本资产升为多源/持续窗口资格。[D1,D2]

### 2.2 必须找回的原文件与 hash

下列路径是原 manifest 记录的历史位置，**不是声称当前工作区已挂载这些目录**。恢复后须验证实际字节，不能把 hash 字符串当成文件内容。[D2–D5]

| 对象 | 原始位置或定位方式 | SHA256 / 核验要求 |
|---|---|---|
| A 完整归档 | `C:/GADEN_OCB_R2_ARCHIVE/s2_discovery/{run_id}/`；VM `/home/zyc/ocb_r2_s2_discovery/{run_id}/` | 逐 `iteration_{record_index}` 对照该世界 `OUTPUT_SHA256SUMS.tsv` |
| B 完整归档 | `C:/GADEN_OCB_R2_ARCHIVE/s2x_matched_source/{run_id}/`；VM `/home/zyc/ocb_r2_s2x_matched_source/{run_id}/` | 同上；不得读取未授权的世界 |
| 占据网格 | `/mnt/hgfs/workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv` | `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb` |
| 原风场 bundle | prefix `/mnt/hgfs/workspace/GADEN_files/scenarios/House01/wind_simulations/1,3-2,4_fast/1,3-2,4_fast`；文件 `{prefix}_{0..10}.csv_{U,V,W}` | bundle `beab5f715fbff2912726517444d0807272cdcbf40322fdc74bba9aa84c9f5fb5`；33 个单文件 hash 见 D4 的首条 `wind_files` |
| 风状态 0，U | 上述 `..._0.csv_U` | `47019de3d5bce9913c6cdd7419ec712a0f2d87bced6a54e50313694527b571fb` |
| 风状态 0，V | 上述 `..._0.csv_V` | `da3bd72b7c28d3a970f3139d9e11fe286beb54da187b8983ff78f5cbcf701bb7` |
| 风状态 0，W | 上述 `..._0.csv_W` | `2d95c18850b10ad77b7f47663227436b9a7bc43009d7b0485733db8ad21ef99e` |
| 已转换风场 | `/home/zyc/ocb_r2_seeded_gaden/wind_compat_s1/cfg00/1,3-2,4_fast` prefix | conversion manifest hash `43055d8b4a531d12f4d8a8447be8b98a18ffbdfbe44bfd2cdca361f9ccdd977b`；manifest 文件名未证实，按 hash 定位，不编造 basename |
| 原始时钟 | 每个已授权世界 `RECORD_TIMELINE.tsv` | 当前 8 件 manifest 指定 `ad08a481961387a3a83af94059fda23fa7e3b46fbb81234c6fe457ad5c532d23` |
| 风状态时序 | 原 timeline 的 wind index sequence | `fd718edb34493fafcfa70efa27f191cddf577e1cc5d5409a498cd7dcc6a40d48`；它不是向量风速 |
| 当前切片时钟映射 | 本地 `metadata/AOD_R2_F0_TIME_MAPPING.tsv` | `145fbd427ff5ef8d32151dcabd91d90b2277f6e9e4cd88b1560ea9ce516b7818` |
| 原生成器 | `/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator` | `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688` |
| 原浓度提取器 | `/home/zyc/rmfe_filament_extractor_omp` | `206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91` |

原生成器父仓库 `MAPIRlab/GADEN` commit 为 `17adaf650a4f11d29aa049cf0661e9f9ea2e636f`，core commit 为 `9e93c36ae1af74f6a62c42f1c9d7b813153222ed`，但两份 checkout 均有已冻结补丁：父 patch SHA256 `5c2b3c543ffd1ed082efd686ba05491b6aa9acc02bb4b834b3ab47186a9c6f6e`，core patch `6a1304d213dd84e70cd6b440e66db3c98e01f78b2c138a849799a117973dd01c`。只拉取同 commit 而不恢复补丁，不能声称同一个已资格化生成器。原 provenance 还记录 `OMP_NUM_THREADS=1`。原 launch 的路径和 hash 可以用于恢复，但本文不据此编造可运行的 ROS 命令。[D5]

### 2.3 最小合法提取计划

1. **先元数据、后原生字节。** 在现有归档检查上述 8 个明确授权的 run，恢复 `RUN_MANIFEST.json`、`OUTPUT_SHA256SUMS.tsv`、`RECORD_TIMELINE.tsv`、occupancy、实际风场/转换 manifest。输出逐文件 SHA 收据、原路径、访问目的和 split。初次 I/O/时钟检查可只用两个源 × r01/r02；这只是 TRAIN 冒烟检查，不能充当留出验证。
2. **先证明空间合法。** 从实际 occupancy 解析 origin、三维 cell size、维度、轴序及 free/solid 编码。核验 A/B 源体素、初始化释放扰动邻域、观测端点、拟合中心和可行路径；保存坐标→索引→原始 cell 值的收据。source B `z=-0.30` 只有在此步骤之后才能从 HOLD 变更。负坐标本身既不证明违规，也不证明合法。
3. **预先固定有限窗口。** 建议从已存在的约 50 s 锚点确定一段 20 s 窗口，按原时钟选取其中每个实际保存记录，并保留滤波、传感器延迟与边界确认所需的前后 padding。窗口规则在查看浓度前冻结；不得按“看到明显羽流”挑选子段。20 s 是最小提取计划的工程起点，不是已经验证的最佳时长。
4. **裁定可用时间尺度。** 原 manifest 报告 1803 records、0–999.502991 s、积分参数 0.1 s、保存参数 0.5 s。实际保存时刻必须读 timeline。当前默认 `SamplingContract.maximum_step_s=0.25`，预设动态库含 0.2/0.5/1.0 s lag；约 0.5 s 保存不能自动支持这套库，尤其不能据积分步长声称持有 0.1 s 读出。可用更粗且经传感器校准的预设库并重新冻结通道，或找到确实存在的更高频原始记录；插值不能补资格。若只能新生成更密记录，它属于另一次明确标识的新数据实验，不能冒充历史恢复。[C6]
5. **共同世界、共同物理时刻。** 每次查询的两个端点必须从同一个 run、同一个原生状态读取；全部查询完成后才能推进模拟时间。不得先查询 L 再推进世界再查询 R，不得按端点重置 RNG。返回两端实际位置、时间与传感器身份，而不是仅返回目标位置。
6. **风和读出一并恢复。** 同一状态的风索引须连到原实际 U/V/W 文件，再在实际观测位置求局地向量；注明向下风方向、坐标系、单位和时间。保留原浓度单位、空间平均体积、缺测语义、饱和/阈值、滤波和响应延迟。不存在传感器动态证据时，只能标明“理想浓度查询”，不能把 `sensor_response_calibrated` 改成 true 代表硬件已校准。
7. **按完整世界划分。** 完整开发恢复使用 8 件，r01/r02 TRAIN、r03/r04 DEV；不能把同 run 的窗口随机拆成训练/评估。它们已被用于 DISCOVERY，故不能再称全新盲确认集。新增 final 必须另有冻结与授权；当前任务不打开 H03/confirmation。

## 3. 标准观测块和原生 manifest

### 3.1 `SynchronousBlock` 实际字段

NPZ schema 为 `gsl-synchronous-block-1`，读取禁止 pickle；CSV 是 long format 并强制配套 `.schema.json`。标准接口是现有 `src/gsl_discrimination/data/schema.py`，不需要把记录索引猜成秒。[C7]

| 字段 | 形状/类型 | 语义与要求 |
|---|---|---|
| `values` | `[T,P]` 浮点 | 实际观测量，当前 paired 标定要求 P=2；有限值，ppm 非负 |
| `times_s` | `[T]` | 每帧真实秒值，有限、严格递增；同帧全部传感器共享此时刻 |
| `positions_m` | `[P,3]` 或 `[T,P,3]` | 同一坐标系下实际位置；现有 M2 fitter/bridge 的冻结驻留动作要求 `[2,3]` |
| `sensor_ids` | P 个唯一字符串 | 顺序固定；第 0 端为 `+`、第 1 端为 `−`，交换会改变 odd 符号 |
| `block_id` | 非空字符串 | 原始观测块唯一身份；派生 E/h 等不另领证据身份 |
| `realization_id` | 非空字符串 | 原生世界身份；包含 run/seed/config 的可审计映射，不能每块随意更名 |
| `units` | 字符串，默认 `ppm` | 原浓度/传感器输出的精确单位；改变单位须重标定 |
| `local_wind_mps` | 可选 `[T,P,3]` | 实际同步局地向量；`qualification.local_wind=true` 时必需 |
| `qualification` | 严格 bool 能力 + scope/limitations | 缺失能力保持 false；插值数据不得自称 native/continuous |
| `metadata` | JSON object | 原文件/提取器/坐标变换/读出/校准收据；`truth_included` 不得为 true |

块中不放真实源标签。离线 evaluator manifest 可以持有源标签用于 TRAIN 和评估；执行后端拥有真世界，策略端只能看到合法观测。`block_id` 去重和非重叠时窗能防重复入账，**不能证明相邻时窗在给定源/机制后条件独立**。持续湍流记忆、混合时刻分布、环境年龄和自适应采样造成的条件律变化仍须建模或验证；否则 M3 的序贯风险主张只在声明的模型族内成立。[C1,C2,C8]

### 3.2 `gsl-native-block-manifest-1`

实际训练/回放入口要求以下内容。应把物理资格审查作为独立文件，先给事实证据，再签发 status，禁止为了通过 loader 写一个空的“QUALIFIED”字符串。[C2]

| 字段 | 必需内容 |
|---|---|
| `schema` | `gsl-native-block-manifest-1` |
| `source_ids`, `source_xy` | 唯一候选标签与对应二维投影；另在审查收据中保留 `source_xyz` 和高度条件 |
| `nuisance_ids` | 冻结机制身份；一个 fixed-source episode 的机制按模型合同保持固定 |
| `actions` | 有序列表；每项 `name`, `cost_s`, `positions_m`，成本、端点顺序、数量都冻结 |
| `temporal`, `sampling_contract` | 是否持续窗口，以及连续性、同步误差、最大间隔、传感器差分延迟、带宽等声明 |
| `capability_review` | `{path, sha256}`；文件 hash 必须匹配，当前 loader 要求其 `status=QUALIFIED_FOR_DECLARED_USES` |
| `records` | 每项 `path`, `sha256`, `source_id`, `nuisance_id`, `action`, `split`；CSV 另有 `schema_sha256`；可有 `episode_id` |
| `final_freeze_authorized` | 仅在被明确授权的 final 实验中为 true；默认不能开启 final |

训练只打开 TRAIN bytes；回放默认只打开 DEV，明确选 final 且授权后才可读 final bytes。回放核对冻结的完整 action/source/nuisance/temporal/sampling 字典，拒绝更换 action ordering、端点、cost 或时钟合同。训练与评估拒绝相同 `realization_id`。每个 action/source/mechanism cell 至少 2 块且平衡，只是当前频率表代码的最低结构要求，**不等于两个独立世界，更不等于充分的通道概率精度**。独立实现数量、置信区间和序贯条件律校准须在物理审查报告中另列。

回放时每个 `episode_id` 必须代表一个实际世界、一组固定源/机制与一条因果轨迹；不得利用可选 episode label 把多个 seed 拼为一条轨迹。当前代码已检查 episode 内 source、nuisance、realization 都一致，并锁定训练时的单位和传感器顺序；这些标识仍须由真实归档身份支撑。跨世界比较应分别初始化 posterior 和 audit，再聚合 evaluator 指标。

## 4. M2 响应几何的普通训练适配

现有命令顺序为：

```bash
gsl-v7 calibrate-blocks --manifest /absolute/qualified_manifest.json --out /absolute/frozen_model --variant secondary
gsl-v7 fit-geometry --manifest /absolute/qualified_manifest.json --model /absolute/frozen_model
gsl-v7 replay-blocks --manifest /absolute/qualified_manifest.json --model /absolute/frozen_model --out /absolute/dev_replay --split dev
```

这些是已实现 CLI 的调用形状，示例路径是占位符，不表示合格文件已经存在。`fit-geometry` 读取 TRAIN，要求驻留两端点动作、至少 3 个不共线中心，以及每个 source/center 至少 3 个训练块。两个 TRAIN seeds 若各只有一块且只有一个动作/中心，将不足以通过当前 covariance 最低计数门槛；可预先固定多个互不重叠窗口，但必须继续按整 seed 划分，不能把同 seed 的窗口当独立实现。它用真实时钟梯形积分得到两端窗口均值，再计算 `E=(c_++c_-)/2`、`O=(c_+-c_-)/2`，拟合普通 RBF 中心响应。令训练中心为 q、核带宽为 ℓ：

\[
K_{ij}=\exp[-\|q_i-q_j\|^2/(2\ell^2)],\quad
\beta=(K+\lambda I)^{-1}\bar E,\quad
\mu(q_i)=(K\beta)_i,
\]

\[
\nabla\mu_s(q_i)=\sum_j K_{ij}(q_j-q_i)\beta_{js}/\ell^2.
\]

当前解析梯度符号和数组轴正确，输出 `gradients[N,S,2]`。这不是新机制，也不是从 M1 联合符号读出真实风或真实源梯度。[C5]

| 输出 NPZ key | 形状 | 下游要求 |
|---|---|---|
| `centers` | `[N,2]` | 训练可支持的固定中心；不得用 test 真场再选中心 |
| `means` | `[N,S]` | TRAIN 的窗口 common mode 响应拟合 |
| `gradients` | `[N,S,2]` | TRAIN 拟合解析梯度，xy 轴及单位固定 |
| `joint_covariance` | `[N,S,2,2]` | 当前按同中心汇集几何/机制的 E/O 协方差；不是逐 action 精确协方差 |
| `action_to_center` | `[A]` | 原冻结 action 到中心的映射；不能用它绕过 bridge 当前 Cartesian 顺序限制 |

拟合另写 `GEOMETRY_CALIBRATION_RECEIPT.json`，status 为 `TRAIN_GEOMETRY_FIT_NOT_PHYSICAL_CERTIFICATION`。拟合的三项物理假设必须可被反驳：

- **高度与中心近似：** 所有感测端点固定同一已知 z；源高度可以因候选不同而不同。对有限间距 d，paired E 近似中心 μ 的误差随曲率变化；独立校准世界上必须检查该误差，不能把 E 无条件视为中心点读出。
- **梯度与线性半径：** 在不参与拟合的开发/校准世界，以真实同步端点对比检查 `O≈(d/2)uᵀ∇μ` 的符号、量级和误差，预先限定允许间距/局部半径。RBF 岭与正协方差小对角只保证数值可算，不保证流体正确。
- **协方差：** 当前中心级协方差把不同方向、间距和机制混在一起，其 spread 可能包含均值的几何变化；应用时必须验证这个池化近似，或改为真实 action 对齐的 `[N,D,U,S,2,2]` 训练协方差。Σ 只决定 M2 候选对比度，绝不直接作为源 likelihood 追加到 M1。

在最初新增版的代码审查中，报告了“按 XY 合并时未锁感测 z”和“未绑定原 M1 训练 manifest 字节”两项边界；当前版本已固定 sensing z，并在打开任何观测块之前要求与 M1 标定 manifest SHA 完全相同。改用新的 TRAIN 数据须另有明确合同，不能悄悄换 records。当前原生 bridge 已强制从冻结 `formation_predictions.npz` 读取 `joint_covariance`，不再接受在线后端提供的测试世界统计；只有明确的 `CONTROLLED_LEVEL1` 且 NPZ 缺 covariance 时才允许 `describe` 中的分析构造值。源码、训练 manifest、几何文件与 receipt 的 hash 应一起冻结。[C1,C5]

## 5. 实际 JSONL 进程协议

### 5.1 消息封装与通信

入口为 `gsl-v7 live --model ... --bridge '<JSON argv array>' --out ... --budget ...`。`--bridge` 必须是 executable 加 arguments 的 JSON 字符串数组；`Popen(shell=False)`。进程 stdin/stdout 每条消息一个完整 JSON 行，stdout 只用于协议，日志写 stderr，回复完整换行并 flush。请求使用单调递增 id，回复必须原样返回 id。[C1]

```json
{"id":1,"method":"describe"}
{"id":1,"result":{"schema":"gsl-action-bridge-1"}}
```

上例只展示 envelope，不是完整合法的 describe result。错误回复应为 `{"id":1,"error":"具体原因"}`。原实现的 selector 仅等待首字节、随后 `readline()` 可能被半行阻塞；该问题已修为非阻塞字节缓冲，整个 JSONL 响应共享一个 deadline，并有 8 MiB 响应预算。进程退出、错 id、无效 JSON、错误回复和超时都应中止 episode，不合成零浓度继续运行。

### 5.2 `describe.result` 字段

| 字段 | 实际类型/语义 | 必须核验的合同 |
|---|---|---|
| `schema` | 字符串 `gsl-action-bridge-1` | 版本完全匹配 |
| `scope` | 字符串 | `CONTROLLED_LEVEL1` 只准用于明确分析构造；原生不得冒用该值规避额外检查 |
| `future_truth_available_to_policy` | bool false | 源真值/未来全场不暴露给策略；该 bool 是声明，须审 executor 数据流 |
| `action_names` | `[A]` | 与 channel 完整顺序一致 |
| `action_cost_upper_bounds_s` | `[A]` 正有限值 | 与冻结 channel.costs 一致；含移动、稳定、观测、恢复所需时间上界 |
| `safety_checked_before_execute` | bool true | executor 承诺在执行前检查端点、路径、碰撞、基线和动力学 |
| `qualification_receipt` | 可 JSON 序列化的收据引用 | 当前 bridge 随结果记录；不能据其存在推断已验证物理资格，外部须核 hash 与 scope |
| `initial_state` | `{position_xy:[2],time_s,heading_rad,gas_detected,local_wind?}` | 与实际世界同钟；heading 是行进方向；gas 判定有固定阈值/延迟合同 |
| `boundary_config` | `BoundaryMemoryConfig` 字典 | 实际字段见下段；所有时间和运动尺度来自目标传感器/平台验证 |
| `formation_geometry` | 几何与不确定管字典 | 字段见下表；仅定义候选动作，不提供源证据 |
| `calibrated_even_odd_covariance` | 仅分析 L1 的可选 fallback；`[N,S,2,2]` 或 `[N,D,U,S,2,2]` | 原生必须从模型 NPZ 的 `joint_covariance` 读取；不接受 test 后端统计替代 |

`boundary_config` 必需字段为 `mode`, `entry_decay`, `entry_gain`, `min_pre_s`, `min_post_s`, `direction_window_s`, `max_observation_gap_s`, `max_memory_age_s`, `min_speed`, `max_speed`, `timing_validated=true`。`entry_only` 是无风工程适配；`wind_gated` 另需 `exit_decay`, `exit_gain`, `initial_upwind_gain`，并提供 `max_wind_age_s` 等风时效参数。可选 `initial_crosswind_gain`, `exit_min_upwind_cos`, `direction_noise_variance`。不能仅凭配置名称称已复现母论文的完整速度控制器。[C9]

局地风结构为 `{"velocity_xy":[u,v],"time_s":t}`，方向是 **downwind**，单位 m/s，时间为采集秒值。它可放在 initial_state 与每个 motion sample 中；两处现在都已接入 `LocalWind`。wind_gated 需要初始及合格退出事件所需的新鲜局地风，不允许未来风或只有风索引。

| `formation_geometry` 子字段 | 语义 |
|---|---|
| `lower_xy`, `upper_xy` | 当前平面边界；不能替代内部障碍和路径检查 |
| `min_separation`, `max_separation`, `linearization_radius` | 允许双点间距与预测局部近似半径 |
| `separations`, `orientations_rad` | D 个间距、U 个方向；两端为 `q ± d/2 [cosθ,sinθ]` |
| `tube_length`, `tube_base_radius` | 因果边界方向返回管参数 |
| `position_covariance` | `[2,2]` 定位协方差 |
| `drift_variance_rate`, `sensor_delay_uncertainty_s` | 方向/时延不确定性传播参数，不是宣称达到某置信覆盖率 |

**当前 bridge 的明确限制：** action catalogue 必须是完整的 Cartesian `center × separation × orientation`，按中心外层、间距中层、方向内层顺序排列，costs 也按此 reshape。每个枚举动作都要与 M1 冻结端点逐项相等；被地图或间距规则删除而导致数量变化的 catalogue 会拒绝执行。当前不能用不规则稀疏动作列表、变高或连续轨迹来冒充这个接口。返回管约束动作中心，端点可跨管边界，但各端点和整个运动仍须 executor 验证。未来若支持稀疏 action，必须增加显式 action-id 映射，而非悄悄改排序。[C1,C10]

### 5.3 `execute` 请求与返回

请求只包含 `id`, `method="execute"`, `action`（零基整数）和 `remaining_budget_s`。策略不发送真源或 test 风场模板。executor 从冻结 catalogue 解码动作，先判安全/预算，再完成移动、稳定、有限窗口观测和传感器恢复，最后返回：

| `execute.result` 字段 | 实际合同 |
|---|---|
| `safety_passed` | 必须严格 true，代表该动作完整通过实际执行安全检查；否则中止 |
| `cost_s` | 有限、正数、不超过该 action 的冻结上界；不得只计采样时长忽略移动/恢复 |
| `block_path` | 已完整落盘、可只读加载的 NPZ 绝对路径；使用上述 SynchronousBlock schema |
| `end_state` | 至少 `{position_xy:[2],time_s}`；必须与动作实际结束状态一致 |
| `motion_samples` | 有序列表；每项 `{time_s,position_xy:[2],heading_rad,gas_detected,local_wind?}`；覆盖因果移动/边界事件所需真实历史 |

客户端已检查：`end_time ≈ start_time + cost_s`，绝对容差 1 ms；观测块全部时间落在该执行区间；motion sample 位于执行的过去区间；同 episode `realization_id` 不变；实际端点与所选 action 匹配；单位/传感器顺序与训练一致。raw ledger 另拒绝重复 block id 和重叠/倒序观测窗口。静态与动态一律要求同步空间、物理时钟、原生样本；非 L1 还要求源占据合法、原生活跃闭环和传感器读出资格；动态模型要求持续窗口，具体时钟形状/时长要与冻结模型一致。[C1,C6–C8]

客户端不能仅凭字段判断时间来自硬件还是伪造数字。executor 还须保证：state/motion/block 同坐标同时间基准，motion 最后样本与 end_state 一致，路径中数据不被悄悄删成低频点，传感器延迟已对齐，实际双端点属于同一物理世界，出界/缺测不变成零浓度。方向记忆只更新动作约束；同一 motion/观测流不能另作为独立 likelihood 重复入账。完整块 SHA、世界文件 hash、动作执行轨迹、原始及校正时钟应进入外部收据和 raw ledger。

## 6. 本地 Codex 仍须补的最小 GADEN executor

**拟新增位置：`source_localization_v7/native/gaden_executor/`。这是缺失组件的建议位置，不是已经存在的可执行程序。** 可用一个 C++ 主程序链接经过确认的 GADEN core，也可由薄 JSONL wrapper 调用原合格播放器/查询器；进程必须实现上节 `describe`/`execute`，写标准 NPZ，并保留原始字节和外部资格收据。现有 `scripts/control_bridge_server.py` 只是分析 L1 示例，不能改 scope 字符串后当成 GADEN。[C1,C4]

本地已持有 GADEN-RT core 源码的真实入口位于：

```text
v6_work/data/s2_review/FSR_S2_CH4_DAY_NIGHT_PRO_REVIEW_20261022/
  evidence/04_native_upstream/core/include/gaden/
```

`Simulation.hpp` 提供 `SampleConcentration(const Vector3&)`、`SampleWind(const Vector3&)`、`AdvanceTimestep()`；`RunningSimulation.hpp` 提供 `GetCurrentTime()`；`PlaybackSimulation.hpp` 有 `startIteration/resultsDirectory` 和推进接口，但这里没有等价的公开 `GetCurrentTime()`，恢复 OCB 必须可靠关联原 `RECORD_TIMELINE.tsv`。这份本地 core pin `1a20e35cd5f174ae9675a2ae3c796137a05c4ee5` 与 OCB 原 core `9e93c36...` 不同，不能未经格式/数值比对就宣称无损播放旧世界。[G1]

最小实现责任：

1. **独立于策略持有世界。** 用允许的 run/seed/config 启动一个世界，载入 occupancy 和真实风；世界真源仅后端与 evaluator 可见。固定 seed 是配对设计条件之一，不能代替相同初始状态/生成器/线程/风状态证据。
2. **原生查询不改变读出语义。** 在每个原生时刻冻结世界状态，再查所有实际端点的浓度和风；保存世界时钟，再统一推进。恢复旧 archive 应先用原查询器或已验证等价 decoder，在既有快照上逐点/逐 pooling 对照，而不是先生成大量新世界。
3. **实现动作物理。** 明确是虚拟固定探头、被动羽流中的移动探头、模拟机器人还是有旋翼反馈的 UAV。计算合法路线、到达/稳定和观测区间，记录实际运动与全成本。若仅改变被动羽流中的查询位置，可称因果主动空间查询；不能称已经建模旋翼—羽流相互作用。
4. **传感器和边界流。** 真实硬件使用校准传感器模型/同步收据；理想浓度模式明确写入 scope。固定阈值与迟滞、延迟、预/后稳定时间后再输出 gas_detected。边界方向需要实际运动方向，不能把姿态 yaw 或静止时的羽流边界漂移当作穿越方向。
5. **审计与恢复。** 所有输出到新的隔离目录；不得覆盖历史原生结果。部分 GADEN 保存初始化会清理目标输出目录，必须事先排除已有归档。Playback 状态不一定保存完整未来 RNG 状态，不能仅用一个 filament snapshot 宣称能接续同一随机未来。

当前环境探针显示有 g++/OpenMP/zlib/OpenCL loader，但没有现成 cmake、fmt/yaml-cpp/libbsc、已安装 GADEN 或 ROS 命令；`native_generation_ready=false`，未进行原生生成。源码可用于明确集成入口，不能把依赖存在或头文件可读等同于已运行 GADEN。恢复既有原始归档是当前首选；新增构建和数据生成应分别记录版本/依赖/实际验证结果。[G2]

## 7. 固定回放、主动实验和 UAV 主张的分界

| 实验 | 公平比较与必须保留的证据 | 允许结论 |
|---|---|---|
| 固定块回放 | 所有方法读同一批原始块、时钟、端点、真实成本；同一训练/DEV 世界划分；模型先冻结 | 观测表征/源判别/审计在固定数据流上的增益 |
| 被动羽流中的主动探头 | 每策略独立因果轨迹；相同生成器和可配对世界条件；只查询已经到达的时间；完整 travel/settle/window/recovery 成本 | 在声明被动场与探头假设下的主动采样性能 |
| 原生机器人闭环 | 合格运动控制、碰撞/动态约束、同步传感器、局地风和实际轨迹 | 声明平台与传感器范围内的闭环性能 |
| 双 UAV 与旋翼干扰 | 旋翼关闭/开启、单机/双机、不同基线与风向、入口位置/高度和响应延迟对照；气流/传感器证据 | 通过相应对照后，才可讨论双机收益与抗扰能力 |

双点观测本身不决定必须双机。至少把固定两探头、单平台双入口、单平台交替采样、两个独立移动端点分开；匹配探头数、观测时长和移动成本。交替采样在相同物理时刻不存在两读数，不能标成 synchronous_spatial。合格基线应由障碍、旋翼扰动半径、风向、传感器带宽与线性近似误差决定，本文不给没有实测支撑的通用米数。

M2 的管/协方差只是动作提案工具，M3 的 source-pair KL 和付费 coverage 审计也以声明的联合通道为条件。估计概率表、非重叠块、相同 seed 和严密文件 hash 都不能单独建立真实过程的序贯 likelihood。需要考察在选定动作与历史条件下的预测覆盖/校准以及跨块残余相关；通道失配时应保留 model-relative 结论和可恢复候选列表，不报告未证明的无条件错误率。

## 8. 官方 PMFS 标准数组对照入口

已新增 `evaluation/pmfs_arrays.py::replay_pmfs_maps` 和 CLI：

```bash
gsl-v7 pmfs-map-replay --maps /absolute/official_maps.npz --out /absolute/pmfs_operator_replay --difference-factor 1
```

实际输入为 `measured_hit[T,C]`, `confidence[T,C]`, `predicted_hit[T,S,C]`, `source_xy[S,2]`，可选 `free_mask`。它回放 pin `4e141e162551e674f2f30ddb8859136c72139aac` 的兼容评分/方差兴趣算子；输出明确 `full_native_pmfs_ros=false`、`previous_posterior_multiplied=false`。原 PMFS 有主动选点，实际兴趣包含 `variance × (1-confidence)`，不能把基线描述成固定航线，也不能声称每轮都重复乘旧 posterior。[P1,C11]

最小官方 exporter 还应附带：真实 `times_s`、cell 坐标与面积、source XYZ/高度条件、occupancy/合法 cell mask、函数与 commit、difference factor、measured hit 的读出/平均语义、前向模拟与 wind 输入、原始数组 SHA。当前 port 不重现 ROS 回调、整套前向传播或导航；把这三组实际中间 map 导出后，才有资格称“官方算子同输入对照”。`source_probability_map.npz` 的 mask 只是候选支撑位置，不能用来证明三维 occupancy 合法；同 XY 的不同高度候选在二维图里汇总 mass，仍须保留原候选身份。[C11,C12]

## 9. 交付前结构 guard 与仍未证明的事项

本次代码复核确认以下修正已经存在：按 allowed_splits 筛选后才打开观测 bytes；TRAIN-only 标定；DEV 默认及 final 显式授权；回放完整冻结合同；initial/motion LocalWind 接线；实际块端点和 M2 action 顺序逐项核验；有限正 cost；时钟—成本一致性；观测/运动位于执行的过去区间；bridge 同一 realization；原始块去重与不重叠；回放 episode 的源/机制/世界一致；单位和传感器顺序冻结；几何拟合感测高度与 M1 训练 manifest 固定；原生 covariance 取冻结 TRAIN 文件；完整 JSONL 消息超时。它们分别防止权限泄漏、合同漂移、错位动作、伪时间、测试统计泄漏和重复观测。[C1,C2,C5,C8]

**这些都是结构 guard。** 它们不证明 occupancy 文件已恢复、不证明 source B free、不证明局地风字节存在、不证明传感器校准、不证明有效独立羽流数量、不证明真实梯度、不证明双 UAV 控制/旋翼流体、不证明 GADEN executor 已运行。当前归档提取、实际原生 `formation_predictions.npz` 与原生闭环仍为 **BLOCKED**；软件生成几何文件的能力已存在，应与“已有合格物理几何产物”分开记录。

从 BLOCKED 转为指定用途 qualified，至少需要：上节资产 hash 真实核验；源/端点/路径 occupancy 收据；所有必要时钟与原生采样间隔证据；同世界同步读出对照；原传感器/体积语义及带宽/延迟；TRAIN/DEV 世界隔离；冻结 M1+M2 产物及独立几何误差验证；本地 executor 协议及真实轨迹/成本日志；明确仍未覆盖的物理作用。任何一项缺失都应收窄 declared uses，不用空白 true 值补齐。

## 10. 证据索引

项目路径以 `source_localization_v7/` 为根；工作证据的 `v7_work/discovery/` 已复制到随包 `evidence/discovery/`；更早源码资产仍按原仓库路径追溯。下列均为本次实际已读取的文件或已冻结来源记录。

- **C1**：`src/gsl_discrimination/navigation/bridge.py`，`JsonLineBackend.call`, `_wind`, `_check_action_geometry`, `run_bridge`。
- **C2**：`src/gsl_discrimination/evaluation/block_pipeline.py`，`load_manifest`, `calibrate_manifest`, `replay_manifest`。
- **C3**：`tests/test_pipeline_integration.py`，最终限定集成复核 13/13 passed，1.12 s；命令 `PYTHONPATH=/tmp/gsl_v5_test_deps:src python -m pytest tests/test_pipeline_integration.py -q`，工作目录 `source_localization_v7/`。构造测试中的 qualification 不能移用至真实数据。
- **C4**：`scripts/control_bridge_server.py`；`results/bridge_demo/BRIDGE_RESULT.json`，L1 的 6 steps / 57.0 s 收据。
- **C5**：`src/gsl_discrimination/m2_boundary/calibration.py::fit_response_geometry`；`src/gsl_discrimination/cli.py` 的 `fit-geometry` 分支。
- **C6**：`src/gsl_discrimination/m1_opponent/operator.py`，`SamplingContract`, `OpponentBank.causal_default`, `time_weights`；同 package 的 `calibration.py::SourceContrastModel.encode` 与 `raw_joint.py` 中的冻结时钟检查。
- **C7**：`src/gsl_discrimination/data/schema.py`，`DataQualification` 与 `SynchronousBlock`。
- **C8**：`src/gsl_discrimination/ledger.py::RawObservationLedger`；`channel.py` 的联合源/机制 posterior 与唯一块更新合同。
- **C9**：`src/gsl_discrimination/m2_boundary/memory.py`，`LocalWind`, `BoundaryMemoryConfig`, `CausalBoundaryMemory`, `ReturnTube`。
- **C10**：`src/gsl_discrimination/m2_boundary/formation.py::score_paired_formations`，几何枚举、pooled covariance 与 pair contrast。
- **C11**：`src/gsl_discrimination/evaluation/pmfs_arrays.py::replay_pmfs_maps`；`src/gsl_discrimination/baselines.py`。
- **C12**：`src/gsl_discrimination/evaluation/maps.py::export_source_map`。
- **D1**：`evidence/discovery/data_qualification_v7.json`；`evidence/discovery/OCB_INTERFACE_FIXED_REPLAY.json`；`evidence/discovery/pmfs_physics_independent.md`。含 8 世界 raw SHA、pooling 与实际时钟核验，不包含未恢复完整世界的替代证据。
- **D2**：`evidence/discovery/ocb_r2/metadata/{run_id}.RUN_MANIFEST.json`；`AOD_R2_F0_TIME_MAPPING.tsv`；原 repo pin `005ba6a34d95fdfe340050df96fe30a688fa71bf`。
- **D3**：同目录 `AOD_R2_F0_TARGET_EXTRACTION.json`，SHA256 `e56f40fe1bc7edf46d4f4eabed4637f6ab77d317ba24142ab9c9d7b78f7c859e`；`extract_f0_targets_vm.py`，SHA256 `d3977b8fe1d82a4fc0ba623916a186ca0b6bc7b42c0236796628d392ebd6aa0b`；`stage_f0_snapshots_host.py`，SHA256 `71bc035301bfc3f4b230a708f81351e3354ec3ba0bfe5eba67640aed9a025226`。
- **D4**：同目录 `HOUSE01_STATIC_ASSET_AUDIT_EXCERPT.json`，SHA256 `21937a32bd74b472331b9ff75d39ba8ddfa3dbf594cd1677170984decaf5b4ab`。完整 33 风文件 hash 取匹配 `1,3-2,4_fast` 条目，不能拿其他 wind context 顶替。
- **D5**：同目录 `BUILD_PROVENANCE.md`，SHA256 `ea5bc5624146acc15b09e5717be9efb65bac065b367f1e35fa750694370ac5d6`。
- **G1**：`v6_work/data/s2_review/FSR_S2_CH4_DAY_NIGHT_PRO_REVIEW_20261022/evidence/04_native_upstream/core/` 内 `include/gaden/{Simulation,RunningSimulation,PlaybackSimulation}.hpp` 及对应实现；这是源码接口证据，不是运行通过收据。
- **G2/P1**：`evidence/discovery/SOURCE_RUNTIME_RECEIPT.json`，含环境命令/库探针、`native_generation_ready=false`、官方 PMFS pin 和逐源文件 SHA。


## 11. 本次审查源码快照

下列 SHA256 固定本报告最后读取的实现/测试/构造运行收据。后续源码变更不自动继承本次审查结论。该表不替代第 2 节真实资产资格。

| 项目内文件 | SHA256 |
|---|---|
| `src/gsl_discrimination/navigation/bridge.py` | `773526defe92e20fca66731a4f35beddc4e61ee30a9ea73116241d75e9259ce0` |
| `src/gsl_discrimination/evaluation/block_pipeline.py` | `132db126605d113c7d6044fe20c6a2474559a4a81e0040c0411fff7af117e35a` |
| `src/gsl_discrimination/m2_boundary/calibration.py` | `f528b769721dcf55639b97dc5a32cb0091b1fdd02a8f37d92134ed1c024ce7c7` |
| `src/gsl_discrimination/data/schema.py` | `f15d8a42c89c66621ee150d62fc39c057197d49e618fb3712e507f76fd620404` |
| `tests/test_pipeline_integration.py` | `f544c5fc37fcfe29ed2d265ae4af268d5f86e04d6912a6c5ff673f833fa29142` |
| `results/bridge_demo/BRIDGE_RESULT.json` | `f9fec337d300f8d7222f6454657a39a75232c171018f3c58d23a01868ae6a1f4` |
