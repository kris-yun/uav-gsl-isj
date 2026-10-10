# B4 终态补全审核包

先读 B4_OFFICIAL_TERMINAL_DECISION_zh.md。只读复核：

```text
python verify_b4_terminal.py
```

需要 Python、numpy、PyYAML、Pillow；默认不修改任何文件。复核仅做存档数据算术，不启动 ROS、GADEN、CFD、Docker、定位或训练。验证所有候选评分、后验、官方指标、地图、样本物理血统、风查询和包内 SHA256。

runtime/ 为正式 goal 的原始消息、服务、日志及更新；run/ 为实际执行程序和状态。official_B4、derived_B4、sample_frames 和 run 中 GATE1/GATE2/生成记录为首次 B4 的冻结物理资产副本，不代表本轮重新生成。完整 bank 留在现有 VM，包内保留全部 1803 帧时间/哈希与五个原始样本。prior_attempts 保留旧运行对照。

preflight_* 为本轮发送 0 个 goal 的失败启动检查，不能混作正式结果。integration 为当前参数接口的真实 ROS 回归；prior_clock_integration 是旧 CLI 版本的历史测试；fixture.py 仅用于接口测试，未进入正式运行。

官方终态为 success=true，但 Top-5% 误差约 5.112m。N1 工程对齐、单份受控仿真、单次完整 goal；论文统计复现和物理归因均 HOLD。
