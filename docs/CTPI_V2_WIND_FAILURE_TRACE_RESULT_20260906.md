# 最新风观测臂：失败迭代追踪归档

归档日期：2026-09-06。状态：`DIAGNOSTIC_ONLY_SAME_FAILURE_REPRODUCED`。
本文件补齐既有失败运行的分析；归档时没有启动新 House 或重新选择参数。

## 改动及运行身份

契约见 [追踪契约](CTPI_V2_WIND_FAILURE_TRACE_CONTRACT_20260905.json)。
`CTPIGmrfCheckedWindV2.hpp` 新增编译期开关 `CTPI_WIND_ITER_TRACE`，
只记录每一步的相邻/隔一步变化、未松弛固定点残差、线性残差与更新关系。
既有 0.5 松弛、0.01 停止条件、100 次上限、地图、输入和权重没有改变。
执行入口是 `tools/run_ctpi_v2_wind_failure_trace.sh`。

本地当前头文件与 VM 编译输入 SHA-256 一致：
`1dcc1c6304c80aa96c29288d2d46e35e522c9925cf7d8a0ab72fd9af21a11ac0`。
实际追踪二进制：`c5293bcee8a1a1e606569a63d0c28008e6d12b67a18908a39720ee1b874370d5`。
原日志：`34914aa1d8cb3156aa5298f8e64dc0e3756f96e326242ae68cd3371dfe62e2b5`。

## 结果与边界

仍在 step=111、t=22.2 s 达到上限，日志以
`GMRF_FIXED_POINT_DID_NOT_CONVERGE_WITHIN_RESOURCE_LIMIT` 结束。
没有 `COMPLETED.json`，不能将失败前缀记为完整预测成绩。

| 第 100 次迭代量 | 数值 |
|---|---:|
| 相邻迭代相对变化 | 0.012170057950680572 |
| 隔一步相对变化 | 0.010803493579576089 |
| 未松弛固定点残差 | 0.024314384825490844 |
| 归一化线性残差 | 2.9867619592740841e-17 |
| 原 0.5 松弛更新关系偏差 | 0 |

线性系统这一步求得很准，不等于非线性固定点已收敛。
隔一步变化没有趋近于数值零，因此记录不支持把失败简单解释为已锁定的二周期。
它也不足以判定最终必定发散或只需多迭代就会收敛；没有提高上限来救运行。

追踪版与未加追踪的失败臂以下文件逐字节相同，表明此次日志插桩没有改变这段输出：

- `predictions.csv`：`9fada9b5a9cd144430c2a941fd2ccd00cfa025e4f76354d2a4c408615df8d592`。
- `solver_audit.csv`：`f7e4c35fcc476ea0498a43f3e01f3999a38ae6a8793c543b9703fc6fb54402c3`。

完整原日志、失败臂场序列、几何、预测、数值审计与二进制保存在
`evidence/ctpi_v2_wind_failure_trace_20260906/gmrf_wind_failure_trace_v1/`。
输入风记录和导航切片补充归档到 `evidence/ctpi_v2_spent_wind_20260905/inputs/`；
它们是既有确定性诊断输入，不是新生成的 bank 或全场真值。

科研结论仍是：当前“只保留每格最新观测”的这一实现没有满足运行前提，
而不是所有动态风估计失败。此追踪不提供 M1/M2 任务收益证据。
