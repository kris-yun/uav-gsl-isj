# M1 实现说明与物理适用边界

## 实际交付状态

本目录包含**可训练、可存取、可逐步采样的 CPU 参考实现**，不是接口占位。主生成器使用 34 个可微非线性源坐标/相对位置/风/前一观测/动作/机制特征以及可训练线性读出。它不是完整扩散神经网络，也不是 GADEN 的替代 CFD。选择该实现，是为了先独立核验新的监督算子、联合归一化、反证规划接口和证据回放，而不把网络规模混入算子验证。

实际训练通过 SciPy L-BFGS-B 更新读出参数；源码给出源导数和参数—源混合导数的解析表达。`Aprime`、`B`、`Bprime` 是三个真正不同的训练路径。原生 PMFS `A` 由外部官方程序及冻结结果适配器提供，不能把此受控模型叫作原生 PMFS。

## 跨领域母算法和迁移

| 来源 | 原领域及实际机制 | 本工程迁移内容 | 尚未移植部分 |
|---|---|---|---|
| ICML 2025, *Conditioning Diffusions Using Malliavin Calculus*, PMLR 267 | 随机分析/条件扩散：将难微分条件事件的导数转为 Gaussian/Malliavin 积分分部权重 | 自然模拟器噪声上的最小范数 lift、含散度的权重 `xi @ v - div(v)`，监督源位置引起的观测证据变化 | 通用高维 SDE 梯度求解、原生粒子模拟器的自动微分接口 |
| ACM TOG / SIGGRAPH Asia 2025, *Automatic Sampling for Discontinuities in Differentiable Shaders*, DOI `10.1145/3763291` | 可微渲染：定位硬分支边界，强制两侧执行轨迹，计入边界测度而非忽略跳跃 | 一维自然高斯噪声门的根定位、两侧观测、coarea 密度权重；受控源依赖路由门确有该跳跃 | 原作者的多维 shader 自动程序变换、所有障碍/碰撞门的自动发现及采样概率校正 |

原文入口：
- https://proceedings.mlr.press/v267/pidstrigach25a.html
- https://arxiv.org/html/2504.03461v2
- https://yashbelhe.github.io/asd/index.html
- https://github.com/yashbelhe/ASD

这里是**数学算子的特例迁移和二次改造**，没有声称完整复现两篇母论文。受控一维边界实现不是把 ASD 的全部一般能力写成已完成。

## 输入、状态、输出

- `source: float[2]`：候选源连续二维坐标，不使用源编号嵌入。
- `history: list[Observation]`：唯一编号、动作、实际局地风、二值检出。
- `actions: list[Action]`：合法候选动作，含位置、高度、时间与驻留。
- `mechanism: Mechanism`：预先固定的机制、起点、持续时间、强度。
- `log_prob(...) -> float`：历史气体与局地风的联合对数密度。
- `source_score(...) -> float[2]`：对固定实际历史求源坐标导数。
- `sample_future(...) -> list[Observation]`：从模型先抽未来局地风，再抽气体的完整未来块；返回新观测，不修改原历史。
- `fit(...) -> receipt`、`save(...)`、`load(...)`：真实训练及带版本哈希的检查点。

`gas_word_probability` 仅用于给定**合成**风路径的归一化诊断。规划器不能把未来实际风传给它。

## 联合分布

对一次动作 $a_t$，

$$q_\theta(O_{1:T}\Vert A,s,e)=\prod_t q^U(U_t\mid H_{t-1},a_t,e)q^Y_\theta(Y_t\mid U_t,H_{t-1},a_t,s,e).$$

风为二维 Gaussian AR；默认由合格训练集拟合两轴均值、共享 AR 系数及残差方差，明确扣除训练标签中预声明的风偏差机制。绝不对真实 House 数据暗用受控默认 `(0.6,0.1)` 风场。少于 8 个训练转移或残差退化会阻止拟合；只有显式 `fixed_qualified` 模式才使用外部已校准参数。气体为带已知检出丢失通道的 Bernoulli：

