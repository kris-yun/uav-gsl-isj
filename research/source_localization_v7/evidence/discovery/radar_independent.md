# V7 独立发现冻结稿：多站定位、未知幅度与主动诊断

冻结日期：2026-10-23。研究代理：radar_independent。

## 0. 范围与结论

本稿只依据任务给定的症状和独立公开文献检索：B4错误高置信；更准的浓度预测未改善源排序；5次观测预测误差≤1位但平均15.7/16源仍相容；既有时间联合、容错码、教师投影没有独立收益；M3曾全部退回EIG。本稿未读取用户新附件、其他代理候选和既有候选报告。冻结后收到的资产信息及其他方向，应另写第二轮意见。

**推荐先检验两个相互独立的母模块，不能把它们直接宣布为最终方案：**

1. **多参数化字典的共享位置支持与未知幅度分离**：Möderl等，FUSION 2025。借用“不同观测域共享位置、各域可有不同未知幅度，直接比较向量响应”的具体结构；对单源16候选改成one-hot精确枚举。它能给出源概率，但必须有除幅度、基线、时延之外仍不同的响应形状。
2. **完整候选对的主动诊断与非等成本采样**：Hsu–Wang，IEEE TIT 2025；Vershinin等，2025预印本/ICASSP 2026。借用所有候选对的似然证据、误判预算及按期望成本分配样本频率。它可让低后验合法候选仍获得辨识动作，不需要NN；它不增加原始观测中不存在的信息。

两条必须拆开做消融。前者是观测模型，后者是行动/停止规则。若使用同一联合观测分布时前者退化成已有时间联合，或后者只在不可分候选上改目标函数，均应明确判无独立贡献。

**最重要的反例是：平移不变匀速对流中的两站时延差不含源位置。** 能测出同一气团的移动速度，不等于能定位气团释放点。因而不推荐把GCC、TDOA、GLRT重新包装成2026气源定位算法。

## 1. 已读来源与证据强度

|编号|来源与日期|实际读到的内容|证据/代码状态|
|---|---|---|---|
|R1|Möderl, Westerkam, Venus, Leitinger, *A Block-Sparse Bayesian Learning Algorithm with Dictionary Parameter Estimation for Multi-Sensor Data Fusion*, FUSION 2025；arXiv v2 2025-11-04|全文HTML，信号模型、证据优化、参数更新、Algorithm 1、单/多雷达实验|原文给Python `scipy.optimize`实现信息；本次未找到该篇作者公开代码，不能写“开源可直接运行”|
|R2|Hsu & Wang, *Tradeoffs Among Action Taking Policies Matter in Active Sequential Multi-Hypothesis Testing: The Optimal Error Exponent Region*, IEEE TIT 71(9):6546–6565，2025-09，DOI 10.1109/TIT.2025.3588527|全文HTML；模型、指数域、随机行动、全部对数似然阈值、探索率及证明|已由台大机构记录确认期刊出版；主要是理论和指数区域数值图，没有气体或机器人恢复实证|
|R3|Vershinin, Cohen, Gurewitz, *Active Sequential Hypothesis Testing with Non-Homogeneous Costs*, arXiv 2509.11632v3，2025-09-30；ICASSP2026官方议程|全文HTML，式(2)–(9)、LP变换、Theorem 1、32假设16动作实验|已确认会议接收；算法推导易重写；未找到作者公开代码|
|R4|Liang & Meyer, *Sparse Signal Reconstruction for Track-Before-Detect*, arXiv 2506.18177v4，2026-10-12；旧标题 *Message Passing for Track-Before-Detect*，2025|全文HTML，相关观测、幅度/噪声状态、BP、雷达仿真和真实浅海声学实验|当前核验到预印本，不能冒称TSP已发表；BP是近似，原文明确无一般精确保证|
|R5|Huang等，*Automated Hypothesis Validation with Agentic Sequential Falsifications*, ICML2025|PDF方法、假设和误差控制；官方PMLR及GitHub|有公开POPPER代码；e值乘积本身为经典工具，不能归为该文原创|
|R6|Zecchin, Simeone, Ramdas, *Quantum Sequential Universal Hypothesis Testing*, arXiv2508.21594，2025|全文HTML，序贯split likelihood ratio、复合零假设、动作选择和定理|预印本；量子测量部分不能直接移植，经典序贯通用推断不是2025新发明|
|R7|Gan等，*Toward a Liquid Biopsy: Greedy Approximation Algorithms for Active Sequential Hypothesis Testing*, Management Science，online 2025-08-19；72(4):3291–3308，2026|出版社摘要、出版日期、任务设定、数据与附录入口|作为生物诊断领域C迁移先例；SSRN全文403，未据此虚构详细算法|
|R8|Zhang等，*A Novel Self-Correcting Direct Position Determination in Asynchronous Sensor Networks*, ICASSP2026|出版社摘要及会议官方议程|全文418；只能保留“跨批共享时钟偏差”线索，不列为已复现候选|

