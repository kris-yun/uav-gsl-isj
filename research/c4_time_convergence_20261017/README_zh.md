# C4二维预热与记录时长收敛审计

先读 `科学裁决_zh.md` 和 `FINAL_DECISION.json`。

结果为 **HOLD_CONVERGENCE_UNRESOLVED**，伴随响应改善但判别未恢复。
延长原生预热确实能产生此前缺失的远端占格响应；360秒仍未稳定，C4末次真源对锁定竞争源的评分差全部为负。
这不是主创新成立，也没有新增机器人闭环收益。没有新世界、ROS回合或新后验。

身份是修风后的2026实现、仿真水平真风、重新生成GADEN世界中的固定历史；不能称2024论文精确复现或湖岸实测。

## 包内数据

- `inputs/`：三份冻结测量/障碍/风输入、设置、源树、156项源状态、全部合法子源、旧原始/模糊地图、Gaussian缓存、实际窗口与未阈值consumer gas读数。
- `inputs/historical_native/`：原历史单次自适应结果的真源及原锁竞争源地图、释放点、Gaussian状态；与三个预测状态的自适应重复分别保存。
- `code/`：上一轮原生运动、释放、评分、模糊、网格和随机函数；核心文件未改。
- `diagnostic.cpp`：仅添加有界时长循环和旁路诊断。156项自适应基准与旧输出精确一致。
- `results/`：每源每状态每时长的全图raw/blur、10秒记录块、20秒累计图、评分、计数和压缩逐帧轨迹。
- `analysis/`：逐受体响应、源对logscore、所有正反例、相关性、存活/到达/出流和成本CSV。未建立新完整源概率。
- `lineage/`：SHA、官方原函数、旧结论、三份历史原生后验读出、技术失败和恢复现场。
- `EXECUTION.json`、`logs/`：实际命令、退出码和成本。

`trace.u32.gz` 解压后是小端uint32数组，每行长度 `9 + 3 * len(receivers.csv)`。
前9项依次为 phase(0暖启/1记录)、phase_step(从1开始)、active_before_move、active_after_move、exits_this_step、released_total、exited_total、moves_low32、moves_high32；
每个受体追加 centre_count、first_lifetime_visits_this_step、cell_entries_this_step。
暖启与记录dt分别为0.2/0.1秒。计数读取不消耗RNG。气团和帧彼此相关，不是独立物理重复。

`consumed_by_this_update=false` 的受体仅为事后诊断，未加入该次测量地图或评分。
PID位置关联不认证每条原始消息与平均窗口的精确owner。
`analysis/RAW_PID_BY_CASE.csv` 将每个原始consumer gas行按case导出一次并保留源行号；
`RAW_PID_UNTHRESHOLDED.csv` 是逐update视图，C4在两个update中重复出现，不能当成额外独立样本。
Oracle是已声明的真值诊断，不是算法输入或增益。

## 实际运行

依赖Python 3.10+、NumPy。完整前向重跑另需Linux、CMake、C++20编译器、OpenCV(core/imgproc)和zlib。
参考运行版本见 `lineage/RUNTIME_ENVIRONMENT.json`。
严格的原生资格校验可能因不同编译器/标准库/OpenCV浮点行为而失败；必须保留失败并核对，不能降低门槛后声称等同。

```bash
python reproduce.py --verify-only
python reproduce.py --analysis-out /tmp/c4h17_fresh_analysis
```

第二条只复算本包保存的地图和轨迹，不调用前向模型。输出目录必须不存在。

如要独立完整重跑本轮冻结离线计划（1092项；不生成GADEN世界、不启动ROS），另行显式执行：

```bash
python reproduce.py --full-forward-out /tmp/c4h17_new_forward
```

该命令先做156项精确原生资格对比，再执行冻结时长。CPU上限1800秒、输出上限512MiB，90分钟运行起点不因恢复而重置。
原研究曾有1次驱动中断，只恢复未完成项，实际1093次启动/1092项有效输出；失败完整保留。
全新重跑不需要也不复现该驱动错误。

`prepare.py`、`scripts/recover.py` 和 `scripts/audit_and_report.py` 同时保留本次历史操作的可审计来源；它们不是新环境下完整重跑的入口。

本轮结束，不自动运行 `FINAL_DECISION.json` 中的下一项提案。
