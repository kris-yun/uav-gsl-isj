# V7第二轮：PNAS联合通道与可实施M3

日期：2026-10-23。独立稿已冻结，本文是在root披露X和数据边界之后的建模审查。未查看V2代码，因此关于其保守LP的分析是结构比较，不是假装定位了实现bug。

## 1. 决策建议

建议主信号采用PNAS式odd/even通道，但后验由**同一个候选条件联合原始块模型**产生；M3采用TIT2025的完整候选对证据和探索结构，配合ICASSP2026的成本频率优化，允许指定challenger绕开零最小值，不用普通聚类删源。审计作用于决策/停止，绝不再乘进源后验。

分开三件事：

1. **源概率图**：每个新raw block只更新一次，所有合法源保留。
2. **动作分配**：用当前估计通道的pairwise KL；可以承担规划估计风险，不要求最坏情况KL下界正才行动。
3. **置信候选列表**：从新数据起点运行共享有限nuisance的split-likelihood e-process；对精确通道有模型内保证，对估计通道只有待验证的经验覆盖率。

这样避免“最坏nuisance下界全为0→全退EIG”的单一失败路径。若通道真的不区分某对，算法应给出未分开的源集合，并继续预留覆盖采样；不能把不辨识伪装成算法成功。

## 2. X与独立母模块比较

|模块|真正能提供什么|在本任务中的位置|必须避免的误用|
|---|---|---|---|
|PNAS2026 MNM|双侧时间信号的交换反对称响应，输出中心线左右方向倾向|候选条件联合通道的固定可解释变换/摘要|把sigmoid输出当16源后验；把sum/gradient/motion独立相乘|
|Nature2026 vector navigation|按历史运动与气味经历维持返回方向|短程返回/几何探测动作的提议器；由概率模型评估其价值|把返回边界方向等同源方向；把动作向量当新增测量|
|ISIT2025 clustered ASHT|按已知条件分布聚类，重复动作后排除整个簇|可作计算加速或簇级诊断对照|早期错误把真源从alive集合删掉；声称其自动恢复B4|
|TIT2025 pairwise evidence|完整误判指数关系、全部对手阈值与探索|M3的推断/探索结构|把渐近定理声称为5步保证|
|ICASSP2026非等cost ASHT|正确区分资源份额与动作抽样频率的小LP|M3成本分配|把逐动作除成本得到的资源份额直接当抽样概率|
|FUSION2025 block-SBL|跨域共享位置、独立未知幅度、参数化向量响应|给联合通道提供nuisance建模检查|单源16候选用gamma归一作概率；无新形状仍声称超分辨|

PNAS全文核验：原文双侧间距0.46mm、0.5s窗口，motion特征延迟约0.017s；MNM中f1/f2是时间滤波器。其sum对“中心线左/右”AUC约0.5，**不意味着sum对源位置无信息**。ISIT原文Algorithm 1第11步确实以交集更新alive，真源被删后没有重新进入机制。[P1/P2]

Nature论文出版社全文本次受重定向阻塞，本文仅使用root披露的返回向量机制，不对该文新增未经核验的公式或实验数字。

## 3. 当前数据究竟允许什么

以下数据事实来自root披露，未由本人读取文件核验：公开cube为50秒间隔、10快照；有64个source×seed discovery，近期工程先处理4seed×2source的同期平面，完整native filaments在用户本地。

|可做|不可据此声称|
|---|---|
|同一快照上左右两个空间位置的浓度、sum和差；源条件静态联合分布的初步比较|连续时间运动响应；0.017s或任意细时延的MNM复现|
|2源错先验恢复的最小检查|16源M3混合动作/聚类性能已验证|
|按seed留出，整个seed的全部位置/快照一起留出|把同一seed内大量像素/时间点算作独立重复|
|检查不同候选的空间joint形状是否不同|仅4seed就得到已校准的高置信源后验或精确真实KL|

两源时，非等cost max–min只有一个对手，最优解退化为单个动作\(\arg\max_aD_{12}(a)/c_a\)。因此2源pilot不能证实多源混合频率优化的独立价值，需要至少3源且互补的动作才能检验那个机制。

**硬件边界**：同一平面取\(x_L,x_R\)是同步双点的离线观测。若实机只有一个传感器，不能把它当无人机同一时刻可得的两次测量。必须是双传感器配置，或在native上模拟真正的异时轨迹\((x_L,t),(x_R,t+\Delta t)\)并包含传感器响应。双方基线使用相同传感器、相同采样次数和总飞行/驻留成本。

