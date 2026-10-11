# RK2 输入与去 oracle 接口静态审查

结论：现有资产足以开展 A 的有限读出原型；训练、压缩评价和源推断必须分别准备输入。没有生成新物理，没有执行浓度、LOS 或原型计算。此次只解析并核验 392 个已保存快照和 196 个旧 NPZ，详细路径、哈希、schema 见 `INPUT_INTERFACE_PATHS.json`。

本审查父包为 `outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010`，父提交 `210b94e5de0ab7e906136fd0765c3639f10103b2`。下列路径均相对于该父包。

## 1. 现有资产与用途

|资产|具体路径|内容与权限|
|---|---|---|
|训练贡献缓存|`RK0_NEW/reference_contribution_cache/{C7_0,C7_1,K2_0,K2_1}/iteration_{frame}.npz`|4 份参考实现 ×49 帧 =196 NPZ，可用于训练。全部粒子及显式零贡献保留；禁止冒充实测输入。|
|缓存清单|`RK0_NEW/reference_contribution_cache/CONTRIBUTION_CACHE_RESULT.json`|196 个缓存 SHA、原快照 SHA、逐帧记录数与权重、204 条原生锚点。|
|10个原生受体位置|`RK0_NEW/reference_contribution_cache/RECEPTOR_POSES_STOP_ORDER.f32.npy`|`(10,3)float32`，按停留点顺序；所有 z 为原生传感器高度，不人为改动。|
|查询到受体映射|`RK0_NEW/reference_contribution_cache/RECEPTOR_ALIAS_51_TO_10.csv`|`query_id,block_id,membership_branch,stop_id,pose_index`；50 主块和1个分支替代。|
|8实现原始快照|`PARENT_M2M3_FROZEN/M2_FROZEN/native_reference_evidence/realizations/{bank}/bank/iteration_{frame}`|每库49个快照，8库总392个；各快照含全粒子 x,y,z,sigma 与物理常量。4旧留出只能供 compression oracle 评价，不得传给 infer。|
|原生查询输入|上述实现目录的 `QUERIES.csv`|`query_id,frame,x,y,z`，含51受体查询与网格查询。|
|原生查询输出|上述实现目录的 `QUERY_OUTPUT.csv`|`query_id,frame,x,y,z,ppm_float32,physical_free,wind_x,wind_y,wind_z`。受体浓度可用来准备标量观测；整体文件不交给 infer，避免访问隐藏网格。|
|物理时间绑定|上述实现目录的 `QUERY_PHYSICAL_LINEAGE.csv` 与 `ALL_FRAME_SHA256_AND_TIME.csv`|实际 target 时间、选中快照时间与 next-frame 时间、风索引、快照 SHA。不得以帧名直接标物理时间。|
|三维几何|`PARENT_M2M3_FROZEN/M2_FROZEN/frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv`|冻结原生3D占据与边界。|
|完整受体计划|`PARENT_M2M3_FROZEN/M2_FROZEN/observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv`|51 行，50主曝光。frame1001重复权重为2，另一分支不是新增训练曝光。|
|已有标量观测事件|`PARENT_M2M3_FROZEN/M2_FROZEN/source_blind_inputs/branch_0.json` 的 `observation_events`|H101–H104和O0匿名任务。只抽取该字段写入新的 ObservedGas 输入，不把 reference_events 或目录名作为任务真实源。|
|原评分函数|`PARENT_M2M3_FROZEN/M2_FROZEN/score_source_blind.py:source_blind_scores`|只接收匿名候选 2份×50二值事件和匿名任务50事件，不接收源坐标、角色或真实源。新规范化规则需另行冻结。|

4个训练库共有224,296个不重复快照粒子记录，按50主曝光加权为229,060记录；旧缓存含2,242,960个粒子×受体贡献值，其中31,311非零，2,211,649显式零。缓存物理读出是全帧×10受体交叉，**不是所有这些交叉查询都实际观测过**。共同查询损失应绑定事前声明的实际查询加权；额外交叉受体响应可用于训练切分构造，但须明确权限与权重，不能静默当作独立观测。

