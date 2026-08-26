# CTT–M1 物理输运场：独立 premise-gate 草案

## 0. 冻结边界与结论资格

本草案只定义 CTT 的 M1：**物理约束的逆向首达时间场**（physics-constrained backward first-passage field）。M1 在任何 Bayesian/PMFS 累积之前，为每个候选源生成可审计的时空因果响应，并据此改变候选间的相对证据排序。

本阶段不得：

- 读取 House01/02/03 的源位置、最终定位误差或任何可反推出真值的汇总；
- 启动、停止或修改 VM、ROS、GADEN、PMFS 代码与参数；
- 调整 likelihood、posterior temperature、planner、kernel、源强、扩散率或阈值来“救”失败 gate；
- 用最终定位误差、单个漂亮轨迹或 posterior 收敛替代 M1 的直接机制证据；
- 把 M2 的 burst-to-path association 或 M3 的 miss-survival evidence 偷渡进 M1。

M1 premise gate 只回答一个问题：**在冻结的、已知生成机制的小型库中，正确的物理输运首达场是否在累积之前，对正观测产生可重复的候选区分信息？** 通过该 gate 也不构成 House 泛化通过，更不构成完整 CTT 主创新通过。

## 1. 估计对象与观测模型

### 1.1 冻结输入

令可通行域为 \(\Omega\)，障碍边界为 \(\partial\Omega_{\mathrm{obs}}\)。冻结：

- 候选源集合 \(\mathcal S=\{s_1,\ldots,s_M\}\)；
- 机器人采样事件 \(\mathcal O=\{(x_i,t_i,y_i)\}_{i=1}^{N}\)；
- 时变风场 \(u(x,t)\) 与对称正定有效扩散张量 \(K(x,t)\)；
- 最大因果回溯时域 \(L\)、源捕获半径 \(\varepsilon\)、传感器响应核 \(k_{\mathrm{sens}}\)；
- 正观测权重 \(z_i=g(y_i)\mathbf 1[y_i>y_{\mathrm{det}}]\)，其中 \(g\)、\(y_{\mathrm{det}}\) 在看到 premise 结果前冻结。

M1 的 estimand 不是源真值、posterior 或可靠性权重，而是：

> 对每个候选 \(s\) 和采样事件 \((x_i,t_i)\)，逆时间随机输运从该观测点首次到达 \(B_\varepsilon(s)\) 的条件延迟密度，以及由此导出的、与源强无关的路线内相对正响应形状。

### 1.2 逆向随机输运

从观测 \((x_i,t_i)\) 沿逆时间 \(\ell\in[0,L]\) 定义扩散过程

\[
\mathrm dY_\ell=-u(Y_\ell,t_i-\ell)\,\mathrm d\ell
+\sqrt{2K(Y_\ell,t_i-\ell)}\,\mathrm dW_\ell,
\qquad Y_0=x_i.
\]

候选 \(s\) 的首达时为

\[
\tau_{is}=\inf\{\ell>0:Y_\ell\in B_\varepsilon(s)\}.
\]

该定义保留了方向、障碍、时变风与随机弥散；它不是欧氏距离，也不是把风速投影成一个标量修正。

### 1.3 生存 PDE 与首达密度

定义逆向生存场

\[
S_{is}(x,\ell)=\Pr_x(\tau_{is}>\ell).
\]

它满足 backward Kolmogorov 方程

\[
\partial_\ell S_{is}
=-u(x,t_i-\ell)^\top\nabla S_{is}
+\nabla\!\cdot\!\bigl(K(x,t_i-\ell)\nabla S_{is}\bigr),
\]

并采用

\[
S_{is}(x,0)=1,\quad
S_{is}(x,\ell)=0\ \text{on }\partial B_\varepsilon(s),\quad
n^\top K\nabla S_{is}=0\ \text{on }\partial\Omega_{\mathrm{obs}}.
\]

首达延迟密度为

\[
f_{is}(\ell)=-\partial_\ell S_{is}(x_i,\ell),\qquad
p^{\mathrm{reach}}_{is}=1-S_{is}(x_i,L)=\int_0^L f_{is}(\ell)\,\mathrm d\ell.
\]

考虑传感器时间响应后，物理响应为

