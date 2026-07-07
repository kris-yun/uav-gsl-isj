# IEEE Sensors Journal 理论充分性评估报告

**论文题目**：*Non-Detection Is Information: Event-Driven Bayesian Inference for UAV Gas Source Localization*  
**评估角色**：IEEE Sensors Journal (ISJ) 资深副主编  
**评估日期**：2026-07-04  
**评估对象**：UAV gas source localization (GSL) 论文的理论框架  

---

## 0. 执行摘要

### 总体判断

**当前理论尚未达到 8.5/10。**

我给当前版本的理论完整度评分为：

| 维度 | 评分 | 判断 |
|---|---:|---|
| 核心洞察新颖性 | 8.5/10 | “non-detection is information” 是好切口，符合 GSL 的间歇 plume 物理特性 |
| 数学陈述清晰度 | 7.5/10 | 多数定理形式清楚，但若干量纲、KL方向、极限条件需修正 |
| 证明严谨性 | 6.5/10 | Theorem 1 最强；Theorem 1c、2、2b、2c、4 多为 sketch |
| ISJ审稿说服力 | 7.2/10 | 对普通 ISJ GSL 论文已较强，但“8.5级理论论文”还差关键闭环 |
| 与实验/物理模型连接 | 7.0/10 | Bridge theorem 方向正确，但 TV bound 与 GADEN/real plume 的假设要更具体 |
| 停止准则理论有效性 | 6.5/10 | e-process 是亮点，但必须处理 adaptive design 与 composite/data-dependent null |

**综合评分：7.3/10。**  
若将 Theorem 1、1b、3、e-process 停止规则补成可检查证明，删除或降格 Theorem 2b 的强相变表述，整体可到 **8.0/10**。  
若再补上 finite-grid posterior contraction、misspecification robustness 和 continuous-sensor lower bound，才有机会达到 **8.5/10**。

### 一句话结论

这套理论已经有“ISJ可投”的雏形，但还不是“ISJ审稿人无法轻易击穿”的理论体系。最大风险不是没有定理，而是**定理太多、若干关键定理仍是启发式，且最有攻击性的 claim（binary vs continuous divergence、phase transition、e-process stopping）恰好证明最弱**。

---

## 1. 当前理论是否达到 8.5/10？

### 1.1 未达到。差距主要在四处

#### 差距一：核心信息量定义需要更精确

Theorem 1 定义：

```math
\mathcal{I}_{\mathrm{nd}}
= \mathrm{KL}(\pi\|\pi^{(0)})
= \Delta t\,\mathbb{E}_\pi[\lambda]
+ \log \mathbb{E}_\pi[e^{-\lambda\Delta t}]
```

这个 closed form 是正确的，但审稿人会立刻问：

> 你为什么用 `KL(prior || posterior)`，而不是 Bayesian surprise 常用的 `KL(posterior || prior)`？

这不是致命错误，但必须正面处理。建议在正文中区分：

- **exclusion information**：`KL(prior || posterior)`，衡量一次 non-detection 从 prior 中排除多少高-rate 假设；
- **Bayesian surprise**：`KL(posterior || prior)`，衡量观测后 posterior 本身偏移多少；
- **mutual information contribution**：观测前对 `d=0/1` 取期望后的信息增益。

最好给出三者的小 `\Delta t` 展开，说明它们在 leading order 上都与 `Var_\pi[\lambda]` 同阶。这样 Theorem 1 才不会被审稿人抓住“你定义的信息不是标准信息增益”。

#### 差距二：Theorem 1c 的极限结论目前不够安全

当前 claim：

```math
\lim_{\bar{\lambda}\to 0}
\mathcal{I}_{\mathrm{bin}}/
\mathcal{I}_{\mathrm{cont}}
= \infty
```

这是最危险的定理之一。若 continuous model 是 additive Gaussian concentration：

```math
z = \kappa_c \lambda + \varepsilon,\quad
\varepsilon\sim N(0,\sigma^2)
```

那么在所有候选 rate 同比例缩小时：

```math
\mathcal{I}_{\mathrm{cont}} = O(\mathrm{Var}[\lambda]),
\qquad
\mathcal{I}_{\mathrm{bin}} = O(\Delta t^2\mathrm{Var}[\lambda]).
```

两者比值通常是常数级，不会自动趋于无穷。  
该定理只有在明确引入 **sensor floor / threshold censoring / low-SNR concentration clipping / continuous model discards zeros** 的假设时才可能成立。

所以 Theorem 1c 不能以当前形式进入主文。它需要改成：

> Under a limit-of-detection continuous sensor model where sub-threshold concentrations are censored to an indistinguishable zero observation, the binary event likelihood retains source-dependent non-detection likelihood whenever candidate rates differ, while the censored continuous likelihood collapses; hence the information ratio diverges under specified censoring asymptotics.

如果不愿引入 censoring 模型，则应把结论降为：

> Binary event inference is not universally more informative than continuous inference; it is more robust under intermittent plume contact and sensor floor conditions.

#### 差距三：收缩定理还不是可审计证明

Theorem 2 给出：

```math
c =
\frac{\lambda_0^2\ell^2(1-\alpha_w^2)\Delta t}
{2(1+\lambda_{\max}\Delta t)}
```

但当前证明 sketch 跨越了太多步骤：

1. 从 Bernoulli likelihood 的 score 到 Fisher information；
2. 从 local information 到 posterior contraction；
3. 从 posterior contraction 到 `R_k^2` 下降；
4. 从 adaptive UAV trajectory 到 persistent excitation；
5. 从 particle approximation 到 `C_noise/\sqrt{N_p}`。

