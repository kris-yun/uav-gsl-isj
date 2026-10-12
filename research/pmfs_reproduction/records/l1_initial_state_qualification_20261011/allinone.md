# L1建模依据检索及使用边界

检索query：`stochastic wind field Bayesian source estimation unknown initial conditions`；年份1980–2026；每API最多2条。API原始命中arXiv=2、Crossref=2，其余=0，合计4条，无重复。阅读可用摘要后，1条风机电网频率调节论文与本问题明确无关，过滤；3条保留为泛统计/领域相邻或待核验记录，不拿它们资格化B4。

未过滤原始JSON（含可用摘要）保存在本地`L1_PAPER_SEARCH_RAW.json`，供恢复检索；公开审核包仅保存元数据及该文件SHA，不再发布整段第三方摘要。脚本CLI与当前SKILL文档不一致，`--json`被拒绝；采用同技能的programmatic API获取结构化结果，没有重复物理实验。

## 全部保留的API记录

| # | 论文 | 日期/期刊 | 引用数 | 来源/本任务相关性 |
|---|---|---|---|---|
| 1 | [Convergent Bayesian formulations of blind source separation and electromagnetic source estimation](https://arxiv.org/abs/1501.05069) | 2015，arXiv；Knuth/Vaughan | 未核验 | arXiv；泛Bayesian源反演，非风/气体物理参数依据 |
| 2 | [Bayesian Source Estimation from Potential Field Data](https://doi.org/10.1007/978-94-017-2217-9_35) | 1993，Maximum Entropy and Bayesian Methods；Pendock | 未核验 | Crossref；没有取得摘要，保留待核验，不当风先验依据 |
| 3 | [Tropical Cyclone Wind Field Reconstruction for Hazard Estimation via Bayesian Hierarchical Modeling with Neural Network](https://doi.org/10.22541/essoar.173160188.86229637/v1) | 检索器日期/期刊缺失；Yang | 未核验 | Crossref；没有取得摘要，气旋尺度也不同，不用于B4校准 |

API的0引用字段不等于真实零引用；不据此做影响力排名。

## Model knowledge补充与一手核验

| 工作 | 核验入口 | 可支持 / 不可支持 |
|---|---|---|
| Thomson，1987，Criteria for the selection of stochastic models of particle trajectories in turbulent flows，JFM | [DOI](https://doi.org/10.1017/S0022112087001940)；[FLEXPART官方文档的引用与方法说明](https://flexpart.img.univie.ac.at/docs/transport.html) | 随机轨迹形式需要物理一致性条件；原DOI本次访问失败，未声称已读全文；不能提供B4 τ/垂向方差 |
| Sherman，1978，A Mass-Consistent Model for Wind Fields over Complex Terrain（检索年份外的基础补充） | [AMS出版页面](https://journals.ametsoc.org/view/journals/apme/17/3/1520-0450_1978_017_0312_amcmfw_2_0_co_2.xml) | 官方检索摘要支持按连续性和边界调整3D风；完整页面403，没有全文重发布；不能校准本任务的未知过去风 |
| Pisso等，2019，The Lagrangian particle dispersion model FLEXPART version10.4 | [GMD官方论文](https://gmd.copernicus.org/articles/12/4955/2019/) | 三维Lagrangian随机输运的模型说明；不能把其大气参数直接搬到室内B4 |
| Scheel等，2026，Dynamic quantification of methane emissions at facility scale using laser tomography | [AMT官方论文](https://amt.copernicus.org/articles/19/2343/2026/) | 复杂风与有限浓度观测下Bayesian反演的相关背景；不是本地单点测风即可识别过去3D场的证据 |
| MAPIRlab GMRF-wind官方实现 | [官方仓库](https://github.com/MAPIRlab/GMRF-wind) | 官方说明是二维风图估计；本研究锁定旧版本保持，未拿当前README替换原核心；不能推出未观测垂向风 |

## 汇总

1. **Overview**：四条API原始记录匹配质量有限，无法由它们识别L1参数。另核验了官方模型文档和论文/出版索引。得到的是模型形式依据，不是B4经验先验。
2. **Trends**：样本量和检索覆盖不足，不做年度趋势/主导会议结论。旧质量一致风场、随机粒子与现代Bayesian反演之间有方法联系，不能据此宣称新颖。
3. **Key themes**：质量/边界一致性（Sherman）；随机传播与适用条件（FLEXPART）；稀疏数据的反演/不确定性（AMT）；局部二维风与全场之间的信息差（GMRF官方范围）。
4. **Keywords frequency**：保留API三标题中Bayesian=3、source=2、field=2、wind=1、hierarchical=1。只是标题词频，无科学权重。
5. **Most cited by accepted paper**：没有经核验引用计数，不编造Top5。
6. **Most cited by first author**：同样不可排名；保留记录的首作者为Knuth、Pendock、Yang。
7. **Reading path**：先核对本地GADEN真实边界/单位，再读质量一致风场与FLEXPART的物理适用条件，最后参考AMT的复杂风反演。泛跨领域Bayesian文章不足以替代本任务初态校准。

HalfNormal(1m/s)、LogUniform(1,267.307s)、24模态空间谱和自由高度均是事前弱假设，不是上述论文给出的B4值。没有独立经验依据时，应保留假设标签与否证门，不从已见定位误差选参数。

## 实际检索错误（原文）

```text
search_papers.py: error: unrecognized arguments: --json outputs/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011/L1_PAPER_SEARCH_RAW.json
[dblp] Error on query 'stochastic wind field Bayesian source estimation unknown initial conditions': Expecting value: line 1 column 1 (char 0)
[open_alex] Error on query 'stochastic wind field Bayesian source estimation unknown initial conditions': 429 Client Error: Too Many Requests
[semantic_scholar] Error on query 'stochastic wind field Bayesian source estimation unknown initial conditions': 429 Client Error
URL https://doi.org/10.1017/S0022112087001940 is not accessible via this tool.
Failed to fetch AMS full page: (403) Forbidden
```

没有绕过这些限制使用不可信镜像，也没有将访问失败说成核验成功。
