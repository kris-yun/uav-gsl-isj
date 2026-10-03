# 公开真实数据优先：资格矩阵与共同机制审计

本轮已完成三条并行审计、公开原件下载与可执行的固定路径基线。正式结论为 **PUBLIC_REAL_CROSS_DATASET_MECHANISM_NOT_ESTABLISHED**：Svalbard支持风表征候选问题，但Mackenzie没有稳健同向复现，Lagoon合同仍未解锁。第一篇主创新暂不冻结为“平均风失效、局地风修复”或任何大理论。没有运行新CFD/GADEN、闭环或多无人机。

协议分支research/lakeshore-observability-r0-r2-20261003，确认已包含17b31989e726b64ac95030a5b3f7dd635578af65。原始协议未改，之前R1/R1A/R1B与Wisco结论未改。

## 数据隔离与原件审计

|数据|C盘独立目录|本轮下载范围|大小|
|---|---|---|---:|
|Lagoon|C:\work\LAGOON_PINGO_REAL_DATA_20261003|原merged/Excel保持原样；补3个processed sensor NC|新增201,131,206bytes；累计已取735,117,279bytes，不包含未下载大影像|
|Mackenzie|C:\work\MACKENZIE_CHANNEL_SEEP2_REAL_DATA_20261003|官方完整唯一ZIP，10个CSV/代码/notebook|29,554,312bytes压缩；解压88,893,067bytes|
|Svalbard|C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003|官方active完整95个tracked原件|115,006,114bytes，其中drone_data86,491,651bytes|

Mackenzie及Lagoon下载逐项核对发布方size/MD5并记录SHA256；Svalbard采用固定Git commit加95个本地SHA，没有虚构官方MD5。克隆或解压空间、processed文件、依赖、报告及ZIP会产生额外本地占用，不等于不同原始数据的科学体积。

完整逐字段资格表见PUBLIC_DATASET_QUALIFICATION_MATRIX.csv，涵盖source truth/type、scene、flight count、gas响应/采样、GPS高度、UAV/ground wind、运动修正/坐标/单位、同步、source-informed路线、重复、定位/plume终点、代码和license。

## 1. 哪些能合法算定位误差

**Svalbard borehole可以**：官方源坐标、原始GPS、CH4、运动修正3D风与8步处理链均公开。实跑得到3126个1s路径记录、2989个气体完整记录、314个10s真实观测。真实field data可直接源反演，不仅能标定synthetic nature run。源坐标精度未独立给出，路线知道源以后设计，高度phase与时间混杂。

官方field calibration把源固定原点，且依赖未公开模块；不能说原版粒子滤波已完整复现。本轮执行相同published mirror forward/log likelihood的**条件风Bayesian网格STE**，真源只在posterior保存后读入评分。官方direction与后续forward结合会反转east分量，保留as-written诊断，主风比较用ENU一致向量，不把代码框架问题当真实大气失效。

**Mackenzie也有条件评分资格**：4个CP/OP真实curtain文件有接收点坐标、CH4和修正水平风，独立源参考点用于评分。原作者GPI是已知源通量拟合，不是未知源位置反演。本轮先复核作者坐标、gas与forward，再建立仅用接收位置/观测风决定域的未知源网格。

但正式 **MACKENZIE_GO_REAL_POINT_SOURCE 未通过**：源距离与sigma=tau*x互相补偿，近远联合依赖相同Q/扩散假设，扩散支持一变MAP及排序明显变；部分源贴域边界。当前为MACKENZIE_HOLD_SOURCE_INVERSION_NOT_ROBUST。误差数字是条件模型诊断，不是已经可靠解开的现场GSL benchmark。

两套Mackenzie UAV主要都是二维水平风，不能宣传为两套3D运动修正风。OP传感器名义100Hz但公开CSV约10Hz。论文的1.5m/2.7m地面风并没有附原始时间序列，ground-only不能跑。CP2时间截为mm:ss，上游lag合同未完整公开；不做跨平台传播滞后。

两个点源数据集均是source-informed路线，能评估固定移动观测反演，不能评价未知源自主搜索成功率，也不能把同一场地的不同高度/平台算多个独立数据集。

## 2. 哪些只能做plume/transport或源区验证

