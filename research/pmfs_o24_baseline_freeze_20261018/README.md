# PMFS-O24阶段0冻结包

先读`阶段0裁决_zh.md`。O24源码/预期参数已冻结；尚未编译O24ROS程序、尚无O24实际成绩。P24历史不能当O24成绩。用户合同要求另行批准才能真实运行。

本轮仅Windows本机C++和文件读取；没有连接VM、启动ROS/CFD/AIMMD、气体世界或其他会话。完整RNG状态/seed预锁尚未满足，上游随机源码未改。

校验：`python verify_manifest.py`。

Linux纯C++离线复算（不需要ROS）：

```sh
g++ -std=c++20 -O2 -Idependencies/DDA/include host_cpp_core_check.cpp -o core_check
./core_check CPP_REPLAY_INPUT.bin
```

上面只重算7组/1120张已保存P24候选响应，没有生成新气体或新路径，不是O24闭环。程序同时检验原生公式、归一化、矩形方差修复与旧P24响应一致性。Top5%的并列排序可随MSVC/libstdc++略变，见验证说明。

`upstream_readonly`是185份已校验所选作者文件；`o24_port_gmrf_source`是新的源码候选，含线性Omega而无P24公式补丁。`PHASE1_QUALIFICATION_PLAN.json`仅为待批准草案，不含自动运行器；模板路径为NOT_BUILT。
