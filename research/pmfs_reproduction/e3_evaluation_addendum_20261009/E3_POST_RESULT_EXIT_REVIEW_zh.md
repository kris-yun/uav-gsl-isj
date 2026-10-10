# E3 结果后 -11 只读审查

**结果完整性PASS；故障出现于结果返回后的关闭阶段。具体崩溃根因及修复仍HOLD。**

| 原始日志行 | 事件 |
| --- | --- |
| 3149 | `RESULT IS: Success=1`，官方误差已记录 |
| 3152–3154 | 驱动结束目标后发SIGINT；launch显示“user interrupted”，这是驱动的关闭信号 |
| 3192 | `DONE, CLOSING` |
| 3194、3196、3198 | rcl订阅、rmw服务datareader删除报错 |
| 3199 | GSL子进程退出-11 |

第一条订阅销毁错误在成功日志后约1.196墙钟秒。墙钟日志与模拟ROS时钟分开解释。`runtime_driver.py:137` 先读取action返回状态和success，再于141行进入`stop_all()`；`PMFS_utils.cpp:60–83` 先写入并关闭结果文件。两次更新都有COMPLETE标记，最终后验与候选评分完整复算。父launch退出0不能替代子进程-11的异常记录。

原包1183项哈希及原verifier全部通过；虚拟机中结果JSON、最终后验、结果CSV、launch日志与本地冻结副本哈希一致。GSL ELF哈希与运行前一致。因此没有发现退出异常损坏已交付定位结果的证据。

现有VM只读检查未观察到可读取进程中的domain76残留，全部18个已知E3/清理PID已消失。三个同用户进程环境不可读取，名称为sd-pam、vmtoolsd、sshd；因此不把进程检查表述为对所有受限进程的绝对证明。原运行清理记录也保存了remaining_pids=[]。没有启动或停止其他窗口的任务。

系统core_pattern指向Apport，未安装coredumpctl；只检查E3目录、runtime、/var/lib/systemd/coredump和/var/crash，未找到对应core/crash。缺少堆栈，不能断言是Fast DDS内部、重复shutdown、对象生命周期或某个具体释放顺序导致SIGSEGV，也不能证明修复后不再发生。

实际结论：故障阶段可限定为结果后SIGINT关闭，当前未见持续占用或结果损坏阻碍；独立运行是否会再次崩溃尚未测试。后续获准运行时应在启动前确认域为空、结果完整，再把子进程退出状态单独验收。本轮不修改shutdown路径，不做新关闭测试，不重跑E3；B4运行继续HOLD待批准。