## 4. 保留边缘浓度且不重复计数的联合通道

### 4.1 原始块与odd/even变量

令一个新的、不重叠的原始块为

\[
Y_t=(L_{t,1:m},R_{t,1:m},U_{t,1:m},X_{t,1:m}),
\]

其中姿态/位置与风若是外生已知协变量，可以在密度中条件化，而不是重复计入被解释的浓度结果。定义even/odd原始序列

\[
S=(L+R)/2,\qquad D=(L-R)/2.
\]

\((L,R)\leftrightarrow(S,D)\)可逆，常数Jacobian在源比值中消去。PNAS响应

\[
H=\operatorname{ReLU}(f_1*L+f_2*R+b)
-\operatorname{ReLU}(f_1*R+f_2*L+b)
\]

是\(Y\)的确定性函数。合法低维模型是\(p_s(S,H\mid a,F_{t-1})\)，等价可写\(p_s(S\mid a,F)p_s(H\mid S,a,F)\)。若选三个cue，则必须是\(p_s(S,G,M\mid a,F)\)，而非三个边缘密度的乘积。

**原始joint是强基线**：\(p_s(L_{1:m},R_{1:m}\mid a,F)\)或等价\(p_s(S_{1:m},D_{1:m}\mid a,F)\)。MNM压缩可能帮助小样本估计，却不创造额外信息；按数据处理不等式，真实最优源判别的信息不可能超过原始joint。

### 4.2 保留既有边缘模型的具体做法

为隔离联合结构的收益，先让joint基线与新法共用同一边缘浓度模型\(F_{s,L},F_{s,R}\)。连续部分可以用copula：

\[
p_s(l,r)=p_{s,L}(l)p_{s,R}(r)c_s(F_{s,L}(l),F_{s,R}(r)).
\]

零浓度原子/离散量化不能直接套连续密度公式，应使用CDF矩形概率。更易实现的是共同分箱后的二维概率表，以IPF匹配固定行/列边缘，再使用带收缩的联合依赖。此处copula/IPF是经典算子，不主张新颖。

浓度尺度、joint残差和传感器nuisance必须使用相同校准数据。不能旧法只给浓度均值，新法偷偷多拿全场随机种子再声称“滤波器更强”。

若完整浓度似然已包含\((L,R)\)，再加\(p(H\mid s)\)是重复证据；正确的\(p(H\mid L,R,s)\)为\(\delta[H-g(L,R)]\)，它不改变源比值。**audit也使用这些raw block，但只决定何时确认，不再作为额外似然乘回概率图。**

### 4.3 反例：为什么不能丢sum

两个源在同一上风中心线上、距离不同。观测点在中心线附近，两个源都可能产生平均\(D\approx0\)、\(H\approx0\)，而浓度和\(S\)分布因距离/源率约束不同。此时仅用odd通道丢掉已有的源距离证据。PNAS的左右判别任务中sum无效，不能推导此处sum无效。

### 4.4 反例：静态MNM退化为经典梯度

没有时间窗时取\(f_1=\delta,f_2=-\delta,b=0\)，则

\[
H=\operatorname{ReLU}(L-R)-\operatorname{ReLU}(R-L)=L-R.
\]

一般静态线性权重也只有\(H=\operatorname{ReLU}(A S+B D+b)-\operatorname{ReLU}(A S-B D+b)\)，是\((S,D)\)的门控摘要。它可作结构先验，却不能被称为新运动信息。

### 4.5 传感器滞后与共享nuisance

用\(\eta=(q,\tau_L,\tau_R,b_L,b_R,z_{0,L},z_{0,R},\text{风校正})\)的固定有限网格作为初始可执行模型。不同左右响应时延本身可制造假运动；先以同气室/同输入校准\(\tau_L-\tau_R\)，并在全部候选下共同积分或剖面化。若nuisance跨块固定，必须

\[
p(Y_{1:T}\mid s)=\sum_\eta w_\eta\prod_t p(Y_t\mid F_{t-1},a_t,s,\eta),
\]

而不是\(\prod_t\sum_\eta w_\eta p(Y_t\mid\cdots)\)。后者悄悄改成每块重抽nuisance，会把长期一致性信息丢掉，也可能改变错误置信。

## 5. same-past conditional channel：接口的精确定义

建议\(P_t[a,s,\eta,o]\)表示

\[
P(Y_t=o\mid F_{t-1}=f_{t-1},A_t=a,S=s,\Eta=\eta).
\]

