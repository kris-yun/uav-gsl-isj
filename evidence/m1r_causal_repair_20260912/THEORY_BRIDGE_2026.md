# PMFS M1R：2026 理论桥接核验

核验日期：2026-09-12。范围：只筛选能解释“如何从现有 gas / pose / wind 时间序列恢复源判别信息”的正式 2026 论文；不修改算法，不使用 bank，不训练网络。当前 M1R 的 2/3 House 终点改善、第三 House 退化，以及共同非负事件权无法区分 H01/H02 等事实来自本次任务输入，本报告没有重新运行实验。

**结论：本次有界检索没有找到满足当前条件、可以直接迁移并保证恢复源可辨识性的 2026 方法。** 保留以下两篇作为可核验的结构性支撑：它们分别提供合法历史工具变量的条件矩结构，以及函数变化与噪声变化的区分结构。两者都不能把同一 forward 别名变成可区分源；当前只能支持新的前提门，不能支持“因果主创新已经成立”。

## 1. 历史工具变量与条件矩：有新结构，缺合法工具变量

**Daqian Shao, Thomas Kleine Buening, Marta Kwiatkowska. _Causal Imitation Learning under Expert-Observable and Expert-Unobservable Confounding_. ICLR 2026.**

- 正式录用及最终题名：[ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/4415e8cb0741bc0beb79b316f0856108-Abstract-Conference.html)。会议日程沿用旧题名 _A Unifying Framework for Causal Imitation Learning with Hidden Confounders_，不得误计成第二篇。
- 可核对原文：[正式 PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/4415e8cb0741bc0beb79b316f0856108-Paper-Conference.pdf)，PDF 第 4–7 页，Assumptions 3.2–3.3、Eq. (4)、Definition 4.2、Proposition 4.3、Theorem 4.5；第 24 页讨论非加性失配。

论文把专家动作写成 $a_t=\pi_E(s_t,u_t^o)+u_t^\epsilon$，利用已知有限混杂记忆 $k$ 构造历史 $h_{t-k}$，得到

$$\mathbb E[a_t-\pi_h(h_t)\mid h_{t-k}]=0.$$

关键不是“用了历史”，而是历史必须满足外生性、排除限制和相关性。其病态性量 $\nu$ 控制函数误差相对于条件矩误差的放大；增大 $k$ 会削弱工具变量。完整算法仍训练 rollout GMM 和 policy NN，DML/IV 本身也不是 2026 首创。新增贡献是把两类隐藏混杂统一到这个序列识别结构，而不是重新命名条件 Bayes。

**PMFS 适用门（本报告的迁移推导，不是论文定理）：**

1. 将目标明确写成 $y_t=\mu_s(X_t;\theta)+\epsilon_t$，说明哪些动态、传感器状态与失配进入 $\mu_s$，哪些进入 $\epsilon_t$。加性分解必须有物理含义。
2. 必须能支持 $\mathbb E[\epsilon_t\mid Z_t]=0$，例如 $Z_t=h_{t-k}$。单个滞后相关不显著不证明对完整历史外生；羽流持续性、FOPDT 记忆、闭环 pose 与过去 gas 的反馈都可能破坏它。不能把 pose、wind 或自己的 forward 输出自动命名为工具变量。
3. 同时验证 $Z$ 对候选差异仍有信息。选很大的 $k$ 使残差看似不相关，也可能把源信息一起删去；这对应论文的弱工具变量问题。
4. 条件矩的校准和评估必须用不重叠时间块，相关序列不能把每帧当独立样本。经验不拒绝只算诊断，不能升级为外生性证明。

**当前状态：不通过第 1–2 门。** 任务输入没有提供能排除持久羽流和传感器隐藏状态的合法 $Z$。把现有残差做 kernel regression / GMM 可以运行，但不能据此宣称去混杂或识别真源。

## 2. 反事实残差与机制／噪声分离：更接近失配定位，仍不是源定位器

