# PMFS-O24-PORT-GMRF：完整ROS与四回合资格交付

先读[中文验收报告](科学验收与四回合结果_zh.md)，再读FINAL_QUALIFICATION_GATE.json。实际运行A2/B2各两次已完成；本包不授权继续运行。

构建、参数及RNG记录测试已通过，四回合实际完成；**最终域隔离审计HOLD**：A2第二次同域存在10月15日历史导航管理进程，无法排除干预。见DOMAIN_ISOLATION_AUDIT.json。四回合全部保留，不能称四回合干净资格PASS，正式论文性能复现也仍HOLD。

原始描述统计：A2平均误差0.708762m、墙钟147.7965s（包含资格HOLD的R02，不能当合格性能均值）；B2为2.043320m、87.7884s。不能用离线数学重放通过来解除运行混杂。

- `cases/`：四回合原始记录及实际参数；不止汇总表。
- `source_runtime/`、`patches/`、`binaries/`：实际源码、相对阶段0的记录补丁、实际ROS ELF。
- `build_logs/`、`build_provenance/`：命令、退出码、CMake配置和实际编译命令。
- `analysis/`：28次源更新、4345个候选响应的复算、随机流重放、成本、时钟和风检查。
- `world_provenance/`：已有A2/B2世界身份与逐帧SHA；原始世界帧未复制。
- `baseline_stage0.zip`：此前原样上游、兼容补丁、合同和预检证据，作为版本链保留。
- `reproduce_offline.py`：在包目录内只执行离线SHA、评分/后验、原生C++读出和RNG流重放。Linux+C++20+Python3/NumPy；不需ROS或气体世界。

离线复算建议在新解压副本中执行：

```sh
python3 reproduce_offline.py
```

`prepare.py`、`build_guest.py`、`run_guest.py`、`postcheck_guest.py`等为实际本机历史执行脚本，包含本机路径及状态保护。不要把它们当作离线入口直接运行；尤其run_guest.py会发出ROS目标，当前本轮已经结束。

`MANIFEST_SHA256.json`覆盖原始payload。离线入口先核验原始文件，再生成自己的QA输出；重算后文件字节可能因打印格式/平台不同而变化，应使用OFFLINE_REPRODUCTION_QA.json的数值判定。原始归档保持不变。
