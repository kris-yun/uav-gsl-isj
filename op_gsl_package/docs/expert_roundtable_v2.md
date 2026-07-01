# 专家圆桌讨论纪要 — OPGSL 方法升级
> 日期: 2026-07-01
> 参与: Prof. Lakshmi (理论), Reviewer Zhang (审稿), Dr. Rivera (代码)

---

## 一、核心诊断

### 1. 水平搜索 Bug（Dr. Rivera 实验验证）
- **症状**: 收敛到 (1.3, 1.07)，源在 (-0.4, -2.9)
- **诊断**: field peak 在 (0.0~0.5, 1.0)，偏差 4m
- **upwind_shift 实际值**: 0.96m（非 6-8m），不是根因
- **真正根因**: WR-SFE 在极低风速（0.026 m/s）下无法正确估计源位置
- **风速问题**: avg_windSpeed=0.026 m/s，几乎无风，kernel 偏移无效

### 2. 方法理论缺陷（Prof. Lakshmi）
- **核心问题**: 观测模型不可辨识——c(z) 不能唯一确定源高度 z_s
- **GP 建模错误**: GP 拟合了混合水平位置效应的虚假关系
- **正确框架**: BOED (Bayesian Optimal Experimental Design)
  - 所有决策统一为 argmax EIG
  - 高度选择和水平搜索是同一个优化问题

### 3. ISJ 投稿问题（Reviewer Zhang）
- **当前状态**: good engineering, not good science
- **缺失**: 零定理、零证明
- **BO+GP 不够新**: BO 在机器人领域已泛滥
- **建议**: 重新定位为 "3D gas mapping" 而非 "GSL"

---

## 二、缝合理论的启示

### 失败原因
90% 的失败是因为简单叠加模块，而不是模块本身不行。
当前 OPGSL 就是这个问题——5 个独立模块各干各的。

### 三步缝合心法
1. **空间投影层**: 异源特征映射到同一流形（Shared Belief State）
2. **分布均衡化**: 注意力权重动态平衡（替代硬编码状态机）
3. **信息流瓶颈**: 残差连接让信号双向流动

### 三层消融证据链
1. **基础消融**: 证明各模块有效
2. **交互式消融**: 证明缝合合理（去掉残差连接性能暴跌）
3. **参数敏感性审计**: 证明缝合点是最优解

---

## 三、升级方案：SBS-BOED

### 科学问题
> "在 3D 浓度场中，如何通过主动选择观测配置 (x,y,z) 来实现
>  源位置 s=(s_x,s_y,s_z) 的快速、可辨识估计"

### 论文故事
> "现有方法将高度选择和水平搜索视为两个独立问题；
>  我们证明它们在信息论框架下是同一个问题——都是选择最有信息量的观测点"

### ISJ 定位
- 贡献 1: 首次将 3D GSL 建模为 BOED（理论）
- 贡献 2: SBS-BOED 统一框架（算法）
- 贡献 3: VGR 数据集验证（实验）

---

## 四、下一步行动

### P0: 修复 field estimator
- WR-SFE 在低风速下失效是根本问题
- 需要更鲁棒的源估计方法

### P1: 实现 SBS-BOED 框架
- Shared Belief State
- Attention-based Dynamic Weighting
- Residual Information Flow

### P2: 消融实验（三层证据链）
- 5 配置 × 3 House × 30 seeds = 450 runs
- Wilcoxon + Cliff's delta + Bonferroni
