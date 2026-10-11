# 工作流存档的权威顺序

本文件夹是执行前设计审查、冻结/监督与报告生成脚本的原样存档，不是新的实验入口。实际执行以RK0_NEW/frozen_contract.json及PRE_RUN_CONTRACT_SHA256.txt、RK0_NEW/source/的冻结源码为准。

contract_review_zh.md包含预冻结的设计建议。其建议R salt与摘要截取长度不同于最终合同；实际R规则在任何计算前冻结为PMFS_RK0_NONPHYSICAL_F32_STATE_HASH_v1、摘要前8字节小端mod4，后续未改。设计建议不冒充实际执行参数。

build_delivery_reports.py只派生报告/图，不做experiment，存档内使用原工作目录路径；审核复算请使用包根verify_review_bundle.py或RK0_NEW/verify_rk0_independent.py，不执行producer或重启run_rk0.py。独立的科学decision脚本可以通过显式--package读取RK0_NEW。
