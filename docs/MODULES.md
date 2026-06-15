# 模块说明

## 模块总览

本方法在PMFS基础上增加3个创新模块，均借鉴自非机器人/嗅觉领域：

### 模块1: PWC (Plume Wind Correction)
- **领域来源**: 大气污染源反演（环境科学）
- **核心思想**: 利用局部风向估计，将源位置估计向逆风方向偏移
- **物理依据**: 气体羽流从源向下风方向扩散，观测到气体的位置必然在源的下风侧
- **实现**: 当风速>阈值时，沿逆风方向偏移sourceLocation，偏移量与plume_spread成正比
- **参数**: beta=0.5, max_correction=5.0m, min_wind=0.01 m/s

### 模块2: PSDE (Plume Spatial Dispersion Estimator)
- **原名**: MAC (Multi-Altitude Constraint) — 已更名以准确反映实现
- **领域来源**: 大气扩散理论（Pasquill-Gifford模型）
- **核心思想**: 利用气体命中分布的centroid-to-peak距离估计源距离
- **物理依据**: P-G扩散模型中 sigma_z = Cz * x^Dz，水平色散特征可反推源距离
- **实现**: 计算hit centroid到概率峰值的方向和距离，结合P-G系数估计源位置
- **参数**: stability_class=3, max_distance_weight=6.0m, distance_sigma=2.0m

### 模块3: SDR (Source probability map Deconvolution Refinement)
- **领域来源**: 医学CT图像重建（Richardson-Lucy反卷积）
- **核心思想**: 用RL反卷积从gas hit分布中恢复更精确的源位置
- **物理依据**: gas hit分布是源信号经过羽流扩散PSF卷积的结果，反卷积可恢复源
- **实现**: 构造各向异性upwind PSF，对hitMap做RL反卷积，取峰值作为源估计
- **参数**: RL迭代10次, PSF size=7, blob_radius=4.5

## 消融设计

| 条件 | PWC | PSDE | SDR | 说明 |
|------|-----|------|-----|------|
| baseline | OFF | OFF | OFF | 原始PMFS |
| pwc | ON | OFF | OFF | 仅风向校正 |
| mac | OFF | ON | OFF | 仅空间色散估计 |
| pwc_mac | ON | ON | OFF | PWC+PSDE组合 |
| sdr | OFF | OFF | ON | 仅反卷积精化 |
| full | ON | ON | ON | 全部模块 |

## 关键修复（v2）
1. **去除GT泄漏**: SDR不再使用sourcePositionGT比较，无条件应用
2. **统一参数**: 所有条件使用相同的maxSearchTime=300s, wccThreshold=0.001等
3. **命名修正**: MAC更名为PSDE，准确反映实现
4. **SDR可控**: 添加sdr_enabled参数开关
