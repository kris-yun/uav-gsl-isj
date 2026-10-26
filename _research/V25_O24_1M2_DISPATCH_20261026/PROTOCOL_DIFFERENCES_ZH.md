# PMFS 论文、作者公开源码与当前 O24 的三种身份

本文件只记录已查到的事实，不把必要移植或数值修复列为创新。

|项目|论文公式协议|作者公开 a8d5a764 配置/实现|实际冻结 O24 1 m² SCREEN12|
|---|---|---|---|
|置信度|Eq.6 使用 Ω²|`PMFSLib.cpp` 使用线性 Ω：`1-exp(-Ω/σc²)`|保留线性 Ω|
|单候选评分|Eq.8 没有显式 D|单格 `lerp(1,1-D*abs(p-f),alpha)`；启动 D=.2|D=.2，不以 D=1 冒充论文协议|
|声明|论文采用 1 m² 级方差条件|启动文件 `convergence_thr=1.5`|严格全后验 covariance trace <1 m²|
|风输入|按论文实验说明分别解释|公开启动 `useWindGroundTruth=True`|`false`，只用局地风/GMRF|
|时间|论文报告本身不能还原全部代码时钟|启动最大300 s；BasicSim 5；GSL `use_sim_time=False`|统一物理时间；BasicSim1；`use_sim_time=True`；maxSearchTime1e9；不循环回放|
|源域|论文任务中的源域|基于导航栅格、尺度缩并和连通性|冻结原域；B2真源格被排除，五角色仅诊断|
|源码身份|论文并未锁定当前本地移植|a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533|631145657461c41840f6844f118de57d1e747ea4，128文件及e63 ELF|
|结果身份|作者各实验及重复统计|当前公开源码不等同原论文每次实验|12槽位、11数值验收、10原生声明；7合法源运行中的6声明+1删失|

因此，当前主基线准确名称应为 **PMFS O24 移植版，局地风/GMRF、D=.2、1 m² 声明协议**。不能说已经严格重现论文全套实验，也不能继续引用 V24 的 1.5 m² 作为当前配置。

## 原生读出和停止中容易误判的细节

`PMFS_utils.cpp::varianceSourcePosition()` 使用所有自由候选的归一化概率，对相对全分布均值的 XY 平方距离求和，单位 m²。`checkSourceFound()` 在相应原生分支采用严格 `<`，`convergence_steps=5` 并不是在此函数额外要求连续五次满足。`distanceThreshold=.5` 与真实源距离用于单列导航时间记录，不能当成部署停止证据。

`expectedValueSource(.05)` 先按概率降序排序，循环条件 `i < size*.05` 等价于选 `ceil(.05N)` 格，取其概率加权中心。排序比较器只比较概率，未规定稳定并列顺序。新 Python 重算必须对齐原生输出或报告有影响的并列边界；不能悄悄更换为 MAP 或全均值后仍称同一指标。

## 现有结果的资格边界

合法源 A2 三次和 C3_R01、D4_R01 原生声明误差分别为 0.24249、0.61325、0.49721、0.42962、0.79966 m。E3_R01 的 Top-5% XY 误差 3.24763 m，源方差 0.52446 m²，真实源排名131，属于当前合法源、1 m² 协议中的高置信错误个案。C3_R02 录制耗尽时方差 1.13241 m²，其最后读出不能称为原生声明。这里是既有已验收结果的读取，不是本轮新运行结果。

B2 的真实源在三维环境中合法，但被原二维源候选规则排除，不能作为“真源属于支持集时的推断失败”主统计。附近约0.248 m的合法候选仍存在，域排除亦不能单独解释全部约2 m误差。E3 的一个反例说明错误置信确实存在，不说明新机制一定可修复，也不提供跨天气统计泛化证据。

## 哈希与换行

镜像 Git blob `ee086dfe21c82e6b76a8bea65f74cd5ca516b9ad` 保存 LF；Windows 冻结清单保存 CRLF SHA。已验证两者只有换行变化。守卫接受两种已证实锁字节身份作元数据核对；完整本机封存仍严格按原始逐文件哈希检查，不能通过自动改写冻结文件消除差异。

## 可直接复核的一手依据

- [作者启动配置，准确 a8 提交](https://github.com/MAPIRlab/GasSourceLocalization/blob/a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533/Environment_config/PMFS/launch/main_simbot_launch.py)。
- [本地冻结锁镜像](https://github.com/kris-yun/uav-gsl-isj/blob/a339136931c4f285697c6e2c7804869646971ed3/workspace/FROZEN_O24_1M2_SCREEN12_20261024/BASELINE_LOCK.json)。
- [完整角色及实际参数](https://github.com/kris-yun/uav-gsl-isj/blob/a339136931c4f285697c6e2c7804869646971ed3/workspace/FROZEN_O24_1M2_SCREEN12_20261024/FROZEN_CASES.json)。
- [原始 SCREEN12 结果](https://github.com/kris-yun/uav-gsl-isj/blob/a339136931c4f285697c6e2c7804869646971ed3/_research/O24_SCREEN12_AUDIT_HANDOFF_20261024/EPISODE_RESULTS.csv)。
- [原生源码及128文件身份](https://github.com/kris-yun/uav-gsl-isj/tree/a339136931c4f285697c6e2c7804869646971ed3/workspace/FROZEN_O24_1M2_SCREEN12_20261024/source_snapshot)。

未读取到用户当前 Windows 卷和虚拟机实时状态；完整运行ZIP在本地交付包中，当前GitHub文本镜像没有这些二进制。故本轮派发不声称已新完成ROS闭环或本机峰值内存实测。