Lagoon有13个未标号merged行、94个变量和Excel7个独立flux/evasion坐标，但不构成唯一点源真值，当前不能算点源定位误差。补传感器NC后Aeris=6、flightrecords=27、Trisonica=13，仍没有权威映射，不能按ordinal配对。flight与flight_frec、单位/坐标/运动修正、时钟/lag缺项仍在，保持REAL_LAGOON_HOLD_METADATA_CONTRACT。

解锁后Lagoon可考虑源区一致性、沿轨迹plume/transport外部验证；当前连这些机制性终点也未运行，Stage C/D保持关闭。Excel并非全部同期观测，不能用分布通量点代替唯一气体源。

Mackenzie与Svalbard也能评价观测路径上的浓度支持、中心线/近远一致性，但没有完整体积羽流真值，不能给未经定义的全3D plume IoU。

## 3. 风表征比较的实际结果

|数据/观测|mean wind误差m|current local误差m|解释|
|---|---:|---:|---|
|Svalbard 2m phase|62.95|7.87|条件STE明显改善，单site/date|
|Svalbard 4m phase|17.01|6.47|同一数据集另一phase，不能算第二数据集|
|Svalbard全部phase|11.51|6.47|合并模型，Q及非稳态假设需保留|
|Mackenzie CP近远联合，主配置|5.08|42.60|local未改善；mean点虽近，但支持域northing跨度约155m|
|Mackenzie OP近远联合，主配置|16.71|56.73|local贴源域边界|
|Mackenzie CP，扩大扩散支持|55.52|42.60|mean变差且贴边；排序反转|
|Mackenzie OP，扩大扩散支持|44.21|56.73|local仍贴边，未稳定改善|

Svalbard背景2.05/2.09/2.13ppm主MAP不变；log sigma0.30时4m local8.15m，其余主结果不变。6m接近背景，local Q_MAP=0，95%模型条件后验面积约69006m²，应判不可辨识，不用于优劣统计。模型后验覆盖率未经独立重复校准。

Mackenzie论文/代码OP背景2.0291/2.064857ppm不一致已记录，本轮背景切换本网格MAP不变；扩散支持才显著改变结果。全部单flight、近远联合、height-dependent风、RSS profile、边界、source truth后评分和图均保存。RSS+5%支持域不是95%posterior；没有杜撰未计算的后验可信度。

## 4. 跨数据集共同失败门

两数据集都对风建模选择敏感，这是可观察的逆问题敏感性；但没有证明同一种真实失败及稳定修复反复出现。不能将“模型参数换了估计就换了”直接升格成第一篇新机制。

候选A“平均/局地风不能描述source–receptor propagation”目前仅Svalbard有同向改善，Mackenzie存在风—扩散—源距离可辨识性纠缠。候选B路径变化同时混杂轨迹/高度/平台/时刻；候选C历史优于瞬时未测试；候选D高度改善无法独立归因；候选E背景/动态主导算法未证实。逐项状态见COMMON_FAILURE_MECHANISM_GATE.csv。

**满足至少两个独立真实数据集的稳健同向失败机制：本轮没有。** 协议另允许1real+controlled，但用户当前指定真实数据先行，且禁止新GADEN，本轮不走该替代门。

## 5. 第一篇科学问题与下一道可检验门

保留候选问题：“有限移动测量下，哪种风表征足以支持可辨识的源反演，以及如何表示沿源—受体传播的未观测状态和不确定性？”目前它是待检验问题，不是已成立主创新，也不预先选择world model、Mori–Zwanzig或神经网络理论。

在选择算法前应先让Mackenzie的距离/扩散联合profile、near/far一致性和源域边界可解释；获得地面风公开原件才允许第四风arm；如无法取得则明确删除该比较资格。Svalbard需独立时间块/重复与噪声校准，不能只依赖同site标定参数。只有在第二独立真实数据中出现稳定、可辨识、排除传感器/背景/坐标混杂的同向误差信号，才冻结该科学问题，再开展控制变量模拟。本轮停在资格审计与已保存的条件基线，不靠换范围把门“救”过去。

原始来源：[Lagoon Zenodo](https://zenodo.org/records/19597182)、[Mackenzie Zenodo](https://zenodo.org/records/20019779)、[Mackenzie方法论文](https://amt.copernicus.org/articles/19/3983/2026/)、[van Hove论文](https://doi.org/10.1017/eds.2026.10029)、[固定版本AlouetteUiO/active](https://github.com/AlouetteUiO/active/tree/2aec1667f10648c4be2ccc15ab2b385ec80305b7)。各track报告、完整receipt、原始SHA、配置和代码见子目录。