这些步骤每一步都需要条件。现在的写法像“把标准定理名字串起来”，不是 ISJ 审稿人可检查的 proof。

尤其要补：

- `x_k` 是 adaptive 且由历史数据决定，证明需要 predictable design 条件；
- `D^2(\pi)` 如何由具体 policy 保证非零；
- Bernoulli likelihood 在 `p≈0` 或 `p≈1` 时的曲率退化如何处理；
- `c` 的量纲是否与 exponent 匹配；
- `\alpha_w` 接近 1 时 rate 可能接近 0，是否会导致 lower bound 失效。

#### 差距四：e-process 停止准则必须处理 composite null

Anytime-valid e-process 是好工具，但 reviewer 会问：

> 你的 null 是什么？如果 null 或 alternative 是由 posterior/MAP 事后选择的，supermartingale 还成立吗？

如果 `M_t` 是：

```math
M_t =
\prod_{k=1}^t
\frac{P(d_k|x_k,\hat{s}_k)}
{P(d_k|x_k,s_0)}
```

而 `\hat{s}_k` 是 data-dependent，则需要证明 numerator 是 predictable mixture / prequential alternative，否则简单 likelihood ratio 的 e-value 论证不成立。

更安全的 ISJ 写法是：

- 对有限网格 `\mathcal{S}`，为每个固定 `s_0` 构造 e-process；
- 对 complement region `H_0: s^*\notin B(\hat{s}_t,\varepsilon)` 使用 mixture e-process 或 union bound；
- stopping rule 写成：

```math
\tau =
\inf\left\{
t:
\mathrm{diam}_{1-\eta}(\pi_t)\le \varepsilon
\ \text{and}\
E_t(H_0)\ge 1/\delta
\right\}.
```

这样才是真正的 anytime-valid source-localization stopping，而不是 textbook likelihood ratio 的直接套用。

---

## 2. 逐个定理审核

### 2.1 Theorem 1：NDI 精确形式

**当前评分：9/10**  
**ISJ状态：rigorous enough，但需澄清信息定义。**

#### 优点

- closed-form 正确；
- 非负性可由 Jensen 推出；
- “zero iff `\lambda` is prior-a.s. constant” 是核心 insight；
- 该定理是全文最稳的数学结果。

#### 主要风险

当前 `\mathcal{I}_{nd}` 是：

```math
\mathrm{KL}(\pi\|\pi^{(0)})
```

而不是标准 posterior surprise：

```math
\mathrm{KL}(\pi^{(0)}\|\pi).
```

这会引发“你是不是重新定义了 information 以服务叙事”的质疑。

#### 修改建议

保留 Theorem 1，但改名为：

> Theorem 1. Exact exclusion information of a non-detection event.

并增加一个 corollary：

```math
\mathrm{KL}(\pi^{(0)}\|\pi)
=
-\Delta t\,\mathbb{E}_{\pi^{(0)}}[\lambda]
-\log \mathbb{E}_{\pi}[e^{-\lambda\Delta t}],
```

且

```math
\mathrm{KL}(\pi\|\pi^{(0)})
=
\frac{\Delta t^2}{2}\mathrm{Var}_\pi[\lambda]
+O(\Delta t^3),
```

```math
\mathrm{KL}(\pi^{(0)}\|\pi)
=
\frac{\Delta t^2}{2}\mathrm{Var}_\pi[\lambda]
+O(\Delta t^3).
```

这样 reviewer 即使质疑 KL 方向，也不会伤到核心结论。

---

### 2.2 Theorem 1b：Pinsker 下界

**当前评分：8/10**  
**ISJ状态：基本可用，但证明要补成 lemma 级。**

#### 优点

```math
\mathcal{I}_{\mathrm{nd}}
\geq
\frac{\sigma^2\Delta t^2}
{2(1+\lambda_{\max}\Delta t)}
```

这个 bound 与 Theorem 1 的核心叙事一致：non-detection 的信息强度由 posterior 下 rate 的方差控制。

#### 风险

当前证明 sketch 写：

> `f''(t)\geq\sigma^2/(1+\lambda_{\max}t)^2`

这一步不是显然成立。tilted distribution 下的 variance 下界需要单独证明。审稿人会要求：

- bounded exponential tilting 如何影响 variance；
- 该 lower bound 是否对任意 `\lambda\in[0,\lambda_{\max}]` 成立；
- 常数 `1+\lambda_{\max}\Delta t` 是否 tight。

#### 修改建议

增加一个独立 lemma：

> Lemma. Let `Y\in[0,b]`, `\sigma^2=Var(Y)`, and define the exponentially tilted distribution `dP_t \propto e^{-tY}dP`. Then for `t\ge0`,
> `Var_t(Y)\ge C(b,t)Var(Y)`.

若当前常数证明困难，宁可使用更保守但容易证明的：

```math
\mathrm{Var}_t(Y)\ge e^{-bt}\mathrm{Var}(Y)
```

则得到：

```math
\mathcal{I}_{nd}
\ge
\frac{1-e^{-b\Delta t}(1+b\Delta t)}
{b^2}
\sigma^2
```

或小步长版本：

```math
\mathcal{I}_{nd}
\ge
\frac{1}{4}\sigma^2\Delta t^2,
\quad
\lambda_{\max}\Delta t\le c_0.
```

ISJ 不要求最 tight，但要求证明不可疑。

---

### 2.3 Theorem 1c：二值 vs 连续模型比较

**当前评分：5.5/10**  
**ISJ状态：不能以当前强形式进入主文。**

