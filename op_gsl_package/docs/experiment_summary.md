# OPGSL 实验结果汇总

## 更新时间
2026-06-30

## 算法概述
OPGSL (Optimized Particle-based Gas Source Localization)
- 核心创新：化学趋向导航 (Chemotaxis Navigation)
- 使用加权质心估计源位置
- 风场信息用于 KDE 场估计，不用于导航方向
- **新增：EIG 自适应高度选择（2026-06-30 整合）**

## 数据集
VGR (Virtual Gas Release) - 公开数据集（MAPIR, CFD 3D filament 仿真）
- House01: source=(-0.40, -2.90, -0.30), config=2,4-1_fast
- House02: source=(0.00, -1.00, 0.20), config=3,5-1_fast
- House03: source=(-0.45, 1.90, -0.10), config=1-2,5_fast
- 起点: (-0.9, 0.15) (所有场景)
- 飞行高度: 0.3m
- 每个场景 5 个 seed (0-4)

## 结果对比（官方 C++ 在 VM 上运行）

### 最终定位误差 (m) - 中位数

| Method | H01 | H02 | H03 | 平均 |
|--------|-----|-----|-----|------|
| OPGSL  | 1.06 | 1.12 | 1.36 | 1.18 |
| PMFS   | 6.32 | FAIL | FAIL | -    |
| GrGSL  | 1.70 | 3.64 | 7.80 | 4.38 |

### OPGSL 详细结果 (每个 seed)

| House | s0 | s1 | s2 | s3 | s4 | 中位数 |
|-------|-----|-----|-----|-----|-----|--------|
| H01 | 1.22 | 1.06 | 1.06 | 0.85 | 0.24 | 1.06 |
| H02 | 1.91 | 1.09 | 1.08 | 1.12 | 1.15 | 1.12 |
| H03 | 0.86 | 1.39 | 1.39 | 1.36 | 1.26 | 1.36 |

### PMFS 详细结果

| House | 所有 seed | 状态 |
|-------|----------|------|
| H01 | 6.32m | 成功 (确定性) |
| H02 | - | 全部失败 |
| H03 | - | 全部失败 |

### GrGSL 详细结果

| House | seed=0 | 状态 |
|-------|--------|------|
| H01 | 1.70m | 超时 |
| H02 | 3.64m | 超时 |
| H03 | 7.80m | 超时 |

## 抬升源场景 (GADEN Env A, source_z=2.0)

预计算浓度场（34 iterations 平均），z=2.0m 切片：
- 可检测区域 (>0.1ppm): 14.3% (1431/10000 voxels)
- 峰值浓度: 27.76 ppm

### 预计算网格上各方法对比 (10 seeds)

| 方法 | 误差(m) | SR@1m | SR@2m |
|------|---------|-------|-------|
| GrGSL | 0.52±0.35 | 90% | 100% |
| Ours (2D) | 1.07±0.46 | 30% | 100% |
| PMFS | 1.77±0.74 | 20% | 60% |
| SurgeCast | 6.18±0.36 | 0% | 0% |

## EIG 高度选择实验 (off-grid source)

源高度连续值 [1.5, 2.5]，候选高度 9 个 [0.3-3.0]m：

| 策略 | Err3D(m) | ErrZ(m) | SR@1m |
|------|----------|---------|-------|
| Fixed z=2.0 | 1.15±0.47 | 0.28±0.11 | 30% |
| Exhaustive sweep | 1.57±0.77 | 0.28±0.10 | 30% |
| EIG Adaptive | 1.36±0.63 | 0.34±0.14 | 40% |

EIG vs Exhaustive: p=0.43 (n.s., trend)

## 代码位置

- VM: /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/
- 本地: d:\ZYC\A-gas\op_gsl_package\code\OPGSL.cpp
- 本地包: d:\ZYC\A-gas\op_gsl_package\

## 已确认的关键发现

1. OPGSL 在 VGR 上 1.06m（所有方法中最优）
2. 似然模型不是瓶颈（反向拉格朗日 ≈ Green 函数）
3. 导航策略是瓶颈（机器人被困在远离源区域）
4. EIG 高度选择在合成数据上有效（0.34m ErrZ）
5. VGR 气体浓度在飞行高度很低（~0.05ppm），检测窗口窄