**Gyeongdeok Seo, Jaeyoon Shim, Mingyu Kim, Hoyoon Byun, Yonghan Jung, Kyungwoo Song. _Dissecting Causal Mechanism Shifts via FANS: Function And Noise Separation_. ICML 2026.**

- 正式会议目录：[ICML 2026 Downloads](https://icml.cc/Downloads/2026)，全文题名对应 poster 62929。
- 原文：[作者仓库 PDF](https://github.com/MLAI-Yonsei/FANS/blob/main/23419_Dissecting_Causal_Mechan.pdf)；[原始 PDF 下载](https://raw.githubusercontent.com/MLAI-Yonsei/FANS/main/23419_Dissecting_Causal_Mechan.pdf)。PDF 首页标注 ICML 2026 / PMLR 306。核对位置：第 3–7 页，Assumptions 2.2–2.8、Theorem 3.2、Assumption 3.3、Theorem 3.4、Proposition 3.7。
- [作者代码](https://github.com/MLAI-Yonsei/FANS)明确先训练基环境 causal normalizing flow；“without retraining”不是不需要训练。

论文在已知 DAG、因果充分性、噪声可逆映射和跨环境不变 link $g$ 下，使用 $X_j=g_j(h_j(PA_j),\epsilon_j)$。把新数据代入基机制的逆映射，得到反事实残差；已发生 shift 的节点若残差仍独立于父变量，归入噪声 shift，否则归入函数 shift。函数和噪声同时变化仍可能不可辨识；其进一步检验需要 generalized affine interaction 与特定基噪声条件。有限样本部分要求逆映射估计误差趋零，提供渐近一致性，并非当前小样本的无条件误差界。

**PMFS 可借鉴的是“先判断失配来自哪里”，不是把 residual independence 当正确源概率。** 以下是本报告的适用门：

1. 用现有物理定义明确父变量集合，包括传感器动态状态；证明或限定无遗漏共同原因。单条移动气体记录通常不能观测全部羽流状态。局部 wind 测量本身不构成完整输运父变量。
2. 只有在可逆物理观测模型可用、且基环境已经校准时，才考虑不用网络直接计算残差。将失配 provider 反演成“噪声”，不满足 FANS 的准确逆映射前提。
3. 先在基环境及独立时间块检查残差—父变量依赖的基线，再看变化。不能把采样位置分布变化、未建模 sensor lag 或 provider bias 都归因为源变化。
4. 源变化必须离开可吸收的噪声／校准等价类。FANS 对可等效为可逆噪声变换的函数变化按不可辨识类处理，不保证区分它们。

一个直接反例（本报告推导）：若错误候选满足 $\mu_{s'}(X)=\mu_s(X)+b$，则其残差为 $\epsilon-b$，仍可独立于父变量。没有独立校准的噪声均值约束时，“残差独立”同时接纳两个源。允许未知 gain 时，相应比例等价也需要单独排除。

**当前状态：不通过第 1–2 门。** 已有 provider + FOPDT 失败不能靠追加“反事实残差”命名弥补。若只想定位失配来源，FANS 提供比 posterior 温度或公共权重更清楚的诊断问题；它没有直接给出可部署的 source evidence。

## 3. 下一步最小门：先检验原始序列中的源对比是否存活

以下是独立的代数推导和实验设计建议，**不是上述论文已经证明的 PMFS 定理，也不是 2026 算法名称**。

令 $X_t$ 是冻结的 raw gas 以外输入及合法历史，$\mu_s$ 是候选响应；$Z_t$ 是具有明确外生性依据的条件变量。选择事先冻结、允许正负的有限测试函数 $q(Z_t)$，定义

$$m_s=\mathbb E[q(Z_t)(y_t-\mu_s(X_t))].$$

两候选差异为

$$m_s-m_{s'}=\mathbb E[q(Z_t)(\mu_{s'}(X_t)-\mu_s(X_t))].$$

因此共同残差基线会消去；区别来自保留时间、浓度、风向变化之后的候选差异，不来自把公共非负事件权换成新缩写。若候选在这些 raw 时序响应上依然相同，上式严格为零。若所有允许的候选差异都能被共享 nuisance 类吸收，投影后也仍为零。

在一个**已证明**真实矩偏差至多 $\eta$ 的模型内，候选矩间隔大于 $2\eta$ 才能排除二者同时解释观测。这只是三角不等式，$\eta$ 不能由“真源最优所需范围”反推，当前 oracle 弃权也不能替代其可部署估计。

建议只做如下有界顺序：

| 门 | 用现有数据能检查什么 | 失败时结论 |
|---|---|---|
| G0 原始信息保留 | 同步 gas 数值、时间戳、pose、wind、采样窗口和传感器状态；查 raw 层是否已出现源别名 | 信息已丢失则停止后续重加权 |
| G1 候选对比 | 先计算原始时间序列上候选差异，再检查其是否落入允许的 gain / offset / lag 等价类 | 共用 nuisance 下等价则不能靠 residual score 修复 |
| G2 合法矩或合法逆映射 | DML 路线需外生性与强度；FANS 路线需基机制、父变量和可逆性 | 只记诊断，不写 causal identification |
| G3 源与失配可分 | 在独立时间块，正确机制须适配，并有至少一个错误候选被同一规则排除；不得仅比较三 House 终点误差 | 全弃权、全部适配或系统反转均不支持主创新 |

G1 能在不训练网络、不新增传感器的条件下先做。若 G1 有差异而 G2 无法成立，下一项工作应是明确缺失的测量校准或设计独立激励，而不是立即运行条件矩算法。独立激励是否允许属于后续研究设计；本报告不授权新增实验。

## 4. 和 ordinary generative Bayes 的边界

直接构造 $p(y_{1:T}\mid s,\theta)$ 并积分或拟合 $\theta$，仍是生成式 Bayes／系统辨识。使用 SCM、do 标签、counterfactual 标签本身不增加可辨识性。用 $\exp(-\lambda\|m_s\|^2)$ 充当证据则是广义评分映射，也不自动成为校准 likelihood。

真正有待实现和证伪的贡献只能是：**在可验证的测量／失配约束下，从原始时间序列取得普通命中图没有保留、且 nuisance 无法吸收的源对比，并证明其识别条件与失败边界。** 条件矩与 FANS 的价值是帮助把这个义务写清楚。当前没有证据允许跳过它，也不应把一般的幅值剖面最小二乘重新包装为 2026 方法。

## 5. 检索范围与访问记录

使用 paper-search 技能作一次 2026 有界多源检索，并通过 ICLR proceedings、ICML 官方目录和作者原文逐项核验；最终只保留上述两篇详细桥接。API 原始记录位于同目录 `theory_search_raw.json`。未经确认的 2026 年份标签、预印本、工作论文与相邻视觉／语言任务没有被作为正式会议理论证据。

已排除的相邻结构中，多分辨率 causal score 路线直接以 $p(Z\mid Y)$ 为目标且需要已知图、观测算子及学习模型；动态表示路线需要另外的可识别图结构及表示训练；线性非高斯条件一、二阶矩独立性路线不能直接覆盖非线性羽流和相关时间样本。它们未被计为可用 PMFS 方案。此前已经判定不可套用的 BHIP、When Shift Happens 和多环境 causal graph 论文未重新评估。

工具限制如实记录：初次 CLI 报 `search_papers.py: error: unrecognized arguments: --json ...`，随后改用同脚本 `search_papers()` API 保存含摘要 JSON；DBLP 报 `Expecting value: line 1 column 1 (char 0)`；Semantic Scholar 报 HTTP 429。OpenReview 对 FANS 要求浏览器验证，改读作者公开 PDF，没有绕过验证。ICML poster 页面被抓取策略阻止，录用状态依据可访问的官方 2026 目录和作者带正式页眉 PDF 交叉核对。没有进行大规模综述；“未找到直接可用方法”仅指本次受约束检索，非全领域不存在性声明。

最终状态：`2026_THEORY_BRIDGE_NO_DIRECT_TRANSFER`；允许推进 G0/G1 的只读证据门；不支持宣称条件矩或 FANS 已修复 M1R。