#### 主要问题

该定理目前是“叙事上最有杀伤力、数学上最脆弱”的部分。  
若 reviewer 用 additive Gaussian continuous sensor model 反例攻击，当前 claim 很难守住。

#### 逻辑漏洞

“`\bar{\lambda}\to0`” 有多种含义：

1. 所有候选源的 rate 同比例缩小；
2. UAV 离所有候选源都远；
3. 均值低但候选之间 rate contrast 仍存在；
4. 传感器读数被 threshold/censor 到 0。

只有第 3/4 种情况下 binary event model 才可能显著优于 continuous model。  
若是第 1 种，binary 和 continuous 的信息都随 `Var[\lambda]` 消失，ratio 不一定发散。

#### 必须修改

建议将 Theorem 1c 拆成两个结果。

**Proposition 1c-A：No universal dominance**

说明在 additive Gaussian concentration model 下：

```math
z=\kappa\lambda+\varepsilon
```

binary 与 continuous 的 leading-order 信息比值是常数级，不能声称 universal divergence。

**Theorem 1c-B：Dominance under detection-floor censoring**

定义 censored continuous observation：

```math
y =
\begin{cases}
0, & z<\tau,\\
z, & z\ge\tau.
\end{cases}
```

在 `P(z<\tau|s)\to1` 且 continuous pipeline 将所有 sub-threshold readings 视为同一 zero observation 时：

```math
\mathcal{I}_{cont}\to0,
```

而 event likelihood 仍保留：

```math
P(d=0|s)=e^{-\lambda(x,s)\Delta t}.
```

若候选源之间 `Var_\pi[\lambda(x,s)]` 不为零，则 non-detection 信息为：

```math
\mathcal{I}_{bin}
=
\frac{\Delta t^2}{2}Var_\pi[\lambda]
+O(\Delta t^3).
```

这样 ratio divergence 才成立。

---

### 2.4 Theorem 2：接触条件后验收缩 / 显式收缩率

**当前评分：6.5/10**  
**ISJ状态：需要更强证明。**

#### 优点

这个定理非常重要，因为它试图把 “non-detection is information” 从单步信息推广到 localization convergence。没有 Theorem 2，全文会停留在“信息量很漂亮，但不一定能定位”的层面。

#### 主要漏洞

1. **persistent excitation 没有被证明**  
   收缩需要 UAV 持续访问能区分候选源的位置。若 policy 一直停在 `Var_\pi[\lambda]\approx0` 的区域，Theorem 1 也救不了收敛。

2. **adaptive design 未处理**  
   `x_k` 由历史观测决定。需要使用 martingale / predictable likelihood ratio，而不能直接套 IID posterior contraction。

3. **constant `c` 的来源不完整**  
   当前 `c` 从 score bound 跳到 log-Sobolev/telescoping，中间缺关键不等式。

4. **量纲疑问**  
   `D^2(\pi)` 的定义、`c` 的单位和 exponent 中的 `\Delta t` 是否匹配需要重新检查。

5. **contact-conditioned 的边界不清楚**  
   “intermittent plume contact” 是经验概念，定理中必须形式化为 hitting frequency / minimum information condition。

#### 建议改写

将 Theorem 2 改成 finite-state posterior contraction，更容易严谨：

设 source grid 为有限集合 `\mathcal{S}`。对任意错误源 `s\ne s^*`，定义累计 log-likelihood ratio：

```math
L_t(s)
=
\sum_{k=1}^t
\log
\frac{P(d_k|x_k,s^*)}
{P(d_k|x_k,s)}.
```

若 policy 满足：

```math
\sum_{k=1}^t
\mathrm{KL}
\left(
P_{s^*}(\cdot|x_k)
\|P_s(\cdot|x_k)
\right)
\ge
\gamma_t(s),
```

且 `\gamma_t(s)\to\infty`，则：

```math
\pi_t(s)
\le
\frac{\pi_0(s)}{\pi_0(s^*)}
\exp[-\gamma_t(s)+O_\mathbb{P}(\sqrt{\gamma_t(s)})].
```

再用 Bernoulli-Poisson likelihood 给出：

```math
\mathrm{KL}
\left(
\mathrm{Bern}(1-e^{-\lambda_1\Delta t})
\|
\mathrm{Bern}(1-e^{-\lambda_2\Delta t})
\right)
\ge
C(\Delta t,\lambda_{\max})(\lambda_1-\lambda_2)^2.
```

这样 Theorem 2 就会从 sketch 变成可审计证明。

---

### 2.5 Theorem 2b：相变

**当前评分：4.5/10**  
**ISJ状态：建议降为 heuristic / discussion，不要作为主定理。**

#### 主要问题

当前给出：

```math
r^*
=
\frac{\ell\log2}{\lambda_0\Delta t}
```

并声称存在：

1. exponential regime；
2. polynomial regime；
3. floor regime。

这个叙事很吸引人，但审稿人会问：

- 为什么 `\Delta t` 越小，floor `r^*` 反而越大？
- 如果总观测时间固定，减小 step size 不应导致物理定位下限变差；
- 这个 `r^*` 是 per-step detectability threshold，还是 total-time estimator lower bound？
- polynomial regime 的 `R_k\sim k^{-1/2}` 从哪个 recursion 推出？
- floor 是 sensor resolution、Bernoulli noise、模型 misspecification，还是 finite time effect？

#### 建议处理

不要把 Theorem 2b 放在主文定理区。改成：

> Proposition / Remark. A heuristic phase diagram of the ED-Bayes search process.

并明确写：

