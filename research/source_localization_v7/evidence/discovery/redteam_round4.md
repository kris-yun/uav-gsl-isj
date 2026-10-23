# V7第四轮建设性红队审查：概率、成本、审计与科学门槛

审查代理：radar / information-theory。日期：2026-10-23。

审查对象：`m1_opponent/calibration.py`、`channel.py`、`engine.py`、`baselines.py`，以及本人负责的 `m3_audit`。读取了控制后端、观测账本和相关算子以核对接口。没有修改其他代理负责的文件；发现的问题已逐项发给root，root随后修正。本人只补充了零备择路径审计测试及说明。

复查数值与所审文件SHA256保存在 `REDTEAM_ROUND4_CHECKS.json`。该收据说明审查时刻的版本，不冒充覆盖后续所有改动。M3在本轮通过18项标准库unittest。

## 1. 结论与本轮处置

目前可以交付可运行的L1研究链、明确的源概率/审计分离和可追查的成本分配。不能据此宣布新气源辨识机制已优于完整原始joint强基线，更不能把估计通道的e-value阈值解释为实际GADEN或UAV错误率保证。

本轮发现并完成复查的修正如下。

|问题|为何必须修|最小修正|本轮状态|
|---|---|---|---|
|M3在planner与engine各抽一次动作|`coverage_draw`原本描述未执行的第一次抽样；第二次抽样和预算截断使记录失真|planner只返回分布，engine唯一抽样；记录执行分布、局部到全局动作索引、预算限制与期望成本|已在复读engine确认|
|Chernoff在含不可负担动作的集合上优化后再剪掉|最优动作不能执行时会退均匀，弱化强基线，改变等资源比较|对可负担子表重解同一个成本LP，再嵌回全动作|已确认；full策略也对可负担子channel规划|
|零后验源导致EIG出现`0*inf`|有限字母表允许结构零；正确EIG应有限且零质量源贡献0|EIG只对正质量源求和|数值复查通过：完全确定后验对应EIG=0|
|整源nuisance行皆为`-inf`使条件nuisance出现NaN|通用FiniteChannel允许某源被结构零排除，后续预测会崩溃|只为反事实提案返回该源已安装nuisance prior；源后验仍严格为0|复查通过；这不构成概率恢复|
|增加odd码同时增加总伪计数，改变even边缘|把平滑强度变化混入“新增联合信息”的收益|固定总Dirichlet质量，单cell为`alpha_total/O`；增加投影一致性测试|复查边缘差为`5.55e-17`|
|mother原为bank第0项静态梯度，却与时序secondary比较|时间摘要、维数与源对选择三种变化混在一起|保留冻结旧结果并准确命名；新版本用同一训练bank的best-one，另加同维固定/原始joint对照|best-one修正已确认；更多同维对照由root继续整合|

这些修正是正确性与公平性修正，不是新方法性能证据。已有冻结OCB结果必须继续使用当时版本解释，不能用修正后的代码悄悄重写旧分数。

## 2. 源对cover选择并不创造新观测信息

令原始双点块为`X`，共同浓度摘要为`E(X)`，一组反对称摘要为`H_F(X)`。在校准已经冻结、对测试块作确定性变换时，

\[
I(S;E(X),H_F(X)\mid a)\le I(S;X\mid a).
\]

若保留的是完整可逆的even/odd序列，则与原始左右序列信息相同；若只保留二元even和少量三元odd码，则是有损压缩。源对cover可改善有限样本估计、限定模型复杂度、减少无用摘要，但不能把增加后的训练JS当作从原始块获得了新信息。

当前even码只保留一个阈值位。它保留了与`even`基线相同的共同浓度摘要，**不等于保留全部原始浓度或旧PMFS的完整边缘模型**。报告和PPT应说“保留共同浓度通道/同一even边缘”，不要写“完整浓度信息无损保留”。

`_pair_distances`对每个源对取全部源特定nuisance组合的最小JS，是保守的训练诊断。有限训练直方图中正JS不提供总体辨识下界；最小值为0也不授权删除源。选择多个滤波器时，测试数据不得回流至阈值、特征数量、separation target或滤波器选择。

### 2.1 已修复的平滑混淆有可解析反例

旧版每个joint cell加同一`alpha`。加入`K`个三元odd码后，even边缘变为

\[
\widehat p(E=e)
=\frac{n_e+3^K\alpha}{N+2\cdot3^K\alpha},
\]

而even-only是`(n_e+alpha)/(N+2alpha)`。即使新odd码为常数，两者也不同。`N=10,n_e=9,alpha=0.5,K=1`时，旧even概率`0.863636`变成`0.807692`。这与新cue的源信息无关。

