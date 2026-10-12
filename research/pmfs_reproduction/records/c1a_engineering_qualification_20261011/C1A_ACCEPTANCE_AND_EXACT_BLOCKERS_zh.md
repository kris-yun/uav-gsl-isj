# C1A 可修复性分支：实际验收与最小剩余决策

判决：ENGINEERING_SCHEMA_PASS / PHYSICAL_B1_NOT_QUALIFIED / NATIVE_CONSUMER_NOT_CONNECTED。本分支完成了真实共享盘写读、隔离C++构建和作用域单元测试，不只列MISSING；仍未启动GSL/Nav2或新的物理预测。

## 已闭合

1. **共享目录**：从实际VMX确定workspace映射为D:/ZYC/A-gas/workspace，不是D:/ZYC。新本任务目录与/mnt/hgfs/workspace/PMFS_C1A_ENGINEERING_20261011双向写读SHA匹配，原错误路径探针保留。没有改变VM共享设置、清理旧数据或扩大磁盘。
2. **447格字段契约**：使用原B4 34×45、0.25m格与447自由格mask，sourceProbability与varianceOfHitProb均要求对应1530格；禁止非自由格质量、NaN/负值、不归一、几何/mask不一致。GSL二维Free编码1与GADEN三维Free编码0不可混用。
3. **因果字段契约**：frame=map、unit=ppm、固定epoch；观测时间不能晚于状态时间，状态不能来自未来或倒退。13类非法payload均被拒绝。只是C++消息结构验收，未声称真实ROS/CDR/TF消费链已通过。
4. **正确候选间命中方差**：计算Var_S[P(hit|S)]，不替换为位置方差，也不混入Bernoulli全预测方差。447×447合成预测库的100次组装完成，Python独立复算最大差1.8041e-16。合成值只用于工程测试，不是GADEN预测或算法成绩。
5. **fail-closed**：没有合格物理算子证书时，applyProduction拒绝更新并保持生产字段不变。fixture消费路径明标测试专用；当前没有挂入PMFS本体，也未将synthetic的qualified标志改成true。

C++编译rc=0，用时1.7146s；测试rc=0，用时0.0518s；最高子进程RSS约122.7MiB。该profile仅覆盖字段组装，不能外推三维输运或整个B1的计算成本。

## 三维算子实际上在哪里

已确认原B4所用libgaden.so仍存在且SHA=0c33caad6ec2b13f3ef2854d8c7e916f5b73c7effe419c5ba26fd8d4fde994c1，与旧正式验收一致，不是缺整个三维库。

- gaden/RunningSimulation.hpp：构造Parameters+EnvironmentConfiguration；AdvanceTimestep保持旧filament状态，GetFilaments/GetCurrentTime可读。source、deltaTime、初始sigma(cm)、growth(cm²/s)、PPM中心、释放率等输入可按原B4复用。
- gaden/Simulation.hpp及Simulation.cpp：SampleConcentration(Vector3)按三维丝团和障碍可视关系计算ppm；已有真实受体读出，不需用R4周期域或二维柱并集替代。
- RunningSimulation::SampleWind(Vector3i)是virtual override，存在以派生类提供因果wind provider的薄封装路径，不必修改原库或重算CFD。但caller必须冻结提供的风权限与历史。
- fake_gas_sensor.cpp：model30调用simulate_pid，单位PPM；correction_factors=false时为各气体ppm求和。单气体B4的原PID读出就是原浓度，不能沿用R4 mg/m³及其Gaussian sd0.02。此处是静态源码单位确认，不是概率似然已资格化。

## 精确剩余缺口

