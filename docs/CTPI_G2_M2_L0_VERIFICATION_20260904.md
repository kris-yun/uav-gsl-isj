# CTPI G2-M2 L0 验证报告 + L1 设计方向

日期：2026-09-04
前置：`CTPI_G2_V1_ARCHITECTURE_AND_INTERFACES_20260904.md`
性质：G2-M2 的 physics-informed 输运预测可行性验证（L0）+ L1 设计。

---

## 1. 两个关键纠正（读源码坐实）

1. **8 member = filament 随机种子，不是 wind**：读 `pf_dei_v3_native_multistream.cpp`，`gaden_initialize_random_engines(seed)`，wind 序列固定 `LoopConfig{loop=true, from=1, to=10}`。bank 只有 1 个 wind 序列。
2. **wind 格式是 legacy double**（3 数组 u,v,w），不是 6 float。正确读取后量级（u mean 0.0036, v mean -0.038）与 vgr CSV 一致——**bank 和 vgr 是同一套 wind 数据**。

## 2. L0 验证结果（可量化）

| 预测方法 | bank 依赖 | 下游定位 rank |
|---|---|---|
| 峰值场（max over time，抹风向） | 需要 bank | 197 |
| **Gaussian plume（稳态 advection-diffusion，保留风向）** | **bank-free** | **95** |

- Gaussian plume 的峰值 cell 定位真源 0.30m（上游观测充分时）。
- 下游观测下 rank 197→95（**改善一倍**），证明 physics-informed bank-free 输运预测方向可行。
- 11 个 wind 里 10 个朝 +y（v≈+0.05），1 个朝 -y（wind_iteration_0），解释了观测 gas 在源上方。

## 3. 为什么 rank 95 非 1（两个根本限制）

1. **Gaussian plume 是稳态近似**：忽略时变风向 + filament 随机性 + 3D 效应。
2. **只有下游观测时源定位病态**：多个上游源产生相同下游羽流（信息论限制）。

参考：bank 的"多时刻瞬时场"（时间对齐）下游 rank=36（更好，但需要 bank + 时间对齐）。

## 4. L1 设计方向（bank-free 精确时变输运）

**目标**：`∂C/∂t + u(x,t)·∇C = D∇²C + S` 的时变数值解，从 online wind 推进浓度场（bank-free）。

- **方法**：semi-Lagrangian advection + 扩散，或 Gaussian puff 叠加（Lagrangian 视角，贴近 GADEN filament）。
- **输入**：online wind u(x,t)（bank-free，来自实时观测）、source hypothesis、geometry。
- **验证**：offline 用 bank 的 11 wind + source 推进浓度场，对比 bank 实测；目标下游 rank 从 95 逼近 36 或更好。
- **bank-free 部署**：held-out House 上只用 online wind + geometry，不查该 House bank。

## 5. 关键结论

M2 的 physics-informed bank-free 输运预测方向**已验证可行**（L0 Gaussian plume，197→95，完全 bank-free）。L1（精确时变输运）是进一步逼近 rank=1 的路径，但最终精度上限仍由 M3 观测覆盖决定。

## 6. 脚本
- `_tmp_m2_plume.py`：Gaussian plume 峰值定位（0.3m）。
- `_tmp_m2_downstream.py`：峰值场 vs 平均 plume 下游（197 vs 191，平均 wind 方向错）。
- `_tmp_m2_plume_v2.py`：峰值场 vs 时变/平均 plume 下游（197 vs 95/94，正确 legacy wind）。
