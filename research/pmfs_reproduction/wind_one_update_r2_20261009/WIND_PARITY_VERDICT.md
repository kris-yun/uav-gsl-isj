# PMFS 风消息/TF真实验收 R2

**P1a：HOLD。方向/位置的新鲜消息子项通过；延迟消息的TF时间一致性失败。** 本轮没有重新审计91项P0，沿用已审核的PASS。唯一合同为 `fd1fa40ea2a1ce0a7ba167b15045ed557679755e` 的R2，旧指南未执行。

## 实际运行及边界

在原已运行的 Ubuntu VM 中，通过SSH新建 `/home/zyc/pmfs_wind_one_update_r2_20261009`，使用 ROS Humble、ROS_DOMAIN_ID=73、localhost通信、单线程计算。任务没有启动或关闭VM，没有启动导航、CFD、DNS、Docker、GADEN气体生成或训练。测试子进程已退出；现有VM保留。启动时可用内存约1205MiB，未扩大内存或场景。

PMFS测试程序是受控 `Algorithm` 子类，直接编译固定 `4e141e1` 的原始 `Algorithm.cpp` 与 `StopAndMeasureState.cpp`，由真实DDS订阅调用原风回调，保存实际窗口的平均风。fixture每个单消息用例重置测量窗口；未调用完整GSL actionserver或PMFS概率图更新。GMRF使用固定 `2ec7a5d` 的原节点，仅在原始insert之后增加被动CSV记录，通过核心公开访问器读实际已存观测、格索引、中心和向量；核心map源与固定Git对象相同，已有共享库哈希冻结，未声明完整clean-build二进制复现。

N0只做“未经转换的FROM消息给两端”的接口探针，保留原消费者，不冒充作者完整原样launch。N1在两个话题分别提供TO/FROM、真实sensor帧和同一stamp。两个位置为(1.25,1.25)、(-1.75,2.25)m，姿态分别0°和90°；在每处测试四向单位风与零速。这里是人为已知的接口物理输入，不是新增气体实验或定位样本。

真实ROS传输录存于 `evidence/real_ros/results/ROS_WIRE_MESSAGES.jsonl`（接收时间、类型与CDR序列化字节），两端消费者原始CSV和GMRF日志均保留。阈值在运行前固定：角度<1e-4 rad、位置<0.01m；零速角度无物理定义，按速度和向量核验。额外时钟年龄门2s也在运行前声明，不用于源排名筛选。

## 结果

| 子项 | 结果 | 实际证据 |
|---|---|---|
| N1四向×两位置 | PASS | 8个非零用例，PMFS平均方向最大误差1.63e-07rad，GMRF最大2.7e-06rad |
| GMRF实际观测位置/格点 | PASS | 最大位置误差0m，实际格索引252/286，中心恰为两处预设位置 |
| 两个零速用例 | PASS于接口 | 速度及已存向量为0，不强求两端零速方向角一致 |
| N1新鲜消息时钟 | PASS于本fixture | 两消费者回调实读use_sim_time=false；消息stamp与系统时间相容，最大消费年龄0.294s |
| map帧旧提案 | 预期负对照成立 | GMRF将实际观测存于(0,0)，落格210/中心(0.25,0.25)，而真实位置(1.25,1.25) |
| N0共享FROM输入 | 预期反向成立 | PMFS约π、GMRF约0；不是原论文历史行为的因果认定 |
| 混合时钟负对照 | 不合格 | fixture模拟时钟消息stamp=100s、消费者系统now约1.79e9s；TF查找和插入仍成功，不能以“没报错”证明时钟兼容 |
| 延迟消息+随后90°旋转 | FAIL于时间一致性 | PMFS取最新TF，GMRF取消息stamp的TF，消费者方向差1.570798937rad≈90° |
| GMRF估计场精度 | HOLD | 查询实际WindEstimation值；有限等待时非零速度约0.50–0.875m/s，未确立收敛或精度资格，不等同已存观测向量真值 |

## 新的时间合同缺环

延迟用例先在t1发布传感器位姿(1.25,1.25,0°)，之后在t2=t1+0.2054145s发布(-1.75,2.25,90°)，再发送带t1 stamp的同一物理风。

原PMFS回调只拷贝 `header.frame_id`，没有拷贝stamp，新PoseStamped的零stamp让TF取最新t2；返回风姿态与测量窗口平均风为90°。GMRF拷贝整个header并按t1 lookup，平均吹向约0°，实际观测仍落(1.25,1.25)。这次回调差异是**真实ROS下的时间语义反例**，不是静态公式推演。

PMFS返回姿态的x/y不是本轮已经观察的PMFS机器人定位或命中图测量格；fixture未运行机器人定位与命中图更新，不扩大该证据结论。也不能把它自动认定为旧H02失败根因或定位收益。

因此，本轮消除了新鲜且TF稳定消息的方向/位置歧义，但没有关闭任意移动/延迟消息的时间合同。固定版本还不能被认定为完整P1a通过，**按用户顺序不执行P1b**。不临时改原生回调或偷偷把timestamp修补并入N1。

最小后续缺项是一项明确的时间策略：若坚持核心不改，须限定停留采样且验证从采样到消费之间TF稳定、时钟同域，并由外部接口按事前规则拒绝迟到消息；任意运动中带历史stamp的输入需要允许明确版本化的时间戳修正对照。当前这两种进一步修正均未执行，不改数据掩码、阈值、源位置或随机种子追求排名。

源码依据：[PMFS共同回调](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/Common/Algorithm.cpp)、[GMRF回调](https://github.com/MAPIRlab/GMRF-wind/blob/2ec7a5db7bf5f2597e9d62ba662d3efcfc788d71/gmrf_wind_mapping/src/gmrf_node.cpp)。本轮仅保留工程接口结论，科学机制仍UNRESOLVED。