新版固定总质量`A`，每个cell加`A/O`，则各even行投影均加`A/2`，所有合法维度保留同一even边缘。该修正解决了一个实际混淆，但不会自动解决训练集选择偏差或稀疏joint估计误差。

### 2.2 对照的最低区分要求

best-one与secondary比较只能回答“同训练规则下，一项摘要与至多两项摘要如何不同”。要把收益归到源对cover，至少还需同样最多两项、同样字母表大小、相同总平滑质量的固定选择或合理常规选择对照。一个18符号的joint摘要仍是粗化表示，命名应说明编码内容，不能直接等同完整42维双侧时间块似然。

原始joint的强基线可以是同原始数据上的适当收缩高斯、明确正则化的条件模型或同复杂度的完整joint码。模型容量与校准数据需相当。已有OCB二维raw-joint Gaussian是必须报告的强参照；不能用低信息静态gradient母基线替代它。

## 3. Joint alphabet共同补零本身正确

不同动作可能选不同数量odd码，局部字母表大小不同。将局部表嵌入共同大字母表，其余位置在**该动作的所有源和nuisance下均为0**，是正确表示。共同不可达符号的KL/EIG贡献均为0。

本轮对同一二源分布额外补4个共同零符号，KL最大差与EIG最大差都为0。因此不应为消除零而把padding统一加epsilon；那会人为创建原编码器永远不会发出的符号，并可能使动作价值随padding维数变化。

必须区分三类零：

1. 动作共同不可达padding：保留精确0，编码器不能输出该符号。
2. 只有部分源/机制概率0：可能产生无限KL与源结构排除，需要显式支持处理；不能静默clip后仍称原通道精确KL。
3. 当前整条观测后缀在所有模型状态下概率0：模型支持失败，应报错，不得归一化出一个高置信源。

当前M3显式报告支持奇异并进入pair challenge；audit对第3类在更新状态之前抛出异常。估计直方图对实际可达cells有正平滑、padding对所有源共同为0，因此该构造本身不会导致某源独有的零支持。

## 4. 固定nuisance顺序推断当前没有重复计数

`JointPosterior`保存`log_weights[source,nuisance]`，每次只加当前raw symbol的完整条件对数概率：

\[
w_{sr,t}\propto\pi_s\omega_{sr}\prod_{k\le t}P(a_k,s,r,o_k).
\]

规划使用条件nuisance权重

\[
\omega_{r\mid s,t}=\frac{w_{sr,t}}{\sum_vw_{sv,t}},
\qquad
p_{s,t}^{a}(o)=\sum_r\omega_{r\mid s,t}P(a,s,r,o).
\]

这只是用历史更新下一块的预测，不是再乘一遍历史观测。当前更新函数也没有把`predict()`的混合概率再乘进每个nuisance状态，故未发现重复更新。

数值反例用于确认共享nuisance语义：源0的两种Bernoulli机制为`0.1/0.9`，源1的两种机制均`0.5`。观测`1,0`后，共享机制给出源0证据`0.09`、源1证据`0.25`，源后验应为`[0.264705882,0.735294118]`；错误地每步重积分会得到`[0.5,0.5]`。当前实现得到正确值。

结构零源没有通常意义的`R|S,data`分布，因为条件事件概率0。新版返回prior只是让该源的反事实动作提案可计算，不能称为恢复了源概率。正先验被极小正似然压低，与结构零永久排除，是两种不同状态；后者若来自模型失配，需要显式模型修订/新审计，不能靠数值floor伪装修复。

## 5. Audit的0/0、reentry与anytime语义

审计使用新后缀，定义

\[
A_{sr}=\sum_{k>t_0}\log P_k(a_k,s,r,o_k),
\quad
Q_{-s}=\sum_{j\ne s,r}w^{(-s)}_{jr}e^{A_{jr}},
\quad
E_s=Q_{-s}/\max_r e^{A_{sr}}.
\]

默认备择对所有其他源和nuisance赋正权。若某null分母和其备择分子同时为0，则所有源/机制的后缀似然均为0。当前`update`先检查这一情况，再计算比值，故不会以`-inf-(-inf)`悄悄产生NaN。

若只有备择后缀已经变为0，它以后仍为0。`prepare`可以在这个零质量历史上返回任意归一化预测；累计备择对数质量仍是`-inf`。新增测试重复确定性支持事件，再输入矛盾事件：前者得到合法`±inf` log-e而没有NaN；后者在状态变化前报模型支持失败。该测试使M3总计18项通过；没有为了通过测试修改物理保证。

### 5.1 两种列表都具有模型内anytime coverage，但含义不同

- `compatible_now={s:log E_s(t)<log(1/alpha)}`可重新进入。
- `not_rejected_since_start={s:max_{u≤t}log E_s(u)<log(1/alpha)}`记录本轮审计从未被拒绝的源，不能重新进入。