- `r^*` 不是 asymptotic localization floor；
- 它是 per-observation contrast scale；
- 随着累计观测次数增加，effective floor 应按 Fisher information 累积下降。

更严谨的替代结果是：

```math
\mathrm{CRLB}_T
\asymp
\frac{1}
{\sum_{k=1}^T I(s^*;x_k)}
```

其中

```math
I(s^*;x_k)
\propto
\Delta t
\frac{\|\nabla_s\lambda(x_k,s^*)\|^2}
{\lambda(x_k,s^*)}
```

在 small-rate Bernoulli-Poisson 近似下成立。  
这个比“相变”更安全。

---

### 2.6 Theorem 2c：Minimax 下界

**当前评分：6/10**  
**ISJ状态：有价值，但当前形式不够严谨。**

#### 当前 claim

```math
\inf_{\hat{s}}\sup_{s^*}
\mathbb{E}\|\hat{s}_T-s^*\|^2
\geq
\frac{|\mathcal{X}|}
{2T\lambda_0\Delta t(1-\alpha_w^2)\ell^2}
```

#### 主要问题

1. **量纲疑问**  
   如果 `|\mathcal{X}|` 是面积，右边除以 `\ell^2` 后变成无量纲，不像 MSE。
   除非 `|\mathcal{X}|` 表示 number of grid cells，否则公式需要重写。

2. **adaptive observation 的 Fano 需要处理**  
   UAV 的 `x_t` 由历史观测决定。Fano 下界可做，但必须限制 policy class 或使用 chain rule：

   ```math
   I(s;D_{1:T},X_{1:T})
   =
   \sum_{t=1}^T
   I(s;D_t|H_{t-1},X_t).
   ```

3. **wind factor 可疑**  
   `(1-\alpha_w^2)` 出现在 denominator 还是 numerator 需要重新推导。风越强时可辨识性通常增强，但也可能产生 anisotropic ambiguity。不能只凭直觉放一个因子。

#### 修改建议

将其改为 finite packing lower bound：

```math
\inf_{\hat{s}}
\sup_{s^*}
\mathbb{E}\|\hat{s}-s^*\|^2
\ge
c\epsilon^2
\left[
1-
\frac{
T K_{\max}(\epsilon)+\log2
}
{\log M(\epsilon)}
\right],
```

其中 `M(\epsilon)` 是 `\epsilon`-packing number，`K_{\max}(\epsilon)` 是任意两个间距 `\epsilon` 的源在单步观测下的最大 KL。  
这样 reviewer 能看到标准 Fano 结构，而不是一个可能量纲错误的 closed form。

---

### 2.7 Theorem 3：Bridge 定理（GADEN → Poisson）

**当前评分：7.5/10**  
**ISJ状态：方向很强，但“9/10”偏乐观。**

#### 优点

这个 theorem 是本文最有 ISJ 味道的理论贡献之一。它把：

- physical simulator；
- filament arrival；
- Poisson event model；
- Bayesian inference likelihood；

连在一起。ISJ 审稿人会喜欢这种“工程物理 + 可计算误差”的桥接。

#### 当前风险

```math
\mathrm{TV}
(P_{\mathrm{GADEN}}\|P_{\mathrm{Poisson}})
\le
\varepsilon_1+\varepsilon_2+\varepsilon_3
```

这个式子需要非常小心。

1. **GADEN 不是天然 probability law**  
   GADEN 是仿真器；要先定义随机性来自哪里：release process、turbulent perturbation、sensor noise、random start，还是 repeated simulation seeds。

2. **TV over trajectory 通常随 T 累积**  
   如果每步误差为 `\epsilon`，trajectory-level TV 往往是 `O(T\epsilon)` 或通过 mixing/blocking 得到更复杂形式。当前 `\varepsilon_1,\varepsilon_2,\varepsilon_3` 的 `T` 依赖要统一。

3. **temporal correlation term 可疑**  
   `\varepsilon_1=\sqrt{\Delta t/(2\tau_{\mathrm{corr}})}` 表示 `\Delta t` 越小误差越小，但若采样间隔远小于 correlation time，观测相关性更强，Poisson independent approximation 反而更差。需要解释它是 blocking 后的误差，还是 single-block approximation。

4. **wind linearization term**  
   `\varepsilon_3=T\alpha_w^2/4` 在强风下可能很大。若 `T` 稍大，该 bound 很快 vacuous。

#### 修改建议

将 Bridge theorem 改为 block-level：

1. 定义 block length：

```math
B\Delta t \ge c\tau_{\mathrm{corr}}.
```

2. 在 block observation 上建立：

```math
\tilde{d}_j
=
\mathbf{1}\{\text{at least one hit in block }j\}.
```

3. 证明 block-level Bernoulli likelihood：

```math
P(\tilde{d}_j=1|s)
=
1-\exp[-\bar{\lambda}_j(s)B\Delta t]
+O(\epsilon_{\mathrm{mix}}+\epsilon_{\mathrm{disc}}+\epsilon_{\mathrm{wind}}).
```

4. 再用 posterior robustness lemma：

```math
\mathrm{TV}(\pi_T^{GADEN},\pi_T^{Poi})
\le
C_T
\sum_{j=1}^{T/B}
\epsilon_j.
```

这样既更真实，也能解释为什么要 block-average。

---

### 2.8 Theorem 4：四阶段搜索时间上界

**当前评分：6.5/10**  
**ISJ状态：适合作为 algorithmic justification，不适合作为核心定理。**

#### 优点

四阶段结构很适合论文叙事：