R1–R3是本稿两个主候选的可复查母模块；R4、R7是主动寻找的跨域证据；R5–R6提供B4恢复时的检验修正。R8因全文未读，不算完成候选。

## 2. 候选A：共享源位置、域内向量响应、域间未知幅度

### 2.1 论文真正做了什么

R1对各雷达建模为

\[
y^{(l)}=\sum_k\psi^{(l)}(\theta_k)\alpha_k^{(l)}+v^{(l)}.
\]

位置\(\theta_k\)跨雷达共享，各雷达幅度不同；不同雷达可以不相干，但**单个雷达内部必须保有相干的多维响应**。证据最大化联合调整位置、共同稀疏超参数、噪声；Algorithm 1还扫描未激活位置以添加组件。新贡献是多参数化字典融合及连续参数更新，非SBL、匹配滤波或幅度消去本身。实验用两目标交叉、最近约0.5m及1–4雷达；比较NOMP和不同虚警阈值。改善来自响应结构和观测视角，非仅样本数量。[R1，§II–V，式(1)、(12)–(18)，Algorithm 1]

### 2.2 气源迁移的最小状态和输入

**状态**：固定离散源\(s\in\{1,\dots,16\}\)；一个观测段内共享的排放强度/低维排放波形；传感器基线和初始响应；校准后的响应时间\(\tau\)及其不确定性；局地风历史，并对未测得的传播路径风场保留有限扰动模型。

**输入**：原始浓度向量、每点时间戳与机器人位置、局地风、传感器阶跃响应校准、同一动作在各源/风扰动下的预测向量或模拟样本。这里“向量”可来自一段路径的多次测量，也可来自多站；它不能是多个独立自由幅度分别解释的单标量。

采用以下小模型，不需要NN：

\[
y=F_s(\eta,\tau)a+B\beta+\epsilon,\quad
F_s=R_\tau G_s(\eta)\Phi.
\]

- \(G_s\)：源到采样路径的输运响应；\(\eta\)表示少量未测风/扩散扰动。
- \(\Phi a\)：共享的低维排放时间过程。恒定源时只需一个排放率；不能每个读数一个自由排放率。
- \(R_\tau\)：传感器卷积。分段常值输入时可用\(z_{k+1}=e^{-\Delta t/\tau}z_k+(1-e^{-\Delta t/\tau})c_k\)。
- \(B\beta\)：基线和可解释漂移；\(\epsilon\)允许非对角噪声协方差。

局地风只约束观测点附近流动，不自动给出源到机器人整条路径的风。把该不确定性设为零可能重新制造B4高置信。

### 2.3 怎样得到候选源概率

对于仅16个互斥源，**直接枚举one-hot源比稀疏多目标求解更合适**。R1的\(\gamma_k\)是幅度先验精度/稀疏性参数，不是\(P(s=k\mid y)\)。不应把归一化\(1/\gamma_k\)当源后验。

若对中心化排放波动和基线采用高斯先验，线性 nuisance 可解析积分。令\(a\sim N(m_a,V_a)\)，\(\beta\sim N(m_\beta,V_\beta)\)：

