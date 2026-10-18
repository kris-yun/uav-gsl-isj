# 供 Codex/数据保管方的**仅导出**任务合同（不授权新仿真）

此文件独立存在。本轮未连接或启动 Codex。用户决定是否复制执行。

**目的**：从旧 E2 受体浓度立方体导出最小的 OPEN DISCOVERY 6源×4实现×10时刻×30虚拟受体数据，建立首次有效物理源对响应 K；不能混合 O24 2D hit-map、不能新建气体世界。

1. 找到 XHOC-R0 审计中已有 E2 的 OPEN 源浓度立方体，按 SHA 校验原归档。**仅**考虑已标为 DISCOVERY 的 House01 `1,3-2,4_fast`、House02 `3,5-1_slow`，两个环境各 6×4=24 原始实现；如果角色存疑即停止，不读取封存的 DEV/House03。
2. 保留每个 House 原 E1 的 30 个 source-blind probe、2×2 0.1m footprint、z=0.20m；不得改变探针位置、时间 ID 或源位置。
3. 导出固定的 record IDs 100、150、...550，并使用已有 `TIMEBASE_MAP.csv` 真正的 writer clock 和风索引。**不是**100...550秒，不可以视作 UAV 时序航线。
4. 验证单位。若原立方体值未证明是 ppm，原样导出并标明 `UNQUALIFIED_UNIT`，**禁止伪标 ppm**。需要 GADEN 原抽取算子/参数/标定、源强或每团 mol 量给出明确单位和线性缩放依据。不要用目标真源浓度去拟合 `hit->ppm` 比例。
5. 对每个实际源实现生成一个 `run_id.csv`，恰好 300 行：`save_record_id,probe_id,ppm`（仅当单位确认，否则不要按这个最终合同提交）；`probes.csv` 每 House 30 行：`house,probe_id,x_m,y_m,z_m`；`timebase.csv` 从旧时钟合同精确复制；`manifest.csv` 每物理运行 1 行，其列详见 `e2_open_response_adapter.py`，必须含场景/风、源 xyz、源强物理单位、独立 seed、原始 cube 哈希、算子/时间/探针 SHA、数据文件 SHA。
6. **最少导出量预计 48×300=14,400 个浓度标量**（排除元数据），远小于原始 168 个浓度立方体。可按 Hash manifest 和 CSV 打 ZIP，不能只给汇总 Top1/排名。
7. 如果只有 1 源或只有一个同源实现、不能验证单位、物理时钟、源强、观测算子，标明 `E2_EXPORT_HOLD_*`，保留所有失败，不自动生成新的 144 世界。
8. 不启动 ROS / PMFS / GADEN，不修改 frozen O24，不能 unseal；不要把数据写进 Codex 正在编辑的仓库，另存可追溯只读资产。

可以使用本分支的 `e2_open_response_adapter.py` 在导出包**通过物理资格审计后**复算普通三臂：固定源强高斯似然、未知非负源强 profile 高斯似然、原 E1-type 二值 Brier。它只比较**固定受体 6源分类**，不是 PMFS 全域概率图/机器人飞行收益。任何候选网络 B 必须另与这些普通模型及强低秩基线公平比较。
