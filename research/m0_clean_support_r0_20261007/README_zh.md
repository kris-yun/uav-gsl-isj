# M0 R0 设计审查入口

本包 **只完成静态设计与冻结，实际 M0 仿真为 0**。旧 `W0C_STAGE0_NO_CLEAN_BASE_HOLD` 保留。40 行 runlist 全部禁止自动 launch。先读 `M0_SCIENTIFIC_CONTRACT.md`，再核查五份领域/风/源/路线/干预 JSON 和 `M0_RESOURCE_ESTIMATE.md`。

八份必需交付：

1. `M0_SCIENTIFIC_CONTRACT.md`
2. `M0_DOMAIN_ROI_GUARD_CONTRACT.json`
3. `M0_BASE_WIND_CONTRACT.json`
4. `M0_SOURCE_CONTRACT.json`
5. `M0_UAV_ROUTE_CONTRACT.json`
6. `M0_PERTURBATION_CONTRACT.json`
7. `M0_RUNLIST_PREVIEW.csv`
8. `M0_RESOURCE_ESTIMATE.md`

补充文件固定 posterior estimand/LORO/BMA、machine PASS/HOLD/STOP gate、字段数学、路线51点、独立静态复核及 parent/native provenance。`provenance/` 包含未经修改的旧 W0C evidence archive，便于独立审查原 HOLD，不把旧 baseline 当成 M0结果。

## 此版静态设计得到的结果

- Simulation 60×40×24 m；ROI 20×16×8 m；六面真正 outlet，ROI最小净 guard 6.75 m。两源同高 5 m，距真正 outlet最小10.75 m。
- Pair A 在全 Free-domain 和 ROI 上的 vector RMSE均完全匹配；Pair B最大不匹配约2.86e−10 m/s，两体积都满足冻结的1e−7绝对/1e−4相对门。
- 解析 wind连续、无散度；native float32 divergence数值余量低于门。B_shear局部任务高度 shear只剩约0.174%，B_speed保留100%。没有 wind/occupancy文件被生成。
- Source-blind route由ROI几何决定；90 m/100 s，转角停留且速度为零，有界加速度。不是已经通过真实飞控的路线。
- 独立 full-potential导数和 norm、几何、timeline、runlist、provenance、decision safety检查通过。合成 gate 案例仅验证判定程序，不是实验。

静态复核发现并在冻结前修正了六面源clearance的计算：最小值在上方，是10.75 m。所有阈值都在 M0观测前确定。

## 尚不能确认的门

Native parser/readback与实际 input/output hash、随机羽流containment、循环Gaussian CRN assignment、A on/off真正mass overlap、source-blind route是否有足够源信息、两种likelihood下的posterior损伤和实测runtime/RSS均需未来执行验证。因此此包只能给 `M0_R0_DESIGN_FROZEN`；不能写 `M0_PASS`、湖岸 benchmark 或 `PRIMARY_GO`。

尤其注意：真实 query始终来自U0，错误 wind只替换候选预测字典；训练模板排除query seed的两个候选源。BMA排除oracle风，只是前人多模型比较，不是新颖性主张。

Native float32 fingerprints绑定此版数学实现和bump evaluation顺序。B_speed gain在量化阶梯附近，把 `exp(1−1/(1−q²))` 随意改成代数等价表达式也可能改变少数float32值；未来应使用本冻结 `static_design_math.py` 生成字节一致的field并做native readback。存在数值/format差异时停止preflight审查，不能悄悄改gain或预期hash。

## 离线复核与保存

`python -B verify_static_design.py` 只做静态代数和合同检查，不启动ROS。冻结后只比较原复核记录，不覆盖它。`python -B freeze_design.py --verify` 检查全部manifest/hash。`build_design.py` 为冻结前document builder；遇到freeze文件拒绝覆盖，没有模拟或launcher依赖。

`M0_R0_FREEZE.json` 和 `M0_R0_FILES_SHA256.csv` 封存字节。ZIP包含同样的portable设计目录，archive成员逐项CRC/hash验证。新增git提交在独立 `codex/m0-clean-support-design-20261007`，parent为handoff head `4e7e1ce16f7c6db3c68214c984337375c8d09e26`。

审查建议优先看：guard是否充足、field误差是否真匹配、route信号门可能造成HOLD、二候选/单context结论边界、以及8条baseline之后的32条是否仍能满足3 h/5 GiB预算。任何未来资格失败都先HOLD，不是机制已被推翻；有效40条的scientific STOP才允许停止这条冻结路线。完成设计即停止，等待审查。