原始快照总压缩文件量6,906,559 B，旧196 NPZ总3,999,614 B。每库 QUERY_OUTPUT 受体51条，主分支50条；8库共408条受体锚点，实际任务主查询400条。详细网格行数由机器清单逐库记录，网格浓度不应进入 infer 观察端。

## 2. NPZ schema 与快照 schema

NPZ 可安全 `np.load(..., allow_pickle=False)`：

- `filaments`: `(N,4)float32`，前三列世界坐标米，第四列 sigma_cm。
- `contributions`: `(N,10)float32`，按原粒子序排列的正确 PID+LOS 单粒子 ppm，包含零。
- `native_totals`: `(10,)float32`，原粒子顺序的串行 float32 累加，不能用普通成对 `np.sum` 声称位级等价。
- `cutoff_eligible,LOS_blocked,positive_contributors`: `(10,)int64`。
- `reference_frame,planned_time_exposure_weight`: `int64` 标量。
- `total_moles,all_gas_moles`: `float32` 标量。

原快照序列：`GADEN_RESULT\0`，compression mode0或1（ZLIB），GADEN版本3.0，`point`源、`filaments`粒子表。解码所得 descriptor 含 dimensions/minimum/maximum/cell_size/source/gas_type/total_moles/all_gas_moles/wind_index/filaments；本8库气体类型13、风索引10。只读取格式与常量不能称已执行物理或原生读出。

## 3. 正确物理读出与回退入口

可直接以隔离模块导入 `RK0_NEW/source/verify_raw_receiver_queries.py`，该模块没有导入即运行的行为。入口为：

- `snapshot(path)`：读取物理候选快照。
- `occupancy(path)`：读取冻结3D占据。
- `concentration(point, desc, occ)`：正确纯 Python 标量 PID/LOS 串行 float32 读出，返回浓度与 eligible/LOS_blocked/contributors。
- `los(start,end,desc,occ)`：原生LOS条件；`cell_state` 使用 float32 除法后朝零截断，不是 floor。
- `dot_sqr,length`：按原生 float32顺序计算距离。

该源码 SHA 为 `78c62afc280ff2975d02421989ea39eb7cfc484f455cef75355cdd76a44df507`，原始 C++ 算子副本位于 `PARENT_M2M3_FROZEN/M2_FROZEN/independent_raw_query_verify/source/Simulation.cpp`，`Simulation::CalculateConcentration`、`CalculateConcentrationSingleFilament`、`ConcentrationAtCenter` 和 `CheckLineOfSight` 可供核验。

完整规则包括：严格 `distance_sqr < (3*sigma/100)^2`，sigma厘米与距离厘米一致；LOS两端都必须Free，再沿线测试；中心浓度使用快照保存的总丝团摩尔数与空气摩尔浓度，原生sqrt/exp按既定返回类型；按原粒子顺序累计到float32。只做二维核均值或省略LOS不能称F。

`RK0_NEW/source/cache_native.py:cutoff_and_contributions(filaments, points, desc, occ, raw)` 是已有向量cutoff、逐合法粒子LOS与exp实现，保留全零矩阵，并原序生成native_totals。可用于同候选状态 F 或合法缺核粒子回退，但不得直接调用 `build_cache` 扩建旧缓存；新输出必须隔离保存。

合法回退应从**当前候选自己的快照**取缺核粒子。可在隔离代码中向 `concentration` 传入仅含这些粒子的 descriptor 副本，或用上述单贡献实现生成缺核子集的φ；常量/占据/受体保持一致。最后将核近似与回退值合并，并记录缺核粒子数、真实cutoff/LOS/exp调用数。它是候选预测侧物理回退，不是RK1观察侧真实尾项。观察侧留出快照或其φ不能被infer访问。

## 4. 两个接口的最小独立输入类