所有\((s,\eta)\)都条件于**同一个已经实际发生的过去\(f_{t-1}\)**。允许不同候选对潜在传感器状态/输运状态产生不同的条件预测，但不能对各候选换成它自己的“假想过去”，不能把真实源标签、未来快照或待观察块用于构造这一轮通道。

`FiniteChannel(probabilities[action,source,nuisance,outcome])`单张表对应最简条件无记忆/已封装成独立块的环境。真实时间相关气体若未被状态吸收，不满足该假设。扩展时可以每轮产生一张**在观察当前outcome之前冻结**的\(P_t\)；同一\(\eta\)索引必须始终表示同一物理参数，审计累积该索引对应的条件似然。不能每轮把索引0改成不同的“最有利拟合”。

窗口重叠要么改用不重叠块，要么对新增样本使用

\[
\log p(Y_{1:t}\mid s,\eta)-\log p(Y_{1:t-1}\mid s,\eta).
\]

旧样本可用于滤波器记忆、动作选择和状态估计，但不能再次作为独立似然增量。离线为每个候选动作查询forward模拟样本用于规划不等于真实观察该动作；只有执行动作返回的一个结果更新后验。

## 6. M3最小实现

### 6.1 持久状态

```text
legal_sources                       # 固定物理合法集合，不能用posterior阈值删除
log_joint_weight[source,nuisance]    # 全部raw block单次更新
audit_loglik[source,nuisance]        # 从审计新起点开始，初值全0
audit_log_alt[source]                # 可由固定备择混合的audit_loglik直接计算
audit_max_log_e[source]              # 记录曾越界；与当前列表可分开
paid_cost, remaining_cost
source_independent_coverage_schedule # 固定ν或提前指定的轮换表
```

主后验：\(\pi_t(s,\eta)\propto\pi_0(s,\eta)\exp\sum_{k\le t}\log P_k(a_k,s,\eta,o_k)\)。源概率对\(\eta\)求和。规划用\(p_s^a(o)=\sum_\eta\pi_t(\eta\mid s)P_{t+1}(a,s,\eta,o)\)，不是乘上\(\pi_t(s)\)之后的混合。

### 6.2 动作与全候选pair diagnostics

对安装的有限通道计算

\[
\widehat D_{ij}(a)=\sum_o p_i^a(o)\log[p_i^a(o)/p_j^a(o)].
\]

这是**当前安装模型的精确离散KL**；若通道来自4seed拟合，它不是实际环境真实KL。若需要概率平滑，应统一在通道建模时施加并记录，不能在动作函数中静默clip后仍声称精确通道。

普通轮：当前incumbent\(i\)，解完整对手的成本LP

\[
\max_{y\ge0,v}v,\quad c^\top y=1,\quad
\widehat D_{ij}^\top y\ge v\ \forall j\ne i,
\quad\lambda=y/(1^\top y).
\]

挑战轮：外部可指定任意合法\(j\)，即使\(p_j\)极小；执行

\[
a^*=\arg\max_{a\in\mathcal A_{\rm feasible}}
\frac{\min(\widehat D_{ij}(a),\widehat D_{ji}(a))}{c_a}.
\]

双向最小值是本稿的实施修正，不是声称原文同式。它让所选动作能在两种真相方向都给证据；完整恢复证明仍由下述coverage保证。

若全对手LP最小值为0，不回EIG：选择一个未充分审计的合法challenger做定向辨识；若该对在全部动作上也为0，记录不可分标记并执行coverage。零KL并不授权排除那个候选。可以在后续实现中使用带饱和上限的pairwise证据覆盖目标，但第一版不必增加这一层。

最终动作频率\(\rho=(1-\varepsilon)\lambda+\varepsilon\nu\)，\(\nu\)预先给定且不依赖源后验。其动作必须计费；在固定预算内，coverage动作替代普通动作。若昂贵辨识动作可能被剩余预算排除，事先保留审计预算，不能仅在即将耗尽时说有coverage。

应输出：完整\(D_{ij}(a)\)、所选challenger、全对手LP值、不可分对、\(\lambda,\nu,\rho\)、期望动作成本\(c^\top\rho\)、实际累计成本和coverage实际执行次数。

### 6.3 低posterior不会消灭探索的证明

先限于精确、固定有限通道，正先验，不提前停止，且log-likelihood比有适当有界矩/鞅大数条件。设真实源\(s_*\)，任意错源\(j\)，每对有至少一个coverage支持动作使真实条件KL正。若每轮\(\rho_t(a)\ge\varepsilon\nu(a)\)，则

