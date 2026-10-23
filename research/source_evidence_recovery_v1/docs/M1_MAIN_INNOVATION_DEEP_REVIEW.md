# M1 主创新深化审查：从特权物理状态到可部署源证据

审查日期：2026-10-23。对象为 V2 工程与本轮已访问的一手文献；不是作者代码复现报告，也不是 House/S2 定位收益报告。三模块主线保持不变：M1 源证据监督联合生成，M2 机制诊断与证据回放，M3 容错反证与恢复列表。本文是可实施方法及验证边界的独立审查，约十页汇报稿的内容规模。

## 1. 最终裁决

**推进附件路线 B 的“合法历史投影源证据”版本；保留路线 A 的已运行算子，路线 C 以明确资格条件待接入。** M1 的主研究对象是源间 log-evidence 的变化及其未来观测分布，不是三维浓度场的整体重建精度。M2、M3 继续使用同一个归一化联合生成器，不再另建互不相容的评分模型。

这不是宣布已有高质量论文结果。它是一项结构完整、可训练、能被强对照推翻的算法候选。现有数学支持其目标与源排序直接关联；现有工程支持有限模型计算与闭环接口；现有真实数据尚不支持原生三维教师与稳定定位增益。具体测试与运行收据以本轮 V2 审计为准，不能引用复制到工程内的 V1 `artifacts/` 充当 V2 实验。

### 1.1 附件 A/B/C 的原义

| 路线 | 保留的定义 | 输入 → 核心运算 → 输出 | 当前裁决 |
|---|---|---|---|
| A | V1 Malliavin/BEL + ASD 微分教师 | 自然模拟器噪声、源扰动、分支轨迹 → 受条件约束的噪声提升、散度及边界补偿 → 完整数据源导数监督 | 保留受控特例；原生 GADEN 内核未接通 |
| B | 特权物理教师 → 任务充分学生 | 训练期物理状态 + 合法历史 → 候选源条件过滤、分布投影、源证据蒸馏 → 仅依赖合法历史的联合生成器 | **本版主选**，学生与有限 bank 算子已具体实现 |
| C | A+B 的合格微分内核统一 | A 的合格完整数据微分 → B 的两次条件投影 → 可部署源条件导数 | 理论组合清楚；**native C BLOCKED**，普通 surrogate autograd 不解除此状态 |

另一个符号体系 `A → A′ → A′+B → A′+B′` 是实验消融链，其中 A 指原生 PMFS。两套字母必须分别注明，不能把“附件路线 B”误写成“母算法直接迁移基线 B”。

### 1.2 为什么主选 B

直接追求 C 需要原生模拟器自然随机数、JVP/VJP、硬分支 trace、两侧强制回放及边界提议测度；当前真实资产没有这些接口。B 则能先把“教师看见什么、学生允许看见什么、给学生什么标签”严格分开，并交付可训练的同容量标准对照。它也允许将来接入 A 的合格导数，无需再换题。

应避免把 B 降格为“换一个 GRU”。B 的可审查计算链是：**外生物理状态库 → 每个候选源对同一历史的过滤 → 完整历史与过去历史的两个证据边缘 → 源对端点/合法路径监督 → 归一化联合学生 → 源概率与主动反证**。其中各个概率恒等式均为已知；二次创新候选是该链条在气源任务中如何定义、计算、约束并验证。

## 2. PMFS 失败如何约束 M1，而非事后包装

用户提供的 B4 错误高置信、M4/RK 预测改善未转化为源排名、R3 指纹审计中近乎所有候选仍相容，是选择目标的依据；这些事实不能自动证明某个具体风场机制。原生兼容评分不是校准物理似然，不能把 14,874.6 等评分比直接解释为 Bayes factor。B4 原始证据入口及来源边界见 `docs/data/DATA_LINEAGE_AND_QUALIFICATION.md`。