$$f_t=\sigma(w^T\phi_t),\quad p_t=r_e(t)f_t,\quad q^Y(Y_t)=p_t^{Y_t}(1-p_t)^{1-Y_t}.$$

$\phi_t$ 包含二次项、相对风项、tanh 和径向基，历史通过前一检出及局地风进入。该有限记忆形式是真实实现的容量边界；不声称能表示任意长程湖岸传播相关性。更长隐状态生成器可以替换同一接口，但必须重新通过联合预测资格测试。

## 教师算子及二次创新

源切向量 $d_i=\partial_{s_i}X$，自然高斯噪声 $\xi$；响应与风噪声 Jacobian 为 $J_X,J_U$。本方法求

$$P_U=I-J_U^+J_U,\qquad v_i=P_UJ_X^T(J_XP_UJ_X^T)^+d_i.$$

只有当 $J_Xv_i=d_i$ 且 $J_Uv_i=0$ 的残差通过门槛，标签才合格。没有通过增加模拟器噪声来制造可逆性的路径。

$$W_i=\xi^Tv_i-\operatorname{div}_{\xi}v_i.$$

`divergence_fd` 对完整 lift 函数中心差分，包含伪逆和切向量对噪声的变化；受控的风保持 lift 只有气体噪声分量，散度恰为零。一般高维情况的有限差分成本不适合原生 GADEN，必须接入 JVP/VJP 或受控迹估计器。

源依赖分支 $g(s,\xi)=\xi_g-b(s)$，此实现的 $v_g=0$。两侧强制观测 $Y^+,Y^-$ 的边界项为

$$\mathcal B_i[h]=-\partial_i b(s)\varphi(b(s))\,\mathbb E[h(Y^+,U)-h(Y^-,U)].$$

`sample_scalar_branch` 实际调用根求解并返回 coarea 系数与两侧输出。对非简单根、无效括区直接报错；不能静默忽略。

令 $g_\theta=\partial_s\log q_\theta(O\mid H,s,e)$，

$$\mathcal L=\mathcal L_{NLL}+\lambda\mathbb E[\|g_\theta\|^2-2W^Tg_\theta]-2\lambda\sum_i\mathcal B_i[g_{\theta,i}]+\tfrac{\rho}{2}\|w\|^2.$$

**监督范围严格为固定历史前缀下的一步条件源 score**，不是整块联合 score 的 Fisher 风险直接最小化。联合 score 由每步条件 score 相加得到；每步误差界可经三角不等式传递到整块误差，但跨时间误差可能同向累积。

`objective_and_gradient` 逐项实现该目标和参数导数；两侧模型 score 不 detach。受控物理标签固定后不对标签再优化。教师输出来自训练源及其固定历史前缀，不能拿未见源标签选点或构造测试期未来响应库。

### A → A′ → A′+B → A′+B′

| 版本 | 实际执行内容 | 主要隔离问题 |
|---|---|---|
| A | 原生 PMFS 外部官方程序/冻结结果 | 经典基线 |
| Aprime | 同一联合生成器，仅 NLL + 相同正则 | 结构适配收益 |
| B | 同一模型 + 无风约束的响应 lift 权重；不计分支修正 | 直接迁移母算法时条件量不匹配 |
| Bprime | 同一模型 + 风保持 lift + 两侧分支修正 | 本文监督算子的增量 |

B 是对“响应分布”的积分分部思路直接迁移，不能假装在联合风—气体目标上已经满足同样条件。为避免只打败一个不合格基线，正式实验必须额外提供 `sensor-only constrained / no-boundary` 与高容量 NLL 标准模型；当前源码已实现 `Bprime_no_boundary`（约束 lift 但无边界项）和 `Bprime_no_wind_constraint`（无风约束 lift 加边界项），可直接传入 `fit`；正式冻结命令由实验合同指定。若 B 的目标条件本来不成立，B′ 对 B 的优势不能单独作为论文主结论。

