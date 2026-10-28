# V46 第一轮代码与因果链核查

审查对象：实际交付 `output/V45A_Overleaf/reference_code/`、主文3--4节、V46补丁。只读核查；此时未改变最终代码。审查者为AI代码/控制视角，不是外部人类专家。

| ID | 原稿/源码 | 裁决 | 证据与修改方向 | 仍需物理验证 |
|---|---|---|---|---|
| C01 | 主文式(5)--(7)，`odor_memory/encode` | 保留 | 同一合格集合在归一化前掩码，因果有限窗权重、双极激活和完整相对风保留一致；原始负值仅在控制副本整流 | ID、标定和时间窗目前由调用者保证 |
| C02 | `propose` PF-01 | 保留 | 失格巨信号在contact和memory前置零，已有1e300回归；默认全1不变 | quality不是气团相干性证书 |
| C03 | 主文T/R闭式解，`decode` | 保留 | T一阶矩、分支二阶矩先求逆后求和、零和投影、统一缩放一致；非M2源后验输出 | 实际飞控执行后仍需重算位移与安全 |
| C04 | 置换结论，旧`test_certificates` | CONDITIONAL / 代码范围缺口 | 只检查encode/decode的行重排；未实现候选库、评分、安全、tie和执行，不能称完整闭环已通过 | 新实现需携带物理ID、标定、历史和状态；证明限定存储重排 |
| C05 | 主文算法1，`propose`返回值 | 缺失实现，非公式反例 | 返回physical_execution_certified=false和source_evidence_certified=false；没有真实执行器、raw ledger或posterior。需实现可调用闭环协调器与明确native backend接口 | 原生GADEN/飞控接口不能由解析测试代替 |
| C06 | 主文M3三个层面 | 定义不足 | time_support_qualified与model_gate_known两个布尔不足区分时间、形态稳定、气团相干、模型覆盖；需三值状态和证据来源 | 无独立数据的状态UNKNOWN；不赋造误拒/误放概率 |
| C07 | 原始y Fisher | 保留 | 实现从未对a±建立源似然；Fisher代码对raw mean Jacobian。ReLU控制零点不是该证明反例 | raw生成模型协方差和微分条件仍需验证 |
| C08 | 唯一计证 | 需要落实 | raw_update_required只是提示；无去重ID、因果block kernel或原始数据账本 | 新协调器应拒绝重复/重叠raw IDs；新模型重算时必须重置账本 |
| C09 | 安全 | 需要接入 | history修复有恒速最近距离与地图segment接口；M1当前尚未调用 | 连续段几何和tracking margin必须由真实接口核实 |
| C10 | 复杂度 | 条件正确，需分项 | M1 O(NHc+Nd²+d³)；旧库未有完整运行统计，不能宣称整体O(N) | 记录K、J、源/干扰支持、N² pair safety和actual call counts |
| C11 | 已下载数据 | 纠正可用性范围 | 本工作区有V35--V43代码、CSV诊断与V43冻结原始观测JSON；未找到VGR原始house浓度场、Orebro、ReD或ADApprox原始数据文件 | 历史本地路径仅为定位线索，不是本机可用文件 |
| C12 | 可用原始记录 | 可执行限域核查 | V43 frozen fixture含t/pos/gas，包含负原始值；无每探头实测局地风和完整原生资格字段 | 能做固定数据/数值/数据流核查，不能冒称新M1反事实定位实验 |

## 拟修订实现（等待第二轮冻结）

1. 保留原M1内核，增补ID键控的输入状态、标定记录、窗口管理和历史足迹；不改变T/R定义。
2. 定义四类资格的独立PASS/FAIL/UNKNOWN记录；确定性时钟/故障可按已知阈值判别，形态仅经验筛选，气团与模型需要外部证据。
3. 建立完整合法动作目录、同预算K提案筛选、统一缩放、连续两机距离和明确地图段接口；用与行顺序无关的候选family/系数ID决胜。
4. M2调用共同source-conditional backend；有限bank分离只称评分，缺少连续覆盖/模型误差不写认证；UNKNOWN有有界补测/覆盖路由。
5. 执行实际动作后，原始block ID ledger控制唯一posterior更新。输出XY概率对全部h/q/m支持边缘化。派生χ/a/T/R不额外计证。
6. 核查端到端存储重排、错排标定反例、ties、raw重复/负值、mask变更、全库相同动作、覆盖与补测安全、执行中断、Green已知域接口。解析测试只证明代码/数学契约。
7. Codex合同用既有VGR House 300s共享world与留出世界；数据清单/哈希先冻结，缺原始字段时停止该benchmark并记录OPEN，不把缺接口归为方法无效。新S2生成禁止。
