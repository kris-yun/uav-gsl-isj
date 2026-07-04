# CP-SBD-GSL 三大核心问题深度诊断与解决方案

**日期**: 2026-07-03
**目的**: 为ISJ投稿制定理论修复路线图

---

## 一、模块间负协同 — 根因诊断

### 1.1 代码级根因

当前停止逻辑 (checkSourceFound函数):
```
检查顺序: CP → DDM → CP(重复!) → V5收敛 → FAST EXIT → 硬超时
```

关键发现:
1. **CP被检查了两次** — 这是bug，不是设计
2. **DDM和CP完全独立运行** — 谁先触发谁停止，没有协调
3. **W-RAIG只影响动作选择** (选哪个格子)，不直接参与停止决策

### 1.2 负协同的因果链

```
W-RAIG引导UAV探索不确定区域
  → MAP轨迹变得不稳定(探索驱动的跳变)
    → CP的residual = ||MAP_t - MAP_{t-1}|| 增大
      → CP width持续高于阈值 → CP无法收敛
      
同时:
W-RAIG引导UAV到低气体区域
  → 后验变化小(没有新信息)
    → DDM的LLR = gas * expected_conc - 0.1 * map_move 趋近零
      → DDM的evidence衰减 → DDM过早触发停止
        → 搜索被截断，CP永远没有机会收敛
```

**CPonly=0.19m的原因**: 没有W-RAIG干扰 → MAP轨迹稳定 → CP residual干净 → CP正确收敛
**Full=1.6-2.0m的原因**: W-RAIG干扰MAP → DDM过早截断 → CP被阻止收敛

### 1.3 核心矛盾

DDM和CP在解决**不同问题**:
- **CP**: "MAP估计是否已经稳定?" → 监控后验位置的收敛
- **DDM**: "后验是否已经收敛?" → 监控证据积累

当W-RAIG驱动exploration时:
- 后验可能很稳定(没有新信息) → DDM说"停"
- 但MAP还在跳动(因为exploration) → CP说"还没好"

**这是一个设计缺陷，不是参数调优问题。**

---

## 二、解决方案：统一停止机制 (Unified Stopping)

### 2.1 设计原则

从统一目标函数出发:
$$\max_\pi \mathbb{E}\Big[\sum_t \gamma^{t-1}\mathcal{I}_t - \lambda\sum_t c(s_t,s_{t+1})\Big] \quad \text{s.t.} \quad \text{CP-Stop}(t) \leq \varepsilon$$

CP是**约束条件**，DDM是**启发式辅助**。正确的优先级:
1. **CP是硬约束** — 分布无关的coverage guarantee
2. **DDM是软辅助** — 加速收敛的启发式信号
3. **W-RAIG是动作选择** — 不参与停止决策

### 2.2 级联停止协议 (Cascaded Stopping Protocol)

```cpp
// 新的停止逻辑:
GSLResult OPGSL::checkSourceFound() {
    // 前置条件不变
    if (elapsed_time_ < 15.0f) return GSLResult::Running;
    if (gas_hit_count_ < 3) return GSLResult::Running;
    if (step_count_ < 15) return GSLResult::Running;
    
    // 第一优先级: CP停止 (coverage guarantee)
    if (use_cp_ && cp_stopping_.shouldStop()) {
        // CP收敛 = MAP稳定 → 这是最可靠的停止信号
        log("CP-STOP: coverage-guaranteed termination");
        return GSLResult::Success;
    }
    
    // 第二优先级: DDM停止 (需要CP宽度已低于2倍阈值)
    // 关键修改: DDM只有在CP"接近收敛"时才允许触发
    // 这防止DDM在W-RAIG探索阶段过早截断
    if (use_ddm_ && ddm_stopping_.shouldStop()) {
        float cp_width = cp_stopping_.getWidth();
        float cp_threshold = cp_width_threshold_;
        if (cp_width < 2.0f * cp_threshold) {
            // CP已经接近收敛，DDM可以作为辅助停止
            log("DDM-STOP: CP width={:.3f} (near threshold {:.3f})", cp_width, cp_threshold);
            return GSLResult::Success;
        } else {
            // CP还没收敛，忽略DDM的停止信号
            log("DDM wants to stop but CP width={:.3f} >> threshold {:.3f}, continuing", 
                cp_width, cp_threshold);
        }
    }
    
    // 第三优先级: V5收敛 + FAST EXIT (保留原有逻辑)
    ...
}
```

