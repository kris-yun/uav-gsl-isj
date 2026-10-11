# 原始三维受体查询与默认 RNG 包装核验

本子任务判决：`PASS_INDEPENDENT_RAW_FILAMENT_RECEIVER_CONCENTRATION_RECOMPUTATION / PASS_HEADER_ONLY_DEFAULT_RNG_DRAW_PARITY`。

## 实际完成及范围

独立 Python 验证器直接解压读取审核包内392个已使用快照（8份 realization，每份49帧），按实际原生源码解析三维环境描述、点源、气体类型、mole常数、风索引与丝团向量。复算每份51个受体查询，包含block40的两个成员分支，共408个查询。没有调用新的 GADEN、ROS、导航、候选前向或输运积分。

所有392帧与原 ALL_FRAME_SHA256_AND_TIME.csv 的SHA一致。快照内几何描述与三维占据文件 float32 值和尺寸完全相同；丝团数与时间清单一致，gas_type=13、wind_index=10。受体XYZ经float32转换与原查询输入相同；查询帧、实际保存时间及下一帧时间与物理时间清单匹配，满足原生零阶保持的时间区间。

## 408次独立浓度复算结果

| 项目 | 结果 |
|---|---:|
| 受体查询数 | 408 |
| 含三维快照SHA核验 | 392/392 |
| 最大绝对浓度差 | 0 ppm |
| 最大相对差 | 0 |
| 最大float32 ULP差 | 0 |
| 0.1阈值事件分叉 | 0 |
| 原生浓度距离阈值的最小余量 | 0.00103313476 ppm |
| 进入严格3σ截止范围的丝团—受体对 | 29,827 |
| 被LOS排除的对 | 20,488 |
| 实际贡献浓度的对 | 9,339 |

声明的跨平台容差在运行前固定为 `abs_difference <= 3e-7 ppm + 5e-6 * abs(native_ppm)`。本次实际结果全部差0，并未用容差掩盖差异；这仍不意味着任意平台、任意输入都能逐位一致。最后一次验证耗时约4.48秒，冷启动首次数值验证约7.14秒；耗时不是可复算的固定算术结果。

## 保留的原生计算语义

`CalculateConcentration` 使用严格 `distanceSqr < (3*sigma/100)^2`，只累计满足 LOS 的丝团。sigma的单位是厘米；空间坐标是米，单丝团指数使用厘米距离。浓度从快照内 `totalMolesInFilament` 和 `numMolesAllGasesIncm3` 得到 ppm，不能替换成粒子计数或随意的归一化值。单丝团和最终累加按原向量顺序以 float32 进行，不使用一次高精度求和冒充原生累加。

LOS首先检查起点和终点都为三维 Free=0，然后按原生 float 距离、`steps=int(distance/cellSize)`、`increment=distance/steps` 检查i=1..steps-1。steps≤1没有中间检查。原生坐标转换是 float32 算术后向零截断成整数，不能用数学floor替代。占据CSV按z层、x行、y列读取，索引与原Environment一致。

原源码的未限定 `sqrt`/`exp` 返回double，输入表达式仍可先发生float计算，最终局部变量/返回值再转float。轻量 C++ header probe确认返回大小都是8字节，pi_cubed为float32的31.006277084350586。Python分别模拟这些转换；它没有重新拟合常数。

## 默认 RNG 包装的廉价原生核验

分别用保存的 pristine MathUtils.hpp 与隔离包装版本编译两个 header-only 程序，完全清除 M2_GAUSSIAN_SEED、M2_UNIFORM_SEED 和 M2_RNG_TRACE。固定相同的交织draw调用及 PrecalculatedGaussian<1000> 构造序列。检查1100次Gaussian调用、101次uniform调用及64个cache输出；两份stdout字节完全一致，SHA256均为 `5cd6499f98515210e8af65060d9176027cdfc9c72ab4e6fa0c5d1ecb61f91b16`。两次编译及运行共2.07秒，无libgaden Simulation调用。

这支持“未显式seed且trace关闭时，隔离初始化包装保留本次既定draw序列”。它不能证明所有seed或完整随机输运轨迹逐位相同，也不能用来宣称8份物理 realization 的统计独立性已经被随机测试证明。初始化seed、划分和实际bank身份仍依赖主合同的独立记录。

首次header probe包含不需要的 Simulation.hpp，因其serialization依赖的libbsc头路径缺失而在编译阶段停止，未运行draw或生成气体；移除该额外依赖后仅用原MathUtils/Vectors头完成。原错误日志与两个版本源码保留。

## 交付与复核入口

`verify_raw_queries.py` 提供主审核器需要的只读 `verify(root) -> result_dict`；root是完整审核包根目录。它不写QA JSON，不执行原生程序。底层 `verify_raw_receiver_queries.py` 同时返回408行逐值比较，可通过 `--out NEW_DIRECTORY` 显式输出新副本；默认只读stdout。

```
python verify_raw_queries.py --package 审核包根目录
```

原生源码从既有VM只读抓取，正文和SHA保存在source/。数值结果、408行逐值表在verification_run_02/；RNG原生对照日志与header副本在rng_header_parity_evidence/。

本验证只覆盖受体查询，未复算每份其余22,797个网格查询；查询风向量也未独立重算，仅核验快照风索引。它证明保存快照到受体浓度的数值算子血统，没有额外输运重新积分、独立CFD验证或真实实验验证，不代替源位置可辨识性、因果机制或新方法有效性的判决。
