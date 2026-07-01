# OPGSL 3D 自适应高度方法设计文档

> 版本: v2.0 | 日期: 2026-06-30
> 设计原则: 以审稿人视角重新设计，解决全部 7 条批评

---

## 1. 问题定义

**输入**: UAV 搭载单点气体传感器 + 风速仪，在未知 3D 室内环境中定位未知高度的气体源。
**输出**: 源的 3D 位置估计 (x̂, ŷ, ẑ)。
**约束**: 源高度未知，不能使用真值导航，所有参数通用默认。

### 1.1 与现有方法的区别

| 方法 | 高度假设 | 高度策略 | 理论基础 |
|------|---------|---------|---------|
| PMFS | 已知（内部仿真） | 固定 | 羽流模型匹配 |
| GrGSL | 忽略 | 固定 | 梯度跟随 |
| SurgeCast | 忽略 | 固定 | 气味/风向状态机 |
| **OPGSL (本文)** | **未知** | **自适应** | **ESC + Lévy + 显著层** |

---

## 2. 方法架构

### 2.1 总体框架

```
┌─────────────────────────────────────────────────────┐
│                    OPGSL 3D 自适应                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐    ┌──────────────┐               │
│  │ 水平导航模块  │    │ 垂直自适应模块 │               │
│  │              │    │              │               │
│  │ 无 hit:      │    │ Phase 0:     │               │
│  │  Lévy 探索   │    │  Lévy 高度   │               │
│  │ 有 hit:      │    │  探索        │               │
│  │  化学趋向    │    │              │               │
│  │  (upwind +   │←──→│ Phase 1:     │               │
│  │   crosswind) │    │  显著层扫描   │               │
│  │              │    │              │               │
│  └──────────────┘    │ Phase 2:     │               │
│                      │  ESC 梯度    │               │
│  ┌──────────────┐    │  跟踪        │               │
│  │ 后验估计模块  │    │              │               │
│  │              │    └──────────────┘               │
│  │ KDE 场估计   │                                   │
│  │ 带时间衰减   │    ┌──────────────┐               │
│  │ 加权质心     │    │ 基线对照模块  │               │
│  │              │    │ Fixed-z      │               │
│  └──────────────┘    │ MaxConc-z    │               │
│                      │ Sweep-z      │               │
│                      └──────────────┘               │
└─────────────────────────────────────────────────────┘
```

### 2.2 三阶段状态机

```
Phase 0: EXPLORE (无气体检测)
  ├── 水平: Lévy 飞行探索 (μ=2)
  ├── 垂直: Lévy 高度采样 (μ=2)
  └── 转换: 首次检测到 gas > threshold → Phase 1

Phase 1: CALIBRATE (首次检测到气体)
  ├── 水平: 停留在当前位置附近
  ├── 垂直: 显著层递归二分扫描
  └── 转换: 扫描完成 → Phase 2

Phase 2: TRACK (ESC 梯度跟踪)
  ├── 水平: 化学趋向导航 (upwind surge + crosswind cast)
  ├── 垂直: ESC 连续梯度跟踪
  └── 转化: 连续 N 步无 hit → 回到 Phase 0
```

---

## 3. 垂直自适应模块（核心创新）

### 3.1 Phase 0: Lévy 高度探索

**来源**: Stromboli et al. 2026, "Intermittent Cauchy Walks Enable Optimal 3D Search"
**理论**: μ=2 是 3D 稀疏目标搜索的最优步长分布（数学证明）。

**公式**:
```
步长分布: P(step > L) ~ L^(-μ),  μ = 2
逆CDF采样: l = l_min * (1 - u*(1 - (l_min/l_max)^(μ-1)))^(-1/(μ-1))
其中 u ~ Uniform(0,1), l_min = 0.3m, l_max = 3.0m
```

**实现**:
```cpp
float levyHeight(float z_current, float z_min, float z_max, std::mt19937& rng) {
    float u = std::uniform_real_distribution<float>(0, 1)(rng);
    float beta = 2.0f;
    float l_min = 0.3f, l_max = z_max - z_min;
    float exponent = 1.0f / (beta - 1.0f);
    float step = l_min * std::pow(1.0f - u * (1.0f - std::pow(l_min/l_max, beta-1.0f)), -exponent);
    // 随机方向: 上或下
    float sign = std::uniform_real_distribution<float>(0,1)(rng) > 0.5f ? 1.0f : -1.0f;
    float z_new = z_current + sign * step;
    return std::clamp(z_new, z_min, z_max);
}
```

