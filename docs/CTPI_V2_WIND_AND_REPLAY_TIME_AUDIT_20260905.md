# V2 局部风变化与回放时序审计

状态：输入前提审计完成；M1/M2 机制和闭环效用仍未通过。没有启动 House 实验。

## 新查实的证据

读取九条已花费 R4 的 `wind_trace.csv` 和 `sim_pose_trace.csv`，只按 step/time
配对，并要求相邻步相差 0.2 s、两步 `is_moving=0`、打印的 xyz 完全相同。
未读取源真值、gas 或 bank。最终口径严格限制在原契约 0–240 s，每条 1200 行。

| House | A0 定点变化对/可比对 | F00 | F01 |
|---|---:|---:|---:|
| H01 | 555/1128 | 558/1127 | 397/1121 |
| H02 | 555/1118 | 546/1108 | 559/1128 |
| H03 | 538/1086 | 469/1110 | 453/1074 |

结论仅为：打印精度下存在局部时间变化，不能把沿轨迹风变化全部当作空间效应。
这些对数不是独立样本数，不用于统计显著性或跨臂比较。坐标打印精度以下的移动
未被排除。它不证明风外生、全局场已知、源可辨识，或旧误差由风时序造成。

九条轨迹还都在 **t=189.8 s、step=949** 出现回放索引 **1997→0**，当时位置相同。
VM `sim_timebase.py` 已重新读取并确认：

```
usable = max(1, max_iteration - 1)
offset = (7919 * (seed + 1)) % usable
iteration = (offset + step) % usable
```

取 `max_iteration=1999`、seed12、dt=0.2 可准确复现日志首帧1050及该接缝。
该 max_iteration 是与日志匹配的值，本次没有重新枚举源数据载荷。
`vgr_sim_node.py::_sample_gas` 将这个索引直接传给 raw/frame query，并继续推进
同一传感器状态；没有因索引回绕而复位传感器。

**索引回绕不等于已证明浓度数值跳变**。是否为物理连续的周期场，需要场生成与
首尾接缝证据，当前没有。原始场帧间隔是否等于推进时钟 0.2 s，也尚未核实。
连续时间 M2 不能将这两项静默当作成立；新增执行前提明确要求先验证。
没有修改旧 replay、seed、起始帧、控制器或冻结结果。

## 可复现产物

- `tools/ctpi_r4_stationary_wind_audit.py`：标准库只读诊断，输出逐文件 SHA-256。
- `tools/selftest_ctpi_r4_stationary_wind_audit.py`：7 项通过，覆盖静态、时间变化、
  空间变化排除、移动标记、缺步、配对不一致和回放接缝。
- `evidence/ctpi_v2_stationary_wind_20260905/RESULT_HORIZON240_R2.json`：当前诊断。
- `RESULT.json`：首次全日志统计，包含 240 s 后尾部；保留但不是任务窗口口径。
- `RESULT_HORIZON240.json`：加入接缝检查前的 240 s 统计；保留。
- `closed_loop/ctpi/ctpi_v2_replay_preflight.py`：独立、尚未接入 launcher 的时序检查。
  不改变任何输入；即使没有 wrap，也只报告 NO_INDEX_WRAP_ONLY，不宣称物理通过。

VM timebase SHA-256：
`a104873911f23c27dba39001d1919092a5f58195f03e37f86fc76b0040c4351f`。

## 对后续行动的改变

1. 源/输运识别设计可以考虑真实局部时间变化，但不能由此冒认全场输运已知。
2. 第二次 idea-spark 候选生成仍无合格机制；选择与具体原因保留在
   `ideaspark_run/causal-source-identifiability-v2/phase2_generate/generation_blocker.json`。
   这不是 Phase 3 终审，也不是全局不可能性结论。无需再凭同一前提重复选题。
3. 下一项必要证据是现有回放的原生时钟和接缝物理语义；先读配置/生成代码，
   不重新消费 bank。若需要改实验世界或起始帧，不能以修复名义静默更换。
4. 本文没有解释全部 R4 失利，也不改变三屋单 seed 同控制器效用门槛。
