# 2026-10-18：寻找 A′ 源—受体物理响应 K 的现成数据资格审计

## 结论

1. **O24 五回合（已由用户提供）**：含 5,335 张二维源候选占格命中响应与 34 次后验更新。具备 O24 数值一致性测试资格，**不具备物理 ppm K**。A2隔离补跑误差 0.5689 m 属 O24 基线恢复，不是新创新收益。
2. **OCB-R2 S2/S2X**：GitHub 的 `OCB_R2_S2X_MATCHED_SOURCE_REPORT.md` 显示 32/32 S2X 运行通过结构审计，和 S2 组合为 8 个非源条件，每条件 2 源×每源 4 个独立实现；1000s 左右、1803 帧/实现。原始归档位于旧本地路径 `C:\GADEN_OCB_R2_ARCHIVE\s2x_matched_source`，并不在本轮提供的 O24 ZIP。报告明确 **未生成浓度响应矩阵**；结构通过不能替代同受体 ppm 算子资格。
3. **E2 历史库**：原 XHOC-R0 源文件说明 168 个 GADEN 浓度立方体（H01 48 / H02 72 / H03 48），每 House 6 个源、每个源—风环境 4 个实现，固定 E1 30 个无源偏置的虚拟受体、z=0.20m、10 个保存记录 ID。旧清单说明 OPEN 72、封存 DEV 48、封存 H03 48。独立物理条件、源、实现多于当前 O24 ZIP，是更值得优先复用的 A′ 物理候选。**只有 OPEN DISCOVERY 可读取科学浓度**；本轮未打开 DEV、H03 的任何浓度，也未拿到原始 E2 浓度文件。
4. **E2 时钟合同已在 E2C-R1 的已有审计中 PASS**：writer record IDs 100...550 对应 `clock_before_s` 约 55.10、85.10、115.10、142.30、167.30、192.30、217.30、242.31、267.31、292.31；风索引 2、9、6、2、7、2、7、2、7、2。为代码级时间重建+后来的独立仪器日志核对，**不是对每一 E2 原始帧直接读出的时间戳**。
5. **E2C 144 次扩充计划不属于已完成数据**：E2C-R1 后来 `HOLD_SOURCE_LOCATION_CONTRACT`，原发布 House 场景配置只含每 House 两种预设源坐标，而 E2 是独立新配置源位置的模拟基准，不是原发布源位置目录的扩充。执行记录仅一次 loader 失败，无新有效迭代文件、无新浓度、零条完成 E2C 仿真。

## 该如何科学使用 E2

- 首先保留旧实验的角色隔离：只从已有 OPEN、 canonical House01 `1,3-2,4_fast` 与 House02 `3,5-1_slow` 两个源—风环境导出。此二者是 E2C 已冻结发现集环境。其他风型是否 OPEN 必须额外核验，不擅自加入。
- 源标签必须作为**候选索引和事后评价用真值**。不能用于选择虚拟受体、针对某个目标屏蔽难源、或用自己的实现构建自己的参考均值。
- 目标与候选源之间匹配场景/强迫/受体/物理时间/观测单位，**不匹配目标随机实现身份**。反事实参考采用每源四个实现中、与目标 replicate 标号不同的三个。不能把真源的测试实现放回候选参考 K。
- 验证已有数据是否真正是 ppm，核验源强的物理单位、GADEN ppm 导出/2x2受体算子 SHA。只有这些确认后，才能宣称在 A′ 连续响应合同下开始第一组真实物理 benchmark。没有源强归一化，不得把经验均值称为单位源强 K。
- 因为 E2 是**固定分布式虚拟受体**，即使源识别效果好也只能表明固定受体源判别，不能直接声称 O24 单无人机移动闭环的定位增益。

## 可复查的已存 GitHub 原始证据（全部为以前工作的报告，未修改）

- [XHOC-R0 E2/多源数据原身份](https://github.com/kris-yun/uav-gsl-isj/blob/research/cross-house-observation-contract-r0-20260929/research/xhoc_r0/XHOC_R0_RESULT_20260929.md)
- [E2C-R1 时钟审计](https://github.com/kris-yun/uav-gsl-isj/blob/research/e2c-common-benchmark-r1-20260929/research/e2c_r1/E2C_R1_TIMEBASE_RESULT_20260929.md)
- [E2C-R1 物理时钟映射表](https://github.com/kris-yun/uav-gsl-isj/blob/research/e2c-common-benchmark-r1-20260929/evidence/e2c_r1/TIMEBASE_MAP.csv)
- [E2C-R1 源位置合同 HOLD](https://github.com/kris-yun/uav-gsl-isj/blob/research/e2c-common-benchmark-r1-20260929/research/e2c_r1/E2C_R1_SOURCE_LOCATION_CONTRACT_AUDIT_20260929.md)
- [S2X 已有 32 条真实 GADEN 结构验收](https://github.com/kris-yun/uav-gsl-isj/blob/research/ocb-r2-r3b-prospective-multisource-20260930/research/ocb_r2/OCB_R2_S2X_MATCHED_SOURCE_REPORT.md)

## 当前不满足的门

`PHYSICAL_K_BYTES_AVAILABLE = NO`：本轮 GitHub 读取到的是元数据和审计，不是 E2 原始浓度数组。

`E2_PPM_UNIT_AND_Q_LINEAGE = UNVERIFIED_CURRENT_TURN`：原审计称 GADEN concentration cubes，不等于已完整验收为对应单位释放率的 ppm 响应。

`A_PRIME_REAL_LOCALIZATION = NOT_RUN`；`NEMO_OR_B_GAIN = NOT_RUN`；`S2_LAKESHORE_TRANSFER = NOT_TESTED`。
