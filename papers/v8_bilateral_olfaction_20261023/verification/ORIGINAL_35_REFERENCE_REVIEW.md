# 原稿35条参考文献逐条核验与V8编辑建议

核验日期：2026-10-23。范围是 `original_bibliography.json` 中35个唯一旧编号（1–35），不是V8新增文献的最终编号。数据源包括原始著录、`original_bibliography_crossref.json`、本次已有一级文献阅读记录和补核后的 `background_crossref.json`。本文件只提供核验与编辑建议，**没有修改论文主工程**。

## 核验范围和判定规则

- **L0：原稿线索／未获独立核验。**可列出原有身份线索，不等于已确认题名、年份或DOI。
- **L1：出版方登记元数据。**通常指Crossref身份、作者、卷期、页码核对；不等于全文阅读，也不足以支持具体性能结论。
- **L2：出版方或作者页面、作者摘要。**身份和相关任务可据所读内容说明；本文明确注明授权数据库作者摘要、出版社主站未核的例外。
- **L3：相关正文／方法。**仅覆盖注明的实际读取部分；“局部”不写成全文通读。
- **L4：作者公开代码／实现。**代码阅读不等于复现实验，更不等于对本项目的物理验证。

删除、替换或移入候选库是围绕V8三机制进行的范围取舍。对未阅读全文的条目，理由仅基于题名、原稿引用位置与当前方法接口，不对原论文的真实性、创新性或性能作否定判断。**HTTP429是限流；Crossref404只表示该次登记查询未返回记录；二者都不自动意味着DOI无效。**纸本卷期年与在线发表年、DOI字符串中的年份可能不同，不能机械替换。

## 完整核验表