### 2.3 DDM的LLR重新设计

当前DDM的log-likelihood ratio:
```cpp
float llr = latest_gas_ * expected_conc - 0.1f * map_move;  // 太粗糙
```

问题:
- `expected_conc = exp(-dist^2/2)` 用的是Gaussian plume，但VGR是filament仿真
- `map_move`项惩罚MAP移动，但exploration阶段MAP必然移动

改进:
```cpp
// 用posterior entropy变化率作为evidence
float entropy_now = computePosteriorEntropy();
float llr = prev_entropy_ - entropy_now;  // 正值 = 信息增益
// 额外: 用gas hit rate作为辅助信号
float hit_rate = gas_hit_count_ / (float)step_count_;
llr += 0.5f * (hit_rate - 0.1f);  // 高命中率 = 接近源
```

这更符合DDM的理论基础: 积累的是"我们是否在接近答案"的证据。

### 2.4 W-RAIG与停止的解耦

W-RAIG应该**只影响动作选择**，不参与停止。当前代码已经这样设计，但W-RAIG的exploration会间接干扰CP。

修复: 在CP width接近阈值时，W-RAIG的beta应该动态降低:
```cpp
// 当CP接近收敛时，减少exploration
float cp_width = cp_stopping_.getWidth();
float cp_ratio = cp_width / cp_width_threshold_;
float effective_beta = wraig_cfg_.beta * std::min(cp_ratio, 1.0f);
// cp_ratio → 0 时，effective_beta → 0，W-RAIG退化为标准EIG(exploit)
```

---

## 三、模块"浅层移植" — 根因诊断

### 3.1 每个模块的问题

| 模块 | 来源 | 问题 |
|------|------|------|
| CP | 统计学习 (Vovk 2005) | 只用了滑动窗口分位数，不是真正的CP |
| DDM | 神经科学 (Gold&Shadlen 2007) | LLR用toy Gaussian plume，不匹配filament仿真 |
| W-RAIG | 最优传输 (CVaR) | 没有closed-form，没有GSL-specific风险解释 |

### 3.2 "浅层"的本质

**不是代码量的问题，是领域适配的问题。**

三个模块都是从源领域直接搬过来，没有回答:
1. "为什么这个工具适合GSL?" — 需要GSL-specific的物理动机
2. "GSL的特殊性如何改变了工具的设计?" — 需要domain adaptation
3. "这个工具在GSL中提供了什么新能力?" — 需要novel capability

### 3.3 浅层→深层的转变路径

**不是加更多模块，而是让现有模块扎根于GSL物理。**

#### CP: 从"分位数"到"真正的Conformal Prediction"

当前实现:
```
residual = ||MAP_t - MAP_{t-1}||  # 位置残差
quantile(residuals, 1-alpha)       # 滑动窗口分位数
```

这不是CP。CP需要:
1. **Nonconformity score** — 衡量"新观测与已有数据的不一致程度"
2. **Calibration set** — 历史score的参考分布
3. **Coverage guarantee** — 在exchangeability下，coverage = 1-alpha

**GSL-specific的CP设计**:

Nonconformity score应该反映"posterior是否已经收敛":
```
s_t = KL(p_t || p_{t-1}) + lambda * ||MAP_t - source_estimate||_normalized
```
- 第一项: 后验变化率 (信息论度量)
- 第二项: MAP与当前最优估计的距离 (物理度量)

当$s_t$的$(1-\alpha)$分位数持续低于阈值 → 后验已收敛 → 停止

#### DDM: 从toy plume到posterior-based evidence

当前LLR用Gaussian plume假设，但VGR是filament仿真。

**GSL-specific的DDM设计**:

Evidence应该基于posterior本身，不依赖plume模型:
```
llr_t = log(p_t(MAP_t) / p_0(MAP_t))  # 后验vs先验在MAP处的对数比
```
或更稳健的版本:
```
llr_t = entropy(p_{t-1}) - entropy(p_t)  # 信息增益
```

这不需要任何plume模型假设，纯粹基于Bayesian update。

#### W-RAIG: 从通用风险度量到plume-specific风险

当前W-RAIG:
```
RAIG(a) = E[EIG(a)] - beta * sqrt(Var[EIG(a)])
```

这是通用的均值-方差优化。需要加入GSL-specific的风险源:

```
RAIG_GSL(a) = E[EIG(a)] - beta_1 * sqrt(Var[EIG(a)])    # 后验不确定性
              - beta_2 * intermittency_penalty(a)          # plume间歇性风险
              - beta_3 * wind_uncertainty_penalty(a)        # 风场不确定性风险
```

- **intermittency_penalty**: 当观测位置的气体信号间歇性强时，EIG的方差自然更大
- **wind_uncertainty_penalty**: 当风场估计不确定时，移动代价更不可预测

---

## 四、理论不深 — 根因诊断与解决方案

### 4.1 当前理论缺陷

1. **没有coverage guarantee** — CP是naive实现，无法证明覆盖率
2. **没有convergence proof** — DDM没有证明与Bayesian convergence的关系
3. **"涌现"声明未证明** — "7模块从同一目标函数涌现"只是verbal claim

### 4.2 理论深度的最低可行方案

**不需要每个模块都有theorem，但需要一个核心理论贡献。**

**核心Proposition: Adaptive CP在序贯GSL中的coverage guarantee**

这是论文的理论支柱。证明思路:

**Setup**:
- 后验序列 $p_1, p_2, ..., p_t$ 由Bayesian update产生
- Nonconformity score: $s_t = f(p_t, p_{t-1})$ (后验变化率)
- Adaptive alpha: $\alpha_{t+1} = \alpha_t + \gamma(\alpha - \xi_t)$，其中$\xi_t = \mathbb{1}\{s_t > q_{1-\alpha_t}\}$

**Proposition 1** (Adaptive CP Coverage Bound):
设后验分布序列满足bounded drift条件:
$$D_{TV}(p_t, p_{t+1}) \leq \delta_t, \quad \text{其中} \sum_{t=1}^T \delta_t = O(\sqrt{T \log T})$$

则adaptive conformal stopping的长期coverage满足:
$$\left|\frac{1}{T}\sum_{t=1}^T \xi_t - \alpha\right| \leq O\left(\gamma + \frac{1}{\sqrt{T}}\right)$$

**证明思路**:
1. Bayesian update的bounded drift: 因为每次只观测一个(gas, wind)数据点，posterior变化率有界
2. Adaptive alpha的regret bound: 来自Gibbs & Candès 2021的Theorem 1
3. 两者的组合: drift有界 → score分布变化有界 → adaptive CP的coverage bound成立

**为什么这对ISJ够用**:
- 这是首次将adaptive CP应用于GSL
- 给出了explicit coverage bound (不是naive的"我们用了CP所以有coverage")
- 引用了Gibbs & Candès 2021 (高引用论文)作为理论基础

### 4.3 辅助Proposition (可选，加分项)

**Proposition 2** (DDM-Bayesian Convergence Connection):
当posterior entropy $H(p_t) \to H_{min}$ 时，DDM的evidence accumulation满足:
$$|E_t| \geq \theta(t) \implies KL(p_t \| p_{t-1}) < \epsilon$$

即: DDM停止 ⟹ 后验已经收敛 (在KL散度意义下)

**Proposition 3** (W-RAIG in Gaussian Posterior):
当posterior为高斯分布 $p_t(\theta) = \mathcal{N}(\mu_t, \Sigma_t)$ 时:
$$\mathcal{I}_t^{RAIG}(a) = \frac{1}{2}\log\frac{|\Sigma_t|}{|\Sigma_{t+1|a}|} - \beta\sqrt{\text{tr}(\Sigma_{t+1|a}^{-1}\Sigma_t - I)}$$