\[
\mathbb E_{s_*}[\Delta\log L_{s_*}/L_j\mid F_{t-1}]
=\sum_a\rho_t(a)D(f_{s_*}^a\Vert f_j^a)
\ge\varepsilon\sum_a\nu(a)D(f_{s_*}^a\Vert f_j^a)>0.
\]

右端不含\(p_t(j)\)或\(p_t(s_*)\)。因此错误高后验不能关闭这个证据来源；在上述条件下对数赔率最终向真源漂移。对固定有限复合nuisance，需更强的辨识条件：对真\((s_*,\eta_*)\)与所有错\((j,\eta)\)的累计coverage KL都发散。若某错源+nuisance能复制真通道，恢复保证不存在。

这不是5步保证。若只有一个有信息动作，且\(\varepsilon=0.25\)、16个均匀coverage动作，则5步内至少试一次该动作的概率仅\(1-(1-0.25/16)^5\approx0.076\)。任何论文名都不能消除此资源限制。指定challenger及数据驱动动作集中可改善实际效率，必须同预算实测。

### 6.4 与V2保守LP的实质区别

V2具体代码未读。针对“所有不确定性下界都近零”的结构，区别是：

- 规划用安装模型的点估计KL，输出估计风险；不把小样本置信下界归零作为禁止行动的理由。
- 可显式挑选任何合法challenger，单个不可分源对不能使全部动作瘫痪。
- 固定coverage独立于posterior，也独立于LP是否成功。
- 判决另由新数据审计决定。不会因为规划采用乐观估计就把过大的模型信心当真。

这是一种规划与确认的责任分离，不能宣传成对未知环境“无模型失配保证”。

## 7. 共享有限nuisance审计：最容易写对的版本

审计起点\(t_0\)只由此前历史选择。对每个源、每个固定nuisance，累计新数据

\[
A_{s\eta}(t)=\sum_{k=t_0+1}^t\log P_k(a_k,s,\eta,o_k).
\]

对检验\(H_s\)，备择使用所有其他合法源+nuisance的固定、正、归一权重\(w^{(-s)}_{j\eta}\)，例如均匀权重，且不使用旧错误源后验：

\[
\log Q_{-s}(t)=\operatorname{logsumexp}_{j\ne s,\eta}
\{\log w^{(-s)}_{j\eta}+A_{j\eta}(t)\},
\]

\[
\log E_s(t)=\log Q_{-s}(t)-\max_\eta A_{s\eta}(t).
\]

这是可直接实现的有限上确界。\(Q_{-s}\)等价于按audit过去更新备择混合权重后再预测下一结果，因此是非预知的正规序贯密度。原始后验仍按全部历史更新一次，绝不把\(E_s\)乘进去。

**证明**：对任意真nuisance\(\eta_*\)，分母\(\max_\eta\exp A_{s\eta}\ge\exp A_{s\eta_*}\)。故\(E_s\)不超过\(Q_{-s}/\exp A_{s\eta_*}\)，后者在真实\(H_{s,\eta_*}\)下是非负检验超鞅；在绝对连续/全支持条件下是通常的均值1似然比鞅。Ville不等式给出\(P(\sup_tE_s\ge1/\alpha)\le\alpha\)。这继承经典通用推断原理；有限网格只是让上确界计算无局部优化漏洞。\(E_s\)自身不必是超鞅，支配关系已足以给出e-process保证。

输出两个清楚命名的集合可避免语义混乱：

- `compatible_now = {s: logE_s < log(1/alpha)}`：当前证据下未被排斥，可随证据减弱重新进入；同时覆盖保证仍由sup事件控制。
- `not_rejected_since_start = {s: max_logE_s < log(1/alpha)}`：本轮审计从未被拒绝的源。

两个集合都不是源概率图。源后验和合法规划集合不因audit列表变化而删除物理候选。若要永久停止，建议使用预先规定的列表规则；空列表是模型不足/低概率审计事件提示，不能归一化\(1/E\)强行出一个高置信源。重复新开审计要使用预先分配的\(\alpha_r\)，而非每次重置成同一个\(\alpha\)。

## 8. 通道估计风险必须怎么说

若`probabilities`是已知模拟环境的真正条件概率，上述有限通道证明成立。若它是从有限seed、插值、KDE、分类器或经验频数估计的\(\widehat P\)，证明只相对安装的\(\widehat P\)成立。仅“每轮只用过去拟合”并不能保证\(\widehat P=P_{true}\)，不能宣称真实错误率≤α。