|原编号|原稿文献身份|核验层级与实际阅读|身份／DOI／年份核对|V8建议及理由|未核项目|证据地址|
|---|---|---|---|---|---|---|
|1|Francis A, Li S, Griffiths C, Sienz J. Gas source localization and mapping with mobile robots: A review. Journal of Field Robotics, 2022, 39(8): 1341–1373. DOI: 10.1002/rob.22109|L1；本轮只核Crossref题名、作者、期刊卷期页码；未阅读全文。|题名、作者缩写、2022年、39(8):1341–1373及DOI一致。|保留；领域综述入口，用于区分气体分布建图与源定位；具体算法论断应引用原研究。|如引用综述中的具体分类或结论，仍需核相应正文段落。|https://doi.org/10.1002/rob.22109|
|2|Ercolani C, Jin W, Martinoli A. 3D gas sensing with multiple nano aerial vehicles: Interference analysis, algorithms and experimental validation. Sensors, 2023, 23(20): 8512. DOI: 10.3390/s23208512|L1+L2；Crossref完整身份；EPFL作者项目页出版记录；未通读该文方法及实验。|2023年23(20):8512为文章号；DOI一致。|保留；双无人机平台相关背景，提醒旋翼／传感器互扰及真实读出条件需要控制。|互扰大小、感知高度、设备配置和性能数值未核，不能直接写入本稿。|https://www.mdpi.com/1424-8220/23/20/8512|
|3|Ojeda P, Monroy J, Gonzalez-Jimenez J. Robotic gas source localization with probabilistic mapping and online dispersion simulation. IEEE Transactions on Robotics, 2024, 40: 3551–3564. DOI: 10.1109/TRO.2024.3426368|L3+L4；已读作者接收稿III–V节计算链、方法与局限；已读官方PMFS关键源码。|2024年40:3551–3564与DOI一致；纠正正文误述：PMFS已有历史命中图和主动方差选点。|保留（核心）；母基线的原始计算链及公平比较必须回到本论文和冻结代码。|用户实际PMFS基线需冻结提交；当前humble代码不能替代固定版本。|https://arxiv.org/html/2304.08879v3 ; https://github.com/MAPIRlab/GasSourceLocalization|
|4|Tian C, Wang A, Fan H, Wiedemann T, Luo Y, Yang L, Lin W, Lilienthal A J, Chen X. Deep learning based topography aware gas source localization with mobile robot. In: 2025 IEEE International Conference on Robotics and Automation. IEEE, 2025: 4380–4386. DOI: 10.1109/ICRA55743.2025.11128134|L1；仅Crossref正式登记元数据，未读方法全文。|9作者及ICRA2025:4380–4386、DOI与原稿一致；题名大小写规范化。|保留（内容引述待核）；已有拓扑／地形感知学习型定位的相关工作，可用于避免把学习源位置当作新概念。|网络结构、数据权限、泛化条件和性能主张尚未核验。|https://doi.org/10.1109/ICRA55743.2025.11128134|
|5|Jin W, Martinoli A. Sense in motion with belief clustering: Efficient gas source localization with mobile robots. In: 2024 IEEE International Conference on Robotics and Automation. IEEE, 2024: 14909–14916. DOI: 10.1109/ICRA57147.2024.10611440|L2+L3（局部）；Crossref、EPFL作者条目及履历；已读作者摘要与可检索方法段落，PDF直取限流，未逐页通读。|ICRA2024:14909–14916、2作者及DOI一致。|保留；连续运动感知和信念聚类已有先行研究；支撑采样时钟、传感器动态与真实移动预算的讨论。|未完成算法复现；不使用其报告增益作为本文证据。|https://infoscience.epfl.ch/entities/publication/22992bbb-65c6-4b2c-a983-17f4050d44f2 ; https://infoscience.epfl.ch/bitstreams/2abb588a-b524-4612-bc8d-22f5fa9a1434/download|
|6|Jin W, Leroy H, Bösel-Schmid N, Martinoli A. Cumulative informative path planning for efficient gas source localization with mobile robots. In: 2025 IEEE/RSJ International Conference on Intelligent Robots and Systems. IEEE, 2025: 18088–18094. DOI: 10.1109/IROS60139.2025.11246224|L1+L2；初次Crossref429，补核已成功；EPFL项目页、作者履历和作者摘要核对，未通读最终排版全文。|IROS2025:18088–18094、4作者及DOI确认；最初429为访问限流，非DOI无效。|保留；沿路径累计信息评价已有先例；M2/M3应比较完整移动和观测成本，不能只评价终点。|不声称已实现该路径规划对照；具体算法和增益需另读／复现。|https://infoscience.epfl.ch/entities/publication/3a6f868c-8d68-4aaa-937e-900941d3c694 ; https://disalw3.epfl.ch/people/alcherio/files/AM_full_CV.pdf|
|7|Ojeda P, Monroy J, Gonzalez-Jimenez J. Gaden-RT: A real time and interactive gas dispersion simulator for mobile robotics. SoftwareX, 2025, 32: 102388. DOI: 10.1016/j.softx.2025.102388|L1+L2+L4（项目说明）；出版方元数据、作者README和Changelog已读；最终期刊全文直取403，未全文阅读。|SoftwareX32:102388、2025与DOI一致；GPU能力只据官方文档限定到可选浓度图计算。|保留；原生物理开发与复核平台来源。|不能将平台引用当作本项目S2资格化或实飞有效性的证据。|https://www.sciencedirect.com/science/article/pii/S2352711025003541 ; https://github.com/MAPIRlab/gaden|
|8|Gongora A, Monroy J, Rahbar F, Ercolani C, Gonzalez-Jimenez J, Martinoli A. Information-driven gas distribution mapping for autonomous mobile robots. Sensors, 2023, 23(12): 5387. DOI: 10.3390/s23125387|L1；仅Crossref作者、题名、卷期和文章号；未读全文。|Sensors2023,23(12):5387为文章号；6作者及DOI一致。|保留（内容引述待核）；建图与源定位任务的差别；信息驱动采样不是本稿首次引入。|具体信息目标、建图后验及性能尚未核验，正文只作限定性相关工作说明。|https://www.mdpi.com/1424-8220/23/12/5387|
|9|Jin W, Rahbar F, Ercolani C, Martinoli A. Towards efficient gas leak detection in built environments: Data-driven plume modeling for gas sensing robots. In: 2023 IEEE International Conference on Robotics and Automation. IEEE, 2023: 7749–7755. DOI: 10.1109/ICRA48891.2023.10160816|L1+L2；Crossref及EPFL作者项目目录核验；未读全文。|ICRA2023:7749–7755及DOI一致；作者顺序采用出版方登记Jin–Rahbar–Ercolani–Martinoli。|保留（内容引述待核）；数据驱动传播模型用于结构化环境GSL已有先例，帮助界定源条件模型来源。|作者履历个别条目顺序与出版方登记不同；以原论文首页／出版方为准。模型训练和测试划分待核。|https://www.epfl.ch/labs/disal/research/gassensingstructure/ ; https://doi.org/10.1109/ICRA48891.2023.10160816|
|10|Hassan S, Wang L, Mahmud K R. Robotic odor source localization via vision and olfaction fusion navigation algorithm. Sensors, 2024, 24(7): 2309. DOI: 10.3390/s24072309|L1；只核Crossref身份，未全文阅读。|Sensors2024,24(7):2309及DOI一致。|删除／移入候选文献库；本稿没有视觉输入或视觉—嗅觉融合模块，删除是范围取舍，非否认论文有效性。|如未来加入视觉语义辅助定位，应重新阅读全文并恢复引用。|https://www.mdpi.com/1424-8220/24/7/2309|
|11|Fukui C, Uchida T, Koizumi S, Murayama Y, Liu H, Nakata T, Terutsuki D. Advanced bio-hybrid drone for superior odor-source localization: High-precision and extended-range detection capabilities. npj Robotics, 2025, 3: 4. DOI: 10.1038/s44182-025-00020-9|L1；只核Crossref正式身份，未读方法和实验。|npj Robotics2025,3,文章号4，Crossref文章号与原稿一致；DOI一致。|保留（背景限定）；说明无人机嗅觉感知已有实体研究；不能据此声称本文传感器实现已完成。|设备响应、有效范围和定位精度未核；仅题名背景引用不承载性能数字。|https://www.nature.com/articles/s44182-025-00020-9|
|12|Sloman S J, Bharti A, Martinelli J, Kaski S. Bayesian active learning in the presence of nuisance parameters. In: Proceedings of the Fortieth Conference on Uncertainty in Artificial Intelligence. PMLR, 2024, 244: 3245–3263.|L0；原稿转录；本轮未查PMLR页面、未读全文。|未提供DOI不代表论文无DOI；UAI卷244和页码3245–3263未独立核。|删除／移入候选文献库；当前V8方法没有逐式采用该文的干扰参数主动学习算法；避免作为泛化装饰性引用。|如讨论干扰参数主动学习并保留该文，需核PMLR正式条目和具体理论前提。|本轮没有新增一级来源|
|13|Huan X, Jagalur J, Marzouk Y M. Optimal experimental design: Formulations and computations. Acta Numerica, 2024, 33: 715–840. DOI: 10.1017/S0962492924000023|L0；原稿和Crossref429错误记录；本轮未新增全文或出版方读取。|DOI10.1017/S0962492924000023当前未独立核，不因429判无效。|保留（正式引述前待补核）；普通贝叶斯实验设计／EIG对照的背景，可连接M2/M3与已有主动设计。|作者全名、2024年33:715–840及所引结论均待出版方确认。|https://doi.org/10.1017/S0962492924000023|
|14|Welch B M, Horel J D, Sauer J A. Application of the NCAR FastEddy microscale model to a lake breeze front. Atmosphere, 2024, 15(7): 809. DOI: 10.3390/atmos15070809|L1+L3；MDPI出版方正文已获取并阅读摘要、模型设置及背景；Crossref补核成功。|2024年15(7):809与DOI确认，FastEddy注册商标可在书目按排版需要处理。|保留（场景动机）；湖风锋和建筑湍流耦合说明目标场景需要局地风与热边界条件验证。|不验证枫树岭S2；不能将大盐湖一次事件外推为本文所有DAY/NIGHT条件。|https://www.mdpi.com/2073-4433/15/7/809|
|15|Norzam W A S, Hawari H F, Kamarudin K, Juffry Z H M, Hussein N A A, Gupta M, Abdullah A N. Mobile robot gas source localization using SLAM-GDM with a graphene-based gas sensor. Electronics, 2023, 12(1): 171. DOI: 10.3390/electronics12010171|L1；Crossref身份核验；未读全文。|Crossref在线日期为2022-12-30，而卷12期1对应原稿2023年；不能仅凭上线日强改卷期年，最终引用以出版方卷期页为准。|删除／移入候选文献库；本文未采用石墨烯传感器或SLAM-GDM实现，硬件支线不作为三创新依据。|若未来恢复引用，需核2023卷期著录与具体硬件动态，不声称年错误已定。|https://www.mdpi.com/2079-9292/12/1/171|
|16|Andreou M, Chen N, Bollt E. Assimilative causal inference. Nature Communications, 2026, 17: 1854. DOI: 10.1038/s41467-026-68568-0|L0；原稿转录及Crossref429；未读正文。|2026年Nature Communications17:1854及DOI本轮未核；429不证明不真实。|删除；旧题名“因果推断”的支撑文献；V8未建立独立因果识别创新，不以因果标签包装源概率推断。|此删除属于题目和方法归属变化，不对该论文内容或真实性下结论。|https://doi.org/10.1038/s41467-026-68568-0|
|17|何丽, 杜洋鋆, 李知远, 冉腾, 肖文东, 姚佳程. 移动机器人主动嗅觉气源定位方法研究综述. 计算机工程与应用, 2025, 61(10): 36–49.|L2（作者摘要；出版社待核）；授权数据库作者摘要、CNKI记录及其他期刊正式引文页交叉核；未通读全文。|第二作者应为杜洋鋆。候选DOI10.3778/j.issn.1002-8331.2410-0128未获主站核验，安全著录不填DOI。|保留（中文综述）；中文主动嗅觉背景及烟羽发现／跟踪／源确认任务梳理；具体算法证据仍引用原研究。|期刊主站503/502、Crossref404不构成DOI无效结论；完整终版和DOI印刷待核。|https://cea.ceaj.org/CN/10.3778/j.issn.1002-8331.2410-0128 ; https://openurl.ebsco.com/fulltext/gcd%3A185509730?crl=f&id=ebsco%3Agcd%3A185509730&jrnl=10028331&sid=ebsco%3Aplink%3Acrawler-gcd|
|18|李世钰, 袁杰, 谢霖伟, 郭旭, 张宁宁. 局部风信息启发的AVW-PPO室内气源定位算法. 哈尔滨工业大学学报, 2025, 57(8): 57–68.|L0；原稿转录；未检索出版方，未读全文。|未提供DOI；作者、2025年57(8):57–68均待正式条目确认。|删除／移入待核候选库；V8不采用PPO训练；压缩与当前三机制没有直接运算关系的强化学习支线。|不能用未核条目评价PPO或所有主动搜索方法的不足。|本轮没有新增一级来源|
|19|许顺, 黄宇鼎, 范靖, 汤达恒, 吕游. 三维环境中无人机气味源定位研究. 电子测量与仪器学报, 2025, 39(7): 236–246. DOI: 10.13382/j.jemi.B2508218|L0；原稿与Crossref429；未读全文。|DOI10.13382/j.jemi.B2508218尚未核；429仅为限流。|移出正文／保留待核候选；题目与UAV定位直接相关，值得后续补读；本轮缺一级身份和算法内容核验，暂不承担方法论据。|作者、39(7):236–246和三维定位方式待期刊原文核对。|https://doi.org/10.13382/j.jemi.B2508218|
|20|张学锋, 唐晶晶, 江军, 陈迪. 大中型化工装置区多无人机查找泄漏源仿真研究. 中国安全科学学报, 2026, 36(5): 56–63. DOI: 10.16265/j.cnki.issn1003-3033.2026.05.1091|L0；原稿与Crossref404；未查期刊全文。|Crossref未收录该请求不证明DOI无效；2026年36(5):56–63暂不确认为已核。|删除／移入第二篇候选库；题名指向装置区多机任务；当前第一篇限定两机同步测量，不展开集群管理。范围判断仅据题名。|保留原始著录线索，后续多机论文需查出版社／CNKI原文。|https://doi.org/10.16265/j.cnki.issn1003-3033.2026.05.1091|
|21|史天乐, 李飞, 陈〔原稿稀有字宏raresheng，待核〕, 卢春喜, 王维. 基于CFD模拟的人工神经网络动态溯源模型. 化工进展, 2025, 44(8): 4772–4784. DOI: 10.16085/j.issn.1000-6613.2025-0551|L0；原稿和Crossref429；未读全文。|第三作者原稿使用raresheng稀有字宏，具体字形未核，不能猜字；其余身份及DOI均待核。|删除／移入候选文献库；当前不训练CFD监督的ANN动态溯源网络；避免由预测网络背景转移论文重点。范围判断据题名。|如恢复引用，应先读原首页核作者字形、页码和预测／反演任务。|https://doi.org/10.16085/j.issn.1000-6613.2025-0551|
|22|陈增强, 齐聪聪, 赵怡雯, 程义. 基于多策略改进哈里斯鹰优化算法的危化品泄漏源反演. 上海交通大学学报, 2026, 60(5): 860–870. DOI: 10.16183/j.cnki.jsjtu.2024.452|L0；原稿和Crossref429；未读全文。|不能仅凭DOI含2024就否定原稿2026卷期年；正式刊期与早期年份关系待核。|删除／移入候选文献库；V8没有哈里斯鹰优化模块，题名所示启发式反演不构成本稿三机制直接来源。|60(5):860–870、作者及DOI待出版方确认；未做算法优劣判断。|https://doi.org/10.16183/j.cnki.jsjtu.2024.452|
|23|江逸远, 谷小婧, 顾幸生. 基于红外视频的VOCs泄漏源定位与气羽实例分割. 华东理工大学学报(自然科学版), 2024, 50(5): 695–707. DOI: 10.14135/j.cnki.1006-3080.20231011002|L0+L2（页面线索）；原稿与Crossref429；检索曾出现该期刊官方页面，但未读该文方法或通篇核验。|已有官方URL线索；本轮未完整核对2024年50(5):695–707及原作者著录。|删除／移入未来任务候选库；红外视频和气羽实例分割与当前二维源概率输出不同，不加入未经验证的完整羽流重建主张。|未检验红外方法具体贡献，不以题名范围判断代替全文评价。|https://journal.ecust.edu.cn/en/article/doi/10.14135/j.cnki.1006-3080.20231011002|
|24|李鹏, 单钰强. 基于协方差拟合的离格气体泄漏源定位方法. 电子器件, 2023, 46(2): 478–484. DOI: 10.3969/j.issn.1005-9490.2023.02.028|L0；原稿与Crossref429；未读全文。|作者、2023年46(2):478–484与DOI待核；不因429判无效。|删除／移入候选文献库；本文未采用协方差拟合和离格阵列反演；删除是篇幅与运算接口的取舍。|若讨论固定阵列反演，需补查原文和阵列假设。|https://doi.org/10.3969/j.issn.1005-9490.2023.02.028|
|25|王蕊, 吴玲玲, 李淑娟, 张欢, 徐智霞. 基于无线传感网络的重气泄漏监测与定位. 火箭军工程大学学报, 2025, 39(2): 70–78. DOI: 10.20189/j.cnki.CN/61-1527/E.202502008|L0；原稿与Crossref404；未读全文。|Crossref404不等于DOI无效；带斜线刊号的DOI原样保留用于后续核对。|删除／移入候选文献库；无线固定传感网络和重气扩散不是本稿当前同步UAV测量与已资格化模型。范围判断据题名。|作者、39(2):70–78、重气模型假设待原文确认。|https://doi.org/10.20189/j.cnki.CN/61-1527/E.202502008|
|26|陈泽众, 姚逸卿, 阳媛, 鲍琳欣. 基于时间加权最大似然估计的室内气体源定位方法. 仪器仪表学报, 2025, 46(2): 92–102.|L0；原稿转录；未查出版社、未读全文。|未提供DOI不等于无DOI；2025年46(2):92–102及作者待核。|移出正文／保留待核候选；时间加权似然与历史观测相关，但尚未读原算法，不能将其作为已明确超越的对照。|后续若比较历史加权，应补读其似然、时间权重和观测假设。|本轮没有新增一级来源|
|27|董红召, 金灿, 唐伟, 佘翊妮, 林盈盈. 基于遗传-模式搜索算法的微尺度管控区域大气污染物PM$_{2.5}$溯源. 浙江大学学报(工学版), 2024, 58(6): 1296–1304. DOI: 10.3785/j.issn.1008-973X.2024.06.019|L0；原稿与Crossref429；未读全文。|2024年58(6):1296–1304及DOI待核；不把429标为无效。|删除／移入候选文献库；PM2.5区域污染物溯源与局地气体泄漏源辨识的对象及模型不同，当前无直接算法继承。|删除不评价遗传—模式搜索性能，也不声称已全文审阅。|https://doi.org/10.3785/j.issn.1008-973X.2024.06.019|
|28|Wang S, Sun S, Liu M, Gao B, Wang Y, Lin F. Resource-aware probability-based collaborative odor source localization using multiple UAVs. China Communications, 2025, 22(12): 269–280. DOI: 10.23919/JCC.ja.2023-0208|L1；Crossref身份、题名、卷期页码核验；未读方法全文。|22(12):269–280、2025及DOI一致。登记given/family疑似按中文姓名顺序拆分，不据此自动倒换原稿作者。|保留（多机背景限定）；资源感知的概率多UAV协作已有先例，双机设备数本身不能成为本文创新。|具体作者标准罗马字顺序待原首页；资源定义、协作机制和与两机编队差别待阅读全文。|https://doi.org/10.23919/JCC.ja.2023-0208|
|29|Pearl J. Causality: Models, Reasoning, and Inference. 2nd ed. Cambridge: Cambridge University Press, 2009.|L0；本轮仅转录原稿，未新增核出版方版本页。|第二版2009著录待正式书目核对；不凭一般熟悉程度冒充本轮核验。|删除；不再以候选源因果识别为论文主线，也未使用do算子／因果识别定理，无须保留因果教材作为装饰性基础。|删除只反映V8不采用该理论，非否定因果推断方法。|本轮没有新增一级来源|
|30|Jeffreys H. Theory of Probability. 3rd ed. Oxford: Clarendon Press, 1961.|L0；原稿转录，未查出版社或阅读全文。|1961第三版、Clarendon Press本轮未核。|删除；本稿不展开概率哲学或Jeffreys先验；用具体后验、模型与审计原始论文支撑方法。|若后续确实采用Jeffreys先验，应查对应章节再引用。|本轮没有新增一级来源|
|31|Shannon C E. A mathematical theory of communication. Bell System Technical Journal, 1948, 27(3): 379–423.|L0；Shannon原稿著录未重新核；新替代教材已查Wiley出版社，见本表附录。|原稿379–423是第一部分的范围线索；若泛指全部论文需另核分期范围，不凭记忆补页。|替换为Cover与Thomas二版；V8所需是确定性编码的数据处理不等式，使用直接讨论DPI的教材章节更贴近论据。|替换不表示Shannon论文错误；仅调整论据与引用对应。|本轮没有新增一级来源|
|32|Vergassola M, Villermaux E, Shraiman B I. ``Infotaxis'' as a strategy for searching without gradients. Nature, 2007, 445(7126): 406–409. DOI: 10.1038/nature05464|L2；Nature官方摘要及元数据已核；未逐页读原文。|2007年445:406–409、DOI一致；原稿7126期号本次未单独查证，可省略期号。|保留；信息导向气源搜索的经典对照，承认熵下降选点已有来源。|如复现infotaxis应进一步核观测模型和动作成本，不只引用标题。|https://www.nature.com/articles/nature05464|
|33|Thrun S, Burgard W, Fox D. Probabilistic Robotics. Cambridge, MA: MIT Press, 2005.|L0；原稿转录；本轮未查MIT Press页面。|2005年MIT Press与作者本轮未独立核。|删除／备选教材；研究稿已有后验公式定义和直接PMFS来源，暂不保留未对应具体定理的通用机器人教材。|如正文引用标准递归贝叶斯滤波定理，可补查版本和章节后恢复。|本轮没有新增一级来源|
|34|Brier G W. Verification of forecasts expressed in terms of probability. Monthly Weather Review, 1950, 78(1): 1–3.|L0；原稿转录；未查AMS原始出版页。|1950年78(1):1–3的著录本轮未独立核；不自造DOI。|保留（指标来源待补核）；若实验方案采用Brier评分，应保留其原始来源而非把该指标称为本文提出。|正式定稿前补核原始出版页；多分类Brier所用归一化也须在正文明确。|本轮没有新增一级来源|
|35|Metzner P, Schütte C, Vanden-Eijnden E. Transition path theory for Markov jump processes. Multiscale Modeling & Simulation, 2009, 7(3): 1192–1219. DOI: 10.1137/070699500|L0；原稿与Crossref429；未阅读全文。|2009年7(3):1192–1219及DOI待核；429不代表无效。|删除；旧PIP／传播路径方案的理论背景；V8不实现转移路径理论，不应继续暗示该理论支持M3审计。|删除依据当前算法无继承关系，不能写成已读全文后的否定评价。|https://doi.org/10.1137/070699500|

