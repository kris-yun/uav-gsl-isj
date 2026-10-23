# V8当前正文29条参考文献逐条核验表

核验日期：2026-10-23。本表严格对应当前 `verification/CURRENT_REFERENCES.json` 的29个引用编号，并从实际章节LaTeX提取引用位置。未修改正文、文献列表或原始工程。阅读深度以本次团队实际完成的核查为限；主代理和算法审计代理的核验明确署为团队记录，不冒称文献子任务个人通读全部材料。

## 覆盖范围和阅读层级

- 29条全部有引用位置、身份元数据、阅读深度、一级来源、允许支撑的论断和待核限制；正文引用键与表项一一覆盖。
- 冻结项目证据为4条（编号23–26），另有1条期刊官方指南（编号29）；两类均不是同行评议论文，不能合并称为5项项目实验。
- 五篇旧保留文献Francis2022、Gongora2023、Ercolani2023、Tian2025、Jin2023均未声称阅读全文。元数据核对只确认身份；具体实验和定量结论需另核正文。
- L1：出版方登记元数据；L2：官方/作者页面或摘要；L3：已标明的相关正文与方法；L4：作者代码。L4不意味着论文全读或运行复现。P：冻结项目证据；G：官方作者指南。组合层级表示分别核过这些证据，不是笼统“全部验证”。
- HTTP429是限流，403/418是该次访问受阻，均不能据此判定DOI或论文无效。未执行新模拟、训练或作者实验复现。
- 预印本、作者稿与最终出版版分开：DGSE引用2026 arXiv v1；QSUT引用实际读过的2025 arXiv v1，其2026最终出版元数据仍待核；Nature边界记忆论文的最终身份已核，方法阅读依靠作者稿和作者代码。
- 双侧算法按正式卷期采用Lin2025Bilateral；DOI中2024不是更改卷期年的理由。Cover2006采用第二版纸本2006年；Wiley在线首次发布日期2005单独记录。

## 逐条核验总表