在精确条件族包含真实固定源/nuisance时，真源曾被排除的事件概率不超过alpha，所以两者都受同一个anytime事件控制。“第二个叫anytime”不意味着第一个只有定时有效。两者均不是后验概率，也不应归一化为概率图。

例如两源Bernoulli`0.1/0.9`、alpha`0.2`：观测1使源0的E=9而被当前列表排除；再观测0使E=1，源0重新进入current列表，但不会回到never-rejected列表。与此同时，规划合法源集合始终完整，不能跟随任一audit列表永久删源。

只有在null族正确、相同实际过去条件化、备择在观测前冻结且归一化、nuisance整段固定、依赖正确建模时，才有

\[
P_{s,r_*}(\exists t:E_s(t)\ge1/\alpha)\le\alpha.
\]

证明来自对真实nuisance似然比检验超鞅的支配；E本身不必是超鞅。精确零支持下用“超鞅”比一概称“均值1鞅”更准确。重复新开audit需alpha spending。任何基于有限校准数据估计的表都只给模型内条件保证，过去数据拟合并不自动建立真实家族包含性。

当前engine的posterior与audit分别处理同一编码一次，audit结论没有回乘posterior，这是正确的职责分离。审计没有使用旧错误源先验初始化备择，因此不会由旧高置信直接拒掉合法低后验源。

## 6. Engine的现有观测与公平性边界

### 6.1 动作频率与可负担集合

复查版本的full与Chernoff均在可负担子集合上重解；full输出局部动作索引映射，engine唯一抽样并记录最终全局频率和期望cost。M2 tube限制普通LP，global paid coverage在当前合法且可负担动作中保留。预算尾段不再有对原始全局集合的永久coverage保证，报告已有显式预算标识。

M3理论中的`y`是单位成本的观测率，采样频率必须为`y/sum(y)`。解析成本反例仍是必要回归测试：资源份额`[.5,.5]`对应采样频率`[.9,.1]`，不能混用。

### 6.2 M2使用了额外的travel传感信息

`_execute_control`每0.1秒生成travel浓度，M2据此检测边界并更新记忆；当前source likelihood主要更新paired dwell block。joint-EIG/Chernoff基线没有使用相同travel内容来更新其概率或提案。因此全链相对这些基线的差异同时包含不同观测利用方式，不能全部归因于源对cover或M3新分配。

最低交付措施是记录travel采样数与来源，把当前概率图准确说明为基于dwell-block likelihood的工作概率，单独的M3政策消融使用相同M2开关/提案条件。更强比较应给方法同一可用原始流，或明确建立travel与dwell的joint conditional law。不能把尚未纳入source likelihood的导航side-channel默称为“所有测量的完整Bayes后验”。

这不自动破坏audit：若给定真实固定`(S,R)`后，每个新dwell确实服从所声明的独立条件律，动作可使用其他过去side-channel而不影响检验超鞅性质。但安装的经验表是否满足这一条件仍须校准验证。

### 6.3 控制后端的运动相位可吸收源平移

控制后端使用

\[
\sin\{3t+\phi-(x-s)^\top n_r\},\qquad
\phi\sim\mathrm{Uniform}(-\pi,\pi).
\]

令`phi'=phi+s^T n_r`模2pi，则phi'仍均匀。固定wind mechanism后，去掉空间幅度`mu_s(x)`的移动波形分布与源位置无关。因此该后端的源信息主要来自空间均值响应及其噪声/联合幅度结构，不能验证“运动相位本身新增源定位信息”。若时序滤波器胜出，它可能是有限样本压缩或幅度/SNR的再表达，不等于真实气流中的新源运动线索。

此外，该后端每个块重新生成共享扰动与相位，并初始化一阶传感器状态；这是所声明的条件独立L1块模型，不是跨flight、dwell与下一块连续继承传感器状态的原生物理模型。0.1s时间戳是真实控制时间单位，但不能单凭这一点称为native连续物理验证。

`response_geometry`对所有候选源离线计算响应，不读取runtime真源作为政策输入，这一点未发现标签泄漏。其固定mechanism和声明协方差是控制预测假设，不是原生测得的联合不确定性校准。

## 7. 联合error channel的正确使用条件

`apply_joint_error_channel`的矩阵乘法表示对整个符号施加一个联合随机kernel，允许相关burst，优于把每个bit的错误独立相乘。它不等于任意物理误差的容错证明。

若把变换后的channel用于实际raw backend，backend或编码后的观测路径也必须经过相同error机制。只变换预测表、仍把未受扰动的raw编码当观察，是新的模型失配。若仅从变换后的finite channel采样，则属于自洽L1机制实验。跨整段“至多k个错误”之类预算不是每步独立kernel，需要显式序列状态/联合模型，不能由现函数自动推出。

