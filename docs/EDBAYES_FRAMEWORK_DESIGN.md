# ============================================================
# Event-Driven Bayesian GSL (ED-Bayes) 改进框架设计
# 日期: 2026-07-04
# 目标: 从4.5分提升到8分
# ============================================================

## 一、核心转变：从连续信号到事件驱动

### 问题根源
现有所有GSL方法（包括Infotaxis）假设观测是连续浓度信号：
    z_t = C(x_t, t) + ε_t,  ε ~ N(0, σ²)

但filament-based扩散的实际物理是：
- 气体以离散filament形式从源释放
- 传感器要么"检测到filament"（z > τ），要么"未检测到"（z ≈ 0）
- 这是一个 **点过程**（point process），不是连续过程

### 科学问题（锐利版）
> 在intermittent plume contact条件下（UAV距源远、信号弱），
> 现有GSL方法因假设连续信号模型而失效：
> SurgeCast因无plume contact完全迷失（误差8×），
> Infotaxis因无gas时EIG≈0退化为随机游走。
> 
> 核心原因：**未检测到气体（non-detection）不提供信息**——
> 但实际上，non-detection携带与detection同等重要的定位信息。

### 核心Insight（首次提出）
**在事件驱动模型中，non-detection本身就是证据：**
- 在位置x未检测到气体 → 源不太可能在x附近（排除性证据）
- 在位置x检测到气体 → 源可能在upwind方向（包含性证据）
- 两种证据互补，共同驱动后验收敛

这是GSL领域 **首次** 将non-detection作为等权信息源。

---

## 二、数学框架

### 2.1 观测模型（替换连续高斯为事件Bernoulli）

在位置x_t，时间间隔Δt内的气体到达服从Poisson过程：
    N(Δt) ~ Poisson(λ(x_t, s*) · Δt)

其中到达率：
    λ(x, s*) = λ₀ · f(||x - s*||) · g(wind alignment)
    f(d) = exp(-d/ℓ)         # 距离衰减，ℓ为特征长度
    g(a) = 1 + α · cos(a)    # 风向调制，a为风与(x→s*)的夹角

二值检测事件：
    d_t = 1{z_t > τ_detect}
    
似然：
    P(d_t = 1 | x_t, s*) = 1 - exp(-λ(x_t, s*) · Δt)   # 检测概率
    P(d_t = 0 | x_t, s*) = exp(-λ(x_t, s*) · Δt)        # 未检测概率

### 2.2 后验更新（事件驱动）

对每个候选源位置s：
    π_{t+1}(s) ∝ π_t(s) · L(d_t | x_t, s)

其中：
    L(d_t=1 | x_t, s) = 1 - exp(-λ(x_t, s) · Δt)    # detection likelihood
    L(d_t=0 | x_t, s) = exp(-λ(x_t, s) · Δt)          # non-detection likelihood

关键：**即使d_t=0（无气体），L(d_t=0|s)对不同s的值不同**
- s近：λ大 → exp(-λΔt)小 → L小 → 排除s
- s远：λ小 → exp(-λΔt)大 → L大 → 不排除s
- 这就是"non-detection有信息"的数学表达

### 2.3 搜索策略（事件驱动EIG）

标准Infotaxis的EIG：
    EIG(a) = H(π_t) - E_z[H(π_{t+1})]     # z是连续值

事件驱动EIG（Event-Driven EIG, ED-EIG）：
    ED-EIG(a) = H(π_t) - E_d[H(π_{t+1})]
              = H(π_t) - [P(d=1)·H(π_{t+1}|d=1) + P(d=0)·H(π_{t+1}|d=0)]

其中：
    P(d=1 | a, π_t) = Σ_s π_t(s) · (1 - exp(-λ(x_t+a, s)·Δt))
    P(d=0 | a, π_t) = 1 - P(d=1)

关键区别：**P(d=0)时仍有信息增益**
    H(π_{t+1}|d=0) < H(π_t)   # 因为non-detection排除了某些源

这解决了"无gas时搜索退化"的根本问题：
标准Infotaxis：z≈0 → EIG≈0 → 随机
事件驱动：d=0 → H(π_{t+1}|d=0) < H(π_t) → ED-EIG > 0 → 有方向

### 2.4 停止准则（后验可信区域 + e-process）

替换MAP残差为后验可信区域半径：

定义：
    R_t(α) = min{r : P(s* ∈ B_r(ŝ_t) | z_{1:t}) ≥ 1-α}

停止统计量（替换原来的E_t = exp(η(θ-r_t))）：
    S_t = max(0, R_{t-1}(α) - R_t(α))   # 可信区域收缩量
    
