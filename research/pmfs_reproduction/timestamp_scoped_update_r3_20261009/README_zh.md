# PMFS R3 小审核包

先读 `PMFS_TIMESTAMP_R3_REPORT_zh.md`。工程修复PASS；固定范围接口PASS；单次源后验更新HOLD，未运行。

复核：在解压目录执行 `python verify_r3.py`，仅用标准库、离线、只读。它检查完整源文件只改变一行，重算5组真实ROS消费者的方向/位置/时间门，校验20条冻结事件、87张离线图、原始远端文件与包内SHA。

`UPSTREAM_VS_STAMP_PATCH.csv`：5组×2版本消费者结果。

`TF_STAMP_TRACE.csv`：采样与消费时刻TF及返回TF时间。

`R3_SINGLE_UPDATE_HOLD.json`：输入和在线状态最小缺项。

`evidence/real_ros/results/stamp/`：原始CSV、CDR消息、TF和日志；`code/`为原版/时间戳版源码与驱动。CDR是保存的ROS序列化消息，不需要执行未知程序读取本报告。

`evidence/frozen_R1/`：沿用旧20事件/87叶/626风格与87张离线C图；它们不是本轮新原生模拟结果。

源上游与本轮ELF哈希、复用库说明在 `RUN_AND_PARAMETER_LINEAGE.json`。未附ELF、虚拟机、SSH信息、原始气体库。

SHA256SUMS覆盖本包除清单自身以外所有文件；ZIP自身SHA在旁边的 `.sha256.txt`。冻结P0/R2和旧STOP/HOLD保留。本轮到此停止。