\[
\mu_s=F_sm_a+Bm_\beta,\qquad
\Sigma_s=\Sigma_\epsilon+F_sV_aF_s^\top+BV_\beta B^\top,
\]

\[
\ell_s=-\tfrac12\{(y-\mu_s)^\top\Sigma_s^{-1}(y-\mu_s)
+\log|\Sigma_s|+n\log(2\pi)\}.
\]

正排放强度可用固定lognormal/截断正态求积；高斯只适合均值附近的中心化波动。对\((\eta,\tau)\)用同一物理先验与有限求积网格：

\[
\log Z_s=\operatorname{logsumexp}_r(\log w_r+\ell_s(\eta_r,\tau_r)),\quad
p_s=\operatorname{softmax}_s(\log\pi_s+\log Z_s).
\]

必须保留\(\log|\Sigma_s|\)。只比较最小残差，会奖励用很大 nuisance 方差解释所有数据的模型。若跨观测段共享\(\tau\)、源率或风偏差，应对完整数据一次积分/递推条件化；不能每段重复采用原先验然后把边缘似然相乘。

### 2.4 真正应该设计的观测量

用源间“不能被 nuisance 模仿的差异”检验可辨识性。局部线性近似下，源差\(\Delta_{ij}=\mu_i-\mu_j\)，nuisance切向矩阵\(J\)，噪声协方差\(R\)。定义

\[
W_\perp=R^{-1}-R^{-1}J(J^\top R^{-1}J)^\dagger J^\top R^{-1},\quad
d^2_{ij}=\Delta_{ij}^\top W_\perp\Delta_{ij}.
\]

这是经典投影/有效信息算子，本稿不主张其新颖。它的用途是**直接判断源排序能否受益**，不再以浓度预测MSE充当替代指标。若所选动作的\(d^2_{ij}\)在关键源对上几乎为零，应增加不同风向/几何位置的观测，而非增加同一轨迹预测器的精度。

### 2.5 两个硬反例与修正

**自由幅度反例。** \(y=qh_s+\epsilon\)，\(h_j=ch_i\)时，\((s=i,q)\)与\((s=j,q/c)\)分布完全相同。即使有5个、500个精准读数也一样。每个站仅一个标量且各站幅度自由时，每个源都能独立拟合所有标量。采用强排放率先验可能产生不同后验，但那是先验提供的辨识，不是数据的形状证据。

**修正**：同一源率约束覆盖多个几何不同读数；对基线/漂移施加独立校准的约束；取得非比例的响应形状。若对源率变化没有依据，宁可输出候选集合。

**时延反例。** 一维匀速无耗散对流，未知释放波形\(q\)：

\[
c(x,t)=q\bigl(t-(x-s)/u\bigr).
\]

两站到达时延差

\[
\Delta t_{12}=(x_1-x_2)/u
\]

与\(s\)无关。改变源位置可以被\(q\)的整体时间平移完全吸收。显著互相关峰只证实共同运动，不证实释放位置。

**修正**：要求候选输运响应存在可验证的非平移差异，例如源依赖的扩散展宽、障碍物路径或不同下风年龄，而非只拟合单时延。必须在 nuisance 消除后检查\(G_i\)与\(G_j\)的可分性。传感器低通\(H_\tau(\omega)=1/(1+i\omega\tau)\)会压掉这些差异；高频采样本身不能恢复硬件未保留的信息。

### 2.6 代码轮廓与适用门槛

```text
for each source s in all_legal_sources:
    for each common nuisance quadrature state r:
        F = sensor_response(tau[r]) @ transport(s, wind, eta[r]) @ release_basis
        mean, covariance = integrate_linear_amplitude_and_baseline(F)
        log_evidence[s, r] = gaussian_log_density(y, mean, covariance)
    score[s] = logsumexp(log_weights + log_evidence[s])
source_probability = softmax(log_prior + score)
```

有限源×少量 nuisance 网格可直接做Cholesky与logsumexp。原始高维BP不必搬来。下列三个条件未过即不扩展：①留出源/风扰动上联合似然校准；②nuisance去除后关键源对仍有信号；③同样原始数据、同样计算预算时优于完整联合似然基线。若第三项基线已使用同一充分统计量，重命名SBL无贡献。