## 8. 已冻结OCB结果与目前科学门槛

root披露的冻结静态pilot为：train-only选择probe12/17，间距7m；4个development world、每world10快照；mean31/40，raw joint Gaussian40/40，invertible even/odd Gaussian40/40，数值等价差`4.51e-17`；静态M1 histogram31/40。本红队未重跑这些数据或据此调参。

允许写入结论的内容：

1. 所选空间双点联合观测在该开发pilot中有辨识信息。
2. raw joint与可逆even/odd Gaussian的等价是理论预期，不是新算子胜出。
3. 冻结静态M1没有优于报告中的mean参考，也没有优于raw-joint强参照。
4. 7m离线同期空间点尚未成为已合法的UAV同步硬件/时序方案。
5. 40个快照不是40个独立seed；两源不能验证多源max–min混合频率机制。

当前可执行的升级门槛：

|待检验声明|必须保持不变的条件|可接受证据|失败时应采取的动作|
|---|---|---|---|
|源对cover优于单cue/常规选择|同原始块、同even边缘、同特征数预算、同平滑总量、训练选择冻结|独立world上的排序/负对数分数与覆盖改善|将模块定位为可解释压缩，不再宣称新增辨识机制|
|M3替代EIG/普通Chernoff有价值|同channel、同观测后端、同初始先验、同可用动作/资源、明确M2 side-channel|至少3源互补动作，动作频率及错误先验恢复的等资源曲线|保留探索修复的机制结论，不能宣布定位精度提升|
|低后验源可恢复|真源未删除、初始质量正、每个错误源+nuisance可被付费coverage区分|错先验压力与结构失配压力分开报告|不可辨识则输出未分开集合；结构失配则修模型，不能强化后验|
|audit有真实错误率控制|独立校准证明条件族包含、正确时序依赖与固定nuisance|实际独立world的候选覆盖与错误确认统计；形式保证需额外包含证明|保留“conditional/model-relative”，不标实际alpha保证|
|源时间运动cue有独立信息|合法连续native窗口、同步/响应校准、保留浓度joint强参照|在相同raw信息与资源上，留出world证实超出静态幅度摘要的独立差异|停止用50秒快照或当前均匀相位控制后端支持该声明|

### 8.1 完成矩阵后的最终补记

上述代码审查之后，root已完成156个L1 episode，原结果为`source_localization_v7/results/control_matrix_v7_frozen/CONTROL_MATRIX_RESULT.json`，配置SHA256为`25d5d047a238c3c846179c3098e2f848ce5fd0d8df28b67cba37082d5053d303`。13变体、6控制世界、两种先验，每次预算300 s。本人核读该JSON：adapted variance普通/错误先验最终top-1为4/6、3/6；其余12变体全部为6/6，涵盖raw-joint/EIG、母算法、M1/M2/M3独立消融与full。强基线已在该终点饱和，没有建立新模块独立定位收益。

full错误先验组六个episode合计七次audit challenger反馈，禁用反馈的消融仍6/6。当前incumbent被current list拒绝后，从compatible其他源取最小log-e者作challenge，只改变规划，不回乘posterior。这证明反馈路径执行，不证明它造成七次独立恢复。no-coverage也6/6，不能宣称该批结果建立覆盖的必要性。

root已在每次结果记录travel/dwell采样数、dwell-only posterior scope和phase平移限制。最终技术文档保留这两个限制，矩阵继续标L1，`native_improvement_verified=false`。无需为了得到正结果继续调整已冻结pilot；后续实验仍须跨过本节升级门。

## 9. 参考与证据位置

- 代码与本轮数值证据：`REDTEAM_ROUND4_CHECKS.json`；`source_localization_v7/tests/test_m3_audit.py`；`m3_audit/THEORY.md`。
- 固定nuisance审计、same-past定义、成本频率公式及风险边界：`radar_round2.md`与`m3_audit/THEORY.md`。
- [TIT2025 primary full text](https://arxiv.org/html/2405.06554v3)，DOI `10.1109/TIT.2025.3588527`。
- [非等成本ASHT primary full text](https://arxiv.org/html/2509.11632v3)，[ICASSP2026官方条目](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)。
- [PNAS2026作者全文](https://emonet.biology.yale.edu/assets/papers/2026/2026_brudner-et-al-PNAS-fly-navigational-responses-exploit-plume.pdf)：其生物时间滤波与中心线转向任务不能直接替代多源位置后验。

本报告区分已经修复并复查的实现错误、仍需标注的模型假设，以及尚未获得的科学证据。没有把经典KL、JS、Bayes、Dirichlet平滑、似然比或Ville不等式包装成2026新算法。
