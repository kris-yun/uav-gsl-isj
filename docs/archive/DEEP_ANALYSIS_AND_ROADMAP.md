# CP-SBD-GSL 深度诊断与投稿路线图

**日期**: 2026-07-03
**目标期刊**: IEEE Sensors Journal (ISJ, Q2, IF~3.4)
**当前评分**: 4.5-5.5/10 → 不可投稿
**目标**: 6-8周内达到可投稿水平

---

## 一、深度诊断：为什么理论"浅层"

### 1.1 CP-Stopping — 最致命的理论缺陷

**现状** (~40行代码):
```
residual = sqrt((mx-prev_mx)^2 + (my-prev_my)^2)
sliding_window.push(residual)
quantile = sort(window)[ceil((n+1)*(1-alpha))-1]
if quantile < threshold for K consecutive steps → STOP
```

**问题诊断**:
1. **这不是Conformal Prediction** — 没有nonconformity score，没有calibration/test split，没有coverage guarantee。Vovk et al. (2005)的CP需要：
   - 一个定义良好的nonconformity score $s_i = f(x_i, \{x_1,...,x_{i-1}\})$
   - exchangeability假设
   - 基于score的prediction interval
2. **当前实现只是一个滑动窗口分位数** — 这在统计学里叫"running percentile filter"，任何审稿人一看就知道不是CP
3. **没有coverage guarantee** — 代码中完全没有target coverage 90% → actual X%的验证

**为什么会被审稿人抓住**:
- Kepler(副主编)直接说了："标准CP要求i.i.d./exchangeable，UAV GSL中分布持续变化"
- 当前代码是"naive split conformal"，严格意义上覆盖保证不成立
- 审稿人会问："请给出empirical coverage table (target 90% → actual X%)"

### 1.2 DDM-Stopping — 缺少GSL特有贡献

**现状** (~120行代码):
- 标准SPRT + Ornstein-Uhlenbeck leak
- urgency-gating阈值衰减: θ(t) = θ₀·exp(-γt) + θ_min
- log-likelihood ratio用toy Gaussian plume模型

**问题诊断**:
1. **Gaussian plume假设错误** — VGR/GADEN都是filament仿真，不是Gaussian plume。用错误的似然函数做SPRT，evidence accumulation的理论保证不存在
2. **无GSL-specific理论** — Cisek 2009已经在robotics用了urgency-gating，我们只是把neuroscience的DDM搬过来，没有说清"为什么DDM适合GSL"
3. **与CP的交互未分析** — 两个停止准则并行运行，谁先触发谁停止。但没有理论分析当两者冲突时coverage guarantee是否还成立

### 1.3 W-RAIG — CVaR重新包装

**公式**:
```
RAIG(a) = E[EIG(a|θ)] - β·sqrt(Var[EIG(a|θ)])
```

**问题诊断**:
1. **这是均值-方差优化** — Markowitz 1952的投资组合理论就是这个公式。β=0退化为标准EIG(Infotaxis)，β→∞退化为最保守策略
2. **与CVaR的关系不清楚** — ISJ副主编直接指出"CVaR Rebranding Risk"。Rockafellar & Uryasev 2000的CVaR是成熟的风险度量
3. **没有closed-form** — 对于plume posterior，W-RAIG的计算需要Monte Carlo近似，计算开销未分析

### 1.4 "统一目标函数涌现" — 核心叙事问题

论文声称"7个模块从同一目标函数涌现"，但：
1. **没有数学证明** — 只有一个verbal argument的表格
2. **模块是独立设计的** — CP来自统计学习，DDM来自神经科学，W-RAIG来自最优传输。它们是"拼装"而非"涌现"
3. **审稿人会问Theorem在哪里** — Kepler: "每个模块都是浅层移植，没有从源领域带来真正的理论深度"

---

## 二、为什么SurgeCast在2/3场景优于我们

### 2.1 数据事实

| House | CP-SBD-GSL | SurgeCast | 差距 |
|-------|-----------|-----------|------|
| House01 | 1.0-1.6m | 2.9-3.9m | 我们好2× |
| House02 | 1.6-2.0m | 0.3-0.5m | 他们好4-6× |
| House03 | 1.2-1.3m | 0.8-1.5m | 相当 |

### 2.2 根因分析

SurgeCast在House02极好的原因可能是：
1. **House02的source在(0, -1, 0.2)** — 靠近起点附近，SurgeCast的简单upwind tracking可能恰好work
2. **CP-SBD-GSL的CP过早停止** — 如果CPonly在House02能达到0.19m，说明CP的"过早停止"反而是对的，但DDM/WRAIG干扰了CP
3. **SurgeCast是基于surge-cast的insect-inspired策略** — 在简单环境中(直通路径)非常高效，但在复杂环境(House01)中exploration不足

### 2.3 叙事重构方向

