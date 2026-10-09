# PMFS P0 风场接口修订及 P1 最小验收合同（2026-10-09）

**状态**：P0 静态血统审计 PASS；完整 P1 `CORE_PARITY_HOLD`；P2 `FULL_PIPELINE_HOLD`；独立科学机理 `UNRESOLVED`。本文件修订旧指南错误；旧指南不覆盖。当前 H02 历史异常不能认定为原生 PMFS 模型缺陷。

## 1. 确定的源码接口（固定版本，须重新核对实际加载二进制）
- PMFS 官方 `4e141e162551e674f2f30ddb8859136c72139aac`，`gsl_server/src/gsl_server/algorithms/Common/Algorithm.cpp` 104–130行：`windCallback` 将消息方向作为 **downwind TO**，使用 TF 从消息frame旋转到 map，不增加π。
- GMRF `2ec7a5db7bf5f2597e9d62ba662d3efcfc788d71`，`gmrf_wind_mapping/src/gmrf_node.cpp` 212–287行：消息按 **upwind FROM**，TF变换后加π获得TO。查询 `lookupTransform(target map, msg.header.frame_id, msg.header.stamp)`，以TF平移作为测量(x,y)。若消息frame_id=map，结果为(0,0)，而非真实机器人位置。
- GADEN模拟风速计 `simulated_anemometer/src/fake_anemometer.cpp`：`use_map_ref_system=false` 发布传感器frame中的FROM；`true` 发布map中的TO、header.frame_id=map。官方2026启动示例 `main_simbot_launch.py` 174行明确为False，因此单一话题接给两消费者时有风向语义风险；并且 True 的 map-frame 消息若直接给 GMRF会使风观测位置变(0,0)。
- 同一示例参数 `useWindGroundTruth=true` 控制 PMFS *源假设模拟* 的风来源，不保证 *观测命中图* 使用同一来源；分别检查，不能将整个算法的风输出一概称反向。
- 示例有 `maxUpdatesPerStop=5`，这是发布的配置，不等于每次停止固定收5个原始ROS消息，更不是普通规范。C1覆盖`iterationsToRecord=300`、`maxWarmupIterations=800`、`initialExplorationMoves=5`；其余必须runtime resolved。
- 静态 launch 显示 GSL `use_sim_time=False`、anemometer `use_sim_time=True`。未确认运行时跨时钟消息/TF；把这个列为**额外待核的潜在合同风险**，不能事先宣称有bug。
- S2 `C*=0.1`→旧归一化等效ppm阈值换算只对经过验证的S2映射成立；不是官方C1/真实传感器标准。

## 2. 两种配置必须独立存档，避免偷偷修官方基线
**N0 `OFFICIAL_AS_IS`**：指定版本的上游启动、话题和原生代码，如实保存实际消费者输入。这是复现上游发布示例的工程基线；不可将接口桥接后的输出称为纯原生论文复现，且2026版本本身并不等于2024发表时版本。

**N1 `INTERFACE_ALIGNED_NATIVE_CORE`**：原生PMFS/GMRF核心不改，**在外部独立ROS话题做消费者适配**：
- 需要真实传感器帧 `sensor_link`，位置通过动态`map←sensor_link` TF 在消息stamp时刻得到；`frame_id` 不得伪造为 map 来省略定位。
- 已知 map 下真实吹向 `θ_map_TO = atan2(v,u)` 与传感器在 map 中航向 `ψ_map_sensor`：
  - PMFS 话题的传感器坐标风向 `θ_sensor_TO = wrap(θ_map_TO - ψ_map_sensor)`。
  - GMRF 话题的传感器坐标风向 `θ_sensor_FROM = wrap(θ_map_TO + π - ψ_map_sensor)`。
  - 两话题均保留同一可信 sensor frame、时间戳、风速和同一实体观察位置（不能凭空“修复”旧档案）。
- 用显式 `anemometer_topic`（PMFS）和 `sensor_topic`（GMRF）参数分别绑定，原生listener不改；记录launch变更、消息录包、TF链、源码/ELF/commit/hash。此方法是**接口对齐的工程修正版**，不是科学算法创新。
- 若仅做核心离线测试，可替代以物理vector直达两模块的受控单测，严格声明未覆盖ROS导航。