\[
h_{is}(\ell)=\bigl(f_{is}*k_{\mathrm{sens}}\bigr)(\ell).
\]

若使用 neural operator，它只能近似 \((u,K,s,x_i,t_i)\mapsto S_{is}\) 或一个预先定义的低维 PDE discrepancy；训练损失必须包含边界条件、单调性 \(\partial_\ell S\le 0\)、取值范围 \(0\le S\le1\) 与 PDE residual。它不得读取气体测量 \(y_i\)、候选真值、posterior 或最终误差。

### 1.4 去源强的路线内相对响应

连续源强 \(q_s\) 会把“输运形状”与“幅值拟合”混在一起。M1 因此只输出归一化响应：

\[
r_{is}=\int_0^L h_{is}(\ell)\,\omega_i(\ell)\,\mathrm d\ell,
\qquad
\widetilde r_{is}=\frac{r_{is}+\epsilon_r}
{\sum_{j\in\mathcal I} (r_{js}+\epsilon_r)}.
\]

\(\omega_i\) 只编码第 \(i\) 个采样窗的时间支撑；\(\epsilon_r\) 只能取由数值零保护所需的最小机器/离散化量级，并在运行前冻结。这样 \(\widetilde r_{is}\) 比较的是候选预测的**相对时空证据形状**，不能靠放大源强获胜。

## 2. M1 的直接正信息指标

令正观测在同一路线内归一化为

\[
p_i^+=\frac{z_i}{\sum_{j\in\mathcal I}z_j},
\qquad \mathcal I_+=\{i:z_i>0\}.
\]

定义 M1 的 pre-Bayes 正信息分数

\[
J_{M1}^+(s)=\sum_{i\in\mathcal I_+}p_i^+
\log\frac{\widetilde r_{is}}{\pi_i^0}.
\]

\(\pi_i^0\) 是冻结的无信息路线基线（同一有效采样窗上的均匀质量，或由采样占空比唯一确定的 exposure null），不得从结果拟合。该分数只使用正观测；miss 信息留给 M3。

对 premise atom \(a\)（其生成源 \(s_a^\star\) 由合成器已知，而非 House 真值）定义三个直接量：

1. **候选间正证据间隔**
   \[
   \Delta_a^{\mathrm{rank}}=J_{M1,a}^+(s_a^\star)
   -\max_{s\in\mathcal D_a}J_{M1,a}^+(s),
   \]
   其中 \(\mathcal D_a\) 是预先匹配距离、可见性与采样覆盖的 distractor 集。

2. **相对无信息基线的增量正信息**
   \[
   \Delta_a^{\mathrm{null}}=
   \sum_{i\in\mathcal I_{a,+}}p_{ai}^+
   \log\frac{\widetilde r_{ai,s_a^\star}}{\pi_{ai}^0}.
   \]

3. **候选顺序改变**
   \[
   \rho_a=\operatorname{rankcorr}
   \bigl(J_{M1,a}^+(s),J_{\mathrm{dist},a}(s)\bigr).
   \]
   这里 \(J_{\mathrm{dist}}\) 是冻结的欧氏/逆距离排序。M1 必须产生至少一个由因果输运决定、与距离排序不同的严格 pairwise reversal；否则它只是距离重参数化，不能作为主机制。

以上全部在 posterior 更新前计算并存盘。**禁止以最终定位误差、posterior mass、entropy 或路径长度补充解释。**

## 3. 最小 premise library

只构造一个小而覆盖关键辨识条件的冻结机制库；不使用 House01/02/03 真值或其结果挑选 atom。

每个 atom 固定候选集合、障碍图、风场、\(K\)、路线采样窗与合成正观测，并显式记录生成源。最小需要覆盖：

- **A1 顺风可达 / 近距不可达**：真源更远但存在高首达质量；近距 distractor 被障碍或逆风阻断。用于证明 M1 不是距离函数。
- **A2 双路径延迟分裂**：同一候选经障碍产生两个延迟模态；匹配 distractor 具有相近总质量但错误延迟形状。用于证明保留时空响应，而不是只算 reachability scalar。
- **A3 时变风反转**：静态平均风给出错误顺序，冻结的时变场给出正确顺序。用于证明时间索引是 load-bearing。
- **A4 弥散主导尾部**：纯平流无法覆盖观测窗，而有限 \(K\) 给出首达尾部。用于证明 stochastic first-passage 不是确定性流线追踪。

