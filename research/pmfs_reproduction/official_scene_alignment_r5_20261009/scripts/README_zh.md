# 核验入口

`verify_r5.py` 为标准库离线证据核验，不访问网络，不启动 ROS 或模拟。输出中的 HOLD 属于明确限定的资格判决，不是脚本失败。

`runtime_driver.py`、`N1_headless_launch.py` 是此次真实运行代码，仅供审计；包含此次固定的 guest 路径、ROS 域和运行锁。它们依赖已构建的 ROS 环境，**不作为双击即运行的复现实验入口**。

`forward_replay.cpp` 及 `r4_replay_support/` 为固定采样前向回放入口。编译命令保存于 `offline_forward_lineage/FORWARD_BUILD_COMMANDS.json`；依赖 R4 构建对象与 ROS/OpenCV 等库。R4 全部源码及固定对象血统见已发布提交 `06f99582658e17bf5d546d21668c3b31949ace0e` 下 `research/pmfs_reproduction/native_capture_r4_20261009`。标准库脚本可验证包内已经保存的 108 组回放结果，无须重建这些对象。