|编号/引用键|本稿引用位置|元数据已核|阅读深度|一级来源|允许支撑论断|待核与使用限制|
|---|---|---|---|---|---|---|
|1. Francis2022（同行评议综述）|第1节“引言”（sections/01_introduction.tex:2）|2022；Journal of Field Robotics 39(8):1341–1373；DOI 10.1002/rob.22109。|L1；只核Crossref登记的作者、题名、期刊、卷期、页码和DOI；未阅读全文。|https://doi.org/10.1002/rob.22109|作为移动机器人气体建图与源定位领域的综述入口；本稿对任务估计对象的区分还依赖问题定义本身。|未逐段核综述分类和具体结论；不得借此引用具体方法优劣、性能数字或声称已通读。|
|2. Gongora2023（同行评议论文）|第1节“引言”（sections/01_introduction.tex:2）|2023；Sensors 23(12)，文章号5387；DOI 10.3390/s23125387；作者顺序已核。|L1+L2；Crossref完整元数据与作者/机构出版记录；出版方全文请求429限流，未阅读全文。|https://www.mdpi.com/1424-8220/23/12/5387 ; https://www.epfl.ch/labs/disal/research/gassensingstructure/|存在面向自主移动机器人的信息驱动气体分布建图研究；与源位置估计的研究对象区分。|具体目标函数、信息准则、实现和性能未全文核查。429表示访问限流，不表示DOI无效。|
|3. Welch2024（同行评议论文）|第1节“引言”（sections/01_introduction.tex:4）|2024；Atmosphere 15(7)，文章号809；DOI 10.3390/atmos15070809。|L1+L3；读出版方HTML摘要、模型与场景相关正文；核Crossref身份；未声称逐页通读全部实验。|https://www.mdpi.com/2073-4433/15/7/809|湖风锋中的微尺度风场与局地变化为湖岸气体传播任务提供物理背景。|不能据此证明枫树岭S2热力场已资格化、已实现真实湖风，或本方法已在湖岸验证。|
|4. Huang2024（同行评议论文）|第1节“引言”（sections/01_introduction.tex:4）|2024；Atmospheric Chemistry and Physics 24(4):2387–2398；DOI 10.5194/acp-24-2387-2024。|L1+L3；读官方摘要、沿岸采样方法、梯度机制讨论及元数据。|https://acp.copernicus.org/articles/24/2387/2024/acp-24-2387-2024.html|Lake Ontario岸线垂直方向的近地面臭氧浓度梯度和局地气象差异可作为应用背景。|臭氧受化学反应与沉降影响；不能等同被动气体单源泄漏实验，也不能外推S2场景验证结果。|
|5. Ercolani2023（同行评议论文）|第1节“引言”（sections/01_introduction.tex:4）|2023；Sensors 23(20)，文章号8512；DOI 10.3390/s23208512。|L1+L2；核Crossref和EPFL作者/机构出版记录；出版方429；未通读方法和实验。|https://www.mdpi.com/1424-8220/23/20/8512 ; https://www.epfl.ch/labs/disal/research/gassensingstructure/|多架微型无人机气体感知已研究平台干扰；支持将感知配置与干扰列为双机实验需控制的因素。|不得引用未核的旋翼干扰大小、推荐间距、传感器型号、布局和性能数字；本轮未阅读全文。|
|6. Lin2025Bilateral（同行评议论文）|第1节“引言”（sections/01_introduction.tex:6）|正式卷期为2025年IEEE Sensors Journal 25(1):697–708；DOI 10.1109/JSEN.2024.3407982；DOI含2024不等于卷期年。旧键Bilateral2024已改为Lin2025Bilateral。|L1+L2；核Crossref和IEEE索引摘要/方法片段；全文PDF访问418，未通读最终PDF。|https://ieeexplore.ieee.org/document/10551708/|动物klinotaxis与双侧浓度信息已用于三维气味源定位，双侧配置本身不能作为本文原创。|未复现该算法；不将其性能数字转借为本方法效果；引用内容限已核摘要与研究范围。|
|7. Shigaki2026Adaptive（同行评议论文）|第1节“引言”（sections/01_introduction.tex:6）|2026；npj Robotics 4，文章号12；DOI 10.1038/s44182-026-00080-5；五位作者已核。|L2+L3；读Nature官方摘要、引言和嗅觉缺损补偿任务/机器人验证范围；未做代码复现。|https://www.nature.com/articles/s44182-026-00080-5|昆虫启发行为补偿与嗅觉缺损条件下的机器人搜索已有先例。|不能据此声称本文首次提出双侧嗅觉、感知缺损恢复或等同M3源假设恢复；未复现实验。|
|8. Tian2025（同行评议会议论文）|第1节“引言”（sections/01_introduction.tex:6）|ICRA 2025:4380–4386；DOI 10.1109/ICRA55743.2025.11128134；完整九作者身份由登记核对。|L1+L2；主代理核Crossref、IEEE官方摘要以及DLR/TUM作者机构页面；未阅读全文。|https://ieeexplore.ieee.org/document/11128134/|地形感知的学习方法已用于移动机器人气体源定位；可支持相关研究方向存在。|训练/测试权限、模型内部结构、泛化条件和增益数值未通读核查；不将“改进表达”写成已核的量化性能结论。|
|9. Jin2023（同行评议会议论文）|第1节“引言”（sections/01_introduction.tex:6）|ICRA 2023:7749–7755；DOI 10.1109/ICRA48891.2023.10160816；采用出版登记作者顺序Jin、Rahbar、Ercolani、Martinoli。|L1+L2；核Crossref与EPFL作者团队页面；主代理读作者页面；未阅读全文。|https://doi.org/10.1109/ICRA48891.2023.10160816 ; https://www.epfl.ch/labs/disal/research/gassensingstructure/|建成环境中面向气体感知机器人的数据驱动羽流建模已有研究。|未核完整模型、具体环境和实验数字；不能据作者页认定已通读论文或证明本项目物理模型有效。|
|10. Ojeda2024PMFS（同行评议论文与作者代码）|第1节“引言”（sections/01_introduction.tex:6）；第1节“引言”（sections/01_introduction.tex:8）；第2.2节“原生PMFS计算链及具体研究动机”（sections/02_problem.tex:44）|2024；IEEE Transactions on Robotics 40:3551–3564；DOI 10.1109/TRO.2024.3426368；作者稿arXiv:2304.08879v3。|L1+L3+L4；读作者稿III–V节的计算链、相关方法和局限；核官方PMFS关键源码，未将代码阅读称为复现实验。|https://arxiv.org/html/2304.08879v3 ; https://doi.org/10.1109/TRO.2024.3426368 ; https://github.com/MAPIRlab/GasSourceLocalization|历史命中图与置信度、候选源传播预测、逐格兼容评分、粗细网格、源分布加权预测方差和未观测置信度选点；PMFS已有历史和主动搜索。|作者代码4e141e1与项目O24来源a8d5a76分开；不能把整个累计命中图重复当新独立似然，不能将本项目V7负结果归因PMFS。|
|11. Kim2026DGSE（作者预印本）|第1节“引言”（sections/01_introduction.tex:6）|arXiv:2608.16221v1，2026-08-17；四位作者已核；正式期刊/会议出版状态未确认。|L2+L3；读作者arXiv v1问题定义、风→浓度→源条件推断链、主动策略及实验适用范围。|https://arxiv.org/html/2608.16221v1|连续浓度、风与源的物理依赖顺序概率推断已有相关研究；源导向建模不是本文独有方向。|明确标预印本，不写成已同行评议；该文性能不能外推到当前两机或S2任务。|
|12. Vergassola2007Infotaxis（同行评议论文）|第1节“引言”（sections/01_introduction.tex:8）|2007；Nature 445:406–409；DOI 10.1038/nature05464。|L2；核Nature官方摘要及书目；未通读完整论文。|https://www.nature.com/articles/nature05464|信息获取/不确定性减少驱动的主动嗅觉搜索已有经典先例。|本稿仅作方法谱系引用；实际实现infotaxis基线前仍需核其观测模型、动作和目标函数；不声称全文读过。|
|13. Jin2024（同行评议会议论文）|第1节“引言”（sections/01_introduction.tex:8）|ICRA 2024:14909–14916；DOI 10.1109/ICRA57147.2024.10611440；作者Jin、Martinoli。|L1+L2+局部L3；核Crossref、作者履历、机构摘要；读作者摘要及可检索方法片段；PDF直取429，未逐页通读。|https://infoscience.epfl.ch/entities/publication/22992bbb-65c6-4b2c-a983-17f4050d44f2 ; https://graphsearch.epfl.ch/en/publication/22992bbb-65c6-4b2c-a983-17f4050d44f2|运动中连续感知、信念聚类以及羽流/传感器时间特性应进入主动定位比较。|不能简化为仅在终点一次EIG；不引用未逐项核对的性能数字；未运行算法。|
|14. Jin2025（同行评议会议论文）|第1节“引言”（sections/01_introduction.tex:8）|IROS 2025:18088–18094；DOI 10.1109/IROS60139.2025.11246224；四位作者已核。|L1+L2+局部L3；核Crossref、EPFL条目和作者正式履历；读作者摘要及作者上传稿可得内容；未声称逐页通读最终PDF。|https://infoscience.epfl.ch/entities/publication/3a6f868c-8d68-4aaa-937e-900941d3c694 ; https://disalw3.epfl.ch/people/alcherio/files/AM_full_CV.pdf ; https://www.epfl.ch/labs/disal/research/gassensingstructure/|气体源定位已有沿路径累积信息规划；比较应包括移动、沿途观测和停留成本。|不将路径累计信息称为本文首次；未运行作者算法，不引用其性能作为本文证据。|
|15. Brudner2026Opponent（同行评议论文与作者代码）|第1节“引言”（sections/01_introduction.tex:12）；第3节“面向竞争源判别的双侧镜像嗅觉计算”（sections/03_04_methods.tex:8）|2026；PNAS 123(29):e2608896123；DOI 10.1073/pnas.2608896123；七位作者已核。|L1+L3+L4；读PNAS主文相关方法、图3模型、作者figure3_models.py和复现说明；未逐项核完全部SI，未运行母算法实验。|https://www.pnas.org/doi/10.1073/pnas.2608896123 ; https://github.com/emonetlab/GradientMotionMultiplePlumes|可学习双侧因果时间滤波、整流、镜像相减与sigmoid中心线侧别判别；梯度和气味运动互补是母文来源。|V7固定核库与TRAIN选择不是原可学习MNM复现；母文不验证候选源后验、双无人机或M1定位收益；新意限任务/证据/选择机制改造。|
|16. Siliciano2026Vector（同行评议论文元数据＋作者稿/代码）|第1节“引言”（sections/01_introduction.tex:12）；第4.1节“M2：动态边界方向记忆与返回区域”（sections/03_04_methods.tex:144）|Nature 657:443–454，2026；DOI 10.1038/s41586-026-10827-7；九位作者与正式题名已核。|L1+L3+L4；核最终Nature书目；读作者2025预印本相关方向记忆方法、官方作者代码及出版方评审材料；最终全文跳转受限，未声称通读最终版。|https://www.nature.com/articles/s41586-026-10827-7 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11844514/ ; https://github.com/rutalaboratory/Edge-Tracking-Model|气味进入/退出事件关联的方向向量记忆和边界返回策略，可启发M2候选动作生成。|作者稿与最终版应区分；不能解释为稳定世界坐标边界图、源概率图或已实现双机编队；向量不能另作独立源似然。|
|17. Hsu2025Tradeoffs（同行评议论文＋作者稿）|第1节“引言”（sections/01_introduction.tex:12）；第4.3节“M3：完整源集上的成本分配与持续覆盖”（sections/03_04_methods.tex:207）|2025；IEEE Transactions on Information Theory 71(9):6546–6565；DOI 10.1109/TIT.2025.3588527；作者稿2405.06554v3。|L1+L3；读作者稿问题定义、动作/资源约束与错误指数框架；未声称逐行验证全部定理证明。|https://arxiv.org/html/2405.06554v3 ; https://cc.ee.ntu.edu.tw/~ihsiangw/NICLab/Publications.html|主动多假设检验中的动作策略、资源分配和竞争假设区分已有理论基础。|已知条件模型及渐近条件不能直接转成有限时长、时变羽流UAV的最优性或恢复保证。|
|18. Vershinin2026Costs（同行评议会议论文＋作者稿）|第1节“引言”（sections/01_introduction.tex:12）；第4.3节“M3：完整源集上的成本分配与持续覆盖”（sections/03_04_methods.tex:207）|ICASSP 2026:91–95；DOI 10.1109/ICASSP55912.2026.11463839；作者稿arXiv:2509.11632v3。|L1+L3；读作者稿相关问题、非同质成本比率目标、改造Chernoff策略及理论假设；核ICASSP官方记录与Crossref。|https://arxiv.org/html/2509.11632v3 ; https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1 ; https://doi.org/10.1109/ICASSP55912.2026.11463839|成本份额与动作抽样频率需区分，q(a)正比w(a)/c(a)；资源效率目标是期望信息与期望成本之比。|不能将E[D]/E[c]写成E[D/c]；已知模型、可实施动作及渐近假设限制移植；不自动证明M3有限样本最优。|
|19. Wasserman2020Universal（同行评议论文）|第1节“引言”（sections/01_introduction.tex:12）；第4.4节“M3：新后缀审计与可恢复候选列表”（sections/03_04_methods.tex:261）|2020；PNAS 117(29):16880–16890；DOI 10.1073/pnas.1922664117。|L1+L3；读通用似然构造和适用条件；未声称逐行复核全部证明。|https://www.pnas.org/doi/10.1073/pnas.1922664117|通用似然比推断为预测备择与零假设似然比较提供基础；本稿须自行列明顺序化与条件校准假设。|不得从该引用直接推出任意失配模型中的e过程有效；新后缀本身不能修复模型误差；审计不能再次乘入气体后验。|
|20. Zecchin2025QSUT（作者预印本；最终出版元数据待核）|第1节“引言”（sections/01_introduction.tex:12）；第4.4节“M3：新后缀审计与可恢复候选列表”（sections/03_04_methods.tex:261）|实际引用读过的arXiv:2508.21594v1，2025-08-29；三位作者已核；不得虚填2026正式卷页/DOI。|L2+L3；读arXiv v1的算法、可预测似然、复合零假设与两侧检验条件；作者主页列npj Quantum Information 2026，但最终DOI未独立核得。|https://arxiv.org/html/2508.21594v1 ; https://web.stanford.edu/~aramdas/|借鉴已读作者稿中的可预测替代密度与复合零假设审计结构，不涉及量子硬件。|复合零假设分母应对整段前缀共同参数最大化；需真实条件分布包含、可预测归一化和多次审计错误预算；量子实验不是气体定位证据。|
|21. Monroy2017GADEN（同行评议论文＋作者项目记录）|第2.1节“场景、观测任务与固有挑战”（sections/02_problem.tex:30）|2017；Sensors 17(7)，文章号1479；DOI 10.3390/s17071479。|L1+L2；核作者项目书目、机构页面和元数据；MDPI请求429，未阅读全文。|https://www.mdpi.com/1424-8220/17/7/1479 ; https://mapir.isa.uma.es/mapirpubsite/index.php/publications/show/362 ; https://github.com/MAPIRlab/gaden|GADEN是移动机器人嗅觉的三维气体扩散仿真平台；支持说明仿真工具来源。|不能由平台论文推出理想浓度等于真实PID动态，也不能证明本项目源高、湖岸热场和实飞已验证；本轮未读2017全文。|
|22. Ojeda2025GadenRT（同行评议软件论文＋作者代码文档）|第2.1节“场景、观测任务与固有挑战”（sections/02_problem.tex:30）|2025；SoftwareX 32，文章号102388；DOI 10.1016/j.softx.2025.102388。|L1+L2+L4；核官方书目、作者README和changelog；出版方全文403；未通读论文全文。|https://www.sciencedirect.com/science/article/pii/S2352711025003541 ; https://github.com/MAPIRlab/gaden ; https://github.com/MAPIRlab/gaden/blob/humble/Changelog.md|实时交互气体仿真平台来源；作者文档中的可选GPU浓度图加速仅按对应环节描述。|不得写成全管线GPU物理求解，也不把代码工具来源当本项目物理资格与定位增益；403不等于文献无效。|
|23. V7Archive（冻结项目代码/研究记录；非同行评议）|第2.2节“原生PMFS计算链及具体研究动机”（sections/02_problem.tex:44）；第2.2节“原生PMFS计算链及具体研究动机”（sections/02_problem.tex:81）；第3.1节“双侧读出、真实时钟与因果镜像算子”（sections/03_04_methods.tex:54）；第4节“判别式双机测量与持续反证定位”（sections/03_04_methods.tex:140）；第5.2节“固定观测下的完整普通对照”（sections/05_experiments.tex:45）|2026项目研究快照；固定提交061ecf5ddea0a59dcf932b5038ad646b7af454a4；不是期刊/会议论文，没有虚构DOI。|P；团队审计读取冻结方法文档、代码、合同与结果汇总；文献子任务读跨领域及理论文档；逐文件身份见代码证据清单。|https://github.com/kris-yun/uav-gsl-isj/tree/061ecf5ddea0a59dcf932b5038ad646b7af454a4/research/source_localization_v7|用于实现状态、固定核库、代码来源、研究原型、已有static pilot与解析矩阵，以及R3汇总的来源和未恢复边界。|R3窗口级收据未完全恢复；40快照来自4开发世界，不等于40独立世界；156解析episode不是原生物理闭环；设计与软件测试不证明性能。|
|24. EvidenceB4（冻结项目失败案例记录；非同行评议）|第2.2节“原生PMFS计算链及具体研究动机”（sections/02_problem.tex:79）|B4终止记录提交c2aacbac7fb2ef7be4be3c9c7dcfce20c11f823c；M0归因记录17c48958f9d7eda98dd61b8e656a8c52205cb7d7；2026。|P；算法审计读取两份冻结原文并核字节SHA；记录来源与当前主张逐项对应，未重跑该实验。|https://github.com/kris-yun/uav-gsl-isj/blob/c2aacbac7fb2ef7be4be3c9c7dcfce20c11f823c/research/pmfs_reproduction/b4_official_terminal_resumed_20261010/B4_OFFICIAL_TERMINAL_DECISION_zh.md ; https://github.com/kris-yun/uav-gsl-isj/blob/17c48958f9d7eda98dd61b8e656a8c52205cb7d7/research/pmfs_reproduction/b4_m0_offline_attribution_20261010/B4_M0_EVIDENCE_ATTRIBUTION_zh.md|特定归档运行的success=true、源图方差约0.329、Top-5%误差5.112m与错/真代表源兼容比约14874.6；集中度与准确性需分开。|项目案例不能证明通用统一根因或所有PMFS条件下失败；没有同行评议身份，未新增运行。|
|25. EvidenceRK（冻结项目响应审计记录；非同行评议）|第2.2节“原生PMFS计算链及具体研究动机”（sections/02_problem.tex:80）|M4提交5f89ae05e29714cc31d006638c5067e6813e7077；RK2提交5df5771ca916f209d041e3e3ecd548ec65eb8424；2026项目记录。|P；算法审计读取M4和RK2冻结报告并核字节SHA；按原报告条件引用，不称为本轮新实验。|https://github.com/kris-yun/uav-gsl-isj/blob/5f89ae05e29714cc31d006638c5067e6813e7077/evidence/causal_compositional_plume_world_model_v1/M4_V2_FROZEN_TRANSPORT_RESPONSE_AUDIT_20260923.md ; https://github.com/kris-yun/uav-gsl-isj/blob/5df5771ca916f209d041e3e3ecd548ec65eb8424/research/pmfs_reproduction/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010/RK2_FINITE_PROTOTYPE_REPORT_zh.md|限定M4/RK归档：场MSE下降不能自动等同源排名收益；RK2-L相对S连续MSE约降29.22%、源NLL约1.22%、Top-1均4/4。|不同报告的数据条件与对照须区分；复合分数不自动成为校准后验；不是独立同行评议研究，也非M1增益证据。|
|26. V7Native（冻结项目原生实验/收据；非同行评议）|第2.2节“原生PMFS计算链及具体研究动机”（sections/02_problem.tex:82）；第3.3节“联合源推断、信息边界与已发现的退化”（sections/03_04_methods.tex:129）；第4节“判别式双机测量与持续反证定位”（sections/03_04_methods.tex:140）；第5节“预实验与后续验证方案”（sections/05_experiments.tex:3）|固定提交061ecf5ddea0a59dcf932b5038ad646b7af454a4；2026-10-23报告及原生R2开发记录。|P；团队读冻结执行报告、R2_RESULT、模型/训练冻结、通道收据与SHA清单；主代理复算已有统计量，未新生成观测。|https://github.com/kris-yun/uav-gsl-isj/blob/061ecf5ddea0a59dcf932b5038ad646b7af454a4/research/source_localization_v7/NATIVE_EXECUTION_REPORT_zh.md|8原生世界、14424帧、71软件测试、1200读出回归；两已标定源4DEV理想粗采样下普通单点/完整双点均4/4、M1为2/4、平均MAP误差约2.427m；覆盖阈值饱和、动态通道0。|不是PMFS正式闭环对照；M2/M3原生闭环未启动，S2多源DAY/NIGHT未完成；不能推广未知源/风/真实传感器，更不能声称已有定位增益。|
|27. Cover2006（信息论教材）|第2.3节“科学问题与总体方案”（sections/02_problem.tex:103）|Thomas M. Cover、Joy A. Thomas；Elements of Information Theory，第2版，Wiley，2006，ISBN9780471241959。官方在线首次发布日期2005与纸本版权/产品年2006不同，保留纸本2006。|L2；核Wiley官方第二版书目、ISBN和第2章目录含数据处理不等式；未读取付费章全文；本稿短证明属一般推导。|https://onlinelibrary.wiley.com/doi/book/10.1002/047174882X ; https://onlinelibrary.wiley.com/doi/abs/10.1002/047174882X.ch2|数据处理不等式的一般出处；固定或仅凭已见训练/历史选定的确定编码不能增加原始观测中关于源的信息。|条件历史、动作和固定模型后才应用Markov链；该定理不证明有限模型性能一定不变，也不否认M2新测点可获取新信息；不声称读完整本。|
|28. Ojeda2023VGR（同行评议数据集论文）|第5.1节“数据来源、划分和读出资格”（sections/05_experiments.tex:6）|2023；Journal of Intelligent & Robotic Systems 109，文章号75；DOI 10.1007/s10846-023-02012-z；75不是页码75–83。|L1+L3；读出版方任务、环境与数据结构相关内容和元数据；不把论文数据集描述当本项目归档结果。|https://link.springer.com/article/10.1007/s10846-023-02012-z|说明House/VGR/GADEN气体扩散数据背景；本项目8世界、源坐标和帧数由冻结收据单独支撑。|不能据VGR论文证明枫树岭S2热力条件、湖岸资格、真实传感器或当前M1增益。|
|29. AASGuide（期刊官方作者指南；非研究论文）|第6节“结论”（sections/06_conclusion.tex:9）|《自动化学报》编辑部《投稿须知》；2026-10-23为核对日期，不将其伪作页面初次发表年。|G；主代理实际读取2026-10-23可见的官方投稿须知；属于动态政策页面，不是同行评议研究或项目代码。|https://www.aas.net.cn/news/tgxz.htm ; https://www.aas.net.cn/news/lunwenmoban.htm|投稿格式、双盲、论据与引文可靠性、AI辅助披露及核心内容生成限制等作者要求的现行依据。|采用aas格式不表示已符合全部投稿条款，也不表示目标期刊已定；缺失导师“小论文撰写要求PDF”不能由此替代或声称已读。|

