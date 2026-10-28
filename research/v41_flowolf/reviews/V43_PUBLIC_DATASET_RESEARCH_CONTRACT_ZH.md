# V43 科学裁决：公开数据集真实性与多机气源定位验证合同（2026-10-28）

**研究对象**：体心风嗅双通路多UAV主动取证，V41→V43；S2=受控原生甲烷开发数据，非真实风洞、非跨气象验证。此文件为科研数据审计及 Codex 实验合同，**不是**已经完成的跨数据集验证结果。

## A. 对外部 AI 三个数据集的真实性裁决

| 对方描述 | 身份核查结论 | 处置 |
|---|---|---|
| MURLI / Multi-Robot Localization in Intermittent Plumes / Zaragoza RA-L 2023 / MURLI-Dataset | 在论文标题、作者、GitHub 名字的交叉检索中未找到相互印证的正式来源；不能证实是3–5架无人机多机甲烷数据 | **UNVERIFIED_DO_NOT_CITE** |
| SnifferBench / Li T-RO 2024 | 未找到正式论文及原始标准接口 | **UNVERIFIED_DO_NOT_CITE** |
| WindFlume-Gas / Neumann Sensors 2022 | 未找到对应Zenodo项目/论文 | **UNVERIFIED_DO_NOT_CITE** |

不能因为搜索结果空白就证明绝对不存在，但在获得DOI、作者页、实际原始文件和数据字段之前，严禁下载同名不明文件或把上述三个名字写进论文。

## B. 核验成功的数据集与用途

### B1. ReD:Vapor（首先新增的独立真实物理样本）
- 论文：Hinsen 等, *Scientific Data* (2026), https://www.nature.com/articles/s41597-026-06927-8 。
- 最新数据**版本v2**：Zenodo https://zenodo.org/records/18299926 ，DOI 10.5281/zenodo.18299926，2026-01-20；作者GitHub https://github.com/DLR-KN/red-vapor。
- 39次独立采集：8次3D栅格扫描、22次传感器移动穿越、9次清洗，真实风洞、三维位姿、三维风、多个MOS与PID等传感器。`overview_table.csv` 仅约3.9KB，官方 `voxel_maps.pkl` 约9MB，完整预处理约841MB CSV压缩包，`experiments.pkl`约1.3GB。
- 先只下载 `overview_table.csv`、字段说明及 `voxel_maps.pkl`，不要一开始占用几个GB。初步审核后选2-3个真实实验原始CSV，完整核对坐标、传感器响应时间、风、源位、训练/测试分组。
- **可以检验**：真实浓度时变/非高斯、风嗅方向、固定轨迹回放上的后验鲁棒性、间歇模型/空间相关性、传感器时间动态。
- **不能直接证明**：任意三架UAV实时闭环优势；栅格扫描耗时70–120min，空间相邻点的观测时间常不同步，不能拼成同一时刻三机观测。若没有同日同风条件下可验证的平稳近似，只做真实读数的离线分析。`voxel_maps.pkl` 是时间聚合后的空间格网，不能假装真实时序同步。

### B2. Orebro3DSEN（优先测试时空身份与气团相干的真实阵列）
- 数据与代码： https://github.com/jburgues/Orebro3DSEN ，对应真实室内 3D MOX 阵列研究；相关发表：https://www.sciencedirect.com/science/article/pii/S0925400519315084 。
- 27个固定探头，约十个乙醇释放实验，源高/释放位置/气流条件变化；不同探头时间对齐的真实读数特别适合验证“谁在什么高度闻到了、向心/离心身份结构、时间一致性资格门”。
- **可以检验**：空间相关与信号采集资格、是否存在线性可分离/高低探头伪曲率、固定几何下的源辨识，及身份置换下的非退化性。
- **不能直接证明**：多机运动控制、任意轨迹反事实，也不能直接把没有提供的每个探头局地3D风或甲烷ppm凭空补齐；原始MOX数字输出需采用文档实际标定。

### B3. ADApprox 数据（小体量真实无人机与普通算法横向验证）
- IROS 2025， https://zenodo.org/records/17189796 ，DOI 10.5281/zenodo.17189796，约13.6 MB ZIP，开源算法 https://github.com/disal-epfl/ADApprox 。
- 可审计稀疏无人机气体读数与真实飞行/仿真接口，复用普通前向强对照；**只有字段和真实轨迹复核后**才能确定可否做完整源定位和动作反事实。
- 既往 ADApprox 在用户资源中单试验内存需求过大：不得要求一次加载全实验的dense covariance；先选少量合法案例和流式预算。

