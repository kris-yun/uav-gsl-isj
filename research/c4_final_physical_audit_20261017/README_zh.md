# C4有界物理证据结束包

先读`科学结束裁决_zh.md`和`FINAL_DECISION.json`。本包结束C4主创新追索，既不宣布新算法，也不自动运行下一轮。

本包：6次普通二维源对控制；809个既有GADEN帧；878条同帧气体服务重算；505条PID消息相容绑定；全部正反例和源评分。所有物理真值只用于离线诊断，禁止作为线上免费参考库。

在解压目录运行（Python 3.10+，NumPy）：

```sh
python reproduce.py --verify-only
python reproduce.py --event-audit-out /absolute/NEW/event_replay
python reproduce.py --analysis-out /absolute/NEW/analysis_replay
```

默认入口不运行气团传播，不启动ROS。NumPy观测复核从已有帧重算浓度和三类中心事件；原运行R6库版本的C++观测重算已在本机通过逐位校验。`scripts/build_physical.py`可在相应GADEN开发环境编译`code/physical_events.cpp`；它读取快照，不推进气团。

`scripts/six_controls.py`是已执行记录，**不要再次自动运行**。它使用前轮编译的、代码哈希已核验的timed程序；对应C++源码、输入、三组原状态及输出都在包内。需要独立重放时应由复核者明确选择新目录与构建环境，不能覆盖本轮结果。

目录：`inputs/physical_frames`是已有真源物理世界的只读片段；`source_runtime`为原R6核心源码及构建身份，`source`为当前主工作区来源对照，两者明确区分；`code`为普通审计工具；`results/six`保留全部6次原输出；`analysis`为逐源逐受体CSV；`lineage`包含上轮HOLD、C3反证、历史原生读数及来源核验；`logs`保留错误和修正过程。

这是2026修风开发记录，不是作者2024原始实验数据或湖岸现场实验。没有重新运行前轮1,092或10,122次模拟。