`CompressionSnapshot` 可持有模拟器 filaments 与mole常量，明确oracle编码权限；`compression`可在留出模拟器快照上测全查询误差。其输出不进入 infer 的 observation 参数。

`CandidateForecast` 仅持有匿名 candidate_id、该候选参考实现的snapshot路径/descriptor、参考编号与时间、许可几何；不得包含 truth_source、heldout_bank、观测φ或observed_snapshot_path。`ObservedGas` 仅持有 task_id、查询ID、ppm/event、受体XYZ、物理时间与许可环境。`ReceiverPlan`仅包含停留/采样计划。用明确不同的数据类与不同目录构造，不能以 `oracle=False` 开关共享隐藏状态对象。

候选参考目录可保留原资产引用用于provenance，但模型路由只能依候选自身粒子物理特征，不依据字符串C7/K2。最终推断若只使用训练4库预测参考，它没有留出候选状态外推测试；其无标签接口有效，但属于旧二源任务，不构成独立泛化证明。

## 5. 三项去 oracle 测试（须运行真实infer入口）

1. **隐藏状态剥离**：先将所有候选参考与ObservedGas准备为独立目录，冻结SHA；获取infer原输出。用全新观察目录删除/替换全部测试snapshot、粒子表、Q计数、φ、native尾项和网格浓度，只保留ObservedGas与ReceiverPlan，重跑同入口。候选逐查询预测、raw score与规范化地图的SHA应完全一致。以候选输入不变为前提；不要求compression不变。额外可用deny-list访问记录明确infer未打开禁止路径。
2. **候选编号置换**：用确定性双射将候选`C7,K2`重命名为不含角色的随机长度标签，并逆序输入。同候选参考路径/物理状态不变；经反置换后预测、raw score、归一化概率按键逐值与原结果完全一致。必须避免JSON字节比较受到字典顺序影响；应先canonical-sort。不得只检验Top1名称。
3. **真源映射缺失**：运行目录中不存在 `HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json` 或其副本，调用infer仍应成功为每任务每候选生成完整预测和归一化结果。冻结全部结果SHA后，独立evaluation模块才恢复映射以计算正确源NLL等。结果输出不可内含test truth。仅检查infer函数形参不足，应验证文件访问与执行成功。

这三项使用已拟合模型重跑推断，不重新拟合模型或再查看测试结果选规则。

## 6. 成本实测要求

必须把已有NPZ载入、从raw快照解码、F物理读出和核模型预测成本拆开。缓存 `native_totals` 或单贡献求和仅是 **cached lookup / cached reduction**，不是完整F成本。公平读出计时可复用同一已解码候选descriptor，但F应实际扫描全部候选粒子并调用cutoff/LOS/exp，报告其循环粒子对数；若报告端到端成本，则还要加上双方各自的读取/解码成本。

应记录每候选每查询：读取字节、decode墙钟、routing/encoding墙钟、核decode墙钟、缺核记录数/比例、cutoff测试次数、LOS次数与LOS网格步数、exp调用数、输出总墙钟与RSS。全F和合法回退读取同一三维几何；全部模型使用同一受体点和sigma/摩尔常量。用perf_counter_ns计时、独立RSS采样，统计cold read与已读共享state的内存读出时必须注明模式。

参考4库实际任务为200主query；含分支替代则204。留出compression评价同样200主query/204含替代。新A若只需要参考源推断和留出压缩，完整成本上界对应400主query，不能把10受体×196缓存的1960次计算混成实际主查询成本。50块相关，预算和结果按4完整实现等权；第51替代只是血统锚点。

L至少把切分候选搜索、训练误差评估、路由节点与阈值字节计入建模和存储；即使最多4叶，真实总容量也可能大于S。缺核回退占比和读取/路由成本会决定是否有实用收益。共用气体传播本次成本为0（旧资产）；其历史生成成本单列，不能说当前读出模型已经省去了传播求解。

本报告不实施新F或回退计算，不提供未实测的性能保证。