## 完整身份与本地核验依据

以下身份从本次实际参考文献元数据读取；具体纠错和版本限制以上表为准。相对路径以本工作目录 `v8_work/literature` 为参照；`original_bibliography_crossref.json` 实际位于其上级目录。项目代码清单和历史证据清单由对应审计任务维护。

### [1] Francis2022

Francis, Adam and Li, Shuai and Griffiths, Christian and Sienz, Johann. Gas source localization and mapping with mobile robots: A review. Journal of Field Robotics. 2022. 39(8):1341–1373. DOI: 10.1002/rob.22109

**核验依据：**original_bibliography_crossref.json；ORIGINAL_35_REFERENCE_REVIEW.md

### [2] Gongora2023

Gongora, Andres and Monroy, Javier and Rahbar, Faezeh and Ercolani, Chiara and Gonzalez-Jimenez, Javier and Martinoli, Alcherio. Information-Driven Gas Distribution Mapping for Autonomous Mobile Robots. Sensors. 2023. 23(12):5387. DOI: 10.3390/s23125387

**核验依据：**original_bibliography_crossref.json；ORIGINAL_35_REFERENCE_REVIEW.md

### [3] Welch2024

Welch, Brittany M. and Horel, John D. and Sauer, Jeremy A.. Application of the {NCAR FastEddy} Microscale Model to a Lake Breeze Front. Atmosphere. 2024. 15(7):809. DOI: 10.3390/atmos15070809

