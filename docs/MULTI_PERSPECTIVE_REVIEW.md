# 多视角审查: ISJ投稿可行性评估

**日期**: 2026-07-04 02:30 CST
**论文**: "Anytime-Valid Sequential Testing for Robust UAV Gas Source Localization"
**目标**: IEEE Sensors Journal (ISJ, IF~3.4)
**当前评分**: 6.0-6.5/10 → 目标7.0+/10

---

## 一、理论视角 (Kant)

### 1.1 Proposition 0 (Approachability): 评分 5/10

**问题**: 这是对Blackwell 1956定理的直接引用，没有GSL-specific的理论贡献。

**审稿人会问**: "你只是把GSL问题塞进了Blackwell框架，然后引用定理说target set is approachable。这和说'GSL问题可以建模为MDP，然后引用MDP收敛定理'有什么区别?"

**改进方案**:
- 证明GSL问题满足Blackwell dual condition的**充分条件**
- 给出identifiability的形式化定义: 对于任意两个不同源位置s₁≠s₂，存在观测z使得p(z|s₁)≠p(z|s₂)
- 证明在VGR/GADEN的filament-based模型下，这个条件成立
- 讨论在什么条件下这个条件不成立(例如风向完全随机)

**改进后评分**: 6.5/10

### 1.2 Proposition 1 (Anytime-Valid Stopping): 评分 7/10 ✅

**优势**:
- Ville's inequality是严格的数学工具
- 分布无关，不需要exchangeability — 这是相对于CP的真正优势
- 实验验证: 97%触发率

**问题**:
- e-value设计 exp(η·(θ-r_t)) 是否最优?
- 为什么不用Bayes factor?
- η和θ的选择是否有理论依据?

**改进方案**:
- 证明: 在GSL的posterior更新下，这个e-value是"最powerful"的(或至少是"reasonable"的)
- 给出η和θ的选择指南(基于posterior的收敛速度)
- 与Bayes factor e-value做对比

**改进后评分**: 7.5/10

### 1.3 Proposition 2 (Search-Stop Coupling): 评分 4/10 ⚠️

**问题**: 只有proof sketch，没有完整证明。审稿人会要求补充。

**改进方案**:
- 方案A: 给出完整证明(可能很难)
- 方案B: 降级为"conjecture" + 实验支撑
- 方案C: 删除这个Proposition，用实验数据代替

**建议**: 选择方案B或C。不要声称无法证明的东西。

### 1.4 理论总评: 6.0/10

