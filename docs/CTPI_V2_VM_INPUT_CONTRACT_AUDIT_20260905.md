# V2 实时输入契约审计（2026-09-05）

状态：`VM_ACCESS_OK_INPUT_CONTRACT_NOT_READY`。只读源码审计，不是新闭环运行或效果验证。

## 当前身份

- 本地 HEAD：`46b33b6`，工作树保留新增 V2 文件及全部旧负结果。
- SSH：`zyc@192.168.111.128` 已恢复，本轮实际读取 VM 源文件成功。
- VM 历史运行源码：`/home/zyc/CTPI_G2_M12_SEED12_20260905/repo`。
- VM 模拟器：`/home/zyc/CTPI_G2_M12_SEED12_20260905/vgr_bridge_overlay_c8454d5/vgr_bridge`。
- 本轮没有启动实验、修改 ROS 安装或读取受保护 bank 载荷。

## 已查实的接口与限制

| 环节 | 源码证据 | 对新实现的约束 |
|---|---|---|
| 启动 | fasttrack launch：server/runner 在 5 s 启动，8 s 固定调用 `/start_simulation` | 固定 wall-time 不是观测链就绪证明；V2 需要就绪握手与完整流检查，不能只延长延时 |
| 初始传感器 | `vgr_sim_node.py` 暂停时输出初始状态，不推进 FOPDT；初始 input/state 都为零 | 可以从模拟 t=0 初始化**传感器**，条件是订阅链收到全部后续样本；不能从晚到首条消息重置 |
| 初始气场 | `sim_timebase.py`：`offset=(7919*(seed+1)) % max(1,max_iteration-1)`；replay frame=`(offset+step) % usable` | 传感器零状态不等于环境气场零状态；不能把 seed12 的既有 plume 当作在 t=0 新释放。源启动年龄/初场属于尚未解决的模型干扰 |
| 起始风消息 | raw/GADEN 路径 `_frame_wind` 初始化为零，只在 advancing `_sample_gas` 时由 frame query 填写；暂停起点直接返回该缓存 | t=0 的零风消息是初始化占位，不是实际无风证据。首个真实风样本到达前的预测必须承认风未知，不能用后来的风倒填，也不能把零风当已观测 |
| 样本时间 | gas、pose、anemometer 均带同一 sim stamp；步长 0.2 s | 保留消息时间与接收顺序；姿态配对不能用异步回调的“最新位置”替代同时间位置 |
| 规划暂停 | `_simulation_tick` 在暂停时继续发布同一 sim stamp 的消息，不推进传感器状态 | 相同时间戳、相同值只计一次证据；同时间戳冲突值、旧帧回流与真正跳帧应报错。不能把正常暂停复播误判成缺失/新证据 |
| 订阅时序 | `Common/Algorithm.cpp::Initialize` 先等待定位，再创建 gas/wind 订阅 | 必须证明无首段样本丢失；不能假定启动节点就是订阅就绪 |
| 全场风服务 | `gmrf_msgs/srv/WindEstimation.srv` 返回 u/v、var_u/var_v/cov_uv，无 header/stamp | 接收时刻只能证明信息此后可用，不能证明场内最新观测时间或陈旧度 |
| 风协方差 | `gmrf_node.cpp::get_wind_value_srv` 确实填写每点 2×2 协方差分量 | 不再声称“没有协方差”；但每点边缘协方差不等于跨空间/时间联合轨迹分布，也不自动等于已校准误差 |
| 旧风接线 | `PMFSLib.cpp::EstimateWind` 的 GMRF 路径只复制 u/v；失败仅警告 | 新 V2 不能从这个路径继承协方差或 freshness 保证；失败不得被当作成功新快照 |
| 风观测独立性 | GMRF 用 anemometer 与传感器姿态插入观测 | 风确实是已有在线输入，不需读取真源；但导航位置是自适应选择的，不能据此宣称全场无偏或源/输运可辨识 |

## 影响机制设计的关键推论（不是已测收益）

1. 新 V2 的 no-flux 数值核心守恒，是数值测试结论。持续正源且没有任何出口时，域内总质量必随时间增长，故不存在有限质量稳态。不能通过任意 warm-up 把未知初场问题“消掉”。实际通风/边界模型尚待建立和验证。
2. 按同源候选共享干扰轨迹是必要的模型一致性要求，但此前已执行的等价性门槛证明：它本身不产生区别于同输入普通 Bayes 的新估计器。新贡献若成立，必须来自可验证的域内因果结构/识别信息，而不是混合公式命名。
3. 当前输运/传感器核心与独立 ROS 输入配对测试通过。M1 新机制、候选初场、风轨迹分布、完整算法 ROS 接线与任务增益均未通过。
4. 进一步读到 `gmrf_map.cpp::insertObservation_GMRF` 没有时间戳参数，直接追加 `activeObs`，并设置 `time_invariant=true`。结合模拟器暂停复播，可确认这一插入路径自身不去重、不按消息时间老化。不能从这些协方差直接构造“独立、时变、已校准”的输运干扰样本；尚未测量此行为对旧 R4 后验的实际影响，不能把它直接定为旧结果失败原因。
5. 本地 `MovingStatePMFS.cpp` 的 MAP 追逐分支以 `cpirEnabled` 为条件。旧 A0 与 F00 的变化包含估计器和控制分支，不能把旧三臂直接称为新 V2 的“同控制器估计器消融”。未来三个臂必须共用同一控制代码、参数、动作候选与触发规则，只更换源信念和 M2 输入；需记录每次控制分支与输入信念，避免把新增追逐策略的收益计到 M1 因果估计器名下。本轮未修改该旧分支。

## 本轮 VM 文件 SHA-256

```text
c6bb07015bed1206a79ed9ef4cda5f2aae8434017b3e89545fbaa0dc3d9d4dc4  /home/zyc/ros2_ws/src/gmrf_msgs/srv/WindEstimation.srv
84e4cba3dac5ed76b25f3eb86703b98db79a939eec491ba5475288bc893b4e74  /home/zyc/ros2_ws/src/GMRF-wind/gmrf_wind_mapping/src/gmrf_node.cpp
2b5d69d5a7cb00def5f462e1f0bc985eb9ca27a4bdad0bd3774abcd7e9204ed5  vgr_bridge_overlay_c8454d5/vgr_bridge/vgr_sim_node.py
a104873911f23c27dba39001d1919092a5f58195f03e37f86fc76b0040c4351f  vgr_bridge_overlay_c8454d5/vgr_bridge/sim_timebase.py
```

下一步先落实新 M1 的识别条件和小规模反例，再按这些条件实现输入层；不启动 House 或多 seed 批次。
