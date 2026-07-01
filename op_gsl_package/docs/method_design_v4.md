# OPGSL-BOED 方法设计文档 v4.0 — 统一机制版
# 从"模块堆砌"到"三步缝合"的完整升级

> 版本: v4.0 | 日期: 2026-07-01
> 状态: 专家圆桌讨论后重构

---

## 0. 核心诊断：为什么 v3 是"模块堆砌"

### 症状
v3 有 5 个独立模块（BO+GP、WR-SFE、Bout检测、自适应步长、Lévy飞行），
每个单独测试有效，但组合后：
- GP 推荐 z=2.77，标定显示 z=0.48 最佳（模块间信号冲突）
- 水平搜索收敛到距源 4.5m 的错误位置（模块间信息不通）
- 三阶段状态机是硬编码切换，不是自适应协同

### 根因（油水不容）
```
v3 架构（失败）：
  WR-SFE ──→ field peak ──→ 化学趋向（水平）
  GP     ──→ z_target  ──→ 高度控制（垂直）
  Bout   ──→ hit/miss  ──→ 状态机切换
  ← 三个模块各干各的，没有信息交互 →
```

就像 CV 里把 ResNet 特征和 Transformer 特征直接 Concatenate——
特征在不同流形空间，直接拼接性能血崩。

---

## 1. 三步缝合心法 → OPGSL-BOED

### Step 1: 空间投影层（异源特征映射到同一流形）

**问题**：field estimator 的输出（2D log-field 矩阵）、GP 的输出（1D 后验）、
wind 的输出（方向+速度）在完全不同的特征空间。

**解决方案**：Shared Belief State (SBS)——统一贝叶斯状态表示

```
定义：联合后验 P(s | D_{1:t})，其中 s = (s_x, s_y, s_z)

投影层：
  Field feature:  f_field = WR_SFE.computeField() → (peak_x, peak_y, entropy, gradient)
  Height feature: f_gp    = GP.predict(z_grid)     → (mean(z), var(z), UCB(z))
  Wind feature:   f_wind  = WindEstimator.get()     → (consensus_x, consensus_y, consistency)
  Bout feature:   f_bout  = BoutDetector.get()      → (hit_rate, peak_conc, duration)

  → 1×1 投影（全连接层）：
    h = W_field · f_field + W_gp · f_gp + W_wind · f_wind + W_bout · f_bout + b
    
  这就是"让异源特征能对话"——所有特征被映射到同一个 belief state 空间。
```

**与 BOED 的关系**：
  h 本质上就是后验 P(s | D_{1:t}) 的 sufficient statistics。
  BOED 框架下，下一步决策是：
    ξ* = argmax_ξ I(s; y | ξ, h)  = argmax_ξ H(s|h) - E_y[H(s|y,ξ,h)]

### Step 2: 分布均衡化（动态协同权重）

**问题**：v3 的三阶段状态机是硬编码切换（EXPLORE→CALIBRATE→TRACK），
权重不随场景变化。当 field estimator 不确定性高时应该多探索，
当 GP 置信度高时应该信任高度推荐——但 v3 不会自动调整。

**解决方案**：Attention-based Dynamic Weighting

```
定义注意力权重：
  α_field = softmax(entropy_field / τ)   // field 不确定性高 → 多探索
  α_gp    = softmax(-variance_gp / τ)    // GP 方差低 → 信任高度
  α_wind  = softmax(wind_consistency / τ) // 风向稳定 → 信任上风搜索
  α_bout  = softmax(hit_rate / τ)        // 有气体 → 信任梯度

统一决策：
  action = α_field · explore_policy(h) 
         + α_gp    · height_policy(h)
         + α_wind  · upwind_policy(h)
         + α_bout  · gradient_policy(h)

  这就是"动态协同"——模型自己平衡各模块权重，而不是硬编码状态机。
```

**关键**：τ（温度参数）是缝合处的超参数，需要参数敏感性审计。

### Step 3: 信息流瓶颈（残差连接）

**问题**：v3 的信息流是单向的（观测→模块→决策），没有反馈回路。
Bout 检测的结果没有反馈给 field estimator，
field 的不确定性没有传给高度控制器。

**解决方案**：Residual Information Flow

