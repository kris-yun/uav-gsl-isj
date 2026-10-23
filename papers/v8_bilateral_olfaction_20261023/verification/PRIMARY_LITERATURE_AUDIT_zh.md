# V8 原始文献与创新归属核验

核验日期：2026-10-23。用途：论文研究稿的文献依据、创新归属和引用边界；本文件不报告新的定位实验。论文正文、作者公开版本、作者代码和出版方元数据分开记录。无法获取的最终全文、补充材料或正式 DOI 不以推测填充。

## 一、最重要的改稿结论

1. **M1 的母算法是真实、已正式发表的 PNAS 2026 研究。**它训练两个时间滤波器，经过整流和左右镜像相减，判别羽流中心线在何侧；源位置后验、竞争源联合证据和源判别通道选择属于拟议的任务改造，不能归为母文已有结果，也不能把镜像算子自身归为本文原创。
2. **固定核库选择不是母文的可学习滤波器复现。**当前 V7 的受限单核对照应标注为“母结构的固定核库单通道迁移”，另列真正学习滤波器的直接迁移实验。代码审计还发现原生单通道迁移也选择了静态梯度核，因此不能称已有实验验证了原始动态镜像网络。
3. **Nature 2026 的边界记忆是遇边事件关联的方向向量。**不能把它解释为已经实现了稳定的气味边界地图、源位置概率图或双无人机编队规划。
4. **PMFS 已有历史积累和主动选点。**其真实链条为观测命中图、候选源传播预测、逐格相容乘积和后验加权预测方差选点。V8 应讨论命中统计对时空关系的压缩、似然与读出的对应关系及后验失准后的采样偏置，不能建立“PMFS 不利用历史／不主动搜索”的稻草人。
5. **M3 的理论只能在明确假设下成立。**成本分配应区分采样频率与成本份额；审计需要可预测的归一化备择密度、真零假设的条件分布包含关系、无泄漏的新证据和重复审计的错误预算。新后缀本身不能消除错误条件模型的风险。审计不得作为独立气体证据再次乘入源后验。
6. **2026 文献状态有两处更新。**非同质成本 ASHT 已有 ICASSP 2026 官方报告记录；QSUT 作者主页将其列在已发表或接收的 npj Quantum Information 2026 论文中。后者最终出版 DOI 未核得，方法仍引用实际读过的 2025 arXiv v1，注明作者列示的接收状态即可。

## 二、逐条文献元数据与阅读证据