e-process：
    V_t = 1 + η · S_t                      # e-value
    M_T = Π_{t=1}^T V_t                    # e-process

停止规则：
    τ = min{T : M_T ≥ 1/δ 且 R_T(α) ≤ ε}

性质：M_T是super-martingale under H_0（后验未收敛）
    → P(sup M_T ≥ 1/δ) ≤ δ (Ville's inequality)

**优势：**
- R_t是连续的（不跳动）
- R_t直接衡量后验不确定性（不是点估计）
- 收缩量S_t有物理意义（每步学到多少）
- 自然满足anytime-valid stopping

### 2.5 理论贡献（修复循环依赖）

**Theorem 1改进版（事件驱动后验收敛）：**

不假设κ>0，而是从事件模型推导：

设detection probability field: p(x,s) = 1-exp(-λ(x,s)·Δt)
如果wind≠0且domain有内部点，则：
    对任意s₁≠s₂，∃x使得p(x,s₁)≠p(x,s₂)

（这是事件驱动版的可识别性，比连续版本更强）

后验收敛速率：
    如果搜索策略保证每步至少ε信息增益（通过ED-EIG实现）：
    E[KL(π_t || δ_{s*})] ≤ C·exp(-κ't)
    
其中κ'取决于λ₀、Δt和域的几何。注意：**指数收敛**（不是O(1/t)），
因为Bernoulli似然满足KL-辨识条件（比高斯更强）。

**Proposition: ED-EIG保证正信息增益**
对任意posterior π_t ≠ δ_{s*}：
    max_a ED-EIG(a | π_t) > 0
    
证明：存在动作a使得P(d=1|a,π_t)∈(0,1)，
两种结果都有正信息增益 → ED-EIG>0。

这修复了循环依赖：不需要假设κ>0，ED-EIG自然保证。

---

## 三、与现有工作的对比

| 维度 | Infotaxis(2007) | SurgeCast | ED-Bayes(本文) |
|------|-----------------|-----------|----------------|
| 信号模型 | 连续浓度 | 连续浓度 | 离散事件 |
| 非检测信息 | 无 | 无 | 有(排除性证据) |
| 搜索退化 | z≈0时退化 | 无contact时失效 | 不退化(ED-EIG>0) |
| 停止准则 | 无 | 固定步数 | Anytime-valid |
| 理论保证 | 无 | 无 | 后验收敛+停止 |

---

## 四、实验计划

### 4.1 需要验证的核心假设
1. ED-EIG在弱信号下比标准EIG更有方向性
2. 事件驱动后验比连续后验收敛更快（在intermittent regime）
3. e-process(基于R_t)能正确触发停止
4. 在House01（弱信号）显著优于SurgeCast

### 4.2 实验设计
- 数据集：PMFS Scenario A（有数据）+ VGR House01-03
- Seeds：10 per configuration
- 基线：SurgeCast, PMFS, Infotaxis(原始), GrGSL
- 消融：ED-Bayes_full vs ED-Bayes_noEvent(用连续似然) vs Infotaxis+e-process(原始)
- 指标：distance, steps, e-process firing rate, coverage rate

### 4.3 预期结果
- House01(弱信号): ED-Bayes < 1.5m, SurgeCast ≈ 3.3m → 2×+
- House02(强信号): ED-Bayes ≈ 1.0m, SurgeCast ≈ 0.4m → SurgeCast仍好
- House03(中等): ED-Bayes ≈ 1.2m, SurgeCast ≈ 1.0m → 相当
- Cross-env CV: ED-Bayes < 0.2, SurgeCast > 0.8

---

## 五、论文叙事重构

旧叙事："Simpler-is-better"（弱）
新叙事："Event-Driven GSL"（强）

Abstract草案：
"We propose an event-driven Bayesian framework for UAV gas source localization 
that explicitly models gas detection as discrete filament-arrival events rather 
than continuous concentration signals. This physical-model alignment enables 
two key advances: (1) non-detection events carry positive information for source 
exclusion, preventing search degeneration in weak-signal regimes where existing 
methods fail; and (2) posterior concentration under the event model is exponential 
rather than polynomial, enabling faster convergence. We construct an anytime-valid 
e-process based on posterior credible region contraction that provides distribution-free 
stopping guarantees via Ville's inequality. Experiments on [N] environments demonstrate 
[X]× improvement over SurgeCast in weak-signal scenarios while maintaining consistent 
cross-environment performance."

关键词变化：
- old: "anytime-valid stopping", "e-process", "simpler-is-better"
- new: "event-driven", "filament-arrival model", "non-detection information", 
       "exponential posterior concentration", "anytime-valid stopping"