每个 atom 至少有两个预先冻结、独立的随机实现；随机实现只检验重复性，不能挑选“成功 seed”。若计算预算只能支持更少 atom，应删减范围并声明不足，不得在结果后合并或替换 atom。

## 4. 最小 premise gate

Gate 按顺序执行；前一项失败即停止，保留失败证据，不进入下一项。

### G0 — 合约与盲态

- 记录输入文件、公式实现、候选集合、atom 定义、随机种子、输出根目录的 SHA-256；
- 静态检查脚本不得打开任何 House123 truth、最终误差或历史 verdict 文件；
- M1 输出接口只允许 \(S,f,h,r,\widetilde r,J^+\) 与数值诊断，不允许 posterior 或 source-truth 字段；
- 任何 neural surrogate 的输入列表中不得出现 \(y_i\)、truth、posterior、error。

失败分类：`CONTRACT_INVALID`，不是科学 NO-GO。

### G1 — PDE 身份与数值收敛

对每个 atom/candidate 验证：

- \(0\le S\le1\)，且 \(S(\ell)\) 随 \(\ell\) 非增；
- \(f\ge0\)，并满足 \(\int_0^L f\,d\ell=1-S(L)\)；
- 源吸收边界与障碍无通量边界成立；
- 网格/时间步加密后，\(J^+\) 的候选顺序不变。

数值容差不预设拍脑袋常数：由一次冻结的 refinement study 给出 observed convergence envelope，gate 容差取该 envelope 与浮点舍入上界的可审计组合。

失败分类：`NUMERICAL_INVALID`，不得解释机制表现。

### G2 — Coverage/activation contract

对每个 atom 的生成源要求：

\[
\sum_{i\in\mathcal I_{a,+}}p^{\mathrm{reach}}_{i,s_a^\star}>0
\quad\text{且}\quad
\operatorname{Var}_{i\in\mathcal I_a}(\widetilde r_{i,s_a^\star})>0.
\]

同时候选间必须存在非退化差异：不能所有 \(\widetilde r_{is}\) 在数值容差内相同。

若生成源无覆盖、正窗落在 \(L\) 之外、路线从未采样其可达域，或所有候选响应塌缩，则该 atom 标记 `ACTIVATION_DIAGNOSTIC_ONLY`。这不是混合性能结果；停止，不调 \(K,L,\varepsilon\)、幅值、温度或路线来救。

### G3 — 直接正信息 premise

在所有有效 atom 和全部冻结随机实现上，同时要求：

\[
\Delta_a^{\mathrm{rank}}>0,
\qquad
\Delta_a^{\mathrm{null}}>0.
\]

并要求 A1 至少出现一个预注册的严格 pairwise reversal：生成源在 \(J_{M1}^+\) 下胜过距离更近的 matched distractor。符号要求是机制定义产生的零基准，不另造百分比阈值。

判定：

- 全 atom、全实现均为正：`M1_PREMISE_GO`；
- 任一有效 atom/实现非正：`M1_PREMISE_NO_GO`；
- 任一 atom 未通过 G2：整体 `M1_PREMISE_INVALID_COVERAGE`，不能把其余成功 atom 报成 GO。

### G4 — 非平凡负对照

完整 M1 还必须严格优于至少两个预注册负对照的同一 \(\Delta^{\mathrm{rank}}\)：

- `TIME_SHUFFLE`：仅打乱风场时间顺序，保持边际风速分布；
- `DELAY_PERMUTE`：保持每个候选的总 reachability mass，但在采样窗间置换延迟形状；
- `WRONG_DIRECTION`：用 \(+u\) 代替逆向漂移 \(-u\)，检查因果方向；
- `DISTANCE_ONLY`：障碍感知最短路或欧氏距离，不使用输运 PDE。

要求对照针对同一直接分数，而非针对最终误差。若完整 M1 与这些对照等价，则结论为 `M1_NONTRIVIALITY_NO_GO`。

## 5. 消融与解释责任

消融不用于调参，只用于回答“哪个物理结构提供了增量信息”。所有 arm 使用相同 atom、候选、正观测与评分代码。