**核验依据：**background_crossref.json；background_sources/fasteddy.html；BACKGROUND_REFERENCE_AUDIT_zh.md

### [4] Huang2024

Huang, Yao Yan and Donaldson, D. James. Measurement report: Observations of ground-level ozone concentration gradients perpendicular to the {Lake Ontario} shoreline. Atmospheric Chemistry and Physics. 2024. 24(4):2387–2398. DOI: 10.5194/acp-24-2387-2024

**核验依据：**background_crossref.json；BACKGROUND_REFERENCE_AUDIT_zh.md

### [5] Ercolani2023

Ercolani, Chiara and Jin, Wanting and Martinoli, Alcherio. 3D Gas Sensing with Multiple Nano Aerial Vehicles: Interference Analysis, Algorithms and Experimental Validation. Sensors. 2023. 23(20):8512. DOI: 10.3390/s23208512

**核验依据：**original_bibliography_crossref.json；ORIGINAL_35_REFERENCE_REVIEW.md

### [6] Lin2025Bilateral

Lin, Qin and Wu, Shuo and Wang, Hui and Ma, Ke and Jiang, Lelun and Zhang, Jinxiu. Incorporating Animal Klinotaxis Behavior and Bilateral Concentration Information: A {3-D} Bio-Inspired Odor Source Localization Algorithm and Its Performance Evaluation. IEEE Sensors Journal. 2025. 25(1):697–708. DOI: 10.1109/JSEN.2024.3407982

