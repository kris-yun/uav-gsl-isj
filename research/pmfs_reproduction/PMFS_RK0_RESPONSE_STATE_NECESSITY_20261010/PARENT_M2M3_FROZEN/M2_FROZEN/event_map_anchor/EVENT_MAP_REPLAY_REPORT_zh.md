# 冻结事件到原生测量图：完整 B4 锚点通过

判决：`OBSERVED_B4_NATIVE_EVENT_TO_MAP_ANCHOR_PASS`。本子任务实际完成隔离入口编译和原 B4 50 块全正检出回放，没有新增候选传播模拟、GADEN、ROS、导航或源后验。

使用冻结 B4 原生二维 occupancy 和可见性构造，34×45 网格，0.25m，447 个合法自由格；原点是官方二维图的 float 坐标 (-7.55,-7.88)。不使用气体生成三维图的不同 y 原点 -7.8795。先验 .3；kernelSigma/stretch=1.5；localEstimationWindowSize=2；confidenceSigmaSpatial/MeasurementWeight=1；visibility range=5，与冻结参数相符。独立入口复用已核验原生 Fixture 的可见性构造和 fresh 编译的冻结 PMFSLib.cpp，不调用 Simulations。

输入 MAP_REPLAY_EVENT_COVARIATES.csv 保留每块机器人 x/y、TO 风向、风速与实际更新时间。由本入口原生 metadata.coordinatesToIndices 做 float 坐标转格；不按事后真源改变受体位置。每块仅传入一个既已形成的 binary event，PID、块成员、原始浓度与阈值阶段由上游合同负责，本入口不替代其核验。

对原 B4 全50块事件=1，1530个完整网格单元的 logOdds、omega、confidence 与冻结 update_2/input.csv 最大绝对差均为 **0.0**，occupancy完全一致；包含被排除格。事件 ledger 50行，event_cell_lineage.csv 22350行（50×447），记录每个原始块对每个自由格的 logOdds/omega增量和更新后置信度。传播格不因表格行数增多而成为独立观测。

编译12.000秒，峰值RSS770,342,912字节；anchor实际运行0.274秒，exit=0、stderr为空。EstimateHitProbabilities调用50次；源候选前向、源后验更新、ROS节点和新气体实现均为0。

原VM入口：`/home/zyc/pmfs_m2_event_map_replay_20261010/event_map_replay`，SHA256 `7d05e5124bd8e2bc6c6e1eb9b567599a6a456b3baf92c9dec9e698fed669cfbc`。调用格式：

```
event_map_replay SNAPSHOT COVARIATES LABELS NEW_OUTPUT
```

LABELS必须是恰好50行、按block_id=0..49排序的`block_id,event_hit`，事件只能为0/1。入口不接受候选坐标或真假角色。所有物理共变量和支持来自同一个冻结公共 snapshot/covariates。输出 map.csv 和逐事件逐格血统，始终没有源后验。

`run_event_map_batch.py`提供匿名批量标签接口：JSON只有`maps`字段，opaque_id映射到50个binary events。最多16个图用于8份 bank 的两个预注册成员分支；这不是物理 bank 或候选前向预算。每张地图 fresh 进程，单线程，公共 executable/输入 SHA 固定，整批120秒、RSS512 MiB。它只能在后续 bank 的上游响应和事件资格通过后由主任务调用；本交付尚未执行这些新 bank 地图。CLI和输入定义在脚本中，脚本不做任何浓度查询或生成。

`verify_event_map_anchor.py`默认只读，核验原 B4 完整锚点、22350行血统、零新增物理/ROS调用和SHA。`frozen_expected_input.csv`是原输入复制，原始文件未改。

锚点成立允许后续比较“同一3D物理候选经过相同PID/块事件与建图算子后的预测图”，但它不证明447格独立，也不把 map 相似度称为合格联合似然。新 sourcebank 的统计或科学结论由主任务产生，本子任务不提前给出。