| Arm | 唯一变化 | 所检验命题 | 预期失败模式 |
|---|---|---|---|
| M1-FULL | 时变 \(u\)+各向异性 \(K\)+障碍+首达延迟 | 完整物理场 | 参考臂 |
| NO-TIME | \(u(x,t)\to\bar u(x)\) | 时间索引是否必要 | A3 间隔消失/反号 |
| NO-DIFFUSION | \(K\) 取冻结的数值极限 | stochastic tail 是否必要 | A4 覆盖丢失 |
| ISOTROPIC-K | \(K\to \frac{\mathrm{tr}K}{d}I\) | 各向异性是否必要 | 定向尾部混淆 |
| NO-OBSTACLE | 移除吸收/反射几何约束 | 障碍拓扑是否必要 | A1 近距 distractor 虚假获胜 |
| REACH-ONLY | \(h_{is}(\ell)\to p^{\mathrm{reach}}_{is}\) | 延迟形状是否必要 | A2 双路径不可辨 |
| DISTANCE-ONLY | 欧氏/最短路评分 | 是否只是几何重参数化 | 无预注册 reversal |
| NUMERICAL-SOLVER | 不用 neural surrogate | surrogate 是否保持物理排序 | 与 FULL 顺序不一致即 surrogate 失效 |

模块增量以同一 atom 上的 paired difference 报告：

\[
\delta_{a,m}=\Delta^{\mathrm{rank}}_{a,\mathrm{FULL}}
-\Delta^{\mathrm{rank}}_{a,\mathrm{ABLATE}(m)}.
\]

若某模块在其专属 atom 上 \(\delta_{a,m}\le0\)，该模块的理论必要性未获支持；不得用其它 atom 的平均增益、总体 posterior 或最终误差掩盖。

## 6. 失效条件与停止规则

以下任一项触发立即停止，不进入 House held-out：

1. 数值 identity、边界条件或 refinement ordering 不成立；
2. 生成源违反 coverage contract；
3. 完整 M1 不能在每个有效 atom/实现上得到正的 \(\Delta^{\mathrm{rank}}\) 与 \(\Delta^{\mathrm{null}}\)；
4. A1 没有产生相对距离基线的严格候选顺序反转；
5. 保持总质量的 `DELAY_PERMUTE` 与完整 M1 等价，说明“延迟场”没有贡献；
6. `WRONG_DIRECTION` 不劣于完整 M1，说明因果方向未被使用；
7. neural surrogate 改变 numerical solver 的候选顺序；
8. 结果依赖事后改变 \(K,L,\varepsilon\)、正阈值、atom、seed 或 distractor；
9. 需要读取 House123 真值或最终定位误差才能判断 M1 是否有效。

失败后只允许：修复可复现的公式—代码矛盾或数值 bug，并以新版本号重跑原冻结 gate。禁止用参数/seed/路线 rescue。科学失败保留为 `M1_PREMISE_NO_GO`。

## 7. 最小可审计输出

建议输出包只包含：

- `M1_CONTRACT.json`：公式版本、所有符号默认值及选择规则、输入哈希、盲态声明；
- `ATOM_MANIFEST.tsv`：atom、生成源（仅合成库）、matched distractors、seed、coverage contract；
- `PDE_QC.tsv`：范围、单调性、质量守恒、边界残差、refinement ordering；
- `M1_RESPONSE.npz`：\(S,f,h,r,\widetilde r\)；
- `M1_DIRECT_INFO.tsv`：每 atom/seed/candidate 的 \(J^+\)、\(\Delta^{\mathrm{rank}}\)、\(\Delta^{\mathrm{null}}\)；
- `M1_ABLATIONS.tsv`：全部 paired \(\delta_{a,m}\)；
- `VERDICT.txt`：唯一终态及首个失败 gate；
- `SHA256SUMS.txt`：上述文件与实现哈希。

## 8. 当前最小主张

若 gate 通过，唯一允许的主张是：

> 在与 House123 真值隔离的冻结机制库中，物理约束的逆向首达时间场在 Bayesian 累积前，对正观测产生了可重复的候选区分信息，并且该信息不能由距离、总 reachability、错误时间顺序或错误因果方向解释。

它不等价于“CTT 改善 PMFS”、不等价于“House 泛化通过”，也不授权启动 VM 或读取 held-out truth。
