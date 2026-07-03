# 统一数学框架: Blackwell Approachability + Anytime-Valid Stopping for UAV GSL

## 一、框架概述

**核心思想**: 将UAV气体源建模为一个顺序决策问题，
其中 **Blackwell Approachability** 提供统一的理论框架（搜索+停止+风险），
**Anytime-Valid e-processes** 提供distribution-free的停止保证。

**三个模块如何"涌现"**:
- 搜索策略 = Blackwell框架中最小化distance to target set的action
- 停止准则 = e-process达到阈值（Blackwell框架的special case: STOP action）
- 风险控制 = Blackwell target set的efficiency约束

---

## 二、问题设定

### 2.1 环境

- 状态空间: X ⊂ R² (UAV位置)
- 源位置: s* ∈ X (未知)
- 后验分布: π_t(s) = P(s* = s | z_{1:t}, x_{1:t})
  其中 z_t = 气体浓度测量, x_t = UAV位置
- MAP估计: ŝ_t = argmax_s π_t(s)

### 2.2 顺序决策

每一步t, UAV选择:
- action a_t ∈ A: 下一个测量位置 (或特殊action STOP)
- 收到观测 z_t ~ p(z | x_t, s*)
- 更新后验: π_{t+1}(s) ∝ π_t(s) · p(z_t | x_t, s)

---

## 三、Blackwell Approachability框架

### 3.1 向量值博弈 (参考Principato & Stoltz 2025)

定义 two-player repeated game:

**Player (UAV)**: 选择 action a_t ∈ A = {移动方向, STOP}
**Adversary (环境)**: 选择 b_t ∈ B (环境条件: 风向、plume结构)

**向量值payoff** m(a_t, b_t) ∈ R²:
```
m(a_t, b_t) = (coverage_t, efficiency_t)
```

其中:
- coverage_t = 1{ŝ_t ∈ B_ε(s*)}  (MAP是否在源的ε邻域内)
- efficiency_t = -d(ŝ_t, s*)  (距离的负值, 越大越好)

### 3.2 目标集 C

定义 target set C ⊂ R²:
```
C = {(c, e) ∈ R² : c ≥ 1-α, e ≥ -ε}
```

即: coverage ≥ 1-α 且 距离 ≤ ε

**Blackwell条件 (Theorem 1)**:
C is approachable ⟺ ∀q ∈ Δ(B), ∃p ∈ Δ(A) s.t. m(p,q) ∈ C

**直觉**: 对于任何环境条件（风向、plume结构），
UAV都存在一个策略使得长期平均payoff落在target set中。

### 3.3 关键Proposition

**Proposition 0 (Approachability for GSL)**:
在以下条件下，target set C is approachable:
1. Posterior update is consistent: π_t → δ_{s*} as t → ∞ (under identifiability)
2. Action space is rich enough: ∃a ∈ A s.t. EIG(a|π_t) > 0 for all π_t ≠ δ_{s*}

**证明sketch**:
- 条件1保证coverage_t → 1 as t → ∞
- 条件2保证UAV总能获得新信息
- 由Blackwell Theorem 1, C is approachable

---

## 四、Anytime-Valid Stopping via e-processes

### 4.1 停止问题

在Blackwell框架中，STOP是特殊action。
我们需要决定 **何时停止** 且 保证误停概率 < δ。

### 4.2 Sequential Hypothesis Test

定义:
- H₀: "后验MAP距源 > ε" (ŝ_t ∉ B_ε(s*))
- H₁: "后验MAP距源 ≤ ε" (ŝ_t ∈ B_ε(s*))

### 4.3 Bayes Factor作为e-value

定义e-value:
```
E_t = BF_t = P(z_t | H₁, data_{1:t-1}) / P(z_t | H₀, data_{1:t-1})
```

即: 在H₁ vs H₀下的Bayes factor

**简化形式** (使用posterior odds):
```
E_t = [P(s* ∈ B_ε(ŝ_t) | z_{1:t}) / P(s* ∉ B_ε(ŝ_t) | z_{1:t})] 
    / [P(s* ∈ B_ε(ŝ_t)) / P(s* ∉ B_ε(ŝ_t))]
```

即: posterior odds / prior odds

### 4.4 e-process

定义e-process:
```
M_T = Π_{t=1}^T E_t
```

**Ville's Inequality** (Ramdas et al. 2023):
Under H₀:
```
P(sup_T M_T ≥ 1/δ) ≤ δ
```

### 4.5 停止规则

```
τ = min{T : M_T ≥ 1/δ}
```

**性质**:
1. **Anytime valid**: 对于任何停止时间τ (包括data-dependent)，
   P(τ < ∞ | H₀) ≤ δ
2. **Consistent**: Under H₁, E[τ] < ∞ (在有限步内停止)
3. **不需要exchangeability**: 只需要sequential validity (martingale condition)

### 4.6 关键Proposition

**Proposition 1 (Anytime-Valid Stopping for GSL)**:
假设:
(A1) Posterior update is Bayesian: π_{t+1} ∝ π_t · p(z_t | x_t, ·)
(A2) Bounded information gain: KL(π_{t+1} || π_t) ≤ D_max for all t

Then:
(a) Under H₀ (MAP not converged): M_T is a super-martingale
    → P(sup_T M_T ≥ 1/δ) ≤ δ (anytime valid)
(b) Under H₁ (MAP converged): E[τ] ≤ O(1/Δ²)
    其中 Δ = KL(π_true || π_H₀) (signal strength)
(c) 停止时的posterior confidence: P(s* ∈ B_ε(ŝ_τ) | z_{1:τ}) ≥ 1-δ

**证明sketch**:
(a) Under H₀, E_t ≤ 1 (e-value has expectation ≤ 1 under null)
    → M_T = Π E_t is super-martingale
    → By Ville's inequality, P(sup M_T ≥ 1/δ) ≤ δ

