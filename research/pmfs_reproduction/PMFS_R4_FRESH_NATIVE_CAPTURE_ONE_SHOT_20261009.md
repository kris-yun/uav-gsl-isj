# PMFS P1b R4：停止追查不可恢复旧记录，首次运行前一次性采集全部状态（2026-10-09）

> **本合同取代以前要求旧20条历史事件必须补出raw stamp/TF与原生随机态才能运行P1b的前置门**。既往缺失状态不可能从保存的steady_ns和离线C-map可靠逆推。该旧档案保留HOLD，绝不篡改；测试新实验要有**独立新ID**。目标不是论文结果，而是在一次受控输入下闭合官方核心概率更新的数值等价性。

## 已确认，不得再重复
- R3：真实ROS TF时间戳工程修复 N1 **5/5 PASS**、原始版新鲜固定姿态 **4/4 PASS**。上游无时间戳版本在延迟旋转运动中仍不合格。各版本二进制严格分离。
- P0静态审计PASS，旧R1核心hit map reconstruction / fixed candidate scores的部分数值复算PASS。
- 旧R1样本缺raw member stamp/frame、模仿消费者采样-消费TF键、在线候选叶内RNG/模拟图/细分后验；旧资料不可再提高P1b资格；**禁止把旧87幅离线C图改名native-online**。
- H02旧失败依然`UNRESOLVED_CONTRACT_HOLD`；理论研究问题暂时是假设。

## 立即执行，只做一条全链样本
**R4-0：10–20分钟只读清点启动资产、构建新capture hook**（不是回头全面审计）：
1. 复用R3已通过的ROS2环境/ELF/TF、冻结occupancy/map/前向风/官方核心；检查原生 `Simulations::updateSourceProbability()` 能否由最小测试环境触发。确定能时，用新的实验ID `P1B_NATIVE_CAPTURE_R4`。
2. 输入分层命名：
   - 如果本地恰有官方B1/C1完整匹配场景+原生GADEN播放资产，可采用，但并不要求先跑完整导航；
   - 否则在隔离ROS测试环境中以**明确标作 `SYNTHETIC_OR_REPLAY_FIXTURE`**的合法新消息（新stamp、TF、风、相同网格和候选）驱动**真实原生算法函数**进行一次 source update。这只证明实现/数值parity，**不证明真实物理或原论文C1成功**；
   - 不得给旧20条事件虚构历史stamp：如引用旧数值，只作为重新注入的新fixture，明确原物理时间已不可逆。
3. 如果上述已有地图/风/可编译函数入口不足以触发 source update，允许造**极小、不依赖GADEN的数学fixture**来测试原生算法核心，但必须标为 `UNIT_CORE_PARITY`；如果任何原生过程都无法执行，记录单条确切构建/依赖错误并停止，不得再重开旧证据调查。
4. 使用固定停留 / 同一时钟 / TF合同；PMFS TO、GMRF FROM与位置观测各走已验收接口。若输入仅静态2D风图，不得宣称GMRF已收敛。

**R4-1：先插桩后运行，执行最多一次成功更新（允许一次明确的环境崩溃修复重试）**：
- 入口：新收到的 raw GasSensor/Anemometer成员 `header.stamp/frame_id`、收到时刻、TF查询时刻、重采样/阈值及 StopAndMeasure 平均块ID，风源与实测风分列。
- 更新前：完整 `logOdds/confidence` grid、占用图/坐标原点、源候选树与active叶、全部有效参数/ELF SHA、线程数和RNG预状态或足以确定每叶的采样点。
- 正向模拟：每个候选叶内实际sample坐标、实际simulated hitMap哈希（必要时全图）、raw likelihood/score，细分子叶及分数；记录随机状态/高斯缓存或者直接保存实现用过的实际采样点及噪声轨迹。尽可能只读输出，不更改任何计算及RNG消耗。
- 更新后：**最终细分后的**posterior与归一化常数/概率图、MAP，以及作用到各个区域的概率；必须是原生实际生成，不接受离线预重算代替。
- 预先校验日志schema全字段非空、数组维度正确、身份为原生进程；出现日志字段缺失则**不启动正式run**。记录钩子可使用隔离编译的被动插桩，原始仓库/ELF原件保持不变；比较插桩前后相同固定输入的输出是否改变。

**R4-2：离线同输入数值parity**：
- 用本次实时保存的同一 input&sample positions&candidate tree 回放；逐层对齐：测量块 → hit map → 2D wind → 模拟hit map → raw score → 最终posterior+rank。
- 把仅校验预先捕获sim map的后半链标为 `POSTERIOR_REPLAY_PARITY`；另行校验相同sample points的forward map才有 `FORWARD_CORE_PARITY`；两者全过才准写`CORE_UPDATE_PARITY_PASS`。
- 固定数值容差依据存储浮点类型在运行前列入 manifest；不得用最终MAP作调试目标，不依据真源排序选样本。
- 数据若为fixture，结果只证明**代码实现等价**，不验证PMFS真实源定位误差或物理时间假设。

## 停止/结果
- `CORE_UPDATE_PARITY_PASS`：所有层通过且原生真的更新过一次；可进入之后的干净作者C1/B1场景评价（还需真实asset）。
- `UNIT_CORE_PARITY_PASS_ONLY`：最小核心fixture通过，但缺ROS原生状态；允许离线代码方法研究，但不得叫完整原生在线复现。
- `CORE_UPDATE_PARITY_FAIL`：完整trace清楚指向首次分叉点及源码/差异；
- `BLOCKED_BY_EXACT_RUNTIME_DEPENDENCY`：列**一个**最早阻碍的真实错误和最小修复，不允许写泛泛“缺时间/TF/随机状态”，因为新运行本来就是为了采集它们。
- 所有结果不能证明2024原论文完整导航可复现；不能宣称科学创新有效。

## 科研优先级
一旦可用方法级baseline明确，才讨论原创假设：风场变化下，观测到的源–受体气体传播历史与当前候选源模拟条件不一致是否带来可重复源排序损害。先用合格、**非饱和**的多候选观测验证失配的定位效应；风接入工程修复/简单时间遗忘/加floor非创新。对比必须包括原生core、同输入简单窗口或时间加权、物理历史对齐和扰乱历史负对照；更高保真输出另评 plume path/shape/forecast。无法证明时不开伪科学“正信号”。