**核心问题**: 两个Proposition是已知结果的直接应用(Blackwell + Ville's)，一个无法证明。

**改进到7分的关键**:
1. 完善Proposition 0的证明(非trivial的充分条件)
2. 给出e-value设计的理论依据
3. 决定Proposition 2的命运

---

## 二、实验视角 (Lagrange)

### 2.1 样本量: 6.5/10

**我们n=30 vs 基线n=3**:
- 审稿人会说: "基线只有3个seed，无法做统计检验"
- 但我们也可以说: "我们的方法有30个seed，统计power足够"
- **关键**: 需要把基线也增加到n=10+

**改进方案**: 重跑基线到n=10 (在数据恢复后)

### 2.2 DDM不显著: 5/10 ⚠️

**问题**: Full vs NoDDM, p>0.46。DDM模块没有显著贡献。

**这意味着**:
- 要么DDM真的没用 → 删除DDM，贡献点减少
- 要么DDM需要更多时间工作 → 去掉step 15限制
- 要么DDM的参数需要调优 → 实验验证

**改进方案**:
1. 去掉step 15限制(已完成，等数据)
2. 如果去掉后仍然不显著 → 删除DDM
3. 如果显著 → 保留DDM

### 2.3 单数据集: 5/10 ⚠️

**ISJ对单数据集的容忍度**:
- 如果方法有强理论贡献 → 单数据集可能可以
- 如果主要是工程贡献 → 需要2+数据集
- 我们声称有理论贡献 → 单数据集风险中等

**改进方案**:
- 用PMFS scenarios (A, B, C, D, E) 作为额外数据集
- 或者用GADEN的不同配置(等数据下载完成)

### 2.4 跨环境一致性: 6.5/10

**问题**: PMFS CV=33%, GrGSL CV=27% — 它们的CV比我们低(42%)。

**但**: 它们的绝对误差很大(3-8m)，我们的误差小(1.8m)。

**正确叙事**: "在保持可接受精度(1.8m)的同时，实现跨环境一致性"
而不是: "最低跨环境方差"

**改进方案**: 用"精度-一致性"的trade-off来表述，而不是单独说一致性。

### 2.5 e-process触发率: 6.0/10

**问题**: 97%触发率听起来好，但所有run都在step=15停止。

**这意味着**: e-process在warm-up(5步)结束后，积累了10步的证据就触发了。

**审稿人会问**: "这是e-process真的在工作，还是step 15的硬编码限制?"

**改进方案**:
- 去掉step 15限制(已完成)
- 如果e-process仍然在类似步骤触发 → 证明它是真的在工作
- 如果触发步骤变化很大 → 说明e-process在适应不同环境

### 2.6 实验总评: 6.0/10

**核心问题**: DDM不显著 + 单数据集 + 基线n太少

**改进到7分的关键**:
1. 去掉step 15后重跑实验
2. 增加基线到n=10+
3. 至少1个额外数据集
4. 如果DDM仍不显著，删除它

---

## 三、副主编视角 (Noether)

### 3.1 创新点评估: 6.5/10

**novelty声明**:
1. "首次将e-process应用于GSL" → ✅ 真实novelty
2. "Blackwell approachability统一框架" → ⚠️ 有novelty但可能被质疑深度
3. "跨环境一致性" → ⚠️ 不是方法novelty，是实验发现

**与ISJ近期论文对比**:
- ISJ 2024 3D Klinotaxis: 生物启发方法，有novelty
- ISJ 2024 DRL indoor: 深度学习方法，有novelty
- ISJ 2025 RL-based CO: 强化学习方法，有novelty
- 我们的novelty: e-process + Blackwell → 理论框架，novelty足够

### 3.2 叙事策略: 关键决策

**选项A: 强调理论贡献**
- 标题: "Anytime-Valid Sequential Testing for UAV GSL..."
- 核心: e-process + Blackwell framework
- 风险: 理论深度可能不够

**选项B: 强调实验贡献**
- 标题: "Posterior-Based Search for Robust UAV GSL in Signal-Degraded Environments"
- 核心: 跨环境一致性 + e-process停止
- 风险: 可能被认为只是工程贡献

**选项C: 两者兼顾(推荐)**
- 标题: "Anytime-Valid Sequential Testing for Robust UAV GSL with Distribution-Free Stopping Guarantees"
- 核心: 理论框架 + 实验验证
- 优势: 既有理论又有实验

### 3.3 最大拒稿风险

| 风险 | 概率 | 严重性 | 应对 |
|------|------|--------|------|
| DDM不显著 | 高 | 严重 | 删除DDM或修复 |
| 单数据集 | 中 | 严重 | 增加PMFS scenarios |
| 理论太浅 | 中 | 中等 | 完善Prop 0证明 |
| 基线n太少 | 中 | 中等 | 增加到n=10 |
| e-process只是应用 | 低 | 中等 | 给出e-value设计依据 |

### 3.4 投稿策略

**推荐**: 先完成以下工作，然后投ISJ

1. **必须做** (1-2周):
   - 恢复数据后重跑实验(去掉step 15限制)
   - 增加基线到n=10+
   - 如果DDM不显著，删除它

2. **应该做** (2-3周):
   - 用PMFS scenarios作为额外数据集
   - 完善Proposition 0证明
   - 给出e-value设计依据

3. **可以做** (如果时间允许):
   - Coverage table
   - Anytime performance curves
   - GADEN数据集

### 3.5 当前评分: 6.0-6.5/10

**距离7分还差**:
1. DDM问题解决(删除或修复) → +0.5
2. 增加数据集 → +0.5
3. 完善理论证明 → +0.5

**达到7分后的预期**: 接收概率40-50%

---

## 四、综合建议

### 4.1 最小可行路径 (达到7分)

1. **恢复VGR数据** (用户正在下载)
2. **去掉step 15限制** (已完成代码修改)
3. **重跑实验** (去掉step 15后)
4. **如果DDM不显著 → 删除DDM** (只保留e-process + W-RAIG)
5. **增加基线到n=10**
6. **用PMFS scenarios作为额外数据集**
7. **完善Proposition 0证明**

### 4.2 论文结构调整

如果删除DDM:
- 标题改为: "Anytime-Valid Stopping for UAV Gas Source Localization with Risk-Adjusted Search"
- 贡献点: e-process + W-RAIG + Blackwell框架
- 消融: Full(eCP+WRAIG) vs eCP-only vs WRAIG-only vs Baseline

如果保留DDM:
- 保持当前标题
- 需要证明DDM有显著贡献

### 4.3 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 1 | 恢复数据 + 重跑实验 | 新实验数据 |
| 2 | 统计分析 + 消融 | 完整实验表 |
| 3 | 完善理论 + 额外数据集 | 理论+泛化 |
| 4-5 | 论文写作 | 完整稿件 |
| 6 | 内部审阅 + 修改 | 最终稿件 |

---

## 五、一句话总结

> **"框架方向正确(e-process替代CP)，但DDM模块贡献不显著、单数据集、理论证明不完整。需要: (1)去掉step 15后重跑实验确认DDM贡献, (2)增加数据集, (3)完善Prop 0证明。当前6.0-6.5分，完成上述工作后可达7.0分。"**