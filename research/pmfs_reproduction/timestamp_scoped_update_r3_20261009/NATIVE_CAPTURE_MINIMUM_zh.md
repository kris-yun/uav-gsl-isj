# R3-B 最小缺项与停止说明

判决：`SCOPED_P1b_HOLD / NOT_RUN_INPUT_QUALIFICATION_HOLD`。本轮0次原生源更新，不生成 `R3_SINGLE_UPDATE_PARITY.csv`。

R3-A的固定姿态门已经通过。阻碍不再是原版动态消息的90°反例，而是旧20事件无法证明其合法时间/TF合同，且没有完整原生更新状态。

|层|现有证据|缺项|
|---|---|---|
|测量入口|20条 delivered-event，4个停留位置；可重构已存地图|组成每次平均测量的原始消息成员、stamp、frame、采样和消费时刻TF|
|物理时间|event/query有steady_ns；播放器日志有t_sim_s/step/iteration|两时间域及具体气体帧、前向风查询之间的可靠连接键|
|候选模拟|87个粗叶、626格已存前向风；87张离线C图哈希全部通过|同一次真实更新中的叶内随机点、RNG和Gaussian缓存、粗层与细分层hitMap|
|后验|固定粗候选的评分复算已合格，沿用P0/P1结果|原生raw score、细分树、最终归一化概率图和排序|

在已知原始R1目录中，`results/`为空；没有ROS bag/逐消息TF记录。仅检查该目录及既有审核资产，没有重新搜盘。`sim_pose_trace.csv`可描述模拟轨迹，不能替代消费者实际采用的TF和平均块成员。`wind_query.csv`未保存对应播放器帧键。不能把steady_ns直接解释为气体物理时间，也不能用当前新鲜消息重写历史stamp。

下一阶段的最小交付是一份合法的单更新快照，而非一套完整300秒导航：入口记录原始消息成员与TF，在 `Simulations::runSimulation()` 保存每个候选/细分子叶的采样点、随机状态、hitMap及raw score；在 `Simulations::updateSourceProbability()` 的局部树销毁前保存细分树，并在归一化后保存全部后验单元。两端使用相同生效参数、网格、风和随机状态，逐层比较。

这些是所需钩子和数据，不是本轮新执行计划。现有文件无法逆推出全部丢失状态；本轮按用户合同停止，不扩大场景或生成新气体数据。
