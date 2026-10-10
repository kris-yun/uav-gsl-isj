# 保护器测试与运行版本血统

| 版本/检查 | 判决 | GSL次数 | 解释 |
|---|---|---:|---|
| 执行政策：runtime_guard_policy.py | 原12合成测试PASS | 0（测试） | 未覆盖缓存积压 |
| 同政策：本轮替代goal | 集成FAIL | 1 | 误报forward jump并取消 |
| 同政策：实际首事件回归 | FAIL（根因精确复现） | 0 | DRAIN决定与保存日志一致 |
| offline_proposal/政策 | 14测试PASS_OFFLINE_PROPOSAL_ONLY | 0 | 未部署；需要可信发布者异常输入 |

根目录`test_runtime_guard.py`保留运行前12测试，`GUARD_OFFLINE_TEST_RESULTS.json`不被14测试覆盖。`run/`保存VM真正使用的政策与driver。`offline_proposal/`清楚标记事后提案，不能把其PASS用来替换本轮FAIL。

只读运行：`python test_runtime_guard.py`、`python offline_proposal/test_proposed_guard.py`、`python verify_b4_terminal.py`。这些命令不导入ROS、不启动GSL。代码中的runtime_driver/worker是血统证据，不应执行；提案runtime_driver仍引用已冻结且具有RUN_STARTED标记的路径，不具备新的运行授权。

官方300模拟秒预算及1.5方差门不变；外部宽限只是等待结果/安全退出，不改变官方预算。新旧源码补丁、文件哈希、真实进程结果均打包。
