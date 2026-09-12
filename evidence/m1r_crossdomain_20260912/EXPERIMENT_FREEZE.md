# H03 seed12：先上传冻结，再做固定源位置小实验

日期：2026-09-12。冻结状态：实验前规格，尚无本轮结果。

目标是快速检验历史 M1R 退化 House 的一个明确代码修复，不扫描其他 House 或 seed，不预设因果创新成立。历史 2/3 指 H01/H02 的末次源 MAP 误差下降，H03 末次误差退化；不是 2/3 找到源。

## 证据、理论与实现

1. [因果目标与失败证据](../../docs/PMFS_M1R_CAUSAL_GOAL_AND_SHORTEST_PATH_20260912.md)及此前冻结的 `evidence/m1r_causal_repair_20260912/` 保持原判决。
2. [推导](SOURCE_COHERENCE_DERIVATION.md)：固定未知源的位置必须在一次完整模拟中共享，位置积分放在整段事件证据乘积之外。旧区域源每次释放气丝重新取位置，模拟的是分布式发射。修复包含固定位置 forward 与完整前缀位置混合两个必要环节。
3. [文献索引](REFERENCE_INDEX.json)关联生物、物理、地球科学原文与本地逐篇核验；不把跨域类比写成可直接移植的定理。六篇正式 2026 文献中一篇 Nature Physics、五篇 Nature Communications，清楚区分期刊。普通潜变量边缘化和本项目旧固定 U 方法都不是本轮新颖性。
4. 核心开关 `m1r_source_quadrature_enabled` 默认 false，仅允许历史 rolling M1R；`Simulations::configureM1RSourceQuadrature` 检查配置。四点 `(.25,.25),(.25,.75),(.75,.25),(.75,.75)` 各占 1/4，点在完整 warmup+recording 内保持固定。U 与 transport K 分开，K=1 不变。
5. 每个 U 分别使用原 scorer 评分完整前缀，再做普通算术混合。context 先在每个首层区域中平均 U，再在首层区域中平均；同次更新所有细化子叶复用该 context。原 legacy hit map 继续进入原 planner 方差公式，新源权重自然改变方差和路线。

## 严格限定的两次运行

| 条件 | BASELINE | FIXED_SOURCE |
|---|---|---|
| House / algorithm seed / sensor seed | H03 / 12 / 12 | H03 / 12 / 12 |
| simulated time budget | 240 s | 240 s |
| 模式 | cer_ratio_m1，历史 rolling persistence | 相同 |
| 新开关 | false | true |
| 每区域 forward | 1 legacy | 1 legacy + 4 fixed point |
| 源更新步数 / warmup max,min | 3 / 3,1 | 相同 |
| 二进制、数据实现、地图、起点、传感器、planner 参数 | 两臂相同 | 两臂相同 |

运行顺序固定 baseline 后 fixed_source，分别保存新目录。仅使用现有 H03 数据，不生成或重建 bank；不触碰旧结果和旧 build。源真值只由模拟环境与离线评价器使用，四点支持、参数及在线模块不得依据真值选择。

两臂计算预算不匹配；必须并列记录源更新时间、更新次数及 forward 次数。初筛不能分离固定源身份、几何积分点、多次模拟与 context 改变的独立贡献，也不能由相同 seed 宣称精确时钟或轨迹重放。

## 实验前固定的判据

- 有效性：两臂配置、代码和二进制身份匹配；唯一算法开关不同；均到达 `time_budget_timeout`；有效源 MAP 轨迹首条时间 ≤10 s、末条 ≥230 s，至少一次完整源更新，后验和为 1。异常退出/覆盖不足判 `INVALID_PAIR`，不能当作方法退化或成功。
- 主指标：有效轨迹末次源 MAP 到真源的平面距离，fixed_source 必须严格更小（差值 < -1e-6 m）。
- 共同主指标：在两臂有效源轨迹的共同时间区间，按时间戳并集分段线性积分位置误差；fixed_source 必须严格更小（差值 < -1e-6 m·s）。不补齐 0 或 240 s，不删不利时间窗。
- 两者同时改善，且点级评分复算、配置及源位置支持核验通过，才记 `DEVELOPMENT_SCREEN_PASS_NOT_MAIN_INNOVATION`。任一效用指标不改善，判 `NO_GO_NO_WEIGHT_TUNING_NO_HOUSE_SWEEP`。不因接近阈值调整权重、积分点、House、seed 或评价窗。
- 源真值所在格后验质量、排名及点级似然作为机制诊断，不作为额外挑选有利结果的替代指标；本轮不据此声称校准后验或识别了因果效应。

评价实现：[evaluate_m1r_h03_source_quadrature_pair.py](../../tools/evaluate_m1r_h03_source_quadrature_pair.py)。点级组件日志单独核验，不能用旧 U 均值 map 的 evaluator 复算新似然。公式玩具反例仅检验概率语义，不代替真实实验。

## 上传与追溯顺序

1. 冻结此文件、文献索引及检索原始记录、数学推导、核心代码、开关接线、运行和评价脚本；生成 `PRE_RUN_MANIFEST.json` 列出文件 SHA256。
2. 提交到独立 `codex/m1r-causal-repair-20260912` 分支并 push 到 origin。VM 用 `git ls-remote` 检查完整冻结 commit 确实已上传，才可开始实验。
3. 在新的 `/dev/shm` build 中构建，保存源码、编译和二进制哈希、派生 preflight 与每臂启动 manifest；两臂共用同一二进制。若遇到构建/接线错误，修复、重新冻结并上传，再重新验证运行身份。
4. 实验后保留两臂原始日志、评价结果及失败原因，另一次提交并上传。上传实验前规格不是实验成功；运行后的真实判决写入独立结果文件。

无论这次结果如何，2026 跨域文献没有替本方法证明跨 House 泛化。H03 单个既有 seed 的成功最多允许下一阶段研究，主创新、H01/H02 是否受损及跨数据集有效性仍待独立验证。