## 编辑优先事项

1. 旧编号3（PMFS）是核心原始方法，必须保留并据真实计算链改写动机；其已有历史累积和主动方差选点。
2. 旧编号5、6支撑连续采样与路径信息的先行研究；已有这些工作，不能把“考虑历史”“运动中测量”“累计路径信息”笼统列为本文原创。
3. 旧编号16、29和35随旧“因果推断”、PIP理论归属退出正文；删除原因是本文没有采用其识别／路径理论，而非论文不成立。
4. 旧编号14可支撑湖风环境动机；不构成枫树岭S2已经完成物理验证的证据。
5. 旧编号17作者“杜洋鋆”已纠正；旧编号21的稀有字宏未实际核明，不得猜字。旧编号28登记姓名字段可能存在次序问题，不能自动倒置作者。
6. 尚未取得一级身份或正文依据的保留项，应在最终投稿前补核；研究稿审计表应明确保留其“待核”状态，不能将35条完整列出说成35篇全文全部读完。

## 附录：Cover与Thomas《Elements of Information Theory》二版及DPI

### 出版方核验

Thomas M. Cover; Joy A. Thomas. *Elements of Information Theory*, 2nd edition. John Wiley & Sons, 2006. 纸本ISBN：978-0-471-24195-9；电子ISBN：978-0-471-74882-3；整书DOI：10.1002/047174882X。

