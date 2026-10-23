# M2 / M3 实现、接口与独立审查

## 1. 已实现范围

本文件对应实际源码，不把受控测试写成 House 或湖岸定位成绩。依赖为 NumPy / SciPy；所有未来输入均经联合生成器抽样。实现中没有读取未来真实风场、真源标签或真实响应库的规划接口。

### M2：机制差分诊断与可撤销证据回放

| 层级 | 实际内容 |
|---|---|
| A | 原生 PMFS 必须由独立原程序运行；本模块不伪造 native PMFS 对照。 |
| A′ | `ReplayEngine.infer(..., variant='Aprime')`：同一正确联合模型、全源支持、原始观测账本，机制似然全部保持 nominal。 |
| A′+B | `variant='B'`：CDN 共享表征差分用于 source-blind 机制提议；机制仅解释最新因子，不重算已有后缀。 |
| A′+B′ | `variant='Bprime'`：源条件差分提议；从机制起点撤销旧后缀并替换为新机制完整后缀。默认精确有限枚举作为计算正确性参考。 |

母论文为 ICML 2025 **Identifying Biological Perturbation Targets through Causal Differential Networks**，PMLR 267，正式题录：<https://proceedings.mlr.press/v267/wu25v.html>；作者代码：<https://github.com/rmwu/cdn>。

原领域是生物扰动靶点识别。实际迁移的母算子为共享编码器处理观测与参考条件，再作机制表征差分，而非把“生物”“因果”当新名称：

\[
D_s=E_\phi(D_{\mathrm{obs}})-E_\phi(D_{\mathrm{ref},s}),\quad
r_\phi(e\mid H,s)=\operatorname{softmax}(V^TD_s+c).
\]

V1 的 `DifferentialDiagnoser` 使用 21 维动态通道统计（局地风两分量、气体的均值/方差/相关/滞后一阶积/增量），共享可训练 tanh 编码器和分类头。网络使用精确 NumPy 反向梯度与 L-BFGS 训练。**这不是作者 FCI + 轴向注意力全网络的复现**；是输入输出与共享差分算子的明确迁移实现。V1 没有足够变量或时长条件证明单条轨迹能恢复完整因果图。

分类输出必须先 `bind_catalog(mechanisms)`，checkpoint 保存机制种类、起点、持续期、幅度及顺序的规范 JSON 与哈希；推断核对精确身份。相同类别数而目录不同亦拒绝。旧无目录 checkpoint 明确 BLOCKED，不会默许类别错位。

二次创新在于：参考条件同时随竞争源变化、机制仅作用于预声明的物理/观测节点、机制提议不能成为第二次似然、错误历史解释通过可审计的后缀替换解除。物理机制只允许固定目录中的风偏置、传感器偏置或检出丢失；不能逐窗口自由拟合残差。

账本 `EvidenceLedger` 验证唯一 ID、时间顺序和数值；整块追加具原子性。`ReplayEngine` 对每个候选源、机制起点检查故障前似然与 nominal 相同，再计算

\[
\log L_{s,e}=\log L_{s,0}
-[\log L_{s,0}(H)-\log L_{s,0}(H_{<u})]
+[\log L_{s,e}(H)-\log L_{s,e}(H_{<u})].
\]

这是完整条件后缀替换。机制持续期结束后仍继续计算后续因子，过去观测对下一风/气体条件状态的影响保留。最终

\[
P(s,e\mid H)\propto\pi_0(s)\pi(e)L_{s,e}(H).
\]

源先验和机制先验固定。不能把上一轮尖锐源后验当下一轮全历史先验，也不能把诊断分类概率再乘到后验。`ReplayResult` 返回源后验、源—机制联合后验、全部似然、每个后缀移除/替换因子与来源记录，并额外保存稳定 `source_log_posterior` 和逐源 log-softmax 计算的 `conditional_mechanism_posterior`。极低源概率在显示数组中可能浮点下溢为零，不能用概率 floor 掩盖；源注册表和有限 log 概率仍保留，M3 使用稳定条件机制分布，因此该源仍可接受轮转挑战。

`infer_budgeted` 真正使用诊断输出形成防御性提议