1. exploration；
2. contact conditioning；
3. upwind convergence；
4. e-process stopping。

它让方法看起来不是单纯 Bayesian update，而是面向 UAV GSL 的完整 strategy。

#### 风险

当前 bound：

```math
\mathbb{E}[T_{\mathrm{total}}]
\leq
O(|\mathcal{X}|/(\lambda_0\ell^2))
+O(1/(\lambda_0\ell\Delta t))
+O(\log(\ell/\varepsilon)/\kappa)
+O(\log(1/\delta)/\kappa_e)
```

问题是：

- stage policy 没有完全形式化；
- obstacles / reachable free space 未进入 bound；
- first contact time 对 plume intermittency 和 wind field 非常敏感；
- `\kappa` 和 `\kappa_e` 不是可由环境参数直接计算的常数；
- big-O 项叠加容易被 reviewer 认为是“工程直觉包装”。

#### 修改建议

将 Theorem 4 改为：

> Proposition. Under idealized rectangular free-space and persistent wind assumptions, the four-stage ED-Bayes policy has the following decomposed expected-time upper bound.

主文只保留 scaling intuition，详细 proof 放 appendix。不要让它承担主贡献。

---

## 3. 哪些证明 rigorous enough for ISJ？

### 3.1 可以进入主文的结果

| 结果 | 当前可投程度 | 建议 |
|---|---|---|
| Theorem 1 NDI exact form | 高 | 主文核心定理，补 KL 方向说明 |
| Small-`\Delta t` expansion | 高 | 作为 corollary 强化 `Var_\pi[\lambda]` 叙事 |
| Theorem 1b Pinsker lower bound | 中高 | 补 exponential tilting variance lemma |
| e-process simple fixed-null validity | 中高 | 可放 appendix，但不能作为最终 stopping 的全部证明 |

### 3.2 需要更强证明的结果

| 结果 | 问题 | 修改优先级 |
|---|---|---:|
| Theorem 1c binary vs continuous | 极限条件不清，可能不成立 | P0 |
| Theorem 2 contraction | adaptive posterior contraction 缺 proof | P0 |
| Theorem 2b phase transition | 启发式，`r^*` 解释不稳 | P0/P1 |
| Theorem 2c minimax | 量纲、adaptive Fano、wind factor | P1 |
| Theorem 3 bridge | 需要 block/mixing/misspecification proof | P1 |
| Theorem 4 search time | policy 与 constants 未形式化 | P2 |

### 3.3 可能的逻辑漏洞清单

1. **NDI 的 KL 方向与 standard information gain 不一致。**
2. **`I_bin/I_cont -> infinity` 不是无条件成立。**
3. **non-detection 有信息的前提是 `Var_\pi[\lambda(x,s)]>0`，不是任意 no-gas observation 都有信息。**
4. **posterior contraction 需要 policy 保证 persistent excitation，否则后验可能不收缩。**
5. **phase transition 中的 `r^*` 可能只是 per-step contrast scale，不是 localization floor。**
6. **minimax bound 可能量纲错误。**
7. **e-process 若使用 data-dependent MAP/null，需要重新构造为 valid prequential e-process。**
8. **GADEN-to-Poisson TV bound 若按 trajectory law 写，误差可能随 horizon 累积到 vacuous。**

---

## 4. ISJ 审稿人会问的 Top-5 问题及应对策略

### Q1. “你说 non-detection has information，但如果所有候选源的 `\lambda` 都接近 0，信息不是也接近 0 吗？”

**风险等级：致命。**

#### 最佳回答

承认：

> Correct. A non-detection is informative only when the candidate sources induce different expected hit rates at the query location.

然后强调真正结论：

```math
\mathcal{I}_{nd}
\approx
\frac{\Delta t^2}{2}
Var_\pi[\lambda(x,s)].
```

所以本文不是说“任何无气体读数都有信息”，而是说：

> 在 posterior 对候选源仍存在 rate contrast 的位置，`d=0` 是可量化的排除证据。

算法上必须配套：

```math
x_t \in \arg\max_x Var_{\pi_t}[\lambda(x,s)]
```

或至少保证 `Var_{\pi_t}[\lambda(x_t,s)]` 不长期为零。

---

### Q2. “你的 binary model 为什么比 continuous concentration model 更好？连续模型难道不能也利用 zero readings？”

**风险等级：致命。**

#### 最佳回答

不要声称 binary universally dominates continuous。改为：

> The advantage appears under intermittent plume contact and detection-floor conditions, where continuous concentration pipelines often collapse sub-threshold readings into non-informative zeros, whereas the event likelihood preserves the source-dependent probability of non-arrival.

需要在 theory 中列出三种 sensor model：

1. ideal additive Gaussian continuous model：binary 不一定更强；
2. threshold-censored continuous model：binary 有严格优势；
3. real MOX sensor with response lag/floor：binary event model 更稳健。

这会显得诚实，反而增强说服力。

---

### Q3. “你的后验收缩定理如何处理 adaptive UAV path？是不是偷偷用了 IID 假设？”

**风险等级：致命。**

#### 最佳回答

把证明改为 sequential likelihood ratio martingale。明确：

- `x_t` 是 `\mathcal{F}_{t-1}`-measurable；
- 条件在历史上的 Bernoulli likelihood 正确；
- 对每个错误源 `s`，LLR 的 drift 是条件 KL；
- 只要累计 KL 发散，posterior mass on `s` 指数衰减。

建议在主文给出 finite-grid theorem，因为它最容易让 ISJ 审稿人接受。

---

### Q4. “e-process stopping 的 null 是什么？你是否用数据选择了 null 或 alternative？”

