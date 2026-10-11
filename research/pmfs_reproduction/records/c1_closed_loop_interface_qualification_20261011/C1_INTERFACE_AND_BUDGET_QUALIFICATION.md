# C1 原生闭环接口与预算资格

**当前判决：NO_GO_NOW_INPUT_AND_INTERFACE。** 原生PMFS/Nav2通路可复用；普通动态B1目前不能公平接入同一物理闭环。阻断来自具体输入、接口与存储条件，不是用户没有授权，也不是RPSPM停门等于整个研究目标完成。

C1是本次资格阶段名称，候选工程场景为已有B4，绝不混称作者官方C1案例。R3/R4/R5阶段与原包冻结，不重跑。

## 已直接核对

- 原VM仍在，已锁定B4/R5工作树、完整B4结果和原启动参数存在；当前相关ROS进程0。最新根盘余量 4.202GiB，可用RAM 3.859GiB。
- 隔离原生构建的PMFS/GSL flags.make包含USE_GADEN=1，仅看launch标志不足。历史B4 useWindGroundTruth=true，原生结果有Action终态、success=true、Top5误差5.111584m、方差0.329068；关闭阶段-6仍留档，不重跑解释它。
- PMFS.cpp维护sourceProbability、hitProbability、simulations；原生真实源更新由已完成停留次数触发。B4 resolved initialExplorationMoves=2、maxUpdatesPerStop=5、stepsSourceUpdate=3，并非默认5。
- MovingStatePMFS选择搜索目标使用simulations.varianceOfHitProb以及hitProbability置信度/可见域、Nav2可达性。Simulations.cpp以第一层候选hitMap与sourceProb计算加权方差。**它不是外部source-map订阅器，也不是把位置后验方差作为每个受体信息值。**
- PMFS_utils.cpp从初始化startTime计300模拟秒，原生方差小于1.5才宣布收敛；Top5用于官方位置误差，完整均值是另一个指标。

## 真正需要接的两个口

I1：连续原生观测→B1 source-conditioned输运状态→同一447合法格源后验。I2：同一输运状态→候选条件受体响应→规划所需命中预测方差。仅替换sourceProbability，原导航仍用旧二维模拟的varianceOfHitProb；那不能声称闭环由新推断机制驱动。必须在隔离派生版本新增严格类型/时钟接口，原版保持不动。

为隔离方法而保持planner核心不变，B1也应提供与原weighted candidate-hit variability兼容的量，不能拿任意新探索奖励制造优势。源码另发现distance-weighted evaluation计算后排序插入interest；这是已冻结实现风险，保持两臂相同行为，尚不宣称是B4科学失败根因，也不在本轮改它。

## 为什么不能直接运行R4 B1

| 项目 | R4 | 原生B4 | 缺口 |
|---|---|---|---|
| 支持 | 25原子点 | 原生447自由格/自适应候选 | 需共同完整支持，不能以粗区回填冒充原子预测 |
| 物理 | 2D周期FV、固定1m厚层 | 房屋3D占据/出口/GADEN气体 | 边界、高度、释放与状态模型不一致 |
| 传感器 | mg/m³删失Gaussian sd0.02 | 原PID model30、原浓度读出 | 不能直接改名ppm或沿用R4噪声 |
| 风 | 局地风sd0.02、空间均匀 | 原anemometer noise_std0.3、TF/GMRF；历史主程序直接全场查询 | 原生公平local模式需另锁定，真风模式仅共同oracle诊断 |
| 导航 | 固定50点路线 | Nav2自适应路径+原命中方差规划 | 需两个实际消费的状态接口 |
| 独立性 | 18未见数学任务 | 一份已看过B4 physical realization | 复用只能做工程配对，不能新方法独立确认 |

故R4 grid-point定位地板与普通模型充分性不直接回答原生闭环增益；也不能故意改困难条件救RPSPM。

## 数量与预算草案

只建议在上述验收后冻结一对B4复用：两臂各最多1goal，共2，原气体、源(-3.2,-3.3,-0.5)、初始机器人(-0.9,0.15,-0.7)、yaw1、导航控制器与300模拟秒一致。primary两臂只用共同因果局部风/GMRF，因此属于保持原核心的共同输入派生配置，不能叫作者N0原样。历史ground-truth配置保留；若作为oracle诊断必须给两臂同样风信息。

R4实际用了 1073.422s；总4h中余 13326.578s（3.702h）。草案2×345s goal外部墙钟上限，加接口构建3600s、单元/消息与传感器验收1800s、预检整理900s，共6990s，在时间算术内。**这些是上限分配与工程估计，不是已通过的B4 B1 profiling。** 未合格前不分配新seed/追加goal。

VM根盘保留4GiB后仅 206.5MiB空间；不能把新二进制、原生全部候选记录和编译缓存写入这里。已确认hgfs挂载及workspace/code等共享根，但具体本任务目录映射和写入校验仍未完成。记录需用新共享子目录；源/运行仍保持原隔离工作树，根盘新写暂限64MiB。不得删除旧结果或自动转存其他任务资产。单科学进程RSS≤1GiB、累计新增≤8GiB继续有效。

附件“一个新物理批次”已经由R4消耗。本草案只复用B4，不生成第二份物理数据；若后续条件闭环放行，两个native goal必须明记为同研究继续计算并扣总额度，不能静默新开一批、不能当作新realization。需要新源/风plant时，当前草案不覆盖。

## 最小下一步与真实阻断

1. 先明确B1在B4的合法物理状态：复用合格GADEN/3D源条件算子或完成与B4出口、释放高度、传感器响应一致的普通动力学资格；不直接搬R4周期模型。现有R4 B1不具备这项接口。
2. 实现两个隔离adapter：原始带stamp/TF的观测输入，以及源后验+受体命中预测方差的原生消费出口。先无导航验证同状态/同源码信息权限，profiling内存与每步时间。
3. 核验新共享输出目录、原生进程隔离与修复后的guard，再冻结两个goal的事件RNG、排序tie规则、初始状态和评价合同。

目前没有一个已验收的B4 B1可执行体，无法如实承诺在当前剩余额度完成上述物理适配，更不能空跑两次旧PMFS冒充比较。工程配对完成也不够SCI独立增益；未见源/风/realization数量以后须先注册并取得合格物理输入。

本步调用：原生goal0、CFD0、气体生成0、构建0，原VM和全部冻结文件保持。C1_FROZEN_PLAN_DRAFT是输入—计算—输出与有界预算草案，不是已签发可运行配置。
