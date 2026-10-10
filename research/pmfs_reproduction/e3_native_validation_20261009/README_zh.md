# E3唯一样本审核包

先读 E3_NATIVE_REPRODUCTION_DECISION.md 与 E3_PHYSICAL_INPUT_QUALIFICATION.md。

离线复核：`python verify_e3.py`。依赖numpy、PyYAML、Pillow，不需要ROS/虚拟机，不启动仿真或修改证据。原生日志/状态在runtime/，生成与门控在run/，原图/STL/CFD在official_E3/。全部ROS消息与服务CDR在gzip JSONL中，无抽样删减。五帧样本的全帧参考哈希在run/ALL_FRAME_SHA256_AND_TIME.csv；完整1803帧库仍在虚拟机，44.17MB，不重复放入轻量包。

scripts/为此次操作源供审核，依赖未随包分发的私有远端访问配置，不建议执行；没有包含SSH凭据或远端认证助手。verify_e3.py是公开可移植的只读核验入口。

判决：物理合同PASS、原生目标执行PASS、官方success=true、正常对照FAIL、科学机制HOLD、B4 HOLD。退出-11发生于结果之后，单独HOLD，不隐藏。