\[
q_\phi(e\mid H,s)=(1-\epsilon)r_\phi(e\mid H,s)+\epsilon\pi(e),\qquad
\widehat Z_s=\frac1R\sum_{r=1}^R\frac{\pi(e_r)}{q_\phi(e_r\mid H,s)}L_{s,e_r}.
\]

未归一化证据估计无偏的条件是 likelihood 精确、提议全支持和抽样正确；归一化后验在有限样本下通常有偏。提议生成消耗的参考轨迹亦被计入成本，不能只统计少量似然调用而宣称加速。

### M3：容错反证观测与可恢复列表规划

母论文为 IEEE ISIT 2025 **Multi-Stage Active Sequential Hypothesis Testing with Clustered Hypotheses**，DOI `10.1109/ISIT63088.2025.11195532`，作者全文：<https://arxiv.org/html/2501.11459v2>。未确认作者公开代码；`ClusteredASHTReference` 是依据有限已知分布算法独立实现的参考，不声称运行了作者软件。

原领域为信息论主动假设检验。母算子：动作相关响应聚类 → 选择能分开这些簇的动作 → 代表间累积 log-likelihood ratios → 接受存活簇 → 下一阶段再拆分。本工程的母算法参考类确实执行两个以上阶段；气体闭环的 B 消融保留动作相关聚类与分离选择，但不套用母文献 iid 定理。

`JointCodebookBuilder.build` 返回每个合法动作块的 `SoftCodebook`：

- `probabilities[N,E,2**L]`：整段气体事件联合分布，未来局地风与气体一起生成；
- `tv_radius[N,E]`：有限字母 MC 估计误差半径；
- `confidence_failure_probability`：一次建码本所含全部动作/源/机制的联合失败预算；
- 原始动作、模型版本、实际成本、阈值。

半径使用保守有限字母界：\(r=\min\{1,\sqrt{(K\log2+\log(M/\delta))/(2n)}\}\)，其中 K 为码字数，M 为本次全部源—机制—动作分布数量。它覆盖生成模型内部的 Monte Carlo 误差，**不覆盖物理模型错误**。小样本时半径会大，系统应承认无法得到强反证功效。

`CorruptionChannel` 支持预声明额外翻转、显式擦除和连续 burst。正常间歇已在联合分布中，不再算作“错误位”。`solve_robust_test` 实现有限 LP：

\[
\max\beta\quad\text{s.t.}\quad
\sum_cp_{h,e}(c)u_c+\rho_{h,e}(u_{\max}-u_{\min})\le\alpha,
\]
\[
\sum_cp_{s,e}(c)v_c-\rho_{s,e}(v_{\max}-v_{\min})\ge\beta,
\quad u_c\ge\phi_y,\;v_c\le\phi_y\;(y\in N(c)).
\]

零 TV 半径下这是精确的有限污染信道随机化检验 LP。非零半径的 range-times-TV 是保守充分界，**不是一般 TV 球下功效最优性的宣称**。求解后用独立有限 TV 极值质量转移算法重算风险/功效证书。

低后验合法源由与后验无关的轮转游标进入第一挑战槽；后续槽优先最近恢复或当前相容列表中的候选，因此列表实际改变行动调度。列表外候选继续由第一槽保障覆盖。挑战结果只触发回放或调度，不增加“反证奖励似然”。所有动作执行完整预声明短块；若中途更改动作，必须废弃旧检测器重新规划。随机化检测器的 uniform 随机数在观察块到来前生成。当所有候选动作的认证功效不超过 alpha 时，回退联合 EIG 行动，同时 `test=None`、不支出风险预算、不执行常量 alpha 的无信息随机拒绝。

`RiskLedger` 分配 \(\alpha_t=\alpha_{\rm total}/[t(t+1)]\)。调用者还应把建码本 MC 失败预算按相同可加形式分配。正确风险边界为模型覆盖条件下 \(\sum_t(\alpha_t+\delta_t)\)，不是无条件实飞误报认证。

`RecoveryList` 使用每个源—机制高概率码字集合与污染邻域判断本块相容性；列表与概率图严格分离，不能把不在列表的源概率置零。当前列表是最新块覆盖/调度集合，**不是跨时间累积有效置信集**。模型版本改变时恢复全部源，旧排除不能继续有效。