## 3. 候选B：全部源对证据与单位资源的最弱对手辨识

### 3.1 两篇母文的具体贡献

R2给出\(M(M-1)\)种误判指数的可行区域、线性预算和随预算变化的探索构造；其判决需胜过每一个备选源，不能只由聚合熵决定。经典Chernoff、MSPRT、KL和探索思想不是2025原创。其证明用已知观测律、固定有限动作及时间独立结构。构造还含小预算时直接随机猜测的理论分支，**不支持“5步即最优”的说法**。[R2，§II、IV–V]

R3的具体可实现增量是非等成本动作频率优化：最弱对手信息速率除以平均动作成本，再化为LP。原文实验设32假设、16动作、单位方差高斯、异质动作成本，5万次重复；报告的成本收益不能外推为无人机收益。[R3，式(7)–(9)、Lemma 1、§IV]

### 3.2 输入、状态和行动输出

输入为每个源\(s\)、动作\(a\)的条件观测律\(f_s^a(y)\)，及包含移动、驻留、读出、计算等待的成本\(c_a>0\)。状态保留全部合法源的对数似然，不剪掉低后验源：

\[
L_s(t)=\sum_{k\le t}\log f_s^{a_k}(y_k),\quad
S_{ij}(t)=L_i(t)-L_j(t).
\]

如果\(i\)当前最受支持，预先或在线解

\[
\max_{\lambda\in\Delta_A}
\frac{\min_{j\ne i}\sum_a\lambda_aD_{KL}(f_i^a\Vert f_j^a)}
{\sum_a\lambda_ac_a}.
\]

这里所有合法\(j\)都参加最小值，**不按当前\(p_j\)把弱后验源抹掉**。用\(y_a=\lambda_a/(c^\top\lambda)\)可写成很小的LP：

\[
\max_{y\ge0,v}v,
\quad \sum_ac_ay_a=1,
\quad \sum_aD_{ij}(a)y_a\ge v\quad\forall j\ne i.
\]

最后\(\lambda_a=y_a/\sum_by_b\)。16源、有限动作时不需要NN。加入来源于全候选动作覆盖分布\(\nu\)的固定预算审计，输出\((1-\varepsilon)\lambda+\varepsilon\nu\)。\(\varepsilon\)是要计费并消融的实施参数；有限时域下不能直接声称继承R2渐近最优性。

### 3.3 期望成本比不是“逐动作除成本后直接抽样”

本稿的解析检查：两个对手，两个动作的信息向量分别为\((1,0)\)、\((0,9)\)，成本为1和9。逐动作除成本得到\((1,0)\)、\((0,1)\)，若把最优资源份额\((1/2,1/2)\)误用为样本频率，实际最弱证据/成本只有0.1。正确频率\((0.9,0.1)\)的比率为0.5。

必须说清：令\(w_a=\lambda_ac_a/(c^\top\lambda)\)后，两种优化可通过变量变换对应。区别在于**资源份额不是抽样频率**，不是发现了两个不可相容的信息定义。

### 3.4 错高置信为什么有机会恢复、为什么仍可能失败

固定正确观测模型下，若当前错源\(i\)的策略确实区分所有对手，真实\(j\)也将产生反对\(i\)的证据。源不被删除是必要条件：\(p_j=0\)后普通Bayes更新永远为零。使用log权重保存正先验，并由全候选对约束安排审计，比只检查高后验集合更稳妥。

但是R3原始“后验>1−δ即停止”会在给定B4前缀后立即终止，不能直接修复B4。应采用**独立于错误旧后验的未来证据审计**：旧后验只用于导航偏好，确认必须由审计起点后的完整对比证据通过。若要推翻旧证据，也可用修正后的传感器/风模型对保留的原始历史重新计算，而不是给真源偷偷加先验质量。

