# V8 保留背景文献六项补核

核验日期：2026-10-23。书目内容已写入 `background_refs.bib`；Crossref 出版方登记元数据保留在 `background_crossref.json`。下面严格区分可取得的正文、作者摘要、身份元数据和未完成核验。

## 1. Jin 等，IROS 2025：累计信息路径规划

**完整信息：**Wanting Jin, Hugo Leroy, Nicolaj Bösel-Schmid, Alcherio Martinoli. Cumulative Informative Path Planning for Efficient Gas Source Localization with Mobile Robots. *2025 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, pp.18088–18094. DOI:10.1109/IROS60139.2025.11246224。

**一级来源：**[EPFL 文献条目](https://infoscience.epfl.ch/entities/publication/3a6f868c-8d68-4aaa-937e-900941d3c694)；[作者团队项目页](https://www.epfl.ch/labs/disal/research/gassensingstructure/)；[作者正式履历第27页](https://disalw3.epfl.ch/people/alcherio/files/AM_full_CV.pdf)。Crossref 登记作者、题名、页码、DOI 与作者履历一致；EPFL 主页直接访问受到限流，搜索索引有作者摘要。作者本人上传的全文亦可在其 ResearchGate 记录读取，未将平台推荐文献摘要混入本文内容。

**正文角色：**“沿运动路径累计评价信息的主动规划已经用于气源定位；移动时间、采样等待和沿途观测应一并计入比较。”可用于动机与公平预算设计，不能宣称本研究首次利用完整路径信息。不要把该方法简化为仅在终点计算一次信息增益。

**限度：**未做其算法运行复现，不引用其性能数字作为本方法证据。

## 2. Jin 与 Martinoli，ICRA 2024：运动中感知与信念聚类

**完整信息：**Wanting Jin, Alcherio Martinoli. Sense in Motion with Belief Clustering: Efficient Gas Source Localization with Mobile Robots. *2024 IEEE International Conference on Robotics and Automation (ICRA)*, pp.14909–14916. DOI:10.1109/ICRA57147.2024.10611440。

**一级来源：**[EPFL 正式条目](https://infoscience.epfl.ch/entities/publication/22992bbb-65c6-4b2c-a983-17f4050d44f2)；[作者稿 PDF 地址](https://infoscience.epfl.ch/bitstreams/2abb588a-b524-4612-bc8d-22f5fa9a1434/download)；[机构摘要镜像](https://graphsearch.epfl.ch/en/publication/22992bbb-65c6-4b2c-a983-17f4050d44f2)。作者履历和 Crossref 双重核对书目；已读作者摘要与方法节可检索内容。PDF 直取限流，未声称通读每页。

**正文角色：**该工作区分羽流动态和传感器动态，研究连续采样与基于信念聚类的路径规划。可支持“传感器迟滞和采样制度会改变定位效率，不能只把传感器数量视为算法优势”。连续运动采样及利用沿途历史均已有先例，M1 的新意应限定在源条件判别表示。

## 3. Lin 等，IEEE Sensors Journal：双侧浓度与趋向行为

**修正后的完整信息：**Qin Lin, Shuo Wu, Hui Wang, Ke Ma, Lelun Jiang, Jinxiu Zhang. Incorporating Animal Klinotaxis Behavior and Bilateral Concentration Information: A 3-D Bio-Inspired Odor Source Localization Algorithm and Its Performance Evaluation. *IEEE Sensors Journal*, **25(1):697–708,2025**. DOI:10.1109/JSEN.2024.3407982。

**一级来源：**[IEEE 文章10551708](https://ieeexplore.ieee.org/document/10551708/)；[IEEE PDF](https://ieeexplore.ieee.org/iel8/7361/10823640/10551708.pdf)；出版方登记的 [Crossref 元数据](https://api.crossref.org/works/10.1109%2FJSEN.2024.3407982)。IEEE 搜索索引可读取摘要／正文片段；直接 PDF 请求418，页面有自动访问校验。Crossref 完整记录保存于本目录。

**必须修改：**原先“Bilateral2024”若使用早期在线年份，不能与最终卷期混写。最终卷期为2025；DOI 的2024字段不等于正式卷期年份。

**正文角色：**“双侧浓度信息与动物趋向行为已用于三维气味源搜索。”该研究采用双侧传感器及风信息，构成直接先行工作。不要宣称首次双侧嗅觉定位，不要把其趋向搜索的成功率当作竞争源联合后验或双机判别编队的证据。

## 4. 何丽等，2025 中文综述

**可确认基本身份：**何丽，**杜洋鋆**，李知远，冉腾，肖文东，姚佳程．移动机器人主动嗅觉气源定位方法研究综述．*计算机工程与应用*，2025，61(10):36–49。

**读取证据：**原作者摘要在[授权数据库记录](https://openurl.ebsco.com/fulltext/gcd%3A185509730?crl=f&id=ebsco%3Agcd%3A185509730&jrnl=10028331&sid=ebsco%3Aplink%3Acrawler-gcd)可读；CNKI 期刊记录和其他期刊官方引文页一致列出作者与页码。候选 DOI 为10.3778/j.issn.1002-8331.2410-0128，但[期刊主站地址](https://cea.ceaj.org/CN/10.3778/j.issn.1002-8331.2410-0128)本次503／502，Crossref404。**这不证明 DOI 错误，也不构成出版方已核验；安全 BibTeX 保留无 DOI 的原有期刊著录。**

**正文角色：**作者摘要按烟羽发现、烟羽跟踪和气源确认梳理主动嗅觉研究；可作为中文领域综述引用。不能将尚未通读的全文评价冒充逐页分析。该综述本身是二次文献，因此具体算法和性能论据仍引用相应原始研究。

**排版：**第二作者姓名应保留“鋆”；若正文字体不含此字，应使用原工程的局部字体回退，不能改成“君”。

## 5. Welch 等，FastEddy 湖风锋

**完整信息：**Brittany M. Welch, John D. Horel, Jeremy A. Sauer. Application of the NCAR FastEddy® Microscale Model to a Lake Breeze Front. *Atmosphere*,15(7),809,2024. DOI:10.3390/atmos15070809。2024-07-06发表。

**一级来源：**[MDPI 正文](https://www.mdpi.com/2073-4433/15/7/809)；[FastEddy 官方文献目录](https://fasteddy-model.readthedocs.io/en/latest/publications.html)。已通过公开访问保存出版方 HTML 并读取摘要和正文设置，另用 Crossref 核对。原 HTML 及纯文本位于 `background_sources/fasteddy.html` 与 `fasteddy_text.txt`。

**正文角色：**湖风锋与建筑诱导湍流的相互作用说明湖岸局地风不能简单视为恒定二维风。该文以大盐湖附近城市的实际一次湖风锋事件验证 WRF–FastEddy 模拟；可用来论证目标场景需要分辨局地风场和明确热边界条件。

**不可外推：**它不是气源定位论文，不验证枫树岭 S2，不为本项目的 DAY/NIGHT 热力场提供实证资格，也不支持由某一次湖风事件断言所有湖岸场景必定发生相同风反转。

## 6. Huang 与 Donaldson，Lake Ontario 岸线臭氧梯度

**完整信息：**Yao Yan Huang, D. James Donaldson. Measurement report: Observations of ground-level ozone concentration gradients perpendicular to the Lake Ontario shoreline. *Atmospheric Chemistry and Physics*,24(4):2387–2398,2024. DOI:10.5194/acp-24-2387-2024。2024-02-26发表。

**一级来源：**[Copernicus 全文与正式引用](https://acp.copernicus.org/articles/24/2387/2024/acp-24-2387-2024.html)。已读摘要、现场采样设置、湖岸机制讨论和正式书目。两作者的全名和题名前缀“Measurement report:”应保留。

**正文角色：**真实湖岸气体浓度具有空间梯度，受季节和局地地表环境影响；可以说明湖岸应用场景需要环境条件验证。

**不可外推：**研究对象为具有化学生成、沉降等机制的背景臭氧，不是单个危险气体泄漏源的被动示踪羽流。不能用其岸线梯度符号直接规定本文气源方向，也不能用它证明危险气体存在普适单调梯度。它不构成本项目湖岸定位或短时态势重建的验证。

## 可直接用于 V8 的紧凑关联段落

已有研究从连续运动采样和信念聚类出发改进源项估计，并进一步将信息评价扩展到完整采样路径，说明传感器动态、移动过程和样本获取制度必须纳入定位算法的比较。双侧浓度信息与动物趋向行为也已用于三维气味源搜索，因此增加第二个传感器或双侧观测本身不构成本研究的贡献。本研究关注的是：在相同双点读出与资源预算下，如何形成可校准的竞争源证据，并通过后续测量位置持续检验当前源假设。湖风锋和岸线臭氧观测提供目标场景的环境动机，House 开发数据与湖岸物理验证仍需分别陈述。

