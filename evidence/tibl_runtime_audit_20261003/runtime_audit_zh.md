# TIBL 工具链能力审计

日期：2026-10-03。目标是查明现有工具能否表达稳定度依赖混合及岸线内边界层，再决定是否值得执行定位机制实验。旧 R1/R1A/R1B/R3 判定不变。

## 结论

建模缺口成立：现有 GADEN 配置和原生粒团模拟接口不能直接表达局地稳定度依赖的各向异性 Kz(x,z,t)、随岸距发展的热力内边界层及其顶端交换。仅把非等温 CFD 导出的 U/V/W 喂给现有 GADEN，仍会丢掉没有体现在解析速度场中的亚网格混合与热力信息。

这个缺口不能证明 TIBL 是此前定位失败的原因。新方向可以进入建模可行性研究，但不是已经成立的科学问题或已通过的场景 gate。TIBL 也存在于海岸等热力下垫面突变场景，不是湖泊独有；真实场景中 TIBL、湖风层顶、逆温层顶和机械内部边界层不能不加区分地统一记为一个 h。

## 当前 VM 与源码核查

- 主机 zyc@192.168.111.128 可达，ROS 2 Humble。
- 当前可读 ROS 工作空间 GADEN commit：17adaf650a4f11d29aa049cf0661e9f9ea2e636f；gaden_core：9e93c36ae1af74f6a62c42f1c9d7b813153222ed；核心数据版本 3.0。
- 实际实验构建目录 PF_DEI_V3_GADEN_BUILD 的 git worktree 指向已失效路径，不能独立用该目录的 git HEAD 证明它与主工作空间完全相同。已保存实际使用源码快照及库文件哈希，而不是隐瞒版本查询失败。
- 实际 libgaden.so SHA256：0b6a2160917a1e8791c1980635b0969c40794b96d591abba31d743758fc5f048。
- 当前 PATH、/opt、/usr/lib 及 /home/zyc 的限定深度检查中，没有找到 foamVersion、常用浮力求解器或 scalarTransportFoam。这个结果表示当前可用安装未发现，不是全盘不存在的证明。未安装、升级或改变 House 环境。

RunningSimulation.cpp 的 MoveSingleFilament 实际执行：

1. 从环境网格读取三维风，推进粒团中心。
2. 以固定空气密度、固定粘度和气体比重估算终端浮升速度；它不是背景温度梯度或稳定度闭合。
3. 三方向使用同一个全局 filamentNoise_std。
4. 粒团单一 sigma 按全局 filamentGrowthGamma 增长。

Parameters 中 temperature、pressure、filamentGrowthGamma 和 filamentNoise_std 都是单一标量，未见局地 T、稳定度、各向异性扩散张量或夹卷接口。OpenFOAM 点云入口生成 WindSequence，而非携带温度与湍流标量的场集合。

原适配器固定 gamma=10000 cm²/s、温度 298 K、噪声 .02，所有场景相同。因此原 R1 是速度场消融，不能否定一个它没有表达的热力闭合机制。反过来，也不能说缺了热力就解释了原结果；R1A 的慢风充分性仍成立。

## OpenFOAM 的一般能力与当前联接缺口

OpenFOAM 一般具有浮力热流求解器，以及可由层流/湍流粘度构建有效扩散率的被动标量输运模块。稳定度依赖的物种混合仍需选择和验证浮力湍流闭合、湍流 Schmidt 数、边界条件及分辨率，不能把热扩散率当成气体物种扩散率。

官方资料：

- https://api.openfoam.com/2312/buoyantBoussinesqSimpleFoam_8C.html
- https://api.openfoam.com/2506/classFoam_1_1functionObjects_1_1scalarTransport.html
- https://www.openfoam.com/news/main-news/openfoam-v20-12/solver-and-physics

未来若使用 CFD，优先在同一个经过验证的热流框架里求解示踪气体，或构建明确传输局地扩散/湍流量的适配器。只导出风再接现有固定 gamma GADEN，不足以完成所提机制验证。

## 最小二维后备模型已做数值烟雾检查

已创建保守有限体积 x-z 标量输运程序：恒定匹配的 u=2 m/s、w=0、Kx=0.5 m²/s，支持空间变化 Kz；地面/顶部零扩散通量，零平流入流和开放平流出流。保存配置后才求解。

运行两个数值夹具：均匀 Kz，以及人为设定的随 x 增长混合高度与上下层 Kz。源、释放率、网格、时间、速度和边界条件一致。检查非负性和注入质量=域内质量+出流质量。

这些 Kz、h、源强和场景设置是数值夹具，不来自 WiscoDISCO 反演，不用于科学判定。没有计算或宣称 TIBL 定位 PASS，没有把“改 K 会改 plume”当作新发现。详见 NUMERICAL_SMOKE_RESULT.json。

## 正式 R0-TIBL 必须先补齐的合同

1. 物理参数：为 h_TIBL、上下层 Kz、过渡厚度及源/受体岸距提供可追溯范围和定义。当前温度剖面本身不能唯一估计 Kz，单站垂直剖面也不能标定 h(x)。已访问的 2026 Chicago 论文支持多层边界层存在，不提供本实验局地气体混合闭合。
2. 对照：除中性均匀场，还需相同平均扩散强度的均匀场、只随 z 变化的剖面场、沿岸距发展的场。否则不能区分“扩散强度变了”与“岸线发展的结构效应”。相同 u 匹配平流到达时间，实际排出/驻留时间另外诊断，不能声称两者全部锁死。
3. 数值验证：网格和时间步收敛、质量与边界敏感性、至少两个独立闭合形式；不能用不收敛的几何差异过门。
4. 几何 gate：预先冻结效应阈值和不确定性处理。二维仅支持垂直/下风几何，不能报告 crosswind variance；改变 Kz 后几何变化是模型预期，必须评估匹配对照后的剩余结构效应。
5. 源映射 gate：源强、背景和噪声应作为未知或敏感参数，报告相同检测机会/信噪比下的区分能力，以及源强边缘化或剖面化后的源间距离。不能再次把浓度幅值差当成源信息优势。
6. 定位 gate：二维只能研究 x_s 与源高等局部参数，不能恢复被省略的 y_s。要输出用户要求的完整水平源坐标及不确定性，需要三维正演或经过验证的横风扩展，并检查真值未知的连续反演和区间覆盖率。

## 文献核验范围

已读取 Chicago 2026 论文和 Allouche 2025 论文的公开内容。前者的观测场景包括城市热岛和 Lake Michigan，后者研究非稳态陆海风；它们支持热力/湍流状态具有复杂性，不证明近地甲烷定位失败。文中两个 ScienceDirect 链接返回 403，不能把未读正文中的 Kz 或 TIBL 量级作为已核实输入。

- https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JD046032
- https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2023JD040708

当前判定：TOOLCHAIN_AUDIT_COMPLETE；CURRENT_GADEN_LOCAL_THERMAL_MIXING_UNSUPPORTED；2D_NUMERICAL_SMOKE_COMPLETE；R0_TIBL_SCIENTIFIC_GATE_NOT_EXECUTED_PARAMETER_CONTRACT_OPEN。未启动非等温 CFD、GADEN 矩阵、训练、闭环或多无人机，也未改变此前停止结论。