### B4. VGR 公开 CFD/GADEN（保留为可交互控制闭环与跨模拟场景验证）
- 官方 https://mapir.isa.uma.es/olfaction-dataset/ ，论文 DOI 10.1007/s10846-023-02012-z；30个环境×4配置=120模拟场景，包含GADEN/ROS/CFD风场。
- 用户旧 House01–03 已审计过并出现多轮负结果；**新增**House/风配置应是预先冻结、独立环境，不重跑House01–03后称外部泛化。
- 若能够通过GADEN时序查询重新执行动作，最适合完成E0→E2闭环；但应标注它是公开 CFD 模拟而非真实世界气象。

### B5. 可选真实单机历史记录
- https://github.com/CHTiansweet/Topography-aware-Gas-Source-Localization ：真实/实验机器人风、位姿、源标签与历史地图记录，核对是否含连续原始浓度，不得默认支持三机反事实。

## C. 分层验证协议，不可混淆实验目标

1. **VALIDITY-0 数据身份**：DOI、发布版本、完整下载URL、发布者、LICENSE/伦理、原始hash、原始字段表、单位/坐标、源标签、风、时间同步、气体种类、传感器动态与观测间歇性。数据只有历史轨迹就标 OFFLINE_REPLAY；能反事实读气体+风+位置才标 CLOSED_LOOP_QUERY。
2. **VALIDITY-1 真实测量/编码**：在 ReD 与 Orebro 的相互独立实验中，检验质量控制门的 false pass / false reject、归一化截面稳定性、同一探头身份与跨探头流向关联、传感器延迟；只有地面真实测量的数量，不能叫「多UAV主动定位成功」。
3. **VALIDITY-2 固定历史源概率**：已知源 GT 仅用于最后评价，真实原始测量统一进入候选源历史前向。比较普通混合/粒子/GLR，BIO在固定历史不得凭额外特征重复计证，**无动作改变则 BIO 不应相对同似然普通法提高后验**。
4. **VALIDITY-3 真实主动闭环**：仅 S2 与 VGR 可通过合格模拟器完整进行；三机同机时/动作域、公开风场、仪器噪声和计算预算，成对比较 BIO、普通 EIG、普通投影、普通等风向覆盖、NoIdentity、NoFlow；主指标首次接触、源 MAP/Top5%、false confidence、harm、预算/时延。
5. **独立性**：按实验/房屋/风配置/真实释放运行进行分组，不按同一次释放的观测窗随机分训练测试。不同气体的信号单位必须按自身标定处理，禁止将乙醇 MOX 数值当成甲烷ppm或将多个数据集浓度做无证据全局归一化。

### 正式关口
- 任何「Biological mechanism indispensable」需要相同候选动作、完全相同控制预算、相同前向和后验，只替换位置-流向-气味身份调制，且在独立场景中有稳定增量。不存在理论上的相变坍塌必需条件。
- S2自身不能证明跨风真实泛化；ReD/Orebro只证明观测方面的外部有效性；VGR能够提供公开模拟器闭环泛化；真实UAV外场试飞另计。

## D. Codex 下载与执行先后顺序

**先执行原生S2接口和V43固定动作域测试**，并行进行免费小元数据审计：ReD v2 `overview_table.csv`、论文数据目录与时钟、Orebro README/实际文件大小与同步协议、ADApprox ZIP索引/原始字段。输出 `PUBLIC_DATASET_PROVENANCE.csv`，每个字段有实际证据路径/源码/DOI，FAIL/CANNOT_VERIFY 不得凭猜测填写。

下一步仅下载必要真实子集用于 VALIDITY-1；若源标签/风/原始时序不合格，止于数据真实性报告，不自动升级成闭环指标。对完整数据大下载先检查磁盘空间；ReD 总计约2.4GB，请避免“整个下载好了但本机没空间”。

**预先冻结的实验合同**：首次使用公开数据前保存 `DATASET_SPLIT_FREEZE.json`，包含选定实验ID、训练/开发/留出组、字段映射、阈值标定来源、时间窗独立性、不得读取的真值文件、数据使用许可。测试时不可挑选有利数据事后筛选。

## E. 当前V43补丁真实性

已经修改并本地运行：保留向心/离心通道、按真实几何而不是数组下标分配三向动作、相同动作集合的BIO/NoIdentity消融、基于噪声的有限历史归一化浓度形态稳定性初筛。33项测试通过；原先BIO/noidentity的六合成开发结果差距消失，两者均4.106m、普通投影4.106m。**这不是身份编码获得了独立收益**。尚未通过S2真实气团、Orebro、ReD或ADApprox实验。