当初始真源质量仅\(10^{-6}\)，要达到0.95后验，所需新增对数赔率约\(\log(19\times10^6)=16.76\)。每块仅0.05 nat的平均辨识信息意味着约335块的量级，远超过5块。此计算是信息量级说明，不是有限样本保证。

### 3.5 最小可实施的恢复审计

对每个源\(s\)检验复合零假设\(H_s\)：该源和任一允许的共享 nuisance 成立。使用只依赖过去拟合的备择预测密度\(q_{-s,k}\)，构造

\[
E_s(t)=\frac{\prod_{k=1}^t q_{-s,k}(y_k\mid F_{k-1},a_k)}
{\sup_{\eta\in\mathcal H_s}\prod_{k=1}^t f_{s,\eta}(y_k\mid F_{k-1},a_k)}.
\]

这是经典序贯通用推断的split likelihood ratio；R6把它具体迁移到量子自适应测量，不可将经典部分说成其原创。它不必每步重新选一个自由 nuisance：分母对整个审计序列使用共享参数。

在真实观测律属于零假设族、动作/备择只依赖过去且分母真为上确界的条件下，\(E_s\)被真实参数对应的非负似然比鞅上界，故越过\(1/\alpha\)即可在任意停止时拒绝源\(s\)。候选集合\(C_t=\{s:\sup_{u\le t}E_s(u)<1/\alpha\}\)保留真的单一源的概率至少为\(1-\alpha\)。证据集合不是后验；不要把\(1/E_s\)归一化当源概率。

实施注意：数值局部最大值不是上确界，它可能把分母低估而造成不合法高证据。有限 nuisance 网格的保证仅针对该离散族；连续族需可证上界。重复重启审计要预先分配\(\alpha_r\)，如\(\alpha/[r(r+1)]\)。如所有合法源被拒绝，应报模型不足，而不是强选剩下“最不坏”的源。

R5的跨领域序贯检验也强调设计不得偷看当前待测数据；这正是防止先看哪一小段最像某源、再把该段当独立证据的门槛。该工具提高错误控制，不承诺提高源分辨率。

### 3.6 动作成本的适用条件

无人机移动代价通常依赖前一个位置，\(c(a_{t-1},a_t)\)不是论文固定\(c_a\)。最小修正是把一个动作定义成从当前局部锚点出发并回到锚点的短路径/驻留组合，从而成本可比较。若无法这样组织，需要路径状态占用/流量约束，不能继续引用独立动作的最优性定理。

如果风、传感器状态和 nuisance 后验随动作改变，\(f_s^a\)必须写为\(f_s(y\mid F_t,a)\)；此时小LP仍可作为滚动启发式，但原固定分布的渐近定理不自动成立。应在相同模型和资源下与EIG比较，不能把理论名词当实验结果。

## 4. 领域C迁移与反向证据

**浅海声学。** R4把原始复数信号的多字典、幅度和噪声推断用于真实SWellEx-96数据。论文给出21个阵元、7个频率、快照处理及高低SNR实验；低SNR还用合成孔径和状态指导的频率选择。这是从雷达式原始信号推断走向另一类物理传播的具体先例。但声学相位响应来自已知波传播模型，气体浓度不能因同为“源定位”就得到同样相位结构；原文多目标BP也不保证单源16候选有额外收益。[R4，§IV-B/C]

**液体活检。** R7把癌症类型当假设、测序区间当动作、突变检出当随机响应；有真实DNA数据的策略比较。它证明“候选类型弱差异+有成本选择测量”并非雷达专有。该文早期工作可追溯至2021，2025是期刊online日期；不能把整个ASHT当2025新发现。[R7，出版社记录]

**气体时间相关本来就有先例。** 独立检索已找到2006年 *Chemical Source Localization in Unknown Turbulence Using the Cross-Correlation Method* 及2023年 *Odour motion sensing enhances navigation of complex plumes*。这足以否定“互相关/双点运动首次迁移气源”式创新表述；本稿未以未读全文的前者推导新算法。未来如果采用时间/运动量，原创点必须落在候选条件似然、nuisance处理及主动验证，而不是经典滤波器名称。