|引用键|已核验书目信息|一级来源与实际读取深度|可用于正文的范围／限制|
|---|---|---|---|
|Brudner2026Opponent|Samuel Brudner, Baohua Zhou, Viraaj Jayaram, Gustavo Madeira Santana, John P. Crimaldi, Damon A. Clark, Thierry Emonet. *Fly navigational responses exploit plume-specific odor motion and gradient cues*. PNAS 123(29), e2608896123, 2026. DOI: 10.1073/pnas.2608896123.|[出版方全文](https://www.pnas.org/doi/10.1073/pnas.2608896123)、[作者代码](https://github.com/emonetlab/GradientMotionMultiplePlumes)。已读主文方法、图3模型、作者 `figure3_models.py` 和复现说明；未声称完整复现 SI。|梯度与运动线索的互补、训练时间滤波器、整流、反对称输出、中心线侧别分类。不能作为气源后验改进或 UAV 编队效果的实验证据。|
|Siliciano2026Vector|Andrew F. Siliciano, Sun Minni, Chad Morton, Charles K. Dowell, Noelle B. Eghbali, Silas E. Busch, Juliana Y. Rhee, L. F. Abbott, Vanessa Ruta. *A vector-based strategy for olfactory navigation in Drosophila*. Nature 657, 443–454, 2026. DOI: 10.1038/s41586-026-10827-7.|[出版方元数据](https://www.nature.com/articles/s41586-026-10827-7)、[作者预印本全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11844514/)、[作者代码](https://github.com/rutalaboratory/Edge-Tracking-Model)、出版方评审材料。最终 Nature 主文直接访问遇登录重定向；已读作者稿方法、记忆更新式与模拟代码，不能写“逐页读完最终 Nature PDF”。|进入／离开事件更新方向记忆，形成返回行为参考。不能等同于固定边界坐标、自动合法候选位置生成或源判别最优编队；这些是 V8 的任务设计。|
|Vershinin2026Costs|George Vershinin, Asaf Cohen, Omer Gurewitz. *Active Sequential Hypothesis Testing with Non-Homogeneous Costs*. ICASSP 2026,91–95；DOI:10.1109/ICASSP55912.2026.11463839。作者稿 arXiv:2509.11632v3，2025-09-30。|[作者全文](https://arxiv.org/html/2509.11632v3)、[ICASSP 官方日程](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)、[出版方登记元数据](https://api.crossref.org/works/10.1109%2FICASSP55912.2026.11463839)。已读问题定义、分配目标、Chernoff 改造及结论。|“期望信息／期望成本”与“信息成本比的期望”不同。固定有限动作、已知分布、正成本等假设下的渐近结果，不能直接成为移动 UAV 有限预算的全局最优性保证。|
|Hsu2025Tradeoffs|Chia-Yu Hsu, I-Hsiang Wang. *Tradeoffs Among Action Taking Policies Matter in Active Sequential Multi-Hypothesis Testing: The Optimal Error Exponent Region*. IEEE TIT 71(9):6546–6565, 2025. DOI:10.1109/TIT.2025.3588527.|[作者稿](https://arxiv.org/html/2405.06554v3)、[作者实验室目录](https://cc.ee.ntu.edu.tw/~ihsiangw/NICLab/Publications.html)、IEEE 元数据。已读问题、动作资源与误差指数框架。|支持多假设动作分配和资源约束的研究背景；V7 不等于完整误差指数区域算法复现。|
|Vershinin2025Clustered|George Vershinin, Asaf Cohen, Omer Gurewitz. *Multi-Stage Active Sequential Hypothesis Testing with Clustered Hypotheses*. ISIT 2025. DOI:10.1109/ISIT63088.2025.11195532.|[作者全文](https://arxiv.org/html/2501.11459v1)、[IEEE](https://ieeexplore.ieee.org/document/11195532/)、作者机构论文目录。已读聚类与分阶段消除结构。|原文有已知动作分布和结构化聚类；V7 的全候选保护不等于已实现原文聚类算法。|
|Zecchin2025QSUT|Matteo Zecchin, Osvaldo Simeone, Aaditya Ramdas. *Quantum Sequential Universal Hypothesis Testing*. arXiv:2508.21594v1, 2025-08-29。|[实际读取版本](https://arxiv.org/html/2508.21594v1)、[作者当前主页](https://web.stanford.edu/~aramdas/)。已读可预测估计、复合零假设分母、两侧检验及证明框架。作者主页“Published (or accepted) papers”列为 npj Quantum Information 2026；最终 DOI／卷号待核。|可迁移的是可预测似然审计原则。不能声称量子硬件、量子加速、量子传感优势，也不能只因用 e 值就声称不依赖模型校准。|
|Wasserman2020Universal|Larry Wasserman, Aaditya Ramdas, Sivaraman Balakrishnan. *Universal inference*. PNAS117(29):16880–16890,2020. DOI:10.1073/pnas.1922664117.|[出版方全文](https://www.pnas.org/doi/10.1073/pnas.1922664117)。已读通用似然比构造及其适用范围。|给出可预测／分样本似然审计的经典来源，避免将所有统计基础归为2026新成果。|
|Ojeda2024PMFS|Pepe Ojeda, Javier Monroy, Javier Gonzalez-Jimenez. *Robotic Gas Source Localization With Probabilistic Mapping and Online Dispersion Simulation*. IEEE T-RO40:3551–3564,2024. DOI:10.1109/TRO.2024.3426368.|[作者已接收全文 v3](https://arxiv.org/html/2304.08879v3)、[含期刊 DOI 的作者元数据](https://arxiv.org/abs/2304.08879)、[官方代码](https://github.com/MAPIRlab/GasSourceLocalization)。已读 III–V 节全部计算链和两个关键代码文件。|历史命中图、风场外推、候选传播、置信加权相容度、粗到细分配、预测方差主动选点。代码读取为当前 humble，用于机制核查；用户基线最终应冻结具体提交。|
|Monroy2017GADEN|Javier Monroy, Victor Hernandez-Bennetts, Han Fan, Achim Lilienthal, Javier Gonzalez-Jimenez. *GADEN: A 3D Gas Dispersion Simulator for Mobile Robot Olfaction in Realistic Environments*. Sensors17(7),1479,2017. DOI:10.3390/s17071479.|[出版方](https://www.mdpi.com/1424-8220/17/7/1479)、[作者项目](https://github.com/MAPIRlab/gaden)。出版方本次429；元数据由作者项目与正式 VGR 文献交叉核验。未将当前项目特性写成2017版本全部能力。|复杂三维传播模拟平台来源；不能证明某一用户场景已物理资格化。|
|Ojeda2025GadenRT|Pepe Ojeda, Javier Monroy, Javier Gonzalez-Jimenez. *Gaden-RT: A real time and interactive gas dispersion simulator for mobile robotics*. SoftwareX32,102388,2025. DOI:10.1016/j.softx.2025.102388.|[出版方元数据](https://www.sciencedirect.com/science/article/pii/S2352711025003541)、[作者 README](https://github.com/MAPIRlab/gaden)、[作者变更记录](https://github.com/MAPIRlab/gaden/blob/humble/Changelog.md)。最终全文直接访问403；已读官方项目实现说明。|实时／交互能力来源。OpenCL GPU 加速指可选浓度图计算，不能扩大成完整传播管线都在 GPU 上运行。|
|Ojeda2023VGR|Pepe Ojeda, Javier Monroy, Javier Gonzalez-Jimenez. *VGR Dataset: A CFD-based Gas Dispersion Dataset for Mobile Robotic Olfaction*. Journal of Intelligent & Robotic Systems109,article75,2023. DOI:10.1007/s10846-023-02012-z.|[出版方全文](https://link.springer.com/article/10.1007/s10846-023-02012-z)。已读任务、环境、数据结构与出版信息。|House 风场及气体数据背景。页码应为文章号75，不应抄某些预印本引用中的75–83。|
|Shigaki2026Adaptive|Shunsuke Shigaki, Keisuke Yokota, Ryoko Sekiwa, Daisuke Kurabayashi, Dai Owaki. *Insect-inspired adaptive behavioral compensation strategy against olfactory sensory deficiency for robotic odor source localization*. npj Robotics4,12,2026. DOI:10.1038/s44182-026-00080-5.|[出版方全文](https://www.nature.com/articles/s44182-026-00080-5)。已读摘要、引言、双侧／单侧感觉缺损任务与机器人验证范围。|存在2026年的直接机器人双侧嗅觉与感觉补偿先行研究；不能声称首次将双侧嗅觉用于机器人。本文源后验和两机位置选择与其任务不同。|
|Kim2026DGSE|Seunghwan Kim, Hyungjin Kim, Junhee Lee, Hyondong Oh. *Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*. arXiv:2608.16221v1,2026-08-17。|[作者全文](https://arxiv.org/html/2608.16221v1)。已读问题、顺序物理依赖、主动策略和实验限定；未核得正式发表。|近期直接 GSL 相关工作，研究风—浓度—源顺序推断；连续浓度建模不是本文独有想法。以预印本标明，不沿用其性能数字为本文证据。|
|Vergassola2007Infotaxis|Massimo Vergassola, Emmanuel Villermaux, Boris I. Shraiman. *‘Infotaxis’ as a strategy for searching without gradients*. Nature445:406–409,2007. DOI:10.1038/nature05464.|[出版方摘要与元数据](https://www.nature.com/articles/nature05464)。未声称逐页读取全文。|以期望熵下降主动选点的经典来源，用于普通 EIG／infotaxis 对照的归属。|

## 三、与正文公式对接的边界

### 3.1 M1：母算子与本文改造

将左右已同步历史记为 \(L,R\)，母结构可概括为

\[
h(L,R)=\operatorname{ReLU}(\langle f_1,L\rangle+\langle f_2,R\rangle+b)
-\operatorname{ReLU}(\langle f_1,R\rangle+\langle f_2,L\rangle+b).
\]

其交换反对称性来自运算结构。原文学习 \(f_1,f_2,b\)，输出用于中心线侧别分类；作者代码最终 softmax 的符号取决于左右类别编码。V8 不宜照搬某一符号就称为物理左右方向真值。

**本文的拟议改造**是以真实传感器读出为输入，在 TRAIN 源条件数据上选择／训练表示，联合共模和反对称信息，形成源条件证据，再用于二维源概率更新。固定有限核库、可学习滤波器应给出独立的实现状态与对照名称。证明表示具有反对称性，不等于证明源可辨识，更不等于证明优于完整 raw-joint。

**本报告的数学推论，非母文性能结论：**若 \(Z=T(Y)\) 为确定性特征，给定已知动作与设计，\(I(S;Z\mid A)\le I(S;Y\mid A)\)。因此 M1 的可检验贡献只能落在有限样本、模型失配、参数预算或估计稳定性上的判别效率；M2 改变新测量位置和真实读出分布，才可能增加后续观测中的可获信息。

### 3.2 M2：方向记忆不是气味边界真值

作者稿与代码中的进入／离开记忆形如
\(m\leftarrow a m+b\widehat v+\epsilon\)。这是事件方向参考；返回动作与内部行为状态关联，而非直接恢复气味边界形状。向 UAV 迁移时，遇边事件时钟、噪声、风变化、合法可达位置及编队采样的规则都应单独定义。不能把原果蝇实验的方向记忆效果当作 UAV 源判别增益。

### 3.3 M3：成本份额与采样概率

对固定候选假设 \(i\)，原成本 ASHT 的核心比率可写作

\[
\max_{q\in\Delta(\mathcal A)}
\frac{\min_{j\ne i}\sum_a q_a D_{ij}(a)}{\sum_a q_a c_a}.
\]

若令 \(w\) 为成本份额，则采样概率应为
\(q_a=(w_a/c_a)/\sum_b(w_b/c_b)\)，相同比率化为
\(\min_{j\ne i}\sum_a w_aD_{ij}(a)/c_a\)。这只是正成本下的变量变换，不能同时把 \(w\) 称为动作采样频率。移动成本随当前状态改变时，逐步重求是本文局部规划设计；母文的静态动作渐近保证不自动继承。

### 3.4 M3：审计的充分条件和不得重复计数

在审计起点 \(\tau\) 之后，以预先可测的备择预测密度 \(q_{r-1}\) 和复合零假设族 \(\mathcal P_i\) 构造

\[
E_{i,t}^{(\tau)}=
\frac{\prod_{r=\tau+1}^t q_{r-1}(Z_r\mid\mathcal F_{r-1},a_r)}
{\sup_{\theta\in\Theta_i}\prod_{r=\tau+1}^t p_{i,\theta}(Z_r\mid\mathcal F_{r-1},a_r)}.
\]

分母中的 \(\theta\) 是同一后缀上共享的零假设参数，不能悄悄改为每步重新选一个与过去不相容的真值参数。保守的逐步上包络也可用于构造，但应另给定义和证明，不能称为原式。若真条件模型属于零假设族、备择归一化且可预测，则对每个真零假设，\(E\) 被相应似然比鞅支配，可用 Ville 界约束任意时刻越阈概率。估计密度、重叠窗口、自适应特征或未建模风变化可能破坏这些前提。

同一历史可用于后续动作设计；审计只能使用其明确定义的新证据增量。多次重启、多个候选源应共享预先规定的错误预算。审计越阈可改变复核调度或终止许可，但不能把 \(E\) 再作为独立气体似然乘入后验。当前原生 M2/M3 未闭环，不可声称已控制真实 UAV 中的错误高置信概率。

### 3.5 PMFS 的实际计算及公平批评

PMFS 原文已把历史命中读出递归更新为概率命中图，并在候选源上运行简化传播模型。其逐格相容度可写为
\(g_{ki}=\alpha_i[1-|f_i^{\rm obs}-f_{ki}^{\rm pred}|]+(1-\alpha_i)\)，对格点乘积后归一化得到源图；原文式建立在所用条件独立近似上。主动价值为置信不足区域的后验加权预测方差。

因此讨论重点可以是：命中频率是否充分保留有限双点时空读出，空间乘积依赖近似是否过于自信，以及低后验候选在后续选点中是否被持续忽略。B4、M4/RK、R3 和 V7 负结果分别提供线索，不能由这些异质案例直接证明统一机制。原文 HTML 的 log-odds 定义处存在排版缺项，论文应使用标准 \(\log[p/(1-p)]\)，不要复制缺 log 的表达。

## 四、原始代码读取证据

以下为机制核查所读文件的 blob SHA；不代表完成运行复现，不替代用户工程的冻结提交。

|作者仓库／分支|路径|blob SHA|用途|
|---|---|---|---|
|emonetlab/GradientMotionMultiplePlumes, main|src/gradient_motion_panels/figure3_models.py|ddd18ed898362ed327555c244637db5e41ee0ea6|学习卷积、整流、镜像相减与输出类别|
|同上|REPRODUCE_FIGURES_1_3.md|86880913fe61b9619058600ec657f3e9c6c7bc55|复现入口和数据要求|
|rutalaboratory/Edge-Tracking-Model, main|state_space_model/simulation_agent.py|9b16818156a938768348102ece607553b97e5aa5|方向记忆、事件确认与内部状态|
|同上|data_preprocess.py|6d1fb49466b1ffa26e5945143b31dfeac7c39c91|数据处理接口；不据此声称在线时钟完成迁移|
|MAPIRlab/GasSourceLocalization, humble|gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp|7ebf4c308f652e871496e2c7d993a2e8312121c4|当前实现的方差信息值与空间权重|
|同上|gsl_server/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp|df6c07454c6dce6783bb599b7b4920249f50f1fb|相容度、置信权重和格点乘积|

快照仅为研究工作记录；交付工程宜保留引用 URL、SHA 和核验表，避免把整份外部源码作为自有创新附件。

## 五、待核事项及禁止升级的表述

- 非同质成本论文最初仅获二级 DOI 线索，随后直接读取出版方在 Crossref 的登记记录，确认 DOI `10.1109/ICASSP55912.2026.11463839`、页码91–95和作者身份一致；已更新正式 BibTeX，登记快照为 `costs_asht_crossref.json`。
- QSUT 的最终 npj Quantum Information DOI、卷／文章号未核得；可以引用实际阅读 arXiv 版本并说明作者列示接收状态，不得编造出版信息。
- Nature 最终主文 PDF 和 PNAS 全部 SI 尚未完整读取；已有作者方法正文和作者代码足以支持本文列出的限定性机制描述。
- 正式母算法可学习滤波器直接迁移、传感器动态匹配、跨源／跨风泛化与真实闭环收益都待实验；目前只能报告受限核库对照。
- GADEN 恢复、SHA、软件回归属于可复核性证据，不等同于物理资格化、定位性能优越或实飞验证。
- 湖岸 S2 DAY/NIGHT、多源泛化和 M2/M3 原生闭环未完成；不得把 House 数据结论外推为湖岸性能。