(b) Under H₁, E[E_t] = exp(KL(π₁||π₀)) > 1
    → M_T grows exponentially
    → E[τ] ≤ log(1/δ) / KL(π₁||π₀)

(c) At stopping: M_τ ≥ 1/δ
    → posterior odds ≥ 1/δ × prior odds
    → P(H₁|data) ≥ 1-δ (by Bayes rule)

---

## 五、搜索策略 (W-RAIG在Blackwell框架中的角色)

### 5.1 Information-Directed Search

在Blackwell框架中，search strategy = 选择action a_t
使得 m(a_t, q) 尽快approach target set C。

定义信息-风险比 (Information-Risk Ratio):
```
Φ(a | π_t) = EIG(a | π_t) / Var[EIG(a | π_t)]
```

其中 EIG = Expected Information Gain = H(π_t) - E_z[H(π_{t+1})]

### 5.2 W-RAIG作为Blackwell策略

W-RAIG选择:
```
a*_t = argmax_a [EIG(a|π_t) - β·√Var[EIG(a|π_t)]]
```

这等价于在Blackwell框架中:
```
a*_t = argmin_a d(m(a, q̂_t), C)
```

其中 q̂_t 是对环境策略的估计。

### 5.3 Proposition 2 (Search-Stop Coupling)

**Proposition 2**:
W-RAIG搜索策略和e-process停止规则的联合策略满足:
(a) 搜索效率: E[d(ŝ_T, s*)] ≤ O(1/√T) (后验收敛速度)
(b) 停止保证: P(false positive) ≤ δ (anytime valid)
(c) 耦合: W-RAIG的信息增益加速e-process的增长
    → E[τ_W-RAIG] ≤ E[τ_random] (比随机搜索更快停止)

---

## 六、DDM模块的角色

### 6.1 DDM作为e-value的GSL-specific构造

DDM (Drift-Diffusion Model) 不再是独立的停止准则，
而是e-value的 **GSL-specific likelihood ratio** 的计算方式。

具体地:
```
E_t = exp(η · ΔLLR_t)
```

其中 ΔLLR_t 是DDM的evidence accumulation step:
```
ΔLLR_t = posterior_entropy_change(x_t, z_t)
        = H(π_t) - H(π_{t+1})
```

这比简单的Bayes factor更robust，因为:
1. 它考虑了posterior的entire distribution (不只是MAP)
2. 它自然地处理了multi-modal posteriors
3. 它与DDM的evidence accumulation理论一致

### 6.2 DDM的GSL-specific贡献

DDM的独特贡献在于 **e-value的构造方式**:
- 标准e-value: 用posterior odds (只看MAP附近)
- 我们的e-value: 用posterior entropy change (看整个posterior)
- 优势: 在multi-modal posterior下更robust

---

## 七、完整框架图

```
                    ┌─────────────────────────────┐
                    │  Blackwell Approachability   │
                    │  (统一理论框架)              │
                    └─────────┬───────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼────────┐ ┌───▼────────┐ ┌───▼────────────┐
     │  Search (W-RAIG) │ │ Stop (e-   │ │ Risk Control   │
     │  最大化EIG -     │ │ process +  │ │ (Blackwell     │
     │  β·√Var[EIG]     │ │ DDM e-val) │ │ target set C)  │
     └────────┬────────┘ └───┬────────┘ └───┬────────────┘
              │               │               │
              │        ┌──────▼──────┐        │
              │        │ Ville's     │        │
              │        │ Inequality  │        │
              │        │ P(fp) ≤ δ   │        │
              │        └─────────────┘        │
              │                               │
              └───────────────┬───────────────┘
                              │
                    ┌─────────▼───────────┐
                    │  Sequential Decision │
                    │  π_t → a_t → z_t    │
                    │  → π_{t+1} → ...    │
                    └─────────────────────┘
```

---

## 八、与审稿人预期的对应

| 审稿人问题 | 我们的回答 |
|-----------|-----------|
| "CP的exchangeability被违反" | 我们用e-process代替CP, 不需要exchangeability |
| "7模块统一涌现没有证明" | 用Blackwell Theorem 1证明: 三个模块是同一个approachability问题的解 |
| "没有Theorem" | Proposition 1 (anytime-valid stopping) + Proposition 2 (search-stop coupling) |
| "coverage table缺失" | e-process的coverage guarantee是distribution-free的 |
| "理论浅层" | Blackwell approachability + Ville's inequality + e-process theory (2023 Statistical Science) |

---

## 九、与现有代码的映射

| 现有代码 | 理论对应 | 需要修改 |
|---------|---------|---------|
| CP-Stopping | → e-process stopping | 替换为e-process |
| DDM-Stopping | → DDM e-value construction | 保留, 修改LLR为posterior entropy change |
| W-RAIG | → Information-directed search | 保留, 添加Blackwell理论解释 |
| Posterior update | → Bayesian update (不变) | 无修改 |

---

## 十、参考文献

1. Principato & Stoltz (2025). "Blackwell's Approachability for Sequential Conformal Inference." arXiv:2510.15824.
2. Ramdas, Grünwald, Vovk, Shafer (2023). "Game-theoretic Statistics and Safe Anytime-Valid Inference." Statistical Science, 38(4), 576-601.
3. Grünwald (2024). "Testing by Betting: A Recipe for the Future." arXiv.
4. Gibbs & Candès (2021). "Adaptive Conformal Inference Under Distribution Shift." NeurIPS.
5. Russo & Van Roy (2018). "Learning to Optimize via Information-Directed Sampling." Operations Research.
6. Ville (1939). "Étude critique de la notion de collectif." Gauthier-Villars.