**核验依据：**background_crossref.json；BACKGROUND_REFERENCE_AUDIT_zh.md

### [7] Shigaki2026Adaptive

Shigaki, Shunsuke and Yokota, Keisuke and Sekiwa, Ryoko and Kurabayashi, Daisuke and Owaki, Dai. Insect-inspired adaptive behavioral compensation strategy against olfactory sensory deficiency for robotic odor source localization. npj Robotics. 2026. 4:12. DOI: 10.1038/s44182-026-00080-5

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [8] Tian2025

Tian, Changhao and Wang, Annan and Fan, Han and Wiedemann, Thomas and Luo, Yifei and Yang, Le and Lin, Weisi and Lilienthal, Achim J. and Chen, Xiaodong. Deep Learning Based Topography Aware Gas Source Localization with Mobile Robot. 2025 IEEE International Conference on Robotics and Automation (ICRA). 2025.:4380–4386. DOI: 10.1109/ICRA55743.2025.11128134

**核验依据：**original_bibliography_crossref.json；主代理本轮IEEE/作者页阅读记录；ORIGINAL_35_REFERENCE_REVIEW.md

### [9] Jin2023

Jin, Wanting and Rahbar, Faezeh and Ercolani, Chiara and Martinoli, Alcherio. Towards Efficient Gas Leak Detection in Built Environments: Data-Driven Plume Modeling for Gas Sensing Robots. 2023 IEEE International Conference on Robotics and Automation (ICRA). 2023.:7749–7755. DOI: 10.1109/ICRA48891.2023.10160816