**为什么比固定菜单好**:
- 连续高度空间，不是离散选择
- 大部分步在附近（利用），偶尔大幅跳跃（探索）
- 无标度：同时覆盖所有高度尺度
- 数学最优性保证

### 3.2 Phase 1: 显著层递归二分扫描

**来源**: WMO Manual No.306（探空仪显著层选择，60 年全球实战）
**目的**: 用最少的垂直采样点，捕获浓度剖面的关键特征。

**算法**:
```
function SignificantLayers(z_lo, z_hi, c_lo, c_hi, threshold):
    // z_lo, z_hi: 区间端点
    // c_lo, c_hi: 端点浓度
    // threshold: 显著性阈值

    z_mid = (z_lo + z_hi) / 2
    c_mid = measure(z_mid)  // 飞到 z_mid 测量浓度

    // 线性插值
    c_linear = c_lo + (c_hi - c_lo) * (z_mid - z_lo) / (z_hi - z_lo)

    // 偏差
    deviation = |c_mid - c_linear|

    if deviation > threshold AND (z_hi - z_lo) > min_resolution:
        // 递归两侧
        layers_left = SignificantLayers(z_lo, z_mid, c_lo, c_mid, threshold)
        layers_right = SignificantLayers(z_mid, z_hi, c_mid, c_hi, threshold)
        return layers_left + {z_mid, c_mid} + layers_right
    else:
        return {}  // 该区间线性即可
```

**关键性质**:
- 保特征：在浓度梯度大的高度层自动加密采样
- 多分辨率：平坦区域粗采，变化区域细采
- 确定性：无随机性，可复现
- 自适应：采样点数取决于剖面复杂度

**典型场景**:
- VGR House01: 源在 z=-0.3m，飞行高度 0.3m → 浓度随高度递减
- 显著层在 z=0.3-1.0m 范围（浓度变化最大的区域）
- 扫描成本：~5-8 次垂直移动

**输出**: 最佳高度估计 z_best（浓度最高的显著层）+ 浓度剖面数据

### 3.3 Phase 2: ESC 连续梯度跟踪

**来源**: Krstic et al. 2024, "Unbiased Extremum Seeking with Prescribed-Time Convergence"
**理论**: 无模型梯度估计，有收敛性证明。

**核心机制**:
```
扰动: z(t) = ẑ(t) + a(t) · sin(ωt)
高通滤波: η(t) = α_h · (η(t-1) + y(t) - y(t-1))   // 去除直流偏移
解调: G(t) = η(t) · sin(ωt) · (2/a(t))              // 提取梯度信息
低通滤波: Ĝ(t) = α_l · Ĝ(t-1) + (1-α_l) · G(t)     // 平滑
更新: ẑ(t+1) = ẑ(t) + K · Ĝ(t)                      // 梯度上升
衰减: a(t+1) = a(t) · (1 - λ)                        // 振幅衰减
```

**关键性质**:
1. **无偏估计**: E[f(θ + a·sin(ωt)) · sin(ωt)] = (a/2) · f'(θ)
2. **无稳态振荡**: 振幅衰减 + 解调增益 → 收敛后振荡消失
3. **收敛时间可控**: 由 λ 设定（设计者选择）
4. **不需要前向模型**: 直接用传感器测量，不需要模拟期望信息增益

**参数设计**:
```
ω = 0.5 rad/s     // 扰动频率（~0.08 Hz，每步约 12 秒一个周期）
a₀ = 0.8m         // 初始振幅（足够大以检测梯度）
λ = 0.02          // 衰减率（~50 步后振幅降至 0.3m）
K = 0.3           // 更新增益（保守，避免过冲）
α_h = 0.3         // 高通滤波系数
α_l = 0.7         // 低通滤波系数
```

