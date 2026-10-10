# B4 单案例审核包

先读`B4_NATIVE_REPRODUCTION_DECISION.md`。**官方最终结果未返回；外部保护起点提前，结果被截断。** 不把`RUNTIME_ERROR`翻译成PMFS官方success=false。

运行只读复核：`python verify_b4.py`（Python、numpy、PyYAML、Pillow）。默认不修改文件，不启动ROS/仿真/训练。`--write-summary`仅供重新生成派生摘要；不要对冻结包写入。C++ Top-5%脚本纯算术，无传播计算；JSON记录同VM std::sort选择，可独立验证选中概率和位置。

四份报告、`B4_RESULT.json`、测量/后验CSV、原始压缩CDR和服务记录、三个完整更新、参数/日志/源码、官方地图和3D占据、原始与转换wind10、五个气体样本，以及所有原始气体帧的时间/SHA索引一起交付。`SHA256_MANIFEST.json`覆盖本文件之外的包内文件（清单自身除外）；ZIP哈希在包外。

轻量包仅包含选定物理原始载荷；现场全部1803帧及11个风场的检查见GATE1/GATE2。完整bank仍在原VM `/home/zyc/pmfs_b4_native_validation_20261009`（`RAW_ASSET_LOCATIONS.json`）。本包验证范围与现场验证范围分开。

运行脚本与shell是血统证据，审核只运行`verify_b4.py`。未包含连接凭据或远程辅助认证文件。原VM继续开机；本轮Domain77进程已清理，其它窗口/Domain未操作。
