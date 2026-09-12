# 2026 地球物理跨域思想核验：源与介质能否分别识别

核验日期：2026-09-12。仅检索文献和读取本地状态文档；未读取 bank payload、访问 VM 或运行 forward/闭环。现有问题以 `docs/M1R_CAUSAL_IMPLEMENTATION_STATUS_20260912.md` 为准：当前候选 hit 响应存在别名，真源证据不足，局部风工具变量条件未建立。完整时序 provider 加 FOPDT 已有 H01 失败记录，不能再把“增加时序物理”写成未试过的新突破。

**结论：找到两篇正式发表的 2026 年高水平地球物理论文，但没有找到一篇能在当前单 UAV 信息条件下直接建立 PMFS 因果源识别保证。** HARPA 提供较有价值的条件性启发；几何相位论文更适合作为源—介质混淆的反例约束。以下将论文事实与迁移判断分开。

## 1. 年份、出处和旧用史

| 论文 | 正式出处与日期 | 核验入口 |
|---|---|---|
| Cheng Shi et al., *High-rate phase association with travel time neural fields*（HARPA） | Nature Communications **17, 8140 (2026)**；2026-06-30 published；2026-08-11 version of record；2026-05-27 accepted | [期刊正式全文及 About this article](https://www.nature.com/articles/s41467-026-74092-y) |
| Bingxu Luo et al., *Geometric phase sensing using seismic waves for comprehensive volcano monitoring at Kīlauea Hawaii* | Nature Communications **17, 7988 (2026)**；2026-06-26 published；2026-08-07 version of record；2026-05-26 accepted | [期刊正式全文及 About this article](https://www.nature.com/articles/s41467-026-73998-x)、[PMC 作者论文全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC13448816/) |

两篇都属于 Nature Communications，不能写成 Nature 主刊论文。没有把 received 年份、2025 年前作或 2026 预印本当作 2026 正式发表成果。以完整 DOI、HARPA、题名固定字符串检索本仓库 `docs/`、`tools/`、`evidence/` 中的 `.md/.py`，在本报告创建前无命中；这只是“未检出此前引用”，不是对全仓库思想原创性的证明。

## 2. HARPA：共同介质下多源多位置的传播约束

**论文事实。** 原文 Methods 式 (1) 为 `t_ij=T_c(s_j;r_i)+tau_j`：多台站记录同一地震源的到时。式 (8) 对各站 P/S 到时分布做 Wasserstein 匹配；式 (10) 用共同低维 latent code `z` 表示两种波速，与源位置/发震时刻联合估计。神经 travel-time field 用数值求解产生的时刻监督训练，不是识别定理。Discussion 明确：该方法没有解决一般的联合唯一性理论，几何一致的虚假事件仍可能需要更密集仪器或波形证据排除。[原文 Methods 与 Discussion](https://www.nature.com/articles/s41467-026-74092-y)

**真正新增的约束是什么——以下为迁移分析。** 有效信息来自多个接收位置对同一隐含事件的共同发震时刻，以及跨事件共用的受限介质。对于已关联事件，两站时间差可消去共同发震时刻，但保留随源位置变化的传播时间差。多源、多站和多波型共同限制介质自由度；优化器和 Wasserstein 距离不会使相同观测分布自动变得可分。

**单 UAV 对应关系与缺口。** UAV 位姿可以对应接收位置，浓度瞬变可以尝试对应到达事件，地图/合法局部风可以约束介质；但连续释放的湍流气体没有自动提供“同一可关联发射事件在各站的到时”。单机先后到不同位置，不等于多个台站同时观测同一波源。浓度与局部风也不是 P/S 两种带共同源时刻的传播相位。若把每个片段的背景/迟滞任意调成各自最优值，会让错误源被介质参数补偿，反而扩张别名集合。

**可保留的思想。** 将所有既有位置和时段绑定到一套受合法风/地图约束的环境状态，让候选源必须同时解释多个位置的关系。要成为新主创新，必须证明这些跨位置关系在当前数据里提供了此前 provider 没有的、错误源无法由环境失配补偿的信息。没有这个证据，联合拟合源与环境只是更大的生成式反演；不能称为新的因果识别。

**准入判断：条件性理论候选，当前不得直接实现为新因果主模块。** 原文不是为“一台移动传感器、一个持续释放源、未知时变输运”给出的唯一性保证。

## 3. 几何相位：控制源变化，才能把响应变化归给介质

**论文事实。** Methods 式 (1) 把参考站与其他站的 cross-correlation 频谱组成归一化复向量；式 (2) 以参考时段向量的内积角度测量波场变化。Table 1 固定介质：只扰动弱背景源时，相位约 `0.022±0.003 rad`；全面重排源时约 `1.571±0.024 rad`。作者明确承认喷发期源与介质耦合，无法严格分开贡献；该量用于整体时序跟踪，不提供明确的空间反演。[原文 Methods、Table 1 与 Discussion](https://www.nature.com/articles/s41467-026-73998-x)

**真正成立的条件——以下为迁移分析。** 归一化可以去掉共同幅度缩放，却不会消掉源空间重排；稳定主源、受限背景扰动和独立介质观测才使“响应变化来自介质”具有支持。它并没有从完全别名的源中恢复源身份。此论文研究的是介质变化，PMFS 要求的是源位置，二者的目标方向不同。

**单 UAV 对应关系与缺口。** 本机的浓度、风、位姿和时间都是合法输入，但无法直接构造多站同时观测形成的互相关网络。把不同时间片段当成不同站会混合传播变化和源/传感变化；在未建立重复性或平稳性条件前，不等价。将现有 hit 向量归一化、做角距离或称为“拓扑指纹”，也不能分开两个完全相同的候选响应。

**可保留的思想。** 因果主张需要双向对照：固定候选源、改变允许介质时，特征如何变化；固定介质、改变候选源时，特征如何变化。两个效应集合若重叠，不能把观测变化唯一归因于源。当前任务没有运行这些对照；这是设计义务，不是新增成功结果。

**准入判断：不选作源定位算法方案；保留为反例与归因约束。** 该论文自身的强源扰动反例，直接反对“归一化后即源/环境不变”的无条件说法。

## 4. 对 PMFS 最小的理论增量

以下是本次比较提出的研究条件，不是两篇论文的定理，也不是已验证方法。

设合法部署输入为 `D={(x_t,c_t,w_t,t,state_t)}`，候选源为 `s`，允许且受独立物理条件约束的环境/传感状态为 `theta∈Theta(D_w,map)`。需要比较的是整个候选响应集合

`R_s={law(c_1:T | x_1:T,s,theta): theta∈Theta(D_w,map)}`，

而非只比较某个最方便的 `theta` 下的两条曲线。若两个源存在允许状态使全部合法输入分布相同，它们仍无法由这些输入分开；任意重权、特征映射、互相关、OT 或神经场不能创造缺失信息。要打破别名，需要已有观测中被旧表示丢弃的独立约束，或合法动作新增的、在允许输运失配下仍有差异的观测。后者还需源稳定性、传感迟滞和行动诱导流场的明示条件，不能拿局部风变异满秩代替。

H01/H02 的当前 hit 别名只说明现有候选表示不可分，不说明所有未来观测都不可分；但 H01 时序 provider 的既有失败也禁止将“保留完整时序”直接宣布为已经解决问题。H03 还要求真源位于允许模型族的可解释支持内；仅压缩环境自由度，可能把真源进一步排除。

因此当前最值得保留的地学借鉴是：**共同环境下的跨位置响应必须形成不能相互补偿的约束，而且需用独立信息限制环境。** 若不能具体指出哪个合法输入限制了哪一个补偿自由度，这条线暂时只是问题重述，尚不足以启动新 forward 或主创新实验。

## 5. 检索记录与覆盖边界

使用 paper-search 技能的 2026-only 检索，查询 `geophysical source attribution transport response identifiability`，每源最多 3 篇；并在 Nature/Science 官方域名检索源归因、介质反演、自然实验等词。仅对上面两篇正式论文做深入原文核验。

技能 CLI 与文档不一致，原始报错为：

```text
search_papers.py: error: unrecognized arguments: --json D:/ZYC/CSTAR_M1R_CAUSAL_REPAIR_20260912/evidence/m1r_crossdomain_20260912/GEOSCIENCE_SEARCH_RAW.json
```

改用技能 `references/programmatic_api.md` 中的 `search_papers()` 接口，原始返回保存为 `GEOSCIENCE_SEARCH_RAW.json`。源计数：arxiv=3、dblp=0、open_alex=3、openreview=0、semantic_scholar=0、crossref=3。出现的源错误：

```text
[dblp] Error on query 'geophysical source attribution transport response identifiability': Expecting value: line 1 column 1 (char 0)
[semantic_scholar] Error on query 'geophysical source attribution transport response identifiability': 429 Client Error:  for url: https://api.semanticscholar.org/graph/v1/paper/search?query=geophysical+source+attribution+transport+response+identifiability&offset=0&limit=3&fields=title%2Cauthors%2Cyear%2Cabstract%2CcitationCount%2Curl%2Cvenue%2CpublicationDate%2CexternalIds&year=2026-2026
```

9 条 API 返回中，4 条有摘要但属于微生物/LLM/网络安全，排除；2 条相关但只有预印本身份，不满足正式顶刊顶会要求（城市平流扩散 IASA；浮游生物 onset 条件源归因）；3 条缺摘要，无法判定不相关，保留未深入条目如下。API 因检索覆盖与错误未找到最终两篇；最终两篇来自官方网页补检，不能宣称系统综述穷尽了 2026 文献。

| 未深入返回 | API 出处/日期 | 状态 |
|---|---|---|
| [Inverse S-T Model-Based Abnormal Source Identification for Parabolic DPSs](https://doi.org/10.1007/978-981-95-3750-1_6) | OpenAlex / 2026-01-01 | 无摘要；书章节标识；未认证为顶会顶刊 |
| [A Bayesian Approach with Gaussian Priors to the Inverse Problem of Source Identification in Elliptic PDEs](https://doi.org/10.1007/978-3-031-99009-0_2) | Springer Proceedings in Mathematics & Statistics / 2026-01-01 | 无摘要；未认证为顶会顶刊 |
| [Optimization of LASSO Reconstruction Scheme to Identify Radioactive Sources Based on Monitoring Air Dose Rates](https://doi.org/10.1007/978-981-95-3409-8_4) | Springer Proceedings in Physics / 2026-01-01 | 无摘要；未认证为顶会顶刊 |

Model-knowledge 补充为 0；没有用未核实记忆补足 2026 名额。正式论文总结依据作者原文；PMFS 映射与否决是本报告的推理，未由论文作者背书。