**为什么解决审稿人批评**:
- 批评 #1（固定菜单）: 连续高度，不是离散选择 ✓
- 批评 #2（不是真 EIG）: ESC 是真正的梯度跟踪，不需要前向模拟 ✓
- 批评 #3（高斯衰减）: 不假设任何衰减模型，用实测梯度 ✓
- 批评 #4（锁死问题）: ESC 振幅自然衰减，不会锁死在旧估计 ✓

### 3.4 高度后验带时间衰减

**问题**: 原方法后验只累积不衰减，导致早期观测锁死后验。

**解决**: 指数衰减加权
```
w(t_i) = exp(-γ · (t_now - t_i))
其中 γ = 0.01（衰减率，~100 步后权重降至 37%）
```

**后验更新**:
```
log P(z_k | D_{1:t}) += log P(y_t | z_k)     // 标准贝叶斯更新
log P(z_k | D_{1:t}) -= γ · Δt                // 时间衰减
归一化: P(z_k) = exp(log P(z_k)) / Σ exp(log P(z_j))
```

### 3.5 垂直-水平联合规划

**问题**: 原方法高度选择与水平路径规划解耦。

**解决**: 高度变化触发水平重定位
```
if |z_new - z_old| > threshold:
    // 高度变化大时，在新高度重新评估水平位置
    // 利用新高度的浓度信息更新水平后验
    trigger_horizontal_replan = true
```

---

## 4. 基线对照模块（审稿人批评 #5）

### 4.1 Fixed-z 基线
- 固定在默认飞行高度 z=0.3m
- 只做 2D 水平定位
- 与现有 PMFS/GrGSL/SurgeCast 对比

### 4.2 MaxConc-z 基线（审稿人要求的平凡基线）
- 记录所有测量过的高度-浓度对
- 选择历史最高浓度对应的高度
- 带滑动窗口（最近 N 步），避免早期噪声

```cpp
float maxConcAltitude(const std::deque<std::pair<float,float>>& z_conc_history,
                      int window_size) {
    float best_z = 0.3f, best_conc = 0.0f;
    int start = std::max(0, (int)z_conc_history.size() - window_size);
    for (int i = start; i < z_conc_history.size(); i++) {
        if (z_conc_history[i].second > best_conc) {
            best_conc = z_conc_history[i].second;
            best_z = z_conc_history[i].first;
        }
    }
    return best_z;
}
```

### 4.3 Sweep-z 基线
- 周期性全高度扫描（每 20 步做一次 z sweep）
- 选择最高浓度高度
- 成本高但信息完整

---

## 5. 完整算法流程

```
Algorithm OPGSL-3D:
  Input: start_pos, z_min=0.3, z_max=3.0, threshold=0.1ppm
  Output: source_estimate (x, y, z)

  Initialize:
    z_current = 0.3m  // 默认飞行高度
    phase = EXPLORE
    esc_state = ESC_init(z_current)
    z_conc_history = []
    altitude_posterior = uniform(z_min, z_max)

  Loop until convergence:
    // 1. 设置飞行高度
    if phase == EXPLORE:
      z_target = levyHeight(z_current, z_min, z_max)
    elif phase == CALIBRATE:
      z_target = nextCalibrationHeight()  // 显著层扫描
    elif phase == TRACK:
      z_target = esc_state.get_z()  // ESC 输出

    // 2. 执行水平导航
    if phase == EXPLORE:
      (x_target, y_target) = levyExploration(cx, cy)
    else:
      (x_target, y_target) = chemotaxisNavigation(cx, cy)

    // 3. 移动到目标位置
    navigateTo(x_target, y_target, z_target)

    // 4. 测量
    concentration = measureGas()
    wind = measureWind()
    z_conc_history.push_back({z_target, concentration})

    // 5. 更新后验
    updateFieldEstimator(concentration, x, y, wind)
    updateAltitudePosterior(z_target, concentration, altitude_posterior)

    // 6. 阶段转换
    if phase == EXPLORE AND concentration > threshold:
      phase = CALIBRATE
      calibrateStartStep = step_count
    elif phase == CALIBRATE AND calibrationComplete():
      phase = TRACK
      esc_state = ESC_init(bestCalibrationHeight())
    elif phase == TRACK AND consecutive_misses > N_miss_threshold:
      phase = EXPLORE  // 丢失信号，重新探索

    // 7. 更新 ESC
    if phase == TRACK:
      esc_state.update(concentration)

    // 8. 更新 MaxConc-z 基线
    max_conc_z = maxConcAltitude(z_conc_history, window=20)

  return source_estimate
```