这个closed-form让W-RAIG的计算从$O(N^2)$ Monte Carlo降到$O(1)$。

---

## 五、统一叙事框架

### 5.1 旧叙事 (失败)

"我们从三个领域各拿了一个工具，组合起来比所有人都好"
→ 被SurgeCast反驳 → 被审稿人批评为"浅层移植"

### 5.2 新叙事 (推荐)

**核心**: "我们将Conformal Prediction适配到序贯GSL，首次给出分布无关的停止保证"

标题: "Adaptive Conformal Prediction for Distribution-Free UAV Gas Source Localization"

贡献重排:
1. **首要贡献 (理论)**: Adaptive CP for sequential GSL
   - 首次将CP用于GSL (novelty verified)
   - 给出coverage guarantee under bounded drift (Proposition 1)
   - 实现adaptive alpha处理non-exchangeability (Gibbs & Candès 2021)

2. **次要贡献 (方法)**: GSL-adapted Bayesian decision framework
   - Posterior-based DDM evidence (不依赖plume模型)
   - Plume-aware risk penalty in information gain
   - Cascaded stopping protocol (CP优先)

3. **第三贡献 (实验)**: Risk-controlled search
   - Coverage table (target → actual)
   - Anytime performance curve
   - 与SurgeCast的风险谱系对比

### 5.3 应对SurgeCast的策略

**不再声称全面优于SurgeCast**，而是:

"SurgeCast在某些环境中达到更低的最终误差(如House02: 0.4m vs 1.7m)，
但CP-SBD-GSL提供了SurgeCast没有的三个特性:
1. **Formal coverage guarantee**: CP保证coverage = 1-alpha
2. **Controlled risk profile**: 方差0.307 vs SurgeCast 1.220
3. **Anytime performance**: 在任何时刻t，CP-SBD-GSL的累积风险更低"

**具体实验**: 画出anytime performance曲线 (每一步的regret)

---

## 六、执行计划

### Phase 1 (第1-2周): 理论核心 — Adaptive CP

**任务**:
1. 实现adaptive alpha机制 (替代fixed alpha)
2. 设计GSL-specific nonconformity score
3. 编写coverage table计算逻辑
4. 证明Proposition 1 (bounded drift → coverage bound)

**产出**: 
- 新的CP_Stopping.hpp (adaptive版本)
- Proposition 1的LaTeX证明草稿
- Coverage table的实验设计

### Phase 2 (第2-3周): 模块协调 — 统一停止

**任务**:
1. 实现Cascaded Stopping Protocol (CP优先)
2. 重新设计DDM的LLR (posterior-based)
3. 实现CP-width-aware W-RAIG beta衰减
4. 修复CP被检查两次的bug

**产出**:
- 新的checkSourceFound()逻辑
- 修复后的Full方法应该优于CPonly

### Phase 3 (第3-5周): 实验补强

**任务**:
1. 10-seed实验完成 (检查VM进度)
2. Coverage table数据收集
3. GADEN数据集编译运行
4. 统计检验 (Wilcoxon + bootstrap CI)
5. Anytime performance curve

**产出**:
- 完整的实验数据表
- Coverage table
- 统计检验结果

### Phase 4 (第5-7周): 论文写作

**任务**:
1. 按新叙事重写论文
2. LaTeX排版
3. 引用文献更新
4. 审稿人回应预案

**产出**: 可投稿的完整论文

---

## 七、风险评估

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| Adaptive CP实现后coverage仍不达标 | 中 | 高 | 用wider alpha或更大的calibration窗口 |
| 修复负协同后Full仍不如CPonly | 低 | 高 | 分析具体场景，可能需要重新设计停止优先级 |
| GADEN编译失败 | 中 | 中 | 用VGR多起点替代 |
| 10-seed实验VM崩溃 | 中 | 中 | 用已完成的3-seed + bootstrap替代 |
| Proposition 1证明不成立 | 低 | 高 | 弱化claim为"empirical coverage" |