**风险等级：致命。**

#### 最佳回答

不要用“MAP vs fixed `s_0`”作为最终停止定理。改为 source-region confidence sequence：

```math
H_0(r): s^*\notin B(\hat{s}_t,r).
```

对 finite grid complement 做 mixture e-process：

```math
E_t(H_0)
=
\sum_{s\notin B(\hat{s}_t,r)}
w_s
\prod_{k=1}^t
\frac{p(d_k|x_k,\tilde{s}_k)}
{p(d_k|x_k,s)}.
```

或使用 posterior credible set + e-value calibration 的两层停止规则。关键是保证每个 e-process 的 null 在构造前固定，或使用 valid mixture/union bound。

---

### Q5. “GADEN/真实气体羽流不是 Poisson independent hits。你的 Poisson model 是否只是方便假设？”

**风险等级：严重。**

#### 最佳回答

把 Bridge theorem 作为核心防线：

- 承认 raw high-frequency hits 有 temporal correlation；
- 使用 block-level event；
- 从 GADEN trajectory 估计 correlation time；
- 在 block observation 上拟合 Poisson arrival；
- 报告 calibration residual 与 posterior robustness bound。

需要新增一张实验图：

> empirical inter-hit time distribution vs fitted exponential / overdispersed Poisson。

如果数据明显 overdispersed，可扩展为 Cox process / negative-binomial arrival，但主算法仍用 Bernoulli event likelihood。

---

## 5. 理论的致命弱点

### 致命弱点不是 Theorem 1，而是从单步信息到全局定位的链条

当前最稳的是：

```math
d=0
\Rightarrow
\mathcal{I}_{nd}
\propto
Var_\pi[\lambda].
```

但论文要证明的是：

```math
d=0 \text{ 可用}
\Rightarrow
posterior 收缩
\Rightarrow
UAV 能定位
\Rightarrow
能 anytime-valid 停止。
```

这条链目前有三处断点：

1. **policy 是否保证观察到有 rate contrast 的位置？**
2. **posterior contraction 是否在 adaptive, intermittent, misspecified plume 下成立？**
3. **e-process stopping 是否针对 localization region 而非 fixed point hypothesis？**

如果这三点不补，审稿人会评价为：

> Interesting single-step information identity, but insufficient theory for UAV source localization.

---

## 6. 与已发表 GSL 文献理论深度对比

### 6.1 先纠正一个引用风险

用户列出的 “[Lilienthal 2023] Infotaxis, [Hernandez 2017] PMFS, [Burgues 2021]” 在文献归属上可能混淆。ISJ 审稿人会查引用，不能把非 ISJ 或不同方法错误归类为 ISJ 已发表 GSL 论文。

更稳妥的说法是：

- Infotaxis 的经典理论源头是 Vergassola et al., *Nature*, 2007，而不是 Lilienthal 2023；
- Hernandez-Bennetts/Monroy/Lilienthal/Gonzalez-Jimenez 2017 更常被引用于 GADEN / gas dispersion simulation 或 indoor GSL simulator 方向；
- PMFS / information-driven GSL 多见于 RA-L/TRO/robotics literature，不应随意标为 ISJ；
- Burgues 的 nano aerial vehicle GSL 工作主要是 empirical sensing/platform study，常见出处是 *Sensors* 2019，而非 IEEE Sensors Journal 2021。

如果论文中写“ISJ已发表的这些论文”，建议改成：

> representative GSL and mobile robot olfaction literature relevant to ISJ readers.

### 6.2 Infotaxis 理论深度

代表文献：Vergassola et al., “Infotaxis as a strategy for searching without gradients,” *Nature*, 2007。

#### 理论特点

- 使用 Poisson hit model；
- 以 posterior entropy reduction 作为 action objective；
- 理论洞察强：search without gradient；
- 有清晰的 information-theoretic objective；
- 但没有现代意义上的 posterior contraction theorem、finite-sample regret bound 或 anytime-valid stopping guarantee。

#### 理论深度评分

**7.5–8/10。**

它的深度来自物理直觉和信息论目标的统一，而不是严密收敛证明。本文若补全 Theorem 1 + finite-grid contraction + e-process confidence sequence，理论深度可以超过 Infotaxis 在 GSL 领域中的常规引用水平。

### 6.3 PMFS / information-driven GSL 理论深度

代表方向：probabilistic mapping、particle/dispersion simulation、gas+wind local measurements、mutual-information planning。

#### 理论特点

- 工程系统完整；
- wind 与 gas 局部观测融合充分；
- 通常有 probabilistic update 或 information value；
- 但多数理论停留在 likelihood/model construction 与 heuristic information objective；
- 缺少 closed-form non-detection information、posterior contraction、valid stopping。

#### 理论深度评分

**6.5–7/10。**

PMFS 的强项是工程现实性和 benchmark 表现，不是数学证明深度。本文只要把 Theorem 1/2/e-process 做扎实，理论维度会明显强于 PMFS 类论文。

### 6.4 Burgues 等 UAV / nano aerial vehicle 实证研究理论深度

代表方向：micro/nano aerial vehicle 搭载 gas sensor，利用 bout features、sensor derivative、local airflow 或 empirical behavior 做 GSL。

#### 理论特点

- 平台贡献强；
- sensor dynamics 处理具体；
- 实验系统可信；
- 理论多为 feature justification、empirical model 或 signal-processing heuristic；
- 很少提供 inference-level theorem。

#### 理论深度评分

**4.5–5.5/10。**

