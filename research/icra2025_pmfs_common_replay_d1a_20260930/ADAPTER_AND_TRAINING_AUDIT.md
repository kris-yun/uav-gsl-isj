# VGR/OCB-R2 适配与训练样本审计

## 状态

`MATCHED_NATIVE_PMFS_300S_LOGS_NOT_AVAILABLE_FOR_OCB_R2_64`

官方三通道适配函数已实现，合成 software smoke PASS；**尚未从真实 VGR/OCB-R2 event stream 构造数据，也未做 transfer 训练或比较**。

## 资产缺口

64 个 S2+S2X run ID、8 context、16 source×context、各4个独立 realization 已从冻结 manifest 核验。这里可用的是 E1 固定30-probe tensor，原10个观测时刻覆盖50..500s。

没有与这些 ID/seed 一一对应的 Native 300s 最终估计、actual UAV trajectory、sensor stop/event/local-wind 日志。现存历史49条 Native 轨迹、旧 VGR 案例、AOD/B2结果属于其他实验，均未用于配对。

本轮只 hash 现有 tensor 文件，不 decode 浓度。confirmation/H03 未读取。64行 metadata split 是未来分组的预留，不是已执行的比较。

## 已实现调用链

`official_three_channel.channels(occupancy, resolution, origin, observed_events, budget_s=300)`

→ 按 timestamp/event ID 顺序，使用截止预算以内事件；

→ encounter=True 的实际访问位置构造 encounter mask；

→ 显式提供的官方 clockwise-degree + quaternion 通过原函数构造局部风 halfplane，累积；

→ 原 occupancy + wind + encounter 构成3×279×279输入。

原 notebook 函数通过 AST 提取执行，无改写；真实源字段不属于输入 schema。未访问位置保持 encounter=0。输出位置函数沿用论文 centroid，peak只诊断。合成 smoke 验证风 raster 与官方函数逐字节一致、300s后不加入、拒绝 truth 字段、未访问格不填值。

该程序是离线转换器，不是已部署的 ROS service/planner，也没有实际执行 VGR waypoint。

## 必须先解决的桥接问题

1. **方向约定**：官方输入是设备 clockwise bearing，经姿态转换。VGR wind `atan2(v,u)` 是 flow-vector 时，不能直接假定与设备 from/to 一致，也不能未经证据加π。当前 adapter 要求调用方显式给出已核验的 official angle；尚不自动将 VGR UV 转成该角。
2. **Observation event**：必须先冻结 hit threshold、窗口聚合、sensor state、event segmentation。固定30个 probe不等于一次 encounter；4 seed与500s tensor不能直接当300s移动机器人日志。
3. **Map 与坐标**：需要实际 map resolution/origin/axes/frame、z footprint。超过279格时拒绝；不能为了输入尺寸悄悄改变物理空间。
4. **Timebase**：用真实 simulator时间筛选≤300s，writer ID不当秒；边界因果取帧与窗口必须来自同一合同。
5. **Native support/估计**：需实际固定合法 support与 Native源图位置估计器，不对 U-Net 或Native重调以迎合结果。

## 训练样本构造：已明确、尚未执行

在获得获准且共同可读的 event stream 后：

1. 每条 physical run 独立生成截至各 encounter 的 prefix；只用 prefix当时已知的气体/风/位姿/地图。
2. 与官方完全相同的累积三通道；N是该 run 的真实 encounter序号，不根据定位成绩重编号。
3. 只在训练label构造阶段读取训练source坐标，按官方 D_N soft label + occupancy公式；测试source只进独立 evaluator。
4. 输入、label一致旋转4次。所有prefix/旋转/窗口跟随原physical realization同fold，不跨fold。
5. 64条 manifest当前预留4fold：replica1..4对应testfold0..3，各fold48train16test。它验证 stochastic-realization split，**不声称source-unseen或House-unseen**。
6. 将真实 stream/地图 hashes 和 sample→parent run mapping提交后再训练。若实际共同合同改变了样本生成，需在揭示测试结果前另行冻结；不能偷偷将当前 reservation写成已完成benchmark。
7. 完整训练的epoch、初始化、是否使用官方预训练、validation/model selection必须在执行前签署。本轮只跑官方自带数据的2步训练，不生成 OCB权重。

## 为什么不能给性能表

固定probe tensors能用于当前离线机制实验；却缺少给官方移动机器人三通道与 Native公平重放所需的状态信息。拿旧轨迹/旧seed代替，或将密集probe真值填进“encounter地图”，会改变信息预算。

因此本轮无逐target PMFS/U-Net误差、无胜负统计，缺失项不填0或伪造N/A成绩。共同合同草案另附；停止在此，不启动采集。
