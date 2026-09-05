# GMRF 风方向/位置契约：实际二进制检验与显式编码修复

状态：`CURRENT_BINARY_DIRECTION_MISMATCH_CONFIRMED_EXPLICIT_PATH_VERIFIED`。
这不是风场预测、误差校准、M1 创新或闭环效用 PASS。

## 实际查到的接口冲突

- VM VGR 模拟器发布 `frame_id=map`，`wind_direction=atan2(v,u)`，表示下风向。
- 当前 GMRF `sensorCallback` 将消息视为传感器坐标系上风向，变换后再加 3.14159。
- 同一回调以 `lookupTransform(map, msg.header.frame_id, stamp)` 获取观测位置。
  对 `frame_id=map` 这是恒等变换，故取到地图原点，而不是 UAV 的观测位置。
- GMRF 的 `AddWindObservation` 服务直接接收 map 位置和下风向，不经过上述转换。
- 本地 `Common/Algorithm.cpp::windCallback` 已按下风向处理消息；不能全局把模拟器
  风角翻转180度，否则会破坏这个消费者。修复必须按消费者接口实施。

源文件路径：

```
/home/zyc/CTPI_G2_M12_SEED12_20260905/vgr_bridge_overlay_c8454d5/vgr_bridge/vgr_sim_node.py
/home/zyc/ros2_ws/src/GMRF-wind/gmrf_wind_mapping/src/gmrf_node.cpp
```

## 二进制实测，不只看源码

在专用 `ROS_DOMAIN_ID=193`、localhost-only 域，运行现有 GMRF 二进制的两个
独立小网格进程。7×7 网格没有气体或源，未启动 House 或读取 bank。
每个进程从新状态开始，输入下风向 (+1,0)，查询四个点。

| 路径 | 四点估计 u 范围 | 解释 |
|---|---:|---|
| VGR 风格 map 消息、方向0 | -0.999999 至 -0.999990 | 当前二进制把下风向翻转 |
| 新编码器 → 显式位置/下风向服务 | +0.999984 至 +0.999995 | 显式路径保留正确方向 |

R1 用直接服务字段确认接口；R2 改为调用新编码器，重跑得到相同结果。
R3 为增加专用域和输出文件存在性检查后的最终探针重新绑定测试，保留 R1/R2。
服务路径的位置字段确实设置为 (1,1)，且源码直接使用这些字段。场估计的数值
本身不能证明内部插入位置，所以没有据场幅值反推位置正确性。
两条路径的内置方差不同，不能拿两组幅值当严格的预测效用比较。

原始结果：`evidence/ctpi_v2_gmrf_interface_20260905/GMRF_BINARY_PROBE*.json`。
包含二进制、核心库、探针及编码器哈希、启动参数、原始向量及 VM 日志路径。
进程均由探针创建并在退出时终止，没有碰其他 VM 进程。

## 已实现的修复构件

`closed_loop/ctpi/ctpi_v2_wind_observation.py` 提供显式编码：

```
stamped pose_xy + downwind_uv
    -> x_pos/y_pos + speed/atan2(v,u)
    -> GMRF AddWindObservation request
```

- 坐标来自同时间戳的实际在线定位，不从 map→map TF 推测。
- 风是原在线下风向，不读取真源、全场真值或 gas。
- 拒绝 t=0 未观测风占位、非法时间、形状和非有限值。
- 不改动模拟器消息或旧 GMRF 安装；不会影响原 Algorithm 的下风向消费者。
- 三项 CPU 单测覆盖四象限/零风、位置、起点占位及非法输入，并通过真实 DDS
  服务路径完成 R2 检验。

编码器只完成请求生成，不是常驻转发节点。投入运行前仍须：

1. 只消费 `StampedIngress` 去重后的新帧，并禁用 GMRF 原 anemometer 订阅，避免双计数。
2. 解决服务空响应的确认语义、请求时序、风场快照的可用时刻及陈旧度。
3. 处理 GMRF 长期保留旧观测的时变性问题。当前服务内置方差未校准，且没有跨时空联合协方差。
4. 在三个比较臂中使用相同的已冻结输入层；不能只给新臂纠正基础风接口。

## 历史与科研结论的边界

当前 HEAD 的 runner 前缀列表指向 `/home/zyc/ros2_ws/install/gmrf_wind_mapping`，
R4 日志也有该节点启动，但没有找到与旧 R4 绑定的不可变 GMRF 二进制哈希。
因此可以确认当前二进制的契约冲突，不能仅凭路径/文件日期宣称旧 R4 完全相同，
更不能将所有闭环失败直接归因于此。原始 NO_GO 及其数据保持原样。

Idea-spark 对共享释放候选的本轮审查仍未给出合格 M1：问题不是不能胜过同模型
Bayes，而是缺少由允许输入产生、可独立论证的源到观测路径传播关系和干扰模型。
审查文件保留为 `phase2_generate/release_coupling_generation_finding.json`，
不是正式 Phase 3 结果。风接口修复消除了一个工程冲突，但不自动补齐这个科学缺口。