这类论文的 ISJ/Sensors 价值不在理论深度，而在 sensor-platform integration 和实验。本文如果主打理论，不应与其比“证明数量”，而应强调：事件化 likelihood 可以解释为什么这些 empirical bout/contact features 在 intermittent plume 下有效。

### 6.5 GADEN / simulator bridge 文献理论深度

代表方向：Monroy, Hernandez-Bennetts, Lilienthal, Gonzalez-Jimenez 等 GADEN simulator。

#### 理论特点

- 物理仿真与 robotics benchmark 价值高；
- 对 advection-diffusion、filament/plume realism 有建模；
- 主要目标是 simulation fidelity，不是 Bayesian inference theory；
- 通常不证明 localization posterior 的统计性质。

#### 理论深度评分

**6/10。**

本文的 Bridge theorem 若补严谨，会成为连接 GADEN 与 inference theory 的亮点。

### 6.6 对比结论

| 文献方向 | 理论深度 | 实验/工程深度 | 本文应如何定位 |
|---|---:|---:|---|
| Infotaxis | 7.5–8 | 6 | 用作 information-theoretic baseline；强调本文补了 non-detection 与 stopping |
| PMFS / information-driven GSL | 6.5–7 | 8.5 | 用作工程强基线；强调本文理论更可解释 |
| Burgues UAV empirical studies | 4.5–5.5 | 8 | 用作 sensor/platform 背景，不要声称理论对标 |
| GADEN simulator | 6 | 8 | 用 Bridge theorem 连接 simulator 与 event likelihood |
| 本文当前 | 7.3 | 待实验支撑 | 已超过多数 empirical GSL 理论，但未达强理论论文 |
| 本文目标版 | 8.5 | 需同步增强 | 可作为 ISJ 中理论贡献突出的 GSL 论文 |

---

## 7. 达到 8.5/10 的具体建议

### 7.1 必须加强的定理

#### P0-1：重写 Theorem 1c

当前强 claim 风险太大。建议改成：

1. 先承认 ideal continuous sensor 下无 universal dominance；
2. 再证明 detection-floor / censoring model 下 binary event dominance；
3. 用真实 MOX/GADEN 数据证明 sub-threshold readings 常见。

这是最值得优先修的定理，因为它支撑标题中的核心对比。

#### P0-2：补 finite-grid posterior contraction theorem

建议替换当前 Theorem 2 的抽象收缩率。主文给出：

> Under predictable adaptive sampling and cumulative pairwise KL separation, posterior mass outside the true source cell decays exponentially.

然后将 GSL-specific 部分放在 corollary：

> For the Poisson event likelihood, cumulative KL separation is lower bounded by accumulated squared rate contrast.

这比直接给一个 `c` 更稳。

#### P0-3：把 e-process 停止从 point test 改成 region confidence sequence

这是投稿时最容易被懂 sequential testing 的 reviewer 击穿的点。必须改。

#### P0-4：将 Theorem 2b 降格

相变可以作为 insight，但不能作为强定理。建议放到 discussion 或 appendix simulation-backed heuristic。

#### P1：Bridge theorem block 化

将 GADEN-to-Poisson 从 step-level independent approximation 改成 block-level event approximation。这个会显著增强物理可信度。

---

### 7.2 建议新增的理论结果

#### 新结果一：双 KL 方向一致性

证明：

```math
\mathrm{KL}(\pi\|\pi^{(0)})
=
\frac{\Delta t^2}{2}Var_\pi[\lambda]
+O(\Delta t^3),
```

```math
\mathrm{KL}(\pi^{(0)}\|\pi)
=
\frac{\Delta t^2}{2}Var_\pi[\lambda]
+O(\Delta t^3).
```

作用：堵住 KL 方向质疑。

#### 新结果二：finite-grid log-likelihood contraction

证明：

```math
\mathbb{E}_{s^*}
\left[
\log
\frac{P(d|x,s^*)}
{P(d|x,s)}
\right]
\ge
C(\Delta t,\lambda_{\max})
(\lambda(x,s^*)-\lambda(x,s))^2.
```

然后累计得到 posterior contraction。

作用：把单步 NDI 变成定位收敛。

#### 新结果三：policy informativeness lemma

证明或假设一个 search policy 满足：

```math
\sum_{k=1}^T
Var_{\pi_k}[\lambda(x_k,s)]
\ge
\rho T \Phi(\pi_T).
```

其中 `\Phi` 是 posterior diameter 或 entropy。  
作用：说明算法不会长期采样无信息位置。

#### 新结果四：censored continuous lower/impossibility result

在 continuous sensor floor 下证明：

```math
I_{\mathrm{cont}}=0
```

或低于某个 bound，而 event model 仍有：

```math
I_{\mathrm{event}}
\asymp
\Delta t^2 Var[\lambda].
```

作用：让 binary vs continuous claim 站稳。

#### 新结果五：misspecification robustness

若 true GADEN block likelihood `P` 与 Poisson event likelihood `Q` 满足：

```math
\sup_s TV(P_s,Q_s)\le\epsilon,
```

则 posterior 或 stopping error 增加：

```math
O(T\epsilon)
```

或 block-level `O((T/B)\epsilon)`。

作用：Bridge theorem 真正服务于 inference guarantee。

---

### 7.3 叙事结构调整

当前理论点太多，建议从“八个定理”压缩为“三主定理 + 三个补充命题”。

#### 建议主文结构

**Theorem 1：Non-detection exclusion information**

- exact form；
- small-`\Delta t` expansion；
- `Var_\pi[\lambda]` interpretation；
- KL-direction clarification。

