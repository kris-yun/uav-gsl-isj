# B4 官方终态补全审核包

先读`B4_TERMINAL_COMPLETION_DECISION_zh.md`：本轮没有补齐官方终态，保护器误判客户端时间追赶；不是PMFS官方失败。一次替代goal已用完，不执行第三次。

复核：`python verify_b4_terminal.py`（Python、numpy、PyYAML、Pillow）。默认只读、不启动ROS/仿真，不修改文件。两套保护器测试也仅运行合成事件。不要执行原始driver/worker。

`run/`和`runtime/`是本轮真实记录；`input_evidence/`是已审第一次B4的物理输入/源码样本及完整索引；`first_B4_reference/`保存第一次的轨迹、三份后验和索引供比较。当前包不含第一次381张候选图，不声称重新评分它们；第一次完整包SHA见`OLD_B4_FROZEN_LOCAL.json`。

`offline_proposal/`是本次停止后的修正提案，有14项离线测试，但没有原生运行资格。运行前执行版本的12项PASS和本轮集成FAIL全部保留。

原1803气体帧、11风场和34份官方资产在VM运行前后哈希核对通过，完整数据仍保留原VM。轻包只放5帧气体样本及原始/转换wind10。包内验证不能冒充重新读完VM所有原始载荷。

原VM继续开机；本轮Domain78已清理，其它Domain未操作。E3/R7/D0/D1与第一次B4冻结；不包含连接凭据。全部文件SHA256清单在包内（清单自身除外），ZIP哈希另附。