| 已有观察 | 支持的能力缺口 | 不支持的跳跃推断 | M1 中可检验的修复 |
|---|---|---|---|
| 浓度误差下降，真实源排名未稳定提高 | 平均预测目标未控制竞争源相对证据误差 | 所有 NLL 或联合生成都必然失败 | 在相同模型/数据下，比较 source-pair evidence 误差及真源 margin |
| 准确预测少量事件，但约 15.7/16 源仍相容 | 当前合法观测下的响应可能不可分，或模型丢失可分信息 | 加一个码距目标就会可分 | 先看投影教师的源条件联合分布是否可分，再看学生保留程度 |
| 三维真风改善响应，错误源也能解释事件 | 完整物理状态与合法历史的信息量不同 | 三维恢复一定提升定位 | 每个源分别过滤隐藏状态，不能复制单次真实世界的响应 |
| 错误尖峰及局部带集中评分差 | 比较/证据模型可能放大错配 | 必然由湖陆风、时间相关或候选面积造成 | 保留唯一账本、同一联合概率模型与 M2 重算，不再叠加派生图证据 |

主科学假设应写成：在教师近似足够准确、合法历史仍含源可辨识信息时，源条件信息投影后的证据监督，能在有限模型容量与训练数据下减少竞争源 log-margin 误差，进而改善概率定位及主动反证。它不等同于“恢复更多传播细节就更有效”。

## 3. 母算法到底借什么

### 3.1 随机分析／逆图形学：路线 A 的具体算子