**Theorem 2：Posterior contraction under event-rate contrast**

- finite-grid sequential contraction；
- adaptive design 处理；
- GSL-specific Bernoulli-Poisson KL lower bound。

**Theorem 3：Anytime-valid localization stopping**

- source-region confidence sequence；
- mixture/union e-process；
- adaptive path validity。

**Proposition 1：Binary advantage under censored continuous sensing**

- 不作为 universal dominance；
- 作为 sensor-floor regime result。

**Proposition 2：GADEN-to-event bridge**

- block-level Poisson approximation；
- empirical calibration。

**Remark / Heuristic：Phase diagram**

- 只作为 intuition；
- 不声称 rigorous phase transition。

#### 推荐标题叙事

不要把论文写成：

> We propose many theoretical guarantees for UAV GSL.

应写成：

> Gas absence is not missing data. Under an event-arrival model, a non-detection is a likelihood event that excludes high-rate source hypotheses. We quantify this effect, prove posterior contraction when the UAV samples rate-contrastive locations, and provide an anytime-valid stopping rule for source localization.

这个叙事更干净，也更像强 ISJ 论文。

---

## 8. 分级修改清单

### P0：不改不建议投稿

| # | 问题 | 修改 |
|---|---|---|
| 1 | Theorem 1c 极限结论可能不成立 | 引入 censored continuous model，或降级为条件优势 |
| 2 | Theorem 2 收缩证明过于 sketch | 改为 finite-grid sequential posterior contraction |
| 3 | e-process stopping 存在 data-dependent null 风险 | 改成 region confidence sequence / mixture e-process |
| 4 | `non-detection always informative` 表述过强 | 明确条件是 `Var_\pi[\lambda(x,s)]>0` |
| 5 | Theorem 2b 相变像启发式 | 从主定理降为 discussion/remark |

### P1：强烈建议修改

| # | 问题 | 修改 |
|---|---|---|
| 1 | Pinsker lower bound 证明不足 | 加 exponential tilting variance lemma |
| 2 | Minimax 下界量纲和 adaptive Fano 不清 | 改为 packing/Fano 标准形式 |
| 3 | Bridge theorem step-level independence 太强 | 改为 block-level approximation |
| 4 | 四阶段上界 constants 不可计算 | 降低 claim，用 idealized proposition |
| 5 | 文献归属可能被抓错 | 不要把非 ISJ 论文称为 ISJ 已发表 |

### P2：增强说服力

- 增加一张 theorem dependency graph；
- 将所有 assumptions 编号并集中列出；
- 把 `\lambda_0,\ell,\alpha_w,\Delta t` 的单位写清；
- 给出一个 two-source toy example 可视化 `d=0` posterior shrinkage；
- 在 appendix 放完整 proof，主文只留核心定理。

---

## 9. 最终评分预测

### 当前版本

**7.3/10。**

审稿结果预测：

- 如果实验非常强：major revision；
- 如果实验一般：reject / reject and resubmit；
- 如果理论 claim 不降调：很可能被理论型 reviewer 击穿。

### 完成 P0 后

**8.0/10。**

可以达到 ISJ “理论贡献明显强于一般 GSL 工程论文”的水平。

### 完成 P0 + P1 + 新增结果二/三/四

**8.5/10。**

这时论文的理论贡献可以概括为：

1. exact non-detection information identity；
2. event-rate-contrast posterior contraction；
3. valid localization stopping；
4. censored continuous sensing 下的 binary advantage；
5. GADEN/physical plume 到 event likelihood 的 bridge。

这才是足以支撑标题 *Non-Detection Is Information* 的完整理论闭环。

---

## 10. 参考核查链接

以下链接用于校准 GSL/robot olfaction 文献背景与理论深度，正式投稿前请再次用 IEEE Xplore / CrossRef / DOI 核验：

- Vergassola, Villermaux, Shraiman, “Infotaxis as a strategy for searching without gradients,” *Nature*, 2007: https://www.nature.com/articles/nature05464
- Monroy, Hernandez-Bennetts, Fan, Lilienthal, Gonzalez-Jimenez, “GADEN: A 3D Gas Dispersion Simulator for Mobile Robot Olfaction in Realistic Environments,” *Sensors*, 2017: https://www.mdpi.com/1424-8220/17/7/1479
- Burgues, Marco, “Smelling Nano Aerial Vehicle for Gas Source Localization and Mapping,” *Sensors*, 2019: https://www.mdpi.com/1424-8220/19/3/478
- Hayes, Martinoli, Goodman, “Distributed Odor Source Localization,” *IEEE Sensors Journal*, 2002: https://ieeexplore.ieee.org/document/1183505

---

## 11. 副主编最终意见

这篇论文真正有价值的不是“用了 e-process”，也不是“又提出一个 UAV 搜索策略”，而是把 GSL 中长期被工程上忽略的事实形式化了：

> 在间歇羽流中，未检测到气体不是空白观测，而是一个具有源依赖 likelihood 的事件。

这个 insight 足以支撑一篇好 ISJ 论文。  
但要达到 8.5/10，必须克制：少放几个漂亮但未证实的定理，多把三条主链证明扎实。

**建议的投稿前最低理论门槛：**

1. Theorem 1 + 双 KL corollary 完整证明；
2. Theorem 1c 改为条件优势，不再 universal overclaim；
3. finite-grid adaptive posterior contraction theorem；
4. valid source-region e-process stopping；
5. GADEN block-level bridge 或至少 empirical calibration。

做到这五点，理论部分才会从“有想法”变成“审稿人很难推翻”。