**A. 初始化与风信息合同。** B4从frame500开始，已有约50s释放历史。LOCAL主模式没有同一阶段的完整局地测风历史，不能把真实CFD0–10无声提供给B1，也不能把零羽流初态当作正确的搜索初态。最小选择是：
- ORACLE_ENGINEERING：先共同向两臂开放直到当前的完整历史CFD，明标oracle，只检验接入/尺度/停止规则；不声称部署或新创新。
- LOCAL_DEPLOYMENT：给源条件初始羽流及未观测过去风一个统一、源盲先验，并先资格化。需要新模型合同和初态/风不确定性验收，不能从已看B4结果调先验。

本报告建议先ORACLE工程接通，再决定LOCAL初态合同，但此处没有改变现有C1主模式草案或执行任何goal。

**B. 可控制且可审计的随机状态与概率读出。** 当前库RunningSimulation Params无公开seed/checkpoint字段；MathUtils中GaussianRandom/uniformRandom为函数内thread_local mt19937，PrecalculatedGaussian缓存索引私有，RunningSimulation.cpp还有thread_local缓存。重复构造447实例不自动得到独立、可回放的参考流。最少需要隔离派生库的per-instance RNG/state hook，或复用已证明同物理与独立RNG的现有正式runner；原物理公式/旧库保持。还需声明和验证连续ppm或二值的合法序贯预测似然及有限参考充分性，不能拿SampleConcentration单条轨迹直接冒充完整概率模型。

**C. 原生实际消费与规模profile。** 现已提供C1A_StateBridge.hpp和可编译测试，仍需把通过物理资格的B1 bank接到PMFS源更新seam，并将其候选预测方差接到MovingStatePMFS用到的simulations字段。保持原planner/停止代码、共同源支持/信息权限及mask/tie规则；sourceProbability marker/topic单独发布无效。当前测试没有调用真实PMFS class或ROS action，故不能宣布实际消费口闭合。

## 最少新增代码与计算安排

1. SourceConditionedGadenBank + CausalWindRunningSimulation：按同447源支持维护实例，复用原3D Environment/出口和ppm读出；公开源盲初态与wind provider，新增实例级RNG/state。
2. B1ObservationFilter：逐事件合法likelihood、源质量及参考状态权重；记录ESS、MC误差，不重复同一事件或地图格。参考数必须先profile/资格化，不能直接搬R4 K24或为省内存选弱基线。
3. NativeB1Hook：只替换源推断与受体预测字段，原MovingStatePMFS/PMFS_utils行为保持；在无导航场景先证明确实读到新字段，再冻结两个goal。

下一最小可证伪资格建议是未见标签的少量原子源、同物理时间前缀和两组独立参考，仅用于一致性/MC/成本profile；具体数量/种子/参考数尚未正式注册，**此报告不授权自动跑新参考**。源码接口构建预算可沿C1草案，三维全过程实际耗时/存储尚无测量，所以不伪报6990s已经足够。共享盘足够，1GiB科学RSS与8GiB新增/4GiB余盘约束不变。无需新CFD；若需新的真实plant realization，当前一个物理批次限制仍阻断它。

## 网络与预算账

R4已完成1073.422s。停网前17:46UTC编译/测试已返回，恢复后00:09UTC未发现本任务相关VM进程。恢复请求00:03UTC来自母任务报告；断网精确起点未直接观测，故只记录可核对的文件时间，不编造暂停区间。跨越网络中断的阶段UTC跨度不证明连续计算，也不修改任何已运行进程的绝对deadline。

按C1A branch_compute_limit_s1800整额保守扣预留，剩11526.578s；已经证实的编译/测试活跃时长1.7664s，其他源读取/共享校验有独立command receipt。未跨日重置预算。当前剩余额只是保守账务，不是已经合格的新闭环窗口；未来动作仍须共同物理、原生接口、信息隔离与现场资源guard过门。

本分支：隔离standalone构建1、原生GSL构建0、physical forward0、CFD0、新气体0、goal0；RPSPM停止判决不动。总体主创新目标仍未完成，当前进入的是明确的模型/初态与工程绑定选择，不是再次翻旧文件或空跑旧PMFS。