## 5. 同资源最小实验，不靠更长轨迹取胜

建议预注册如下矩阵；全部保留同一16源集合，不挑选更容易的episode。

|组|观测评分|行动|用于辨别|
|---|---|---|---|
|B0|现有浓度似然|现有EIG|原始参照|
|B1|同一浓度似然|完整候选对成本LP+付费审计|政策是否单独有用|
|B2|共享nuisance的one-hot向量证据|现有EIG|观测模型是否单独有用|
|B3|同B2|同B1|组合是否存在交互收益|
|B4-control|同B3，但打乱允许的跨点/时间配对并保持边缘分布|同资源行动|收益是否真正来自联合结构|

总成本应包含飞行时间/距离、驻留、传感器稳定时间、所有额外站点和计算时间；高频采样不得把强相关样本虚增为独立样本。先固定总资源看准确率/后悔，再固定错误率看资源；不要只给不同提前停止规则下的“平均成功时间”。

关键指标：全部episode正确源排名、真源对最强错源的log evidence margin、错误且最大后验>0.9的频率、真源集合覆盖率、B4前缀后固定额外预算内恢复率、额外资源、计算时延。浓度MSE只是附属指标。

明确分离两种B4压力测试：①只人为改变先验/前缀置信，未来观测模型正确；②风/传感器失配导致错置信。前者改善不证明后者解决。联合误差控制只在观测族覆盖真机制时有效。

## 6. 可交给后续实现的最小接口

```text
score_sources(history, action, nuisance_grid)
    -> log_predictive_density[source, hypothetical_or_real_outcome]
    -> source_posterior[16]
    -> optional_composite_null_upper_likelihood[16]

pairwise_information(action_set, source_predictives)
    -> D[action, source_i, source_j]
    -> identifiability_flag[action, pair]

allocate_actions(D, full_cost, incumbent, legal_sources)
    -> sample_frequencies[action]
    -> explicit_audit_cost

update_audit(real_outcome, past_only_alternatives, null_upper_likelihoods)
    -> evidence_against_each_source
    -> candidate_set_or_model_failure
```

母文事实、此处的气体适配和未验证设想必须分别标注。以上接口及伪代码是本稿建议，未写全局代码、未运行PMFS实验、未声称任何恢复率提升。

## 7. 可复查链接

- [R1 原文全文](https://arxiv.org/html/2503.12913v2)；[FUSION出版记录](https://doi.org/10.23919/FUSION65864.2025.11124160)。
- [R2 原文全文](https://arxiv.org/html/2405.06554v3)；[台大期刊出版记录](https://scholars.lib.ntu.edu.tw/entities/publication/8b20458e-d251-4daa-b7d8-53db935563cd)。
- [R3 原文全文](https://arxiv.org/html/2509.11632v3)；[ICASSP2026官方报告](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)。
- [R4 最新全文](https://arxiv.org/html/2506.18177v4)；[版本历史](https://arxiv.org/abs/2506.18177)。
- [R5 ICML论文页](https://proceedings.mlr.press/v267/huang25n.html)；[PDF全文](https://arxiv.org/pdf/2502.09858)；[作者代码](https://github.com/snap-stanford/POPPER)。
- [R6 全文](https://arxiv.org/html/2508.21594v1)。
- [R7 出版社记录](https://pubsonline.informs.org/doi/10.1287/mnsc.2023.00829)。
- [R8 ICASSP2026官方报告](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=2876&bare=1)；[DOI](https://doi.org/10.1109/ICASSP55912.2026.11461983)。
- [气体相关旧文线索](https://www.researchgate.net/publication/224641706_Chemical_Source_Localization_in_Unknown_Turbulence_Using_the_Cross-Correlation_Method)；[2023气味运动论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10039482/)。

**冻结判断**：A为“有向量形状可分性时值得做的小观测模型”；B为“有可区分动作时值得做的小政策”；二者均不以先验高置信、未来预测MSE或相关峰显著性代替源辨识。后续如果现有数据不满足A的观测要求，保留B的小规模同预算政策审查，并明确数据层面的不可辨识边界。