可以用以下准确表述：

> e-process在指定有限条件通道族内满足任意停止误差控制。对GADEN估计通道，本实验报告留出seed的候选覆盖率、错误高置信率和恢复曲线，不把模型内α解释为已证明的实环境错误率。

若未来确有独立校准得到、以至少\(1-\beta\)概率包含真实通道的统一不确定性族，并对该族计算合法上确界，整体错误才可界为\(\alpha+\beta\)。有限网格漏掉连续真参数、误用当前数据校准、未建模时间依赖均会破坏这一论证。无需第一版就做大规模鲁棒族；先正确标注模型内保证。

## 9. 最小检验矩阵

1. **joint强基线**：同源同forward样本拟合\(p(L,R)\)/\(p(S,D)\)，对比\(p(S,H)\)，同时保留sum。静态snapshot只做静态版本。
2. **依赖消融**：在同源同条件中打乱左右配对，保持边缘；如果收益消失，才支持联合依赖有用。打乱操作只用于诊断，不能用其假独立数据报告主结果。
3. **同观测政策消融**：同一个joint模型下比较现EIG、全对手cost LP、指定challenger+paid coverage；共同记录总资源。
4. **B4双压力**：错误先验但模型正确；风/滞后/通道失配。分别报告，后者不能用前者的理论替代。
5. **审计消融**：source posterior只更新一次；关闭/开启audit停止规则，检查错误高置信和候选覆盖，不能借audit额外增加一遍观测权重。

4seed×2source作为接口和局部可辨识检查；扩到全部合法源后才评估M3混合频率、不可分对与资源分配。旧时间联合若已包含相同raw block完整条件律，是必须战胜的强基线；MNM的合理优势只能是有限样本结构约束/可解释低维压缩，而非新增信息。

## 10. 来源

- P1：[PNAS2026作者开放全文](https://emonet.biology.yale.edu/assets/papers/2026/2026_brudner-et-al-PNAS-fly-navigational-responses-exploit-plume.pdf)，尤其p.3–6；[作者代码](https://github.com/emonetlab/GradientMotionMultiplePlumes)。
- P2：[ISIT2025全文](https://arxiv.org/html/2501.11459v3)，§III、Algorithm1及§IV假设；[会议DOI](https://doi.org/10.1109/ISIT63088.2025.11195532)。
- [TIT2025全文](https://arxiv.org/html/2405.06554v3)。
- [非等cost ASHT全文](https://arxiv.org/html/2509.11632v3)；[ICASSP2026官方议程](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)。
- [FUSION2025多字典SBL全文](https://arxiv.org/html/2503.12913v2)。
- [序贯split likelihood在2025量子自适应检验中的具体应用](https://arxiv.org/html/2508.21594v1)，式(12)–(15)。
- [Nature2026论文入口](https://www.nature.com/articles/s41586-026-10827-7)：本稿未据受阻全文作额外方法声明。

## 11. 实现冻结与第四轮声明边界

M3现已实现于 `source_localization_v7/src/gsl_discrimination/m3_audit/`，初次17项、第四轮补充零备择路径检查后18项 `unittest` 均通过。导出 `CoveragePlanner.plan(channel,predictives,source_posterior,step,*,challenger=None,exploit_mask=None)` 与 `AuditLedger.prepare(action)` / `update(action,outcome,event_id)`。M2 mask只限制普通LP，全局coverage保留；zero-min可从tube跳出挑战，绝不退EIG。实现/证明/接口与测试边界详见同目录 `THEORY.md`。独立稿 `radar_independent.md` 保持原冻结，不修改。

第四轮收到root已冻结OCB静态pilot结果：训练集选probe12/17、间距7m，四个development world各10快照；mean为31/40，raw joint Gaussian为40/40，even/odd Gaussian同为40/40且差异仅4.51e-17，静态M1 histogram为31/40。本人未重跑或按此调参。该结果支持所选离线空间联合观测有信息，也明确表明EO可逆重参数化不创造信息；它没有显示静态M1优于原始joint强基线。7m同步双点尚未成为合法UAV硬件/时序观测方案，40个快照也不是40个独立seed。两源不能检验多源LP混合机制。

后续从安装的估计FiniteChannel采样所得control matrix只能标为L1条件机制测试。它可以揭露成本频率错误、零对瘫痪、错先验停止、nuisance错误与重复计数，不能被表述为M3已经在独立物理观测上提高真实源定位精度或满足实际\(\alpha\)风险保证。