---

## 6. 参数表（全部通用默认，不 per-scenario 手调）

| 参数 | 值 | 来源 | 敏感性 |
|------|-----|------|--------|
| z_min | 0.3m | VGR 最低安全高度 | 低 |
| z_max | 3.0m | VGR 房屋高度限制 | 低 |
| Lévy μ | 2.0 | 3D 最优理论证明 | 无 |
| Lévy l_min | 0.3m | 最小有意义高度变化 | 低 |
| Lévy l_max | 3.0m | z_max - z_min | 低 |
| ESC ω | 0.5 rad/s | ~0.08 Hz，每步约 12s | 中 |
| ESC a₀ | 0.8m | 足够检测梯度 | 中 |
| ESC λ | 0.02 | ~50 步收敛 | 中 |
| ESC K | 0.3 | 保守增益 | 中 |
| ESC α_h | 0.3 | 高通滤波 | 低 |
| ESC α_l | 0.7 | 低通滤波 | 低 |
| 显著层阈值 | 0.02 ppm | 远低于检测阈值 | 低 |
| 显著层最小分辨率 | 0.3m | 最小高度差 | 低 |
| 后验衰减率 γ | 0.01 | ~100 步半衰期 | 中 |
| MaxConc 窗口 | 20 步 | 滑动窗口大小 | 低 |
| Phase 转换阈值 | 0.1 ppm | 气体检测阈值 | 低 |
| 连续 miss 阈值 | 10 步 | 回到探索的耐心 | 中 |

---

## 7. 审稿人可能的质疑及回应

### Q1: "ESC 假设浓度场在高度方向是单峰的，如果多峰怎么办？"
**回应**: ESC 收敛到局部最优。配合 Lévy 跳跃（Phase 0→2 转换），当 ESC 丢失信号时回到探索阶段，可以逃逸局部最优。此外，显著层扫描（Phase 1）提供全局视图，帮助 ESC 初始化在正确的峰附近。

### Q2: "Lévy 飞行是随机的，没有利用已收集的信息。"
**回应**: Lévy 只用于 Phase 0（无 hit 时）。一旦检测到气体，切换到 ESC（有信息利用）。这是 exploration-exploitation 的标准权衡，Lévy 在数学上是 3D 稀疏搜索的最优策略。

### Q3: "显著层扫描需要额外的飞行时间，成本是多少？"
**回应**: 典型扫描需要 5-8 次垂直移动（~40-60 秒）。相比 200 步总预算（~1600 秒），成本约 3-4%。但提供了关键的高度先验，使 ESC 初始化在正确区域，大幅减少后续搜索时间。

### Q4: "ESC 的参数（ω, a₀, λ, K）需要 per-scenario 调整吗？"
**回应**: 不需要。ESC 的收敛性不依赖于被跟踪函数的具体形状（Krstic 2024 证明）。参数设计为鲁棒的通用值，在不同浓度剖面下都能收敛。唯一可能需要调整的是 a₀（初始振幅），我们设为 0.8m，覆盖 VGR 房屋的典型高度范围。

### Q5: "与 2D 方法（GrGSL/SurgeCast）相比，3D 自适应的实际增益是多少？"
**回应**: 在 VGR 数据集上，源高度在 z=-0.3 到 0.2m 范围。2D 方法固定在 z=0.3m，可能错过源附近的高浓度区域。3D 自适应可以向下探索到 z=0.0-0.1m，获得更强的信号。增益取决于浓度剖面的陡度——剖面越陡，增益越大。

### Q6: "后验衰减率 γ 如何选择？会不会太激进（遗忘太快）或太保守（不衰减）？"
**回应**: γ=0.01 对应 ~100 步的半衰期。在 200 步总预算下，早期观测在后期仍有 ~13% 权重（exp(-2)≈0.135），不会完全遗忘。同时，近期观测权重更高，避免早期噪声锁死后验。γ 的敏感性分析在消融实验中展示。

