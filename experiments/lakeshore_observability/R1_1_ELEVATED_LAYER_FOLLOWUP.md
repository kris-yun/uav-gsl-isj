# R1.1 Follow-up: 湖风锋抬升形成的“高空源信息层”确认实验

日期：2026-10-03

## 结论背景

R1 原协议的最终判定保持 `R1_HOLD_WEAK_OR_UNSTABLE`，不回溯改判。
但完整 864 个 realization 暴露出一个此前 gate 没有专门检验的结构：

- N0/L1：10 m 可辨，30 m 及以上基本无气体命中，30 m Top-1≈11.11%；
- F1/F2：10 m 可辨，**30 m 仍保持 Top-1=100%**，且 30 m 有大量 gas hits；
- 60/100 m 再次失去信息。

这不是“湖岸让低空失效”的证据，而是一个新的、更具体的探索性信号：
**湖风锋抬升可能把源判别信息搬运到一个新的中高空可观测层。**

因此下一步不是执行 R2，而是做新的、独立 seed 的确认性 R1.1。

---

## 1. 冻结结论

1. 原 R1 判定不改：HOLD。
2. 不执行原 R2。
3. 不把“高空源信息层”写成已成立创新。
4. R1.1 必须使用全新 plume seeds 和预注册参数。
5. R1.1 若失败，停止这一具体“锋面抬升→高度可观测层”机制。

---

## 2. 本轮核心问题

Q1：F1/F2 在 30 m 出现的可辨识性，是不是在新随机实现中复现？

Q2：该信息层是否随 front 位置移动，而不是由固定代码/轨迹伪影造成？

Q3：该效应是否在较弱、仍合理的抬升强度下存在，而不是只在强 w 设置下出现？

Q4：source identity 的提升是否不仅仅来自“多了一些 hit”，而是不同 source 在高空仍保留可区分的时空结构？

---

## 3. 参数矩阵

### 高度
改为：
- 10 m
- 20 m
- 30 m
- 40 m
- 50 m

去掉 60/100 m，避免已知无信息高度浪费预算。

### front 位置
- x_front = 90 m
- x_front = 120 m
- x_front = 150 m

### 抬升强度
- W025: w_max≈0.25 m/s
- W050: w_max≈0.50 m/s
- W100: w_max≈1.00 m/s

### controls
- N0
- L1

### source/release
第一轮确认只用：
- 9 sources 全部保留；
- mid release=10 为 primary；
- low/high release 仅在 primary 通过后补做稳健性。

### seeds
使用全新 seeds：
40001–40008

不得复用 30001 系列。

---

## 4. Primary confirmatory endpoint

不再用“每个环境内部 best-worst height spread”作为主判据。

主效应改为预注册的 **environment × height interaction**：

在每个 front 位置和 w 强度下，计算：
- ΔTop1_30 = Top1(front,30m) - Top1(N0,30m)
- ΔRank_30 = medianRank(N0,30m) - medianRank(front,30m)
- ΔHit_30 = hitRate(front,30m) - hitRate(N0,30m)

Primary PASS 要求：
1. 在 W050 的至少 2/3 front positions：
   - ΔTop1_30 ≥ 50 pp；
   - ΔRank_30 ≥ 2；
2. 8 个新 seeds 中 ≥6 个方向一致；
3. 20–40 m 中存在连续至少 2 个高度 bin 显著优于 N0，而不是单个 30 m 网格点偶然峰值；
4. L1 不能复制该效应，证明“仅垂直剪切”不足。

---

## 5. Front-tracking test

对每个 x_front：
- 记录 20/30/40 m 的 gas hit centroid / peak x；
- 记录 source-identifying observation 的 x 分布；
- 检查其是否随 x_front 的 90→120→150 m 改变而平移。

定义：
`Δx_info / Δx_front`

若信息层位置与 front 完全无关，则标记 `FRONT_TRACKING_FAIL`。

不要求 1:1 平移，但至少方向一致并在 ≥2/3 source-x groups 中可观察。

---

## 6. “不只是 hit 数增加”的检验

对 F 条件在 30 m：

### 6.1 hit-count matched subsampling
在 source pair 比较时，对 hit 更多的 source/time series 做随机下采样，使不同 source 的总 hit count 相近，再重复 Brier/source-rank 评分 100 次。

若 source rank 仍明显优于 chance，说明高空信息不仅是“哪个源 hit 更多”，还包含时空位置/序列结构。

### 6.2 time-shuffle control
每个 source 保持总 hit count不变，随机打乱时间顺序，重复100次。

若真实序列 rank 显著好于 shuffled，说明时序/轨迹结构携带 source identity。

输出：
- matched-count true-source rank
- shuffled rank distribution
- empirical p / percentile（仅描述性，不包装为正式显著性推断）

---

## 7. 新判定

### `R1_1_PASS_ELEVATED_SOURCE_INFORMATION_LAYER`
必须同时：
- Primary PASS；
- front-tracking PASS；
- matched-count/time-shuffle 至少一项表明 source identity 不只是 hit 总量。

### `R1_1_HOLD_FRONT_LIFT_SIGNAL_ONLY`
30 m hit/Top1 可以复现，但：
- 仅强 w 才成立，或
- 不随 front 位置，或
- matched-count 后 source identity 消失。

### `R1_1_FAIL_STOP_ELEVATED_LAYER`
新 seeds 下 30 m 的 source-identifiability 增益不能复现。

---

## 8. R1.1 通过以后再决定方法

若 PASS，新的科学表述优先改为：

“湖风锋及其垂直抬升可使泄漏源判别信息在高度方向重新分布，形成与普通近地羽流不同的高度依赖可观测层。”

这时主动感知的合理动作不再是泛泛“升高试一下”，而是：
**根据当前证据判断源信息可能位于哪一个高度层，并用短时垂直微剖面主动确认。**

只有 R1.1 PASS 才重新设计 R2。

---

## 9. 工程输出

追加：
- `R1_1_CONFIG_FREEZE.json`
- `R1_1_MANIFEST.csv`
- `R1_1_HEIGHT_INTERACTION.csv`
- `R1_1_FRONT_TRACKING.csv`
- `R1_1_MATCHED_COUNT.csv`
- `R1_1_TIME_SHUFFLE.csv`
- `R1_1_REPORT.md`
- `R1_1_DECISION.json`
- hashes

不得覆盖原 R1 evidence。