```
残差连接 1：Bout → Field
  当 bout 检测到高浓度时，给 field estimator 的对应区域增加权重：
    field_weight(x,y) += β_bout * bout_peak_conc * gaussian(pos, bout_pos)
  原始 field 信号通过残差保留：
    field_final = field_raw + field_weight

残差连接 2：Field → GP
  field 的 peak 位置传给 GP，限制 GP 只在源附近收集观测：
    if dist(robot, field_peak) < threshold:
        gp.addObs(z, concentration)
  原始 GP 信号通过残差保留：
    gp_z = gp.getNextZ() * α_gp + calibration_z * (1 - α_gp)

残差连接 3：Wind → Exploration
  风向一致性决定探索策略：
    if wind_consistency > 0.7:
        policy = UPWIND_FOLLOW（稳定风→上风追踪）
    else:
        policy = INFORMATION_GAIN（不稳定风→信息增益探索）
  两种策略的信号通过残差连接：
    action = α_wind * upwind + (1-α_wind) * info_gain
```

---

## 2. 科学问题定义

### 表面问题（v3 的表述，审稿人会拒）
> "如何在源高度未知时自适应选择飞行高度"

### 深层科学问题（v4 的表述，有理论深度）
> "在 3D 浓度场中，如何通过主动选择观测配置 (x,y,z) 来实现
>  源位置 s=(s_x,s_y,s_z) 的快速、可辨识估计，
>  同时处理传感器噪声、风场不确定性和模型失配"

### 理论基础
- **BOED**：每一步决策都是选择最有信息量的观测点
- **Fisher Information**：FIM 的秩决定源位置的可辨识性
- **Regret Bound**：BOED 的累积遗憾 O(√T log T) 保证收敛速率

---

## 3. 论文故事（ISJ 投稿定位）

### Hook
> "现有 3D 气体源定位方法将高度选择和水平搜索视为两个独立问题；
>  我们证明它们在信息论框架下是同一个问题——都是选择最有信息量的观测点，
>  并提出首个基于 Bayesian Optimal Experimental Design 的统一框架。"

### 核心 Insight
> "高度不是控制变量，而是观测配置的一部分。
>  选择在 (x,y,z) 做观测，本质上是在设计一个实验，
>  目标是最大化关于源位置的信息增益。"

### 三个贡献（对齐 ISJ scope）
1. **理论贡献**：首次将 UAV 3D GSL 建模为 BOED 问题
   （定理：EIG 的 regret bound O(√T log T)）
2. **算法贡献**：提出三步缝合的统一框架 SBS-BOED
   （Shared Belief State + Dynamic Weighting + Residual Flow）
3. **系统贡献**：在 VGR 公开数据集上验证
   （3 House × 30 seeds，Wilcoxon + Cliff's delta）

### ISJ 适配
- 定位为 **"3D gas concentration mapping system"**（不是 "GSL algorithm"）
- 贡献在传感器空间采样策略优化（sensor placement in 3D）
- 源定位是 downstream application

---

## 4. 与 3D Klinotaxis (ISJ 2025) 的对比

| 维度 | 3D Klinotaxis | SBS-BOED (ours) |
|------|---------------|-----------------|
| 高度选择 | 9个固定高度，离散选择 | 连续高度，EIG驱动 |
| 理论保证 | 无 | regret bound O(√T log T) |
| 水平+垂直 | 独立处理 | 统一为 argmax EIG |
| 生物启发 | ✅ 昆虫趋化 | ❌ 信息论最优 |
| 不确定性量化 | 无 | GP posterior + field entropy |
| 模块协同 | 硬编码状态机 | 动态注意力权重 |

---

## 5. 消融实验设计（三层证据链）

### 第一层：基础消融（证明模块有效）
| 配置 | Field | GP | Bout | Wind | 说明 |
|------|-------|-----|------|------|------|
| A0 | ✓ | ✗ | ✗ | ✗ | 仅 field（固定z=0.3） |
| A1 | ✓ | ✓ | ✗ | ✗ | + 高度自适应 |
| A2 | ✓ | ✓ | ✓ | ✗ | + bout 检测 |
| A3 | ✓ | ✓ | ✓ | ✓ | 完整方法 |