### Q7: "为什么不用 EIG（期望信息增益）做高度选择？"
**回应**: EIG 需要前向模型来模拟 "如果我在高度 z 测量，期望获得多少信息"。这要求：
1. 准确的 3D 浓度场模型（我们没有）
2. 对每个候选高度做前向模拟（计算量大）
3. 模型与现实匹配（已知不匹配，Pitfall #4）

ESC 直接用传感器测量提取梯度，不需要前向模型，更鲁棒且计算量小。这是 "model-free" vs "model-based" 的权衡——在模型不准确的场景下，model-free 方法更优。

### Q8: "MaxConc-z 基线比 ESC 更简单，ESC 的优势在哪？"
**回应**: MaxConc-z 是贪心策略——只记住最高浓度高度，不跟踪梯度变化。在浓度剖面随时间变化（如风向改变导致气体分布变化）的场景下，MaxConc-z 会卡在旧的最优高度。ESC 持续跟踪梯度，能适应动态变化。此外，MaxConc-z 对噪声敏感（单次高浓度测量就锁定），ESC 通过滤波平滑噪声。

---

## 8. 预期结果

### 8.1 与基线对比（VGR 3 House，5 seeds）

| 方法 | H01 预期 | H02 预期 | H03 预期 | 平均预期 |
|------|---------|---------|---------|---------|
| PMFS | ~6m | FAIL | FAIL | - |
| GrGSL | ~1.7m | ~3.6m | ~7.8m | ~4.4m |
| SurgeCast | ~3.7m | - | - | - |
| OPGSL (Fixed-z) | ~1.1m | ~1.1m | ~1.4m | ~1.2m |
| OPGSL (ESC-3D) | ~0.8m | ~0.9m | ~1.1m | ~0.9m |

### 8.2 消融实验

| 配置 | 说明 | 预期误差 |
|------|------|---------|
| A0 | Fixed-z 基线 | ~1.2m |
| A1 | + Lévy 高度探索 | ~1.0m |
| A2 | + 显著层扫描 | ~0.95m |
| A3 | + ESC 跟踪 | ~0.9m |
| A4 | + 后验衰减 | ~0.85m |
| A5 | 全部模块 | ~0.8m |

### 8.3 统计检验

- Wilcoxon 秒和检验（非参数，小样本）
- 显著性水平 α=0.05
- 效应量：中位数差异 / IQR

---

## 9. 实现计划

### 9.1 C++ 修改范围

1. **OPGSL.hpp**: 新增 ESC 状态、Lévy 高度状态、显著层状态
2. **OPGSL.cpp**:
   - `levyHeight()`: Lévy 高度采样
   - `significantLayerScan()`: 显著层递归二分
   - `escUpdate()`: ESC 梯度跟踪
   - `updateAltitudePosterior()`: 带衰减的后验更新
   - `maxConcAltitude()`: MaxConc-z 基线
   - 修改 `chooseGoalAndMove()`: 设置 z 坐标
3. **launch 文件**: 添加 3D 相关参数

### 9.2 VM 部署

1. 修改 OPGSL.cpp/hpp
2. colcon build
3. 清理旧 ROS2 进程
4. 运行实验（3 House × 5 seeds × 4 配置）
5. 收集结果 CSV

---

## 10. 创新点总结

1. **ESC 连续高度梯度跟踪**（主创新）
   - 来源: 控制论（Krstic 2024）
   - 贡献: 首次将 ESC 应用于 UAV 气体源定位的高度选择
   - 理论: 无偏梯度估计，有收敛性证明

2. **显著层多分辨率高度采样**（辅助创新 1）
   - 来源: 气象学（WMO Manual No.306）
   - 贡献: 用递归二分高效捕获浓度剖面特征
   - 理论: 保特征多分辨率

3. **Lévy 高度探索**（辅助创新 2）
   - 来源: 生态学（Stromboli 2026）
   - 贡献: 3D 最优高度探索策略
   - 理论: μ=2 数学最优性证明

4. **带衰减的高度后验**（技术贡献）
   - 解决审稿人批评 #4（锁死问题）
   - 指数衰减加权，平衡新旧观测