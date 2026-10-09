# PMFS 时间戳修复与单更新资格复核 R3

**结论：时间戳工程修复PASS；固定姿态接口验收PASS；单次原生在线—离线后验仍HOLD；物理机制尚未合格。**

|用户要求的回答|本轮结果|
|---|---|
|时间接口工程修复是否通过？|`STAMP_PATCH_PASS`。真实ROS对照5组，修正版5/5通过。|
|原始PMFS在固定停留条件下是否有可信输入？|受控固定姿态接口4/4通过；该结论限于同钟、新鲜消息、实测TF漂移合格的fixture。旧20事件尚不能据此升级。|
|单次原生在线—离线后验是否真正一致？|`SCOPED_P1b_HOLD`。旧输入资格不足，执行前停止，本轮0次源更新，没有声称后验一致。|
|最小阻碍是什么？|旧20事件的原始测量成员、物理时间/TF连接及同一次原生候选随机状态、模拟图、细分后验快照缺失。详见 `R3_SINGLE_UPDATE_HOLD.json`。|

## R3-A：实际消费者对照

沿用固定上游 PMFS `4e141e162551e674f2f30ddb8859136c72139aac` 与 GMRF `2ec7a5db7bf5f2597e9d62ba662d3efcfc788d71`。原版完整保留，独立目录中的修正版只把 `header.frame_id = msg->header.frame_id` 改为 `header = msg->header`。核验脚本检查整份文件除这一替换外逐字节相同；diff在 `evidence/real_ros/code/STAMP_ONLY.patch`。

原版ELF SHA256：`973ffd38953e1eb0d6f7449fd3380b55092fe0b496564f3867348c91973c928e`。

修正版ELF SHA256：`0722267a80b0a13db550f757c6d9caf2e952b1d0da0eccdeae6f550e7d2d64d1`。

|输入|原版N0|时间戳修正版N1|
|---|---|---|
|新鲜、固定姿态0°|PASS|PASS|
|新鲜、固定姿态90°|PASS|PASS|
|新鲜、非原点、传感器yaw33°|PASS|PASS|
|旧stamp，之后平移并旋转90°|方向偏差90°；超出固定范围|PASS；使用t1方向与位置|
|延迟但姿态位置不变|PASS|PASS|

修正版最大方向误差 1.50995799419e-07 rad；GMRF最大方向误差 2.66961730233e-06 rad；GMRF存储位置误差0 m。所有修正版返回TF时间与原消息时间完全相等，最大消费消息年龄 0.513051981 s，低于执行前冻结的2 s限值。固定范围4组的采样至消费TF漂移均为0，原版和修正版风读数相同。动态反例的实际航向变化约π/2，平移约3.1623 m。

这次是实际ROS订阅、TF变换、StopAndMeasure存储和GMRF插入的对照。PMFS harness为共同 `Algorithm::windCallback` 的受控子类，未启动完整GSL actionserver或导航。GMRF沿用现有core共享库，已冻结哈希及源码绑定；没有宣称全依赖干净构建的二进制一致性。GMRF估计风图收敛HOLD保留。

原始CSV、TF两时刻、实际消息CDR、消费者日志、构建命令与源哈希随包提供。R2的共享FROM、map原点和混用时钟负对照结果原样引用，本轮没有重复14例测试。

## R3-B：门已分离，旧快照仍不合格

固定姿态接口PASS已解除R2的动态场景门控。本轮随后只检查已知R1运行目录及现有审核包：20条事件、29×38网格、626个自由格及前向风格、87个粗候选叶均存在，4份冻结输入哈希和87张C图哈希通过。

但 `measurement_events.csv` 只有消费日志的 `steady_ns`、聚合浓度/命中、聚合风及机器人位置；缺原始消息stamp/frame/平均块成员。模拟轨迹与传感器记录用 `t_sim_s/step/iteration`，缺把这两类记录与实际消费者TF连接的键；前向风查询也没有对应播放器帧键。4个停留位置的轨迹不能代替每条事件采样至消费的实际TF合同。

87张图来自固定候选离线评分回放，不能当成原生在线更新图。原始 `results/` 为空；缺原生叶内采样/RNG及缓存、细分树、raw score和最终后验。此前的评分复算最大绝对差约9.16×10^-16和测量图重构零差仍保留，不能据此宣布本轮P1b通过。

按[用户R3合同](https://github.com/kris-yun/uav-gsl-isj/blob/7871f6cd11e77f1755e2434a9c677c247ab2ca7f/research/pmfs_reproduction/PMFS_R3_STAMPED_TF_SCOPED_ONE_UPDATE_20261009.md)的输入资格与缺状态停止规则，本轮没有把历史数据改写成当前静止实验，也没有另建ROS触发的离线核心包装器冒充原生在线更新。最小缺项及采集钩子在 `NATIVE_CAPTURE_MINIMUM_zh.md`。没有生成单次更新一致性CSV。

## 保留判决及交付范围

P0 PASS冻结。原版移动延迟输入的时间一致性缺陷保留；时间戳修正版是工程变体。历史H02仍为UNRESOLVED_CONTRACT_HOLD，M0/M4/TNQC STOP和开题冻结版保持。`PHYSICAL_MECHANISM_NOT_YET_QUALIFIED`：本轮没有证明原生PMFS存在传播模型科学缺陷，也没有验证主创新的定位收益。

未启动新CFD/GADEN/DNS/Docker、网络训练、完整导航或新数据下载。复用已运行虚拟机，未启动或关闭虚拟机；本轮测试子进程全部退出。

`verify_r3.py` 使用Python标准库，只读核验源补丁、真实消费者方向/位置/时间、TF漂移、已存冻结输入/图及SHA清单。审核ZIP小于20 MB。报告和证据提交独立Git分支 `codex/pmfs-stamped-scoped-update-r3-20261009`，旧输出保留。

本轮完成后暂停，等待审核。
