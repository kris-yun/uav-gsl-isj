# PMFS R4 小审核包

结论：CORE_UPDATE_PARITY_PASS，仅限本次受控合成ROS输入、实际捕获的候选树/随机态、单线程。

已执行1次真实核心源更新；84个初始候选、116次候选模拟、104个最终叶。模拟图、最终后验及无插桩对照一致。完整官方导航仍HOLD，物理传播失配仍UNRESOLVED。

先读 PMFS_R4_NATIVE_CAPTURE_REPORT_zh.md，再用 `python verify_capture.py .` 复核。evidence包含输入、raw ROS CDR/TF、测量块、采样点、噪声缓存、全部模拟图、评分、细分树和后验。失败的预检也保留；“89=87自由+2障碍”的解释已撤回。

代码读取与标准库复核无需运行Docker、ROS或仿真。evidence/code中的ROS入口是可审计复现源码，复跑需原Humble环境，不应把它当成本包自动执行动作。

采用原有Ubuntu虚拟机和独立R4目录，未新建VM。完成后不自动进入新实验。