**不能说**: "我们全面优于SurgeCast"
**应该说**: "CP-SBD-GSL提供risk-controlled search，SurgeCast在某些环境中更快但不稳定"

具体策略：
1. 引入**anytime performance curve** — 展示在每一步的累积风险
2. 引入**CP coverage metric** — SurgeCast没有formal coverage guarantee
3. 引入**resource-constrained scenario** — 当UAV电量有限时，CP-SBD-GSL的stopping guarantee更有价值
4. 诚实承认SurgeCast在某些场景更优，但强调risk profile不同

---

## 三、投稿可行性评估

### 3.1 ISJ的投稿标准

IEEE Sensors Journal (IF~3.4)要求：
- **新颖性**: 有明确的创新点 (当前得分6/10 → OK)
- **理论深度**: 有formal analysis或proof (当前3-5/10 → 不足)
- **实验充分**: 多数据集+统计检验 (当前4/10 → 不足)
- **可复现性**: 代码/数据公开 (当前OK)

### 3.2 可投稿的最低标准

要达到ISJ大修(major revision)的最低标准：
1. 理论贡献从3/10 → 至少6/10
2. 实验支撑从4/10 → 至少7/10
3. 总分从4.5-5.5 → 至少6.5-7.0

### 3.3 可行性判断

**可行，但需要6-8周密集工作**。核心在于：
- CP部分需要重写为adaptive CP (Gibbs & Candès 2021)
- 需要增加至少一个Proposition/Theorem
- 需要10-20 seeds的统计检验
- 需要GADEN数据集

---

## 四、6-8周投稿路线图

### Phase 1: 理论修复 (第1-2周) — 决定性

#### 4.1.1 CP重写：Adaptive Conformal Prediction for Sequential GSL

**当前问题**: 滑动窗口分位数 ≠ Conformal Prediction

**修复方案**: 实现Gibbs & Candès (2021) "Adaptive Conformal Inference Under Distribution Shift"

核心思想：
```
# 非自适应CP (当前naive版):
prediction_interval = quantile(scores, 1-alpha)

# 自适应CP (Gibbs & Candès 2021):
# 在每个时间步t，调整alpha_t:
alpha_{t+1} = alpha_t + gamma * (alpha - err_t)
# 其中 err_t = 1{y_t not in C_t(x_t)} 是覆盖失败指示
# gamma > 0 是学习率
```

**具体实现步骤**:
1. 定义nonconformity score: $s_t = \|MAP_t - MAP_{t-1}\|$ (MAP位置残差)
2. 用adaptive alpha替代fixed alpha
3. 每步更新: $\alpha_{t+1} = \alpha_t + \gamma(\alpha - \mathbb{1}\{s_t > q_{1-\alpha_t}\})$
4. 停止条件: 当$s_t$的$(1-\alpha_t)$分位数持续低于阈值

**理论贡献** (论文中需要证明的):
- **Proposition 1**: 在bounded drift假设下（$\|p_t - p_{t+1}\|_{TV} \leq \delta$），adaptive CP的长期coverage满足 $|\bar{coverage} - (1-\alpha)| \leq O(\gamma + \delta)$
- 这给出了GSL中CP coverage guarantee的explicit bound
- 需要证明drift rate $\delta$ 在UAV GSL中是有界的（因为posterior update是Bayesian，变化速率有理论bound）

#### 4.1.2 DDM与GSL的理论桥接

**修复方案**: 将DDM的log-likelihood ratio从toy Gaussian plume改为基于实际posterior的evidence

```
# 当前 (错误):
llr = log P(z|source at MAP) / P(z|no source)  # 用Gaussian plume

# 修复后:
llr = log [p_t(MAP) / p_{t-1}(MAP)]  # posterior在MAP处的变化率
# 或者更精确:
llr = KL(p_t || p_{t-1})  # 两步posterior之间的KL散度
```

**理论贡献**:
- **Proposition 2**: 证明当posterior收敛时（$KL(p_t \| p_{t-1}) \to 0$），DDM的evidence accumulation会自然停止
- 这建立了DDM stopping与Bayesian convergence的formal connection

#### 4.1.3 W-RAIG的理论定位

**修复方案**: 明确定位为"mean-variance optimization of information gain"，并给出closed-form approximation

**理论贡献**:
- **Proposition 3**: 在Gaussian posterior近似下，W-RAIG有closed-form:
  $\mathcal{I}^{RAIG}(a) \approx \frac{1}{2}\log\frac{|\Sigma_t|}{|\Sigma_{t+1|a}|} - \beta\sqrt{\text{tr}(\Sigma_{t+1|a}^{-1}\Sigma_t)}$
- 证明W-RAIG在posterior multi-modal时退化为robust action selection

### Phase 2: 修复CPonly > Full矛盾 (第2-3周)

#### 4.2.1 停止时序分析