## 2. 可执行接口

```python
ledger = EvidenceLedger(observations)
engine = ReplayEngine(generator, source_xy, mechanisms,
                      mechanism_prior=[0.8, 0.1, 0.1])
result = engine.infer(ledger.history, variant="Bprime")
books = JointCodebookBuilder(generator).build(
    ledger.history, legal_action_blocks, source_xy, mechanisms,
    draws=512, rng=rng, delta=0.01/((round_id+1)*(round_id+2)))
planner = RobustCounterEvidencePlanner(len(source_xy),
    channel=CorruptionChannel(max_flips=1), total_alpha=0.05)
plan = planner.plan(books, result.source_posterior,
                    mechanism_posterior=result.conditional_mechanism_posterior,
                    variant="Bprime")
# 执行 plan.actions 整块后，仅将原始 observations 追加一次。
event = planner.observe(plan, new_observations)
ledger.extend(new_observations)
updated = engine.infer(ledger.history, variant="Bprime")
```

`planner` 应在整条航次中复用；不能每一块重新初始化风险账本和轮转游标。

## 3. 真实运行结果与限制

- `tests/test_m2_replay.py`：账本 exactly-once/原子性、后缀等于全历史重算、记忆尾部、固定先验重放、margin 恒等式、防御性提议权重、共享差分网络可训练性、纯解析共享机制纠错。
- `tests/test_m3_planner.py`：1 位容错功效、不可分反例、TV 极限、burst/擦除、风险支出、列表版本恢复、联合相关性、执行块一致性、重复证据拒绝、低概率候选轮转、母 ASHT 真正两阶段、鲁棒 EIG 最小化。
- `python -m gsl_recovery.m2_diagnosis.demo --out artifacts/m2_diagnosis` 已真实运行 72 个受控训练例，写入 checkpoint、训练对与 receipt。诊断训练 loss 下降，500 次迭代到预算上限，不能称优化已收敛。
- 极小预算 `R=2/source` 的重要性后验与精确枚举偏差明显；其 receipt 完整保留。它证明接口联通，**未通过低预算准确性资格**。V1 默认在线 exact 枚举；提议近似必须由冻结预算误差/成本合同再验收。

## 4. 独立消融与强对照

M2：nominal / 仅最新机制解释 / source-blind 提议 / source-aware 提议 + 完整后缀回放 / 普通正确有限机制 Bayes 枚举。无限计算下，正确 Bayes 枚举本来应与回放目标相同；诊断贡献只能在相同有限计算预算下评估。

M3 已实现 `A`（原 Eq.11 的方差核心，c=0；不是完整 native PMFS）、`Aprime`（joint EIG）、`B`（响应聚类分离选择）、`Bprime`（风险反证+列表）、`min_hamming`、`channel_eig` 与 `robust_eig`。后者实际以行单纯形上的 pairwise Frank-Wolfe 和一维导数根线搜索最小化同一污染邻域允许的公共随机信道下联合互信息；独立计算可行性和全局对偶间隙，默认要求不超过 1e-5 nats，未达标明确失败。原 SLSQP 在稀疏五位码本上未收敛，失败日志保留。该对照是有限凸优化，不声称涵盖所有风场失配。

## 5. 新颖性审查：可主张范围

M2 的 Bayes 边缘化、重要性修正、后缀重算本身不是新定理。可以研究的气源二次创新是“源竞争条件下的差分机制提议 + 可撤销原始观测依赖重放 + 不重复计证据 + 有限预算可审计恢复”。若 source-blind 提议或普通层次 Bayes 在同成本下同样有效，诊断网络不得单独宣称优势。

M3 的 LP 和 Neyman–Pearson 检验也是成熟理论。可主张候选在于“动作相关联合随机码本 + 明确额外污染信道 + 低后验源轮转反证 + 机制版本变化后列表恢复”的气源闭环机制。它针对错误高置信恢复，不能宣称普遍超越正确 EIG。其物理解释是航线决定可辨识的时空响应，而非自由指定代数码字。

工程/理论资格已可进入冻结验证，跨源/House/湖岸性能和真实传感机制可辨识性尚须实证。这些是可实现的候选创新，尚不是已验证的 SCI 贡献。