### 第二层：交互式消融（证明缝合合理）
| 实验 | 操作 | 预期 | 意义 |
|------|------|------|------|
| B1 | 去掉 Field→GP 残差连接 | GP 推荐 z=2.77（漂移） | 证明 Field 对 GP 的校准必要 |
| B2 | 去掉 Bout→Field 反馈 | 源附近搜索效率下降 | 证明 Bout 对 Field 的增强必要 |
| B3 | 去掉 Wind→Exploration 路由 | 风向不稳定时性能暴跌 | 证明风向自适应必要 |
| B4 | 用硬编码权重替代注意力 | 性能下降但不崩溃 | 证明动态协同优于静态 |

### 第三层：参数敏感性审计（证明缝合点是最优解）
| 参数 | 扫描范围 | 预期 | 意义 |
|------|----------|------|------|
| τ (注意力温度) | [0.1, 0.5, 1.0, 2.0, 5.0] | τ=1.0 最优 | 缝合点精密 |
| GP weight α | [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] | α=0.3-0.5 最优 | 动态平衡点 |
| proximity threshold | [1.0, 1.5, 2.0, 2.5, 3.0m] | 2.0m 最优 | 观测过滤点 |
| calibration points | [4, 6, 8, 10] | 6 最优 | 标定点数 |

### 可视化对质（直观绝杀）
- 热力图：缝合前后的 field posterior 对比
- 轨迹图：各配置的 UAV 路径叠加
- 高度曲线：GP 推荐 vs 实际飞行 vs 标定最佳

---

## 6. 审稿人 Top 5 问题及应对

### Q1: "BOED 在 GSL 中的 novelty？BO 已经很常见了。"
**A**: 我们不是用 BO 做参数调优，而是用 BOED 做**观测设计**——
选择在哪个 (x,y,z) 做观测。这在 GSL 领域是首次。
BOED 的 regret bound 提供了理论保证（定理 1）。

### Q2: "如何保证可辨识性？c(x,y,z) 不能唯一确定源位置。"
**A**: 我们不依赖单一观测。通过主动选择不同 (x,y,z) 的观测序列，
Fisher Information Matrix 的秩逐步增加，直到满秩（可辨识）。
Proposition 1 给出了 FIM 满秩的充分条件。

### Q3: "计算复杂度？能实时吗？"
**A**: 1D GP: O(n²), n≤50 → <1ms。
Field posterior: O(G²), G=40×40 → ~5ms。
EIG 近似: O(M·G²), M=100 Monte Carlo → ~50ms。
总计 <60ms/step，满足 1Hz 决策频率。

### Q4: "与 3D Klinotaxis (ISJ 2025) 的 novelty？"
**A**: 3D Klinotaxis 用 9 个固定高度离散选择，无理论保证。
我们用连续 EIG 优化，有 regret bound。
关键差异：我们把高度选择和水平搜索统一为同一个优化问题。

### Q5: "ISJ scope fit？这看起来是 robotics paper。"
**A**: 我们的核心贡献是**传感器空间采样策略优化**——
在 3D 空间中选择最优的传感器放置位置以最大化信息增益。
这是 ISJ 的核心 scope（sensor systems + signal processing）。

---

## 7. 实验方案（450 runs）

### 实验矩阵
- 3 House × 30 seeds × 5 方法 = 450 runs
- 方法：A0, A1, A2, A3(完整), GrGSL
- 指标：定位误差、收敛时间、路径长度、成功率

### 统计检验
- Wilcoxon signed-rank test (paired)
- Cliff's delta (effect size)
- 95% bootstrap CI
- Bonferroni correction

### Stopping Conditions
- 单次 >300s → TIMEOUT
- error >10m → DIVERGED
- 同配置 5 seeds 全 FAIL → 中止

---

## 8. 实施路线图

### Phase 1: 修复已知 Bug（1天）
- [x] BO+GP 高度控制（已修复）
- [ ] upwind_shift 偏移过大
- [ ] 化学趋向梯度方向
- [ ] PMFS 崩溃

### Phase 2: 实现三步缝合（3天）
- [ ] Shared Belief State（统一状态表示）
- [ ] Attention-based Dynamic Weighting
- [ ] Residual Information Flow

### Phase 3: 消融实验（2天）
- [ ] 基础消融 A0-A3
- [ ] 交互式消融 B1-B4
- [ ] 参数敏感性审计

### Phase 4: 论文撰写（3天）
- [ ] Introduction + Related Work
- [ ] Method (BOED + SBS)
- [ ] Experiments + Results
- [ ] Conclusion
