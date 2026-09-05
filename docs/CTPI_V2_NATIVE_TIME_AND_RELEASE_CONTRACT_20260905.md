# 原生时间与源释放契约：查实配置、实现显式双时钟

状态：`DECLARED_METADATA_AND_DUAL_CLOCK_UNIT_PASS`。不是 M1/M2 机制资格或闭环收益 PASS。

## 配置证据及其边界

由三屋 R4 的 `formal_runtime_manifest.json` 选择对应配置，而非挑选有利配置：
H01=`2,4-1_fast`，H02=`3,5-1_fast`，H03=`1-2,5_fast`。
读取 VM `/mnt/hgfs/workspace/GADEN_files/scenarios/House0*/launch/<config>/GADEN_ros2.launch`。
三份文件均声明：

| 属性 | 声明 |
|---|---:|
| sim_time | 1000 s |
| time_step | 0.1 s |
| results_time_step | 0.5 s |
| results_min_time | 0 s |
| wind_time_step | 1 s |
| variable_rate | true |
| num_filaments_sec | 7 |
| allow_looping / loop_from_step / loop_to_step | true / 1 / 10 |

`variable_rate` 的配置注释说明释放数具有随机性，但本次没有核实生成旧数据的
确切随机释放实现。因此不能将 7 直接作为 M1 已知源强、推定独立均匀分布、
或将未知源强降为单一恒定幅值。当前安装的新版模拟器不等于原数据生成程序。

这些 launch 文件目前没有与历史快照生成过程的不可变清单绑定；字段值是
**配置声明**，不是实际快照时间戳的最终证明。1000 s / 0.5 s 与约 2000 帧相容，
但相容不是生成身份验证。未读取浓度/风载荷或受保护 bank。
H01 所选 gas 结果目录的限定元数据文件检查没有找到独立 sidecar；不推断其他位置不存在。

旧运行日志已直接确认三屋 `max_iteration=1999`，因此上轮用索引推得的值
现在有日志支持。旧 sim 的一帧/0.2 s 与配置声明的一帧/0.5 s 不同。
**若配置绑定成立**，原生场时钟与传感器时钟之比为 2.5；此数不是拟合参数。
风序列 allow_looping 也不证明积累的气场首尾周期连续；189.8 s 接缝仍未物理合格。

## 已实现的模型改进

新增 `CTPIDualClockV2.hpp`，不修改旧核心、旧算法或冻结结果：

- `DualClock` 显式接收原生帧初始索引、原生帧间隔、传感器间隔，无 2.5 隐含默认值。
- `ClockedHypothesis` 将条件源假设的输运场按原生时间推进，再按传感器时间执行 FOPDT。
- 初始气场必须显式提供；每一步的源率以“每原生秒”为单位显式提供，可随时间变化。
- 未来才可用的风、原生帧缺口/回绕、传感器跳帧、非法输入均拒绝。
- 先在副本上推进再提交；拒绝输入不留下部分推进的气场或传感器状态。
- 这是单个条件假设的预测器，不是源位置估计器、先验选择器或新因果贡献。
  真实在线全场风、初场和源率分布仍未提供，不能直接用于闭环。

两个时钟的连续段计算为：

```
C_next = Transport(C, wind_available_before_prediction, source_rate, native_dt)
predicted_sensor = FOPDT(C_next[pose], sensor_dt)
```

没有修改回放起点、seed、时间间隔或用模拟器隐藏真值构造预测。
若现有回放的物理语义需要改变，必须另行明确实验契约，不能静默改世界来救 gate。

## 实际验证

VM C++17、O2、Wall/Wextra/Werror 编译和运行通过；本地/VM 三份源文件 SHA-256 匹配。
`tools/selftest_ctpi_v2_dual_clock.cpp` 检查：

1. 单格守恒、20 步、交替源率 1/2 的代数例子：原生 dt=0.5 得 15，误用 dt=0.2 得 6。
2. 对同一输入场序列，传感器 dt=0.2 的预测 9.4615767712765404，
   误用 dt=0.5 为 12.809157312873683；这是与既有 FOPDT 的组合时钟对照，
   不是独立重做传感器物理校准。
3. 三格纯平流，速度 2、dx=1：原生 0.5 s 将脉冲移动整格；误用 0.2 s 仅转移 0.4。
4. 相同时钟模式与原数值核心和传感器的逐步组合一致。
5. 接缝、缺步、未来风、畸形风场、修改过的时钟步均被拒绝；拒绝后正确下一步仍可执行。

原始数值及代码哈希：`evidence/ctpi_v2_dual_clock_20260905/RESULT.json`。
三屋配置白名单及哈希：`evidence/ctpi_v2_generation_metadata_20260905/RESULT.json`。
可复用采集脚本：`tools/ctpi_v2_generation_metadata_audit.py`。

## 当前尚需解决

- M1 必须有针对时间变化源率的明确假设和证伪；配置声明不提供已知源率轨迹。
- 回放首尾连续性、原生时间绑定、初场和全局输运不确定性仍待资格验证。
- 双时钟核心尚未与完整 M1/ROS 控制链连接；没有运行新 House screen。
- 以上问题不是全部 R4 失利的已证根因；也不能凭单位测试宣称任务收益。