ICML2025 *Conditioning Diffusions Using Malliavin Calculus* 的输入是参考 SDE 路径、Brownian 增量和终端观测。其 Theorem 2.1、Algorithm 1 构造路径权重过程，再用平方回归学习条件控制，而非对不连续观测函数硬求梯度。原文要求漂移和噪声系数的正则性、非退化扩散等条件。气源迁移将监督对象改为源坐标引起的观测证据导数；V1 的受约束噪声提升还要求不改变已条件化的风通道。[原文](https://arxiv.org/html/2504.03461v2)

SIGGRAPH Asia2025/ACM TOG *Automatic Sampling for Discontinuities in Differentiable Shaders* 的实际机制是程序变换为分段常值代理、随机线段上的 segment snapping、边界两侧求值及测度权重。V1 实现的是一维自然噪声门的根定位/coarea 特例，不是作者的一般 shader 编译和全部高维边界自动发现。[作者页及代码](https://yashbelhe.github.io/asd/index.html)

两篇提供“在观测/传播存在硬边界时，不能忽略边界质量”的具体计算依据；它们没有证明原生 GADEN 可以无改造地产生同样合格导数。

### 3.2 特权 POMDP：把完整状态教师投影到历史信念

NeurIPS2024 *Provable Partially Observable Reinforcement Learning with Privileged Information* 的一般情形先学历史 belief，再把特权 critic 按 belief 加权：

\[
\overline Q(H,a)=\sum_z b(z\mid H)Q(z,H,a).
\]

Proposition 3.1 说明部分可观测条件下，直接复制知道隐藏状态的教师动作可以失败。迁移到气源时，输出从动作价值改为**源条件联合观测概率**，belief 必须由每个候选源分别解释同一历史得到，不能只使用真实源条件的 belief。[正式全文](https://proceedings.neurips.cc/paper_files/paper/2024/file/74d188c51d97fcfbc0269f584d6a53b7-Paper-Conference.pdf)

这是有具体输入和运算的母机制迁移，但年份是 2024，不能替代 2025—2026 扩展文献要求。

### 3.3 新近任务充分学习：借任务选择，不硬复制 latent

ICML2026 MIST-WM 的门控、任务互信息和“同因子值不同 rollout”的成对训练，是具体的任务选择机制；AISTATS2025 RID 的教师过滤器、学生过滤器和交替优化，是具体的任务相关蒸馏机制。它们提醒本研究：不能把完整风场所有细节都当作学生必须恢复的标签。**当前 V2 没有实现 MIST-WM 全套探索技能/门控或 RID 全套多层优化**；其完整实现应作直接母算法对照，不能在名称中宣称已复现。[MIST-WM](https://proceedings.mlr.press/v306/feng26aa.html)；[RID](https://proceedings.mlr.press/v258/dissanayake25a.html)

我们的任务对象是合法动作块下的一组源条件证据，而非预先指定的“真实传播机制 latent”。负样本不能仅凭源标签强制分离：若两源在合法历史下的投影分布相同，就不应制造源间间隔。

### 3.4 ICLR2025 Compositional SBI：有条件/先验修正的 score 组合

原方法输入完全观测的 Markov 状态转移及待估参数，训练局部 posterior-score，再组合为序列参数score。在原始无噪声参数层，其结构为

\[
\nabla_\theta\log p(\theta\mid x_{0:T})
=\sum_{t=0}^{T-1}\nabla_\theta\log\widetilde p(\theta\mid x_t,x_{t+1})
-(T-1)\nabla_\theta\log p(\theta).
\]

母算法的具体教训是：可组合的局部得分要校正反复计入的条件/先验；任意把局部得分相加并不正确。其训练状态proposal需独立于参数并覆盖支持，原文§5.2明确不包含HMM。当前气体序列只有局地观测，不能直接调用这套完全观测Markov分解。[正文§3及§5.2](https://arxiv.org/html/2411.02728v2)

气源二次改造将参数换成源坐标，改为对潜在传播bank计算完整历史与过去历史两个边缘的导数差；候选源自己的过滤责任度随之参与。它与特权POMDP的belief投影一起构成V2母机制依据。**这不是已经复现原论文的score-diffusion网络，也不是已经证明其算法一般化到HMM**；当前新增的是可执行有限bank监督标签生成协议，Fisher恒等式本身仍为已知。若严格要求“2025/26整套母网络直接迁移已完成”，本版仍有该对照实现缺口，不能用文献名称填补。

## 4. 可执行的气源二次算子

令 $H$ 为合法历史，$Q$ 为事前合法动作块，$s$ 为连续候选源，$c$ 为预声明机制，$z_j$ 为外生物理世界原子。每个原子提供归一化、前缀一致的联合密度 $p_{T,j}(H\mid s,c)$。定义

\[
L_s(H)=\operatorname{LSE}_j[\log\pi_j(s)+\log p_{T,j}(H\mid s,c)],
\qquad
w^H_{s,j}=\operatorname{softmax}_j[\log\pi_j(s)+\log p_{T,j}(H\mid s,c)].
\tag{1}
\]

未来条件证据及源导数是

\[
\ell_s^T(Y\mid H,Q)=L_s(H\Vert Y)-L_s(H),
\tag{2}
\]

\[
g_s^T
=\sum_jw^{HY}_{s,j}\nabla_s\log[\pi_j(s)p_{T,j}(H,Y\mid s,c)]
-\sum_jw^{H}_{s,j}\nabla_s\log[\pi_j(s)p_{T,j}(H\mid s,c)].
\tag{3}
\]

这里先混合概率，再取 log；两次过滤权重不能混用；历史归一项不能删去。式(3)是已知 Fisher 型恒等式，本研究不能署名为原创定理。`m1_distill/projection.py` 已具体实现端点差、源 score、ESS、路径积分与资格阻断。

对竞争源 $a,b$：

\[
\Lambda_{b:a}^T=\ell_b^T-\ell_a^T,
\qquad
\Lambda_{b:a}^T=\int_0^1g_{\gamma(r)}^{T\top}\gamma'(r)\,dr
\tag{4}
\]

第二式需要连接路径合法、密度正且足够光滑；跨障碍断开的源区域使用端点锚。有限 bank 上的光滑 surrogate 梯度只对该 surrogate 有效，不等于对真实原生传播过程的无偏梯度。

### 4.1 物理教师与学生

| 层 | 实际输入 | 运算 | 输出及边界 |
|---|---|---|---|
| `PhysicalBank` | `[K,P,7]`，每点 xyz、time、3D wind；外生世界权重及 lineage | 时间/空间支持检查、源无关世界身份 | 训练期 bank；不是某一真实源的气体快照库 |
| `PrivilegedPhysicalTeacher` | bank、候选源、合法历史、几何、机制 | 物理场特征聚合 + source-conditioned GRU；局地风由 bank 插值，气体为可学习读出 | 每原子联合密度；属于可训练物理条件 surrogate，不是 CFD、PINN 或原生 GADEN |
| `ConditionalEvidenceProjector` | atom likelihood、prior、同一 $H,Y,a,b$ | 式(1)–(4)、分别过滤、资格及 ESS 检查 | 合法条件 evidence/score/pair/path |
| `NeuralJointGenerator` | 历史局地气体/风及 mask、相对几何、候选源、动作、机制 | 因果 GRU、轨迹级潜在模式、归一化风/气体头 | 历史 log-density 与同模型未来联合采样；部署不读 bank |

学生结构为

\[
q_\theta(O_{1:T}\mid A,s,c,G)
=\sum_{k=1}^{K_s}\pi_{\theta,k}(s,G)
\prod_{t=1}^{T}q_{\theta,k}(O_t\mid H_{t-1},a_t,s,c,G).
\tag{5}
\]

采样时先依据当前源的模式责任度选一个轨迹模式，再整段生成；不能逐时刻独立重抽。风为二维 Gaussian，气体为显式二值事件或带 LOD 的 censored lognormal。原始观测单位、LOD、时钟必须来自数据合同，不能由模型暗改。

相对坐标与 mean aggregation 提供点序不变和水平平移一致的结构基础；**没有旋转等变、障碍通量守恒、Navier–Stokes 约束或几何迁移定理**。这是应承认的物理边界，而非增加模型名字的理由。

### 4.2 训练目标及真实实现边界

固定同一学生容量，采用规范化分布锚与源证据约束：

\[
\min_\theta R_{\rm density}(\theta),\quad
\text{s.t. }R_{\rm evidence}(\theta)
=\tfrac12 R_{\rm pair}(\theta)+\tfrac12 R_{\rm dir}(\theta)\le\tau,
\tag{6}
\]

\[
R_{\rm pair}=E[(\Lambda^\theta_{b:a}-\Lambda^T_{b:a})^2],\quad
R_{\rm dir}=E[(d^\top\nabla_s\ell_s^\theta-d^\top g_s^T)^2].
\tag{7}
\]

密度锚由合格实际训练观测 NLL 和教师联合样本的交叉熵构成。对偶更新、MSE、Adam 均是标准优化，不能被列为第四创新。

源码复审确认：`train_student` 支持 `nll`、`distribution`、`privileged_pair`、`mean_log`、`projected_evidence`、`projected_no_anchor`。初审只有endpoint pair的问题已修正：现在在源对中点 $s_m=(a+b)/2$，用 `torch.autograd.grad(..., create_graph=True)` 计算沿 $d=b-a$ 的方向导数，真正反传至学生参数，并与端点误差等权构成式(6)。教师 `build_targets` 提供投影方向标签以及对应的raw/mean-log对照。

准确的已实现能力是**端点＋中点方向训练**，不是整条路径每个积分节点都受到监督；完整路径积分仍用于教师一致性证书。中点误差小不能证明整条路径上的统一误差界。运行成功需另引用本轮 `artifacts/v2/` 收据，源代码存在不等于已达到训练约束或改善定位。原生 C 始终另行资格，不因加入 surrogate 方向损失而自动完成。

### 4.3 复杂度与信息权限

设源数 $N_s$、机制数 $N_c$、历史长 $T$、教师原子数 $K_T$、学生模式数 $K_s$。学生一轮全候选历史计算约为 $O(N_sN_cTK_sC_{
m GRU})$；教师条件标签约为 $O(K_T(2T+L)C_T)$，每个 $J$ 点路径再乘 $J$。训练方向损失需参数—源混合二阶自动微分，显存与时间必须单独计费。不能只报小学生推断时间而隐去全源教师标签成本。

部署接口不传真实源；离线训练源标签是合法监督，不能混淆二者。未来动作可从训练路线/合法候选生成，但不能按未见源实际响应库或未来真风选择。当前固定每个训练历史的短动作后缀能验证接口，不能替代广覆盖主动动作训练。

## 5. T1—T4：究竟蒸馏什么

| 目标 | 合理用途 | 关键不足 | 本版地位 |
|---|---|---|---|
| T1：完整三维物理状态/浓度 | 教师训练、诊断、可选辅助表示 | 单条局地历史未必唯一确定全场；MSE 受大体积背景支配 | 不作主目标 |
| T2：特权源 posterior | 可作为标准软标签蒸馏强基线 | 随先验/候选集合变化；单独不能生成未来观测 | 必须比较，不能错误排除 |
| T3：源对 evidence / conditional source score | 与竞争源 margin 直接对应 | 单独不确定观测出现频率，不能独立支撑 EIG/风险 | **主监督，保留密度锚** |
| T4：教师动作/价值 | belief 合格时可辅助策略 | 知真风/真源的 oracle 动作一般不可部署 | 作为下游标准对照，当前不直接模仿 oracle |

对 T2 必须公平：同一个正确联合模型下，$E[p(S\mid H,Z)\mid H]=p(S\mid H)$。普通正确的分布蒸馏在总体上也可得到合法混合；显式投影的价值应在有限样本、候选源反事实一致性及目标方差上验证，不能声称所有未显式投影的 CE 都数学错误。

## 6. 为什么可能有效，以及不能证明什么

对真实源 $a$ 与竞争源 $b$，真实未来分布为 $P_a$，模型为 $Q$：

\[
E_{P_a}\log\frac{Q_a}{Q_b}
=D_{KL}(P_a\Vert Q_b)-D_{KL}(P_a\Vert Q_a).
\tag{8}
\]

一个源的预测误差下降不能决定两个项如何共同变化。M1 直接限制两源对数差；若路径上方向导数误差不超过 $\epsilon$，路径长为 $d$，则端点证据差误差不超过 $d\epsilon$（再加数值积分误差）。只有 teacher margin 超过该误差和教师物理失配时，才可保留判别方向。训练点均值 MSE 下降不是这项统一上界的证明。

`tests/test_v2_projection.py` 的有限模型反例给出：正确未来源 score 为 0.15625，固定历史 belief 会给 0，遗漏历史归一项会给 0.46875；这些是结构性失败的数值证伪测试，不是气源定位收益。另一测试中源比逐观测完全相同，但未来 EIG 不同，说明只监督 ratio 而丢弃密度锚不能恢复完整主动功能。

物理不可辨识边界是：对所有合法动作块 $Q$，若 $P_a(Y_Q\mid H)=P_b(Y_Q\mid H)$，没有蒸馏、纠错码或规划能创造源信息。另一方面，学生当前无认证反证功效也可能是机制集合太大、MC 半径太保守或模型丢失差异，不能直接宣布物理不可辨识。

## 7. 与 M2/M3 的技术联系及独立性

M2 的具体母机制来自计算生物学 CDN 的观测/参考条件共享表示差分。本项目把参考改成逐源名义响应，只将诊断作为全支持机制提议，并在 likelihood 中撤销和替换旧后缀。精确枚举无需诊断网络，因此**“回放有效”不能证明“诊断网络有效”**；后者应在相同计算预算下比随机/先验提议。[CDN](https://proceedings.mlr.press/v267/wu25v.html)

M3 的具体母机制来自 ISIT2025 clustered ASHT 的动作相关假设聚类与分阶段鉴别。气源二次改造使用联合软码本、额外污染邻域、风险—功效 LP 与恢复列表。额外翻转/擦除不是正常羽流间歇的另一个名字。MC TV 半径只覆盖模型内部采样误差；列表是调度机制，不是累积有效置信集。[ASHT](https://arxiv.org/html/2501.11459v2)

统一闭环是：账本 → M1 历史密度 → M2 源—机制后验/回放 → M1 未来联合采样 → M3 合法动作块 → 实测观测回账本。teacher 不在线。删除 M1 的源监督仍可运行 M2/M3；删除 M2 可以保持名义机制；删除 M3 可运行同模型联合 EIG，故模块可以独立消融。

## 8. 六篇以上 2025—2026 扩展文献的资格与用途

下表不是再增加八个模块。全文访问范围、方法公式与代码状态详见 `docs/literature/MOTHER_METHOD_AUDIT.md` 和 `docs/data/GEOMETRY_OPERATOR_LITERATURE_VERIFICATION.md`。本轮由母算法、理论与数据三个代理分工核验；未运行这些作者代码。

| 论文 | 实际可借运算 | 已检查范围/代码资格 | 本项目合理作用与限制 |
|---|---|---|---|
| [MIST-WM，ICML2026](https://proceedings.mlr.press/v306/feng26aa.html) | 可学习门控 + 任务目标 + 因子条件轨迹对 | 全文方法/实验/附录；未核实可下载代码 | 任务目标选择、成对轨迹强对照；源静态不可干预，不能搬其识别保证 |
| [LANO，AAAI2026](https://ojs.aaai.org/index.php/AAAI/article/view/37001) | masked latent attention、部分卷积边界扩张、MPT遮蔽训练 | 正式9页方法/实验/消融，独立附录未读；作者 `Kingyum-Hou/LANO` 有源码 | 稀疏场重建基线；场预测不等于源判别 |
| [RID，AISTATS2025](https://proceedings.mlr.press/v258/dissanayake25a.html) | 教师任务过滤器与学生过滤器交替优化、按方差加权残差 | 正式页及全文§4–5、Eq10–13；正式页有作者软件 | task-aware distillation 强基线；理论条件 $I(\epsilon;Y\mid f_s(S))=0$ 不由 MSE 自动满足 |
| [Compositional SBI，ICLR2025](https://arxiv.org/html/2411.02728v2) | 局部转移 posterior score 的组合与重复先验校正 | 全文方法/实验/§5.2局限；`mackelab/markovsbi` 可读 | 完整状态教师对照；原文不覆盖 HMM，不能直接用于原始气体历史 |
| [RoPE，ICML2025](https://proceedings.mlr.press/v267/wehenkel25a.html) | 任务统计上的半平衡熵 OT → 仿真后验软混合 | 全文 Eq2–3、消融、局限；完整作者代码未核实 | 真实域校准对照；需要独立校准标签和支持，不能补出缺失的源依赖 |
| [RIGNO，NeurIPS2025](https://arxiv.org/html/2501.19205v2) | 物理点→区域网格→多尺度消息→查询点；edge masking/fractional pairing | 全文方法、附录A/B/F8/F9；JAX源码可读 | 不规则几何编码强基线；大幅源中心位移的 Smooth Transport 明显退化 |
| [SNI，ICLR2026](https://arxiv.org/html/2504.00510v2) | 随机局部域训练 + 重叠子域 Schwarz–Richardson 拼接 | 数据代理读正式28页及附录C/D/G；`questionstorer/sni` | 几何外推备选；收敛前提不能迁到未知湍流平流 |
| [Gen4Turbulence，Nature Communications2026](https://www.nature.com/articles/s41467-026-70145-4.pdf) | time-conditioned UNet、L1/感知/RaGAN；稀疏重构另用conditional GAN/EDM | 数据代理读正式17页，方法/消融/代码；本代理HTML入口受登录重定向 | 谱/场保真基线；不同任务不可混为一个算子，“zero-shot”限同几何新mask |

GFNO2026 的 DOI/正式题录已核对，但全文403、只有摘要可读，**不计入上述方法级深读数量**。HIB 和 TWIST 保留为相关基础/直接蒸馏基线，分别是 CoRL2024（2025出版）和 ICRA2024，不冒充2025/2026新会议论文。

## 9. 一次决定性的实验链

| 比较 | 固定条件 | 若没有优势，必须怎样判决 |
|---|---|---|
| 原生 PMFS vs 同容量合法联合 NLL | 相同真实航次/候选支持/readout | 只有该比较获胜，只能主张结构重构有效 |
| NLL vs 标准分布蒸馏 | 同学生、同teacher、同动作/样本预算 | 若相同，teacher额外训练成本未体现价值 |
| 标准蒸馏 vs 投影证据 | 同容量、同teacher、同生成样本 | 若相同，不主张源证据监督独立收益 |
| projected endpoint vs qualified directional/path | 相同网络、联合分布锚与目标预算 | 若相同，保留简洁端点版本；不硬保连续微分贡献 |
| true-world raw target / mean-log / shared-belief / missing-normalizer | 仅受控机制诊断，明示错误或oracle对照 | 不能把击败故意错误对照当主性能证据 |
| M2回放 vs名义；诊断 vs同预算随机/先验 | 固定M1、先验、候选与机制目录 | 分开回放价值和诊断价值 |
| M3 vs联合EIG、鲁棒EIG、ASHT | 固定M1/M2、动作集合、成本、阈值 | 若无附加功效/恢复收益，缩减M3贡献而非改评测集 |

判据应首先是冻结未见源的 Top-1、MAP/Top-5%误差、真实源margin、后验可靠性、原正确案例退化；之后才是浓度误差。对相同物理 realization 的配对结果按 episode/realization 分层 bootstrap，不能把重叠窗口充当样本量。

House02 是已打开的数值开发资产；S2 是单源短时接口资产。它们不能拼成“已合格多源三维教师”。未来所需资产与独立 House03 留出、有限补数规模见 `docs/data/HOUSE_TO_LAKESHORE_TRANSFER_CONTRACT.md`。至少 10% 稳定改善是目标，不是修改真源/阈值/留出集的许可证。

## 10. 源码审查的必要限定与最终评分

只读检查覆盖 `m1_neural/model.py`、`teacher.py`、`training.py`、`m1_distill/projection.py`、`m2_replay/engine.py`、M3代码及数据资格报告。

必须保留以下边界：

1. 缺测读出当步删除对应密度项是精确的通道边缘化；GRU 用零值与mask更新不等于对缺测值影响的整段隐藏状态做精确积分。准确说法是**给定缺测协议的归一化序列模型**。
2. bank 的 metadata/hash 是来源检查，不是独立物理校准证明。原生导数、teacher calibration、源条件覆盖均须外部证据。
3. 原生部署适配器必须接受 V2 checkpoint 并检查 scope；V1 JSONL 能运行不自动代表 V2 神经模型已接入。最终接通状态看独立运行收据。
4. resume 必须固定 dataset、teacher bank、teacher checkpoint、目标文件哈希和训练目标；否则不能把续训当同一实验。
5. 缺失合格局地风、真实时间和机制目录时，保持数值/接口资格，不能静默启用原生主动运行。
6. 当前是单源二维候选、固定声明源高度和释放/传感器协议；未知排放强度、浮力、多个同时气源及新型传感器故障不自动属于现有机制目录。源—传播不可辨识不能靠扩大自由机制偷偷解决。

设计成熟度按用户六维权重、每项10分给出：失败匹配8.5、二次算子深度7.2、文献机制8.0、当前可实现性6.0、理论可能性8.0、计算/解释性7.0，加权 **7.5/10**。这是“值得按合同完成一轮研发”的判断。原生物理教师与跨源/跨场景稳定收益尚缺，**论文实证准备度仅 2.5/10**；受控接口与数学测试不能抬高该项。

拟发表贡献应收缩为：提出合法历史条件的源证据监督算子；建立可审计的错误解释撤销与源—机制重算；在同模型风险约束下实现低概率源可恢复的主动反证。三项都需要强基线和独立收益。无需声称每个组成数学工具从未出现，但必须证明气源二次改造产生了不能由更简单标准方案同成本替代的作用。

### 本审查实际读取的 V2 收据

以下是审查截面已经存在的结果，后续全量运行汇总交由最终工程审计追加，不将正在运行任务预写为成功。

| 路径 | 已读取事实 | 不能据此声称 |
|---|---|---|
| `artifacts/v2/tests_initial.xml` | 81项、0失败、0错误，9.350秒；本轮初始测试 | 最终所有代码修改都已经再次验证 |
| `artifacts/v2/teacher_engineering/training_receipt.json` | 82,733参数、48训练episode、4外生world、8epoch、CPU 4.929秒，`ENGINEERING_ONLY` | GADEN物理teacher合格；真实三维泛化 |
| `artifacts/v2/student_nll/training_receipt.json` | 同模型20,139参数、8epoch、48独立工程lineage、CPU 3.346秒 | 新源证据监督优于NLL |
| `artifacts/v2/house_student/training_receipt.json` | 20,139参数、恢复至40epoch；当前恢复段60.039秒；192路线样本来自96原lineage，`NUMERICAL_ONLY` | 192个独立物理世界，或40epoch全程只有60.039秒；House高阶teacher或M1独立收益 |
| `artifacts/v2/house_numerical_data/PROTOCOL_FREEZE.json` | 2条事前固定探针序列；0.1ppm数值LOD取原ordinal首边界；未打开测试响应字节；无真实时钟/主动资格 | 该数值LOD是实飞仪器标定；路线为原生主动选择 |
| `artifacts/v2/projected_targets/targets.json` | 32条完整训练目标，含端点、源对中点方向及路径一致性证书 | 32个新独立世界、已训练student或已证明方向loss有效 |

四层 M3 功效诊断的额外独立接口收据由数据代理实际生成：`v6_work/m3_batch_diagnostic_receipt.json`（发布时由工程汇入 V2 artifacts）。其scope明确为未训练工程接口，名义clean至污染/TV层功效变化只用于回退原因检查，绝不是定位成绩。


**实现归因补充：** HIB 的 cosine/IB 对齐、MIST-WM 的门控/InfoNCE 与探索技能均未在 V2 实现；它们仅作为动机或待实现强基线，不计为已完成的直接母算法迁移。