**问题**: CPonly在House02达0.19m，但Full达1.6-2.0m。DDM和WRAIG反而降低了性能。

**诊断方案**:
1. 记录每步的CP width、DDM evidence、WRAIG field
2. 画出三个指标随时间变化的曲线
3. 找到DDM/CP的冲突点

**修复方案**:
1. **优先级机制**: CP > DDM > V5 convergence。CP是distribution-free guarantee，优先级最高
2. **DDM阈值调优**: 当CP width已经很低时，降低DDM的停止阈值
3. **WRAIG的exploration控制**: 当CP width < threshold时，WRAIG应该exploit而非explore

### Phase 3: 实验补强 (第3-5周)

#### 4.3.1 统计检验

**当前**: 3 seeds，无统计检验
**目标**: 10 seeds (优先) + 20 seeds (理想)

需要的统计检验：
1. **Wilcoxon signed-rank test** — 方法间比较
2. **Bootstrap 95% CI** — 中位数的置信区间
3. **Effect size (Cohen's d)** — practical significance
4. **Friedman test + post-hoc Nemenyi** — 多方法多场景比较

#### 4.3.2 CP Coverage Table

**必须提供**: target coverage → actual coverage

| Target | Actual (House01) | Actual (House02) | Actual (House03) |
|--------|------------------|------------------|------------------|
| 80%    | ?%               | ?%               | ?%               |
| 90%    | ?%               | ?%               | ?%               |
| 95%    | ?%               | ?%               | ?%               |

这需要在每个seed中记录：source是否在CP confidence region内

#### 4.3.3 GADEN数据集

ISJ要求至少2个独立数据集。VGR的3个house只是同一数据集的不同配置。

**方案**:
1. 用GADEN (Gas Dispersion Simulator) 生成新场景
2. 至少3个不同wind condition + obstacle configuration
3. 在VM上编译GADEN bridge并运行

#### 4.3.4 多起点敏感性实验

当前只有1个起始位置。需要3-5个不同起点。

### Phase 4: 论文写作 (第5-7周)

#### 4.4.1 叙事重构

**旧叙事**: "我们比所有baseline都好" (被SurgeCast反驳)
**新叙事**: "Risk-controlled Bayesian search with formal stopping guarantees"

标题候选:
- "Adaptive Conformal Stopping for Risk-Controlled UAV Gas Source Localization"
- "Distribution-Free Termination Guarantees for Bayesian Gas Source Search"

核心贡献重新排序:
1. **首要**: Adaptive CP for sequential GSL (首次将CP用于GSL + 理论coverage guarantee)
2. **次要**: Risk-aware information gain (W-RAIG with closed-form)
3. **辅助**: DDM-inspired evidence accumulation (Bayesian convergence detection)

#### 4.4.2 审稿人回应预案

| 审稿人问题 | 回应策略 |
|-----------|---------|
| "SurgeCast在2/3场景更好" | 承认并reframe: CP-SBD-GSL提供risk-controlled profile + coverage guarantee |
| "CP exchangeability?" | 用adaptive CP (Gibbs & Candès 2021) + bounded drift证明 |
| "3 seeds不够" | 增加到10-20 seeds + bootstrap CI + Wilcoxon |
| "CPonly > Full?" | 提供stopping time analysis + 优先级机制修复 |
| "理论太浅" | Proposition 1-3 + coverage table |
| "单数据集" | GADEN + VGR (多起点) |

---

## 五、关键决策点

### 决策1: 是否继续投ISJ?

**选项A: 继续ISJ** (推荐)
- 需要6-8周密集工作
- 核心: adaptive CP重写 + 10-seed实验 + GADEN
- 预期: major revision (6.5-7/10)

**选项B: 降级到Sensors (MDPI, Q3)**
- 工作量减半
- 但IF只有3.0左右，学术价值降低

**选项C: Workshop paper**
- 最快，但影响力最低
- 不推荐

### 决策2: 理论贡献的最低可行方案

**最小改动** (3-4周):
- 实现adaptive CP
- 给出Proposition 1 (coverage bound)
- 10 seeds + Wilcoxon

**中等改动** (6-8周):
- 上述 + Proposition 2-3
- GADEN数据集
- Coverage table

**大改** (12周+):
- 重新设计模块交互
- 解决CPonly > Full的根本问题
- 20 seeds + 全面统计

**推荐**: 中等改动 (6-8周)

---

## 六、立即可执行的任务

### 今天:
1. 检查VM上10-seed实验进度
2. 搜索adaptive CP的最新实现 (Gibbs & Candès 2021)
3. 设计nonconformity score的候选方案

### 本周:
4. 实现adaptive CP原型
5. 设计coverage table的计算逻辑
6. 修复10-seed批处理脚本的map_dist缺失问题

### 下周:
7. Proposition 1的证明草稿
8. GADEN环境编译测试
9. CP/DDM stopping时序分析脚本
