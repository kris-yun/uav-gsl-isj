# JTD-G0：联合时序依赖离线机制 Gate（Codex 执行包）

**日期：2026-09-25**  
**任务性质：机制 falsification / discovery gate，不是闭环实验，不是最终论文确认实验。**

## 你现在只做一件事

检验已经通过 R0 的 18-source × 16-realization stochastic benchmark 中：

> 在保留每个时间块自身分布不变的前提下，**跨时间块属于同一次 plume realization 的对应关系**，是否提供了额外的源位置判别信息。

比较两臂：

- **FULL**：保留同一次 independent realization 的 5 个时间块对应关系。
- **SHUFFLED NULL**：块内数据完全不改，只在同一个 source 内打乱不同时间块的 realization 对应关系，破坏跨块依赖。

如果 FULL 与 SHUFFLED 在独立 held-out realizations 上几乎没有差异，则立即停止“联合时序依赖是核心遗漏信息”的主张。

## 已有证据边界

R0 已正式通过：

`R0_PASS_STOCHASTIC_BENCHMARK_USABLE`

历史记录给出的基线锚点：

- branch: `research/stochastic-benchmark-refoundation-20260924`
- commit: `e527beea07c33cdbc362d156545409245f029968`

执行前必须在本地核实 commit、R0 PASS 报告和实际数据都存在。不存在时不得用别的数据替代，不得生成 synthetic fallback。

R0 已支持的是 **source-conditioned encounter/support 的边际稳定性**。  
R0 **没有确认**完整 300 维 path distribution，也没有确认 higher-order temporal dependence。

## 新分支

建议：

`research/joint-temporal-dependence-gate-20260925`

绝对不要改写原 R0 evidence。

## 绝对非目标

本轮禁止：

- 闭环；
- ROS/PMFS 在线集成；
- 新主动规划；
- 新神经网络；
- world model / causal model / biorthogonal / adjoint；
- 新增 House；
- 扩到 ≥143 sources；
- 新生成大规模 plume bank；
- 用 truth coordinate 调参；
- 根据结果改 block 数、PCA 维数、阈值或 Gate；
- 把 1 Hz / time points 当独立样本；
- 把 SHUFFLED pseudo-realizations 当独立 plume samples；
- 把 18-source discovery 结果写成论文级 confirmation。

## 执行顺序

1. 读 `CODEX_MASTER_PROMPT.md`
2. 读 `01_INPUT_AND_PROVENANCE_CONTRACT.md`
3. 完成 A0 data audit
4. 读 `02_EXPERIMENT_SPEC.md`
5. 实现 FULL / SHUFFLED
6. 读 `03_METRICS_AND_DECISION_GATE.md`
7. 输出 evidence
8. 运行 `scripts/validate_evidence.py`
9. 写最终 decision
10. **到此停止**

结果只有四种：

- `JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL`
- `JTD_G0_HOLD_WEAK_OR_UNSTABLE_SIGNAL`
- `JTD_G0_STOP_NO_INCREMENTAL_TEMPORAL_SIGNAL`
- `JTD_G0_STOP_INPUT_CONTRACT_INVALID`

GO 也不授权自动扩样。必须先回报用户。