## 为什么可能改变源间判断

若模型联合源 score 近似真实联合源 score，沿连接两个合法源的路径 $\gamma$ 有

$$\left|[\log q(o|s_a)-\log q(o|s_b)]-[\log p(o|s_a)-\log p(o|s_b)]\right|
\le\int_\gamma\|\nabla_s\log q-\nabla_s\log p\|\,d\ell.$$

这约束的是竞争源 log-score 差，浓度 MSE 本身没有该性质。此结论需要联合密度正且沿路径可微；断开候选分区的相对概率质量不能靠局部 score 学出，所以仍保留 NLL。教师正确只保证针对受控物理分布的监督正确；不能保证真实湖岸源排名必然提升。

## 受控后端的物理解释与限制

自然噪声为两维风扰动、一个气体响应扰动及一个路由门。响应均值随源—测点相对位移和实测风变化，上一检出引入短记忆；读出是硬阈值，可附独立检出损失。路由门表达一个可检验的随机通道跳变，**不是声称真实湖岸都由此四维模型产生**。

已覆盖：`nominal`、`sensor_offset`、`wind_bias`、`detection_loss`，固定起点与持续时间；所有机制在起点前严格不生效。未覆盖：三维障碍流场、完整传感器响应卷积、动态排放、多源同时释放、原生 GADEN 分支发现。涉及这些机制的标签未经资格检查不得训练 B/Bprime。

## 成本

特征维数 $F=34$，一轮 NLL 及弱监督目标约 $O(NF+N_w\cdot2F)$，训练内存约 $O(NF+2N_wF)$。单次历史密度 $O(TF)$，一条未来块 $O(LF)$。一般有限差分散度要 $2D$ 次 lift；这是受控参考，不是高维部署承诺。

## 原生教师 BLOCKED 的确切接口

要将 `ControlledPlumeBackend.teacher_record` 换成 GADEN，原生后端必须提供固定自然噪声种子下的：

1. 当前源坐标、可获取局地风及传感器统计的真实观测算子；
2. `response_jvp/vjp`、`wind_jvp/vjp` 和源切向量；
3. 硬分支编号、门函数、两侧强制回放、proposal 密度及 coarea 因子；
4. lift 可行性、散度误差和边界覆盖率收据。

缺任一项，`fit(..., variant='Bprime', teacher_backend=None)` 显式报 BLOCKED，不能静默变为普通 NLL 并报告 M1 完成。其余 M2/M3、Aprime 训练、数据接口和受控闭环不受此阻碍。


## 独立自评（候选方法，不是发表概率）

M1 算法候选设计成熟度 **7.1/10**：问题与源间证据直接相关 8；物理和统计可解释性 8；二次创新清晰度 7；可执行验证 8；真实模拟器及真实源泛化证据 3.5。此分数表示具备进入完整研发的具体候选，并不表示论文已有 7 成录用概率。原生模拟器教师及竞争源排序改善仍未验证；实证成熟度单独评为 **3/10**，不能用受控演示替代。核心拒稿风险是风保持 lift/边界积分分别属于已有数学工具，必须证明气源联合观测适配后的增量不能被同容量 NLL、普通 source-score regression、约束 lift 无边界等标准模型替代。

### 数值概率边界

工程对 Bernoulli 概率使用 `1e-12` 数值下限及对称上限，生成器采样与其 likelihood 使用同一概率。`source_score` 及混合梯度在饱和区归零，与实际截断后的 log-probability 一致；拐点处不声称经典导数存在。受控物理 `step` 仍使用高斯硬阈值，极端尾部的 floored 密度仅是数值近似，因此精确积分分部/路径推导和受控数值证明限定在未触发截断的合格参数范围。真实实验须报告概率 floor 触发率；不得以尾部截断制造正确源优势。
