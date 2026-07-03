# 统一数学框架候选方案分析

**目标**: 找到一个最新顶刊/顶会的数学框架，未在UAV GSL领域使用过，
能统一我们的三个模块（posterior搜索 + 停止准则 + 风险决策）。

---

## 候选1: Anytime Valid Inference (AVI) — 最有前途

**来源**: 
- Grünwald (2024) "Testing by Betting" (e-book, JMLR)
- Grünwald, Meinke, Vovk (2024) "Anytime Valid Inference" (NeurIPS workshop)
- Ramdas, Grünwald, Vovk, Wang (2023) "Game-theoretic Statistics and Safe Anytime-Valid Inference" (Statistical Science)
- Turner, Grünwald, Ramdas (2024) "Anytime-Valid, Fully-Sequential Confidence Sequences" (Bernoulli)

**核心数学结构**:
- **e-value**: 非负随机变量 E，满足 E[E₀] ≤ 1 (under H₀)
- **e-process**: 乘积 Π Eᵢ，anytime valid（不需要预设停止时间）
- **Confidence sequence**: 对所有停止时间τ都有效的置信区间

**为什么适合我们**:
1. **直接解决CP的exchangeability问题** — AVI不需要exchangeability，只需要sequential validity
2. **自然的停止准则** — e-process达到阈值就停止，有distribution-free guarantee
3. **未在GSL中使用** — 差异化明确

**如何统一三个模块**:
- **搜索**: Bayesian posterior update（这是prior）
- **停止**: e-process检测"后验是否已收敛"（这是anytime-valid test）
- **风险**: e-value的构造可以包含risk-sensitive term（类似W-RAIG）

**具体做法**:
```
H₀: "后验MAP距离真实源 > ε"  (还没找到)
H₁: "后验MAP距离真实源 ≤ ε"  (找到了)

e-value: E_t = posterior_odds(H₁|data_{1:t}) / prior_odds(H₁)
e-process: Π_{t=1}^T E_t
停止规则: 当 e-process > 1/δ 时停止 → 误停概率 < δ

Proposition: 在bounded posterior drift下，
e-process是super-martingale under H₀
→ 停止时的误停概率 ≤ δ (anytime valid)
```

**优势**:
- 2024-2025最新文献，审稿人可能不熟悉
- 直接解决"CP的exchangeability被违反"这个审稿人攻击点
- 有成熟的数学工具（martingale theory, testing-by-betting）
- 可以给出distribution-free stopping guarantee

**风险**:
- 需要构造GSL-specific的e-value（需要设计）
- 理论证明可能有难度

---

## 候选2: Online Conformal Prediction (OCP)

**来源**:
- Gibbs & Candès (2021) "Adaptive Conformal Inference Under Distribution Shift" (NeurIPS)
- Angelopoulos, Bates, Candès, et al. (2024) "Conformal Inference" (Annual Review)
- Bastani et al. (2022) "Practical Adversarial Multivalid Conformal Prediction" (NeurIPS)

**核心数学结构**:
- Adaptive α_t: 根据过去coverage调整显著性水平
- 保证: 长期average coverage ≥ 1-α
- 不需要exchangeability，只需要"long-run coverage"成立

**为什么适合我们**:
1. **直接改进我们现有CP** — 不是换框架，而是升级CP
2. **处理non-exchangeability** — 用adaptive α_t代替固定α
3. **有成熟的理论** — Gibbs & Candès Theorem 1

**如何统一**:
- 搜索: Bayesian posterior（不变）
- 停止: Online CP的adaptive coverage（代替naive CP）
- 风险: CP的prediction interval可以包含risk term

**优势**: 改动小，保留CP叙事
**风险**: 审稿人可能已经知道Gibbs & Candès 2021，不算太新

---

## 候选3: Stochastic Optimal Control + Information-Theoretic Objective

**来源**:
- Todorov (2007, 2009) "Linearly-solvable Markov decision problems" (NeurIPS)
- Levine (2018) "Reinforcement Learning and Control as Probabilistic Inference" (ICML tutorial)
- Botvinick et al. (2020) "Reinforcement Learning, Fast and Slow" (NeTrends)
- Recent: "Active Inference" (Friston, 2010-2025)

**核心数学结构**:
- 单一目标函数: min_π E[Σ_t c(x_t, a_t) + λ·H(posterior_t)]
- 搜索、停止、风险都是这一个目标函数的不同方面
- 停止 = 特殊动作 a=STOP，有固定的停止成本

**为什么适合我们**:
1. **真正的"统一涌现"** — 三个模块真的是同一个优化问题的解
2. **Active Inference是热点** — 2024-2025大量顶刊论文
3. **有成熟的理论** — 最优控制、MDP、变分推断

**具体做法**:
```
State: s_t = (UAV位置, 后验分布, t)
Action: a_t ∈ {移动方向, STOP}
Cost: c(s_t, a_t) = -EIG(a_t|s_t) + β·Var[EIG] + γ·1[a_t=STOP]·||MAP - source||

Proposition: 最优策略 π* 同时实现:
(a) 最大化信息增益 (搜索)
(b) 在后验收敛时停止 (停止准则)
(c) 最小化风险 (W-RAIG)
```

**优势**: 审稿人最认可这种"从第一性原理出发"的框架
**风险**: 证明最优策略满足(a)(b)(c)可能很难

---

## 推荐: 候选1 (AVI) 为主，融入候选3的元素

**理由**:
1. AVI是2024-2025最新框架，差异化最强
2. 直接解决审稿人的exchangeability攻击
3. 可以给出Proposition: "e-process在bounded drift下是super-martingale → anytime-valid stopping"
4. 搜索部分可以用Active Inference的objective来表述（融入候选3的元素）

**论文标题方向**:
旧: "CP-guided Sequential Bayesian Design"
新: "Anytime-Valid Sequential Testing for UAV Gas Source Localization with Distribution-Free Stopping Guarantees"

**理论贡献**:
- Proposition 1: e-process的anytime-validity（引用Grünwald 2024）
- Proposition 2: bounded posterior drift下的coverage bound
- 证明e-process是super-martingale under H₀

**与现有代码的关系**:
- CP模块 → 替换为e-process模块
- DDM模块 → 保留（作为e-value的GSL-specific构造）
- W-RAIG模块 → 保留（作为risk-sensitive action selection）
- 统一框架: 都是sequential hypothesis testing的组成部分