一级来源：

- [Wiley纸本产品目录](https://www.wiley.com/en-hk/Elements%2Bof%2BInformation%2BTheory%2C%2B2nd%2BEdition-p-9780471241959)：搜索索引显示第二版、两作者、ISBN、June2006及784页；直接打开403。
- [Wiley Online Books整书页](https://onlinelibrary.wiley.com/doi/book/10.1002/047174882X)：已实际打开，确认两作者、第二版介绍、纸本／电子ISBN、整书DOI及Copyright2006。
- [Wiley第2章官方页](https://onlinelibrary.wiley.com/doi/abs/10.1002/047174882X.ch2)：已打开，章名为“Entropy, Relative Entropy, and Mutual Information”，目录包含“Data-Processing Inequality”和“Sufficient Statistics”；整书目录列本章页码13–55。未取得付费章节全文，不声称本轮逐页读完教材证明。

**日期差异：**Wiley在线书及章节登记显示“First published:7 April2005”，纸本目录与版权为2006。本文采用通常的第二版纸本2006著录，记录线上元数据差异，不把其中一个日期悄悄覆盖另一个。建议BibTeX见 `cover_thomas_2006.bib`。

### 在本文中的一般理论依据与条件

数据处理不等式讨论在给定条件下的马尔可夫链：若 (S	o Y	o Z)，则 (I(S;Z)le I(S;Y))。对M1，更明确地固定训练资料、已选动作与过往历史为 (C)，并令 (Z=T_	heta(Y;C))，则

[
I(S;Ymid C)=I(S;Y,Zmid C)
=I(S;Zmid C)+I(S;Ymid Z,C)ge I(S;Zmid C).
]

这是本文对一般DPI的直接应用／简短推导，不是PNAS母论文的气源定位性能结论。等号对应给定条件下保留了与源有关的充分信息。训练资料和模型先验不应被省略后再宣称编码凭空创造源信息。

其适当科研表述是：确定性镜像特征可能改善有限模型和有限样本下的估计稳定性、参数效率或抗噪表现；不能超过完整原始观测中包含的真实信息量。M2改变未来测量位置及真实观测分布，可改变后续可获取信息。此信息论边界也不证明M1一定优于或一定劣于某个有限参数raw-joint估计器；相应性能仍需公平实验。

## 机器可读文件

同名CSV包含35行，另保留原稿出现顺序、原始LaTeX著录、原始Crossref状态与错误、独立元数据身份及本轮核验日期。CSV采用UTF-8 BOM，便于中文表格软件读取。逐行编号覆盖1–35，无遗漏、无重复。
