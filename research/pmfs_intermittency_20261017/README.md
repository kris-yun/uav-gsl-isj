# PMFS间歇观测：先看裁决，再复算

结论：`NO_GO_FOR_MAIN_INNOVATION`，保留`HOLD_OBSERVATION_SEMANTICS_ONLY`。
这次没有新算法名称，也没有新增世界/ROS；原生C++和普通强对照都实际运行了。

先读`analysis/CAUSAL_CHAIN_DECISION.md`，再查`analysis/results/EVIDENCE_MATRIX.csv`、
`STRONG_CONTROLS.csv`、`STOP_INFLUENCE.csv`和`03_OPERATOR_TO_SOURCE_SCORE_TRACE.csv`。
数据身份在`analysis/DATA_IDENTITY_AND_ORIGINAL_RELEASE.md`，逐文件血统在
`analysis/00_ASSET_AND_VERSION_PROVENANCE.csv`，全部输入和输出SHA在根目录manifest。

## 一个命令独立复算

Linux上需要Python3、NumPy、SciPy、pandas、PyYAML、matplotlib、CMake、GCC（C++20）。
不需要ROS、GADEN、GPU或联网，不启动传感器节点。参考编译器GCC11.4。

```bash
python3 reproduce_all.py --out /absolute/path/NEW_REVIEW_FOLDER
```

必须使用不存在的新目录，约需1.5GiB临时空间。计算本身很小，许多小文件的解包/复制可能慢于数学计算。
输出包括全部命令、退出码、墙钟、子进程CPU和累计子进程RSS；不预告固定完成时间。
仅检查包完整性：`python3 reproduce_all.py --out UNUSED --verify-only`。

`evidence/native20_*.zip`为修风20配置的完整源输入、候选/owner/随机状态、原始CDR、运行状态、三维占据及风资产；
只含必要物理资产及逐帧身份/时间，不包含体积庞大的完整气体帧，也不冒充作者论文原始轨迹。
`evidence/b4_anchor.zip`保留原始八次B4审计入口和反例。
`evidence/historical46.zip`是46次已校正时钟版本采样记录，八次B4已经包含在其中。

## 下一轮研究要求

不要把A3普通分块后的0.36858m诊断读出当成真实闭环最终误差；它的源方差7.4258m²，原生停机机制会看到不同状态。
不要把A4去掉混合停留后仍落后的-1.733985评分差，写成“间歇性造成了整次错源”。
不要把2026候选快照移植到2024 R05，冒称历史随机状态匹配。
不要把普通Beta、有效块数、源域/风/时钟修复或前向事件对齐起一个新名字当主创新。

请实际运行入口，先尝试推翻本次裁决。只有在合法源域、真实同类仪器事件预测和强普通对照下，
发现一个可重复、能通向任务收益的残余缺口，才提出一个有明确输入、内部状态、公式和输出的跨领域主模块。
当前没有通过这个门，因此不安排新世界或闭环批次。唯一最小未启动补数在`analysis/MINIMUM_SUPPLEMENT.md`。