**核验依据：**original_bibliography_crossref.json；ORIGINAL_35_REFERENCE_REVIEW.md

### [10] Ojeda2024PMFS

Ojeda, Pepe and Monroy, Javier and Gonzalez-Jimenez, Javier. Robotic Gas Source Localization With Probabilistic Mapping and Online Dispersion Simulation. IEEE Transactions on Robotics. 2024. 40:3551–3564. DOI: 10.1109/TRO.2024.3426368

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md；MAPIRlab_GasSourceLocalization_Simulations.cpp；MAPIRlab_GasSourceLocalization_MovingStatePMFS.cpp；../algorithm_audit/V7_CODE_EVIDENCE_AUDIT.md

### [11] Kim2026DGSE

Kim, Seunghwan and Kim, Hyungjin and Lee, Junhee and Oh, Hyondong. Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference. arXiv. 2026.. arXiv: 2608.16221

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [12] Vergassola2007Infotaxis

Vergassola, Massimo and Villermaux, Emmanuel and Shraiman, Boris I.. `Infotaxis' as a strategy for searching without gradients. Nature. 2007. 445:406–409. DOI: 10.1038/nature05464

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [13] Jin2024

Jin, Wanting and Martinoli, Alcherio. Sense in Motion with Belief Clustering: Efficient Gas Source Localization with Mobile Robots. 2024 IEEE International Conference on Robotics and Automation (ICRA). 2024.:14909–14916. DOI: 10.1109/ICRA57147.2024.10611440

**核验依据：**background_crossref.json；BACKGROUND_REFERENCE_AUDIT_zh.md

### [14] Jin2025

Jin, Wanting and Leroy, Hugo and B{\"o}sel-Schmid, Nicolaj and Martinoli, Alcherio. Cumulative Informative Path Planning for Efficient Gas Source Localization with Mobile Robots. 2025 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). 2025.:18088–18094. DOI: 10.1109/IROS60139.2025.11246224

**核验依据：**background_crossref.json；BACKGROUND_REFERENCE_AUDIT_zh.md

### [15] Brudner2026Opponent

Brudner, Samuel and Zhou, Baohua and Jayaram, Viraaj and {Madeira Santana}, Gustavo and Crimaldi, John P. and Clark, Damon A. and Emonet, Thierry. Fly navigational responses exploit plume-specific odor motion and gradient cues. Proceedings of the National Academy of Sciences. 2026. 123(29):e2608896123. DOI: 10.1073/pnas.2608896123

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md；emonetlab_GradientMotionMultiplePlumes_figure3_models.py；emonetlab_GradientMotionMultiplePlumes_REPRODUCE_FIGURES_1_3.md

### [16] Siliciano2026Vector

Siliciano, Andrew F. and Minni, Sun and Morton, Chad and Dowell, Charles K. and Eghbali, Noelle B. and Busch, Silas E. and Rhee, Juliana Y. and Abbott, L. F. and Ruta, Vanessa. A vector-based strategy for olfactory navigation in {Drosophila}. Nature. 2026. 657:443–454. DOI: 10.1038/s41586-026-10827-7

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md；rutalaboratory_Edge-Tracking-Model_data_preprocess.py；rutalaboratory_Edge-Tracking-Model_simulation_agent.py

### [17] Hsu2025Tradeoffs

Hsu, Chia-Yu and Wang, I-Hsiang. Tradeoffs Among Action Taking Policies Matter in Active Sequential Multi-Hypothesis Testing: The Optimal Error Exponent Region. IEEE Transactions on Information Theory. 2025. 71(9):6546–6565. DOI: 10.1109/TIT.2025.3588527

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [18] Vershinin2026Costs

Vershinin, George and Cohen, Asaf and Gurewitz, Omer. Active Sequential Hypothesis Testing with Non-Homogeneous Costs. 2026 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). 2026.:91–95. DOI: 10.1109/ICASSP55912.2026.11463839

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md；costs_asht_crossref.json

### [19] Wasserman2020Universal

Wasserman, Larry and Ramdas, Aaditya and Balakrishnan, Sivaraman. Universal inference. Proceedings of the National Academy of Sciences. 2020. 117(29):16880–16890. DOI: 10.1073/pnas.1922664117

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [20] Zecchin2025QSUT

Zecchin, Matteo and Simeone, Osvaldo and Ramdas, Aaditya. Quantum Sequential Universal Hypothesis Testing. arXiv. 2025.. arXiv: 2508.21594

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [21] Monroy2017GADEN

Monroy, Javier and Hernandez-Bennetts, Victor and Fan, Han and Lilienthal, Achim and Gonzalez-Jimenez, Javier. {GADEN}: A {3D} Gas Dispersion Simulator for Mobile Robot Olfaction in Realistic Environments. Sensors. 2017. 17(7):1479. DOI: 10.3390/s17071479

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [22] Ojeda2025GadenRT

Ojeda, Pepe and Monroy, Javier and Gonzalez-Jimenez, Javier. {Gaden-RT}: A real time and interactive gas dispersion simulator for mobile robotics. SoftwareX. 2025. 32:102388. DOI: 10.1016/j.softx.2025.102388

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [23] V7Archive

{项目研究记录}. Source Localization V7：方法、数据合同与实现快照. . 2026.

**核验依据：**../algorithm_audit/V7_CODE_EVIDENCE_AUDIT.md；../algorithm_audit/SOURCE_MANIFEST.json；CROSS_DOMAIN_DISCOVERY_AND_TRANSFER.md；THREE_INNOVATIONS_AND_THEORY.md

### [24] EvidenceB4

{项目研究记录}. B4官方终止判定及M0离线归因记录. . 2026.

**核验依据：**../algorithm_audit/HISTORICAL_SOURCE_MANIFEST.json；../algorithm_audit/historical/B4_OFFICIAL_TERMINAL_DECISION_zh.md；../algorithm_audit/historical/B4_M0_EVIDENCE_ATTRIBUTION_zh.md

### [25] EvidenceRK

{项目研究记录}. M4传播响应审计与RK2有限响应原型报告. . 2026.

**核验依据：**../algorithm_audit/HISTORICAL_SOURCE_MANIFEST.json；../algorithm_audit/historical/M4_V2_FROZEN_TRANSPORT_RESPONSE_AUDIT_20260923.md；../algorithm_audit/historical/RK2_FINITE_PROTOTYPE_REPORT_zh.md

### [26] V7Native

{项目研究记录}. 原生执行报告及冻结R2开发对照收据. . 2026.

**核验依据：**../algorithm_audit/V7_CODE_EVIDENCE_AUDIT.md；../algorithm_audit/SOURCE_MANIFEST.json；../algorithm_audit/snapshot/research/source_localization_v7/NATIVE_EXECUTION_REPORT_zh.md

### [27] Cover2006

Cover, Thomas M. and Thomas, Joy A.. Elements of Information Theory. Wiley. 2006.. ISBN: 9780471241959

**核验依据：**ORIGINAL_35_REFERENCE_REVIEW.md；cover_thomas_2006.bib（另稿键CoverThomas2006，当前键Cover2006）

### [28] Ojeda2023VGR

Ojeda, Pepe and Monroy, Javier and Gonzalez-Jimenez, Javier. {VGR Dataset}: A {CFD}-based Gas Dispersion Dataset for Mobile Robotic Olfaction. Journal of Intelligent \& Robotic Systems. 2023. 109:75. DOI: 10.1007/s10846-023-02012-z

**核验依据：**PRIMARY_LITERATURE_AUDIT_zh.md

### [29] AASGuide

{《自动化学报》编辑部}. 投稿须知. . 2026.

**核验依据：**主代理官方作者指南阅读记录；论文第6节研究稿与辅助工具说明

## 本次引用位置快照

章节名和引用键是主要定位依据；行号仅对应本次读取快照，后续文字或排版编辑可能改变。输入JSON SHA256：`11986e67a7a4c9afee0d91ae90f619222d292a6cc979b544b1a9b08c07e94720`。

|章节文件|SHA256|
|---|---|
|sections/01_introduction.tex|`f9e7ccf16e6763123fd5b7540849de96640f7f1f2abe6c8d4e7f1924ca1bade5`|
|sections/02_problem.tex|`44dbd091697e48b24f3a8c6dae7b69dc5541e7aba989d5906b02a29d57471046`|
|sections/03_04_methods.tex|`b1ef2359a724938e2fe4ebe9016334d92a92e82f563e7a9bb7679b5a26ee232d`|
|sections/05_experiments.tex|`265e8306b916cd185af5e2a672ad4a75e4e7aae1c027f374da54d59f50f26b67`|
|sections/06_conclusion.tex|`9af8a78643b6cf8485cbc20cdc8ff3f6e6af0f345fb3426841c624c5ac263b24`|

## 仍须由作者完成的引用收尾

五篇旧保留文献目前只支撑所列的研究方向和任务背景，不能承担未核的机制细节与实验数字。若定稿进一步扩展这些论断，应读取相关原文并记录准确页段。QSUT最终出版身份和Nature边界论文最终版相对作者稿的差异仍可在定稿前补核；未核之前保留现在明确的版本说明。冻结项目收据可以证明对应运行发生过及其记录值，不能代替独立重复实验和同行评议；AASGuide用于报告作者要求，不能证明本研究讨论稿已获投稿资格。