## 3. P1a 必须先做：风通道最小真实验收（不是仅静态真值表）
- 独立ROS测试，两观测位置（不得都在map原点）＋一个非零传感器yaw（例如90°）；在每种位置发(1,0),(0,1),(-1,0),(0,-1) m/s 的物理风vector，以及零速特殊情况。
- 核对消息发布、两个topic各自的 `frame_id/stamp`，TF查询成功、观测位置正确、消费者实际解析map下TO方向和速度。比较真实GMRF map已插入位置、风方向估计以及PMFS命中图所用的风；检查风向wrap和低风速处理。
- 对frame_id=map的旧提案提供**可复现预期失败负对照**（GMRF位置归原点），但仅作为独立实验，不向原论文声称其历史H02 root cause。
- **数值门先声明**：正确参考方向与消费后方向角差 <1e-4 rad（若传感器添加随机噪声，必须设噪声0或记录并在期望中加入采样误差）；位置误差 <0.01m，TF无法变换或时钟域混淆则FAIL/HOLD。映射网格位置必须在正确格点（考虑GMRF索引舍入、地图分辨率）。
- 观察到GMRF内部估计风未收敛时，记录输入存储/回调及未收敛状态，禁止把其estimated field直接宣称准确。
- 输出 `WIND_TOPIC_TF_CONSUMER_TEST.csv` `TF_CLOCK_MATRIX.json` `WIND_PARITY_VERDICT.md`。

## 4. P1b 再做：单次原生候选更新记录，避免假“在线—离线一致”
- 只对一条已有的**合法**观测序列，执行最小单次 native source update；尚无合法播控资产时可搭建固定输入 ROS test harness，明确不是完整原论文闭环。
- 被动抓取 native 实际解析参数、测量事件归属、hit-map完整logOdds/confidence、按消费接口解析的测量风和源模拟风、quadtree原始/细分树、每叶模拟采样位置/真实RNG状态/命中float32图/raw logscore/后验。
- 同一组固定物理输入，运行 CORE-PARITY 离线适配；逐层比对事件 → 测量图 → 两风通道 → 候选采样 → hit map → score → 最终细分posterior及MAP/rank。若RNG不可完整复演，可注入**预先捕获而与真实源无关的原生采样点序列**，声明比较的是条件核心逻辑，不是独立RNG等价。
- 旧score-only复算PASS依然有效，但不能被升级成完全P1PASS；没有online native candidate hit maps/后验就必须HOLD。
- 禁止通过调整方向/数据掩码/阈值/航迹/seed来追逐源排名，禁止重启M0和否定证据。
- 输出 `NATIVE_ONE_UPDATE_STATE_MANIFEST.json` `P1_LAYER_DIFF.csv` `CORE_PARITY_GO_NOGO.md`。

## 5. P2/P3: 当前只做准备，不无条件启动
- P1a & P1b PASS 后才考虑用作者配置 C1、合法连续气体记录和ROS导航跑完整系统；如现有C1连续记录缺失，提供最小重生预算，等待用户授权。
- P3科学问题候选不变：时变气体传播下**源—受体历史条件不一致**会否可重复损害源后验。但接口转换本身只是工程修复。以 N1 为合法基线后，按独立源/风况/realization对照真实历史时序对齐 vs 错乱历史，验证是否存在非平凡增益；无有效多案例证据则HOLD。
- 开题报告冻结版不改；科学技术路线中按研究假设表述，除非P3合格，绝不写“已证明PMFS原生失效”。

## 6. 预算与交付
本轮只运行P1a和尽可能的P1b；不生成新的CFD/GADEN数据，不下载新数据集，不训练网络；P1b受合法输入合同限制。给出PASS/HOLD/FAIL与最小缺项，不做无上限审计。

**source review**: `PMFS_CORE_PARITY_REVIEW_20261009_SMALL.zip` 和 GitHub commit `dce7b0264aa3a156b2527216898d32a912e04aa0`; 本规范是独立修订，不能把先前静态事实升级为运行历史因果。
