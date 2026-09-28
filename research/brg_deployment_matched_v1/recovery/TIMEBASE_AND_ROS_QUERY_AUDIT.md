# BRG V1 连续资产时基与查询审计

本记录在任何 V1 网络训练或闭环评分前完成。它只验证输入资产与回放接口，**不是算法 PASS**。

## 原生写帧时钟

冻结设置为 GADEN `sim_time=300.0`、`time_step=0.1`、`results_time_step=0.5`、11 个 wind state，循环 `1..10`。原二进制对应的 `RunningSimulation::AdvanceTimestep()` 在每步对 float32 `currentTime` 检查 `currentTime > lastSaveTime + saveDeltaTime`；写帧后才更新风 state，然后递增时间。`SaveResults()` 使用连续保存序号命名 `iteration_0..`，**文件号不是物理秒**。

`derive_frame_time_map.py` 按这些原语重建 IEEE float32 时钟。预测 3000 simulation steps、566 个保存帧、首帧 `t=0`、末帧 `iteration_565` 位于 `t=299.809082031 s`。三组环境首条各实得 566 帧；最终 72 条全部是 566 帧。映射保存在 `RESULT_TIME_MAP_300S.tsv`，SHA256 为 `a0af8f46ab91fa0e2f46f0af69076a72e5884e7d0ad38858c280e0aa4f38f728`。

## VGR 可选物理时间回放

原 `seeded_time_replay` 采用 seed offset 和 VGR step 对 564 帧取模，不表示这批 GADEN asset 的物理时间。已在 VM VGR `sim_timebase.py` 增加**仅供这批资产使用**的 `physical_time_replay_300s` 可选模式：每个 VGR 时刻读取不晚于该时刻的最近原生帧，300 s 末使用帧 565。它要求 `max_iteration=565`；旧 `seeded_time_replay`、`fixed_debug` 分支不改。VM 原文件有 SHA 备份，安装后哈希与路径见 `VGR_PHYSICAL_REPLAY_PATCH.json`。`check_physical_replay_vm.py` 核验了 1501 个 0.2 s VGR 步、单调与因果选帧、300 s 覆盖，并逐步对比旧模式结果，PASS。

## 实际 ROS 数据路径

从已转存且校验的 H01 原生 archive 恢复一条测试副本，在独立 `ROS_DOMAIN_ID=226` 启动已编译的 `gaden_player`，使用 `manual_iteration_mode=true` 与真实 occupancy file，通过 `/frame_query` 查询帧 `0,1,300,565`。四次均返回有效且有限的气体与风值，见 `PLAYER_SMOKE_RESULT.json`。测试副本已在宿主 archive 哈希一致且 smoke 结果复制后清理；宿主唯一持久副本未删除。

此项 smoke 证明 native archive 可被实际 player 查询，尚未证明 248 次完整 VGR 采集、BRG V1 训练或 32 次四臂评价已完成。正式运行仍须在相同物理回放模式下记录每一步 `t_sim_s`、`iteration`、source-independent 原始传感器读数与事件窗口。
