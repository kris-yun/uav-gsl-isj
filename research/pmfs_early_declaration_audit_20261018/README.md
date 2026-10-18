# PMFS 提前错误声明审计

先读 `核查结论_zh.md`，结果为性能复现HOLD，AIMMD暂停。

保存四次真实ROS闭环、1,120次实际前向候选图、28组固定历史公式控制、原生C++读出、时钟与B2地图独立核验。所有负结果均保留。

仅校验：`python reproduce.py --verify-only`

离线复算：`python reproduce.py --out /tmp/pmfs_early_audit_replay_01`

离线复算需要Python+NumPy与Linux g++/C++20，自动在新输出目录解开所附旧基线；不会启动ROS、气体世界或AIMMD。输入文件必须逐字节匹配SHA；五个重算表须在双精度容差1e-12内一致，允许跨平台BLAS末位浮点差异。原始完整ROS复跑仍需要本机已有世界与安装，包中没有所有世界帧，也不把这些帧当算法免费参考库。

`FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv`是权威Top5/方差读出；NumPy控制表另留用于评分/概率核查。
