# CODEX MASTER PROMPT — JTD-G0

你现在执行 **JTD-G0：联合时序依赖离线机制 Gate**。

## 0. 任务目标

不要提出新算法。不要跑闭环。

只回答：

> 在 R0 已经验证稳定的 source-conditioned encounter/support 数据中，跨时间块的 joint dependence 是否含有超出各时间块边缘分布的增量 source information？

核心 destructive null：

- FULL：保留同一 independent plume realization 的时间块对应。
- SHUFFLED：在同一 source 内打乱 block-to-realization correspondence，保持每个 block 的所有边缘样本、均值、方差和分布不变。

如果破坏跨块对应关系后 source evidence 基本不变，STOP。

---

## 1. Git / provenance

先检查：

- 是否存在 commit `e527beea07c33cdbc362d156545409245f029968`
- 是否能找到 `R0_PASS_STOCHASTIC_BENCHMARK_USABLE`
- 是否能找到 R0 使用的原始/导出 benchmark arrays
- 是否确实是 18 sources × 16 independent full realizations/source
- 是否能明确恢复时间轴与 query/probe 轴
- 是否有 realization IDs / seeds / hashes 足以证明独立重复，而非 pseudoreplicates

若任一项不满足：

1. 不修数据；
2. 不合成数据；
3. 不猜 shape；
4. 输出 `JTD_G0_STOP_INPUT_CONTRACT_INVALID`；
5. 报告缺什么；
6. 停止。

从 R0 PASS commit 创建新 branch/worktree：

`research/joint-temporal-dependence-gate-20260925`

保留旧 evidence 只读。

---

## 2. A0：数据审计

期望的 R0 语义 contract 是：

- 18 source labels；
- 每 source 16 independent full realizations；
- 每个 realization 对应完整的 ordered observation object；
- 旧审计描述为 10 × 30 = 300 维 ordered observation/support object。

**必须从真实文件与元数据验证，而不是因为本 prompt 写了 10×30 就强行 reshape。**

如果真实导出确实是 flattened 300，但缺少能证明 10×30 顺序的元数据，STOP。

生成：

`evidence/jtd_g0_20260925/audit/R0_INPUT_AUDIT.json`  
`evidence/jtd_g0_20260925/audit/R0_INPUT_AUDIT.md`

至少记录：

- base commit
- input paths
- SHA256
- source IDs
- source coordinates（若存在，仅用于最终评价）
- realization IDs / seeds
- tensor shape
- time ordering
- query/probe ordering
- observable name
- NaN / Inf
- duplicates / identical-realization audit
- whether all sources have exactly 16 full realizations

将真实数据无损规范化为：

`evidence/jtd_g0_20260925/cache/canonical_r0.npz`

schema 见 `01_INPUT_AND_PROVENANCE_CONTRACT.md`。

---

## 3. 预注册模型：不要根据结果修改

### 3.1 时间分块

PRIMARY：

- T 必须等于 10；
- B = 5 contiguous blocks；
- 每 block = 2 consecutive time slices。

即：

- b0 = t0,t1
- b1 = t2,t3
- b2 = t4,t5
- b3 = t6,t7
- b4 = t8,t9

不做滑窗。

若真实 T != 10，先 STOP INPUT CONTRACT INVALID，不自动改 B。

### 3.2 每个 block 的无监督压缩

对每个 CV fold：

1. 只用 reference realizations；
2. 对每个 block 将该 block 内所有 probe/channel 维 flatten；
3. pooled across all sources；
4. 仅 training/reference 数据做标准化；
5. 每个 block 单独 fit PCA；
6. 固定 `q = 2 PCs/block`；
7. FULL 和所有 SHUFFLED null 共用同一个 scaler + PCA。

于是每个 realization 得到：

`z = [PC1_b0, PC2_b0, ..., PC1_b4, PC2_b4]`

维度 d = 10。

若某 block 有不足 2 个非零方差维度，记录并 STOP_INPUT_CONTRACT_INVALID，不偷偷换特征。

### 3.3 4-fold realization CV

realization index 按 R0 冻结顺序 0..15。

四个 eval folds：

- F0: {0,4,8,12}
- F1: {1,5,9,13}
- F2: {2,6,10,14}
- F3: {3,7,11,15}

每折：

- eval = 4/source
- reference = remaining 12/source

每个 realization 在该 CV scheme 中只作为 eval 一次。

这是 discovery CV，不是 fresh external confirmation。

### 3.4 FULL source likelihood

对每个 source，使用其 12 个 reference z 向量：

- source mean；
- source-specific full covariance；
- 使用 OAS shrinkage（优先 sklearn.covariance.OAS）；
- 加极小 numerical jitter 只为稳定矩阵，不允许调到改变结果。

source likelihood：

`log p(z | source=s)` = multivariate Gaussian logpdf.

source prior 固定 uniform over 18 sources。

posterior 用 log-sum-exp 归一化。

注意：

- 这是 Gate 的普通工作模型，不是创新；
- 不进行 temperature calibration；
- 不调 prior；
- 不加入 source coordinate；
- 不用 truth source 做超参选择。

### 3.5 SHUFFLED destructive null

每个 fold 生成 `N_SHUFFLE = 200` 个 null models。

在每个 source 内：

- block b0 保持原 realization pairing，作为 anchor；
- 对 b1..b4 的 12 个 reference realization indices 分别做独立 derangement；
- 不跨 source 打乱；
- 不改变 block 内任何数据；
- 不改变每个 block 的样本集合；
- 不改变 scaler/PCA；
- 不改变 eval targets；
- 每个 shuffle replicate 重新估计 source-specific OAS covariance；
- source mean 理论上应与 FULL 相同（允许数值误差），必须审计。

SHUFFLED 只破坏：

**cross-block realization identity / dependence**。

它不得破坏：

- block marginals；
- source labels；
- per-block distribution；
- target data；
- candidate priors。

所有 shuffle RNG seeds 写进 manifest。

---

## 4. 主指标和 Gate

PRIMARY endpoint：

`mean held-out truth-source NLL`

每个 target：

`NLL = -log posterior(true_source)`

FULL 产生一个值。  
200 个 SHUFFLED null 每个产生一个对应值。

SECONDARY：

- truth-source rank
- top-1
- top-3
- posterior(true)
- MAP spatial error（仅 source coordinate 可用时）
- per-source confusion
- per-source paired ΔNLL

统计独立单位：

**full independent plume realization/task**。

不把 300 entries 当 n=300。

详细 Gate 见 `03_METRICS_AND_DECISION_GATE.md`。

---

## 5. 结果解释边界

即使 GO，也只能说：

> 在当前 18-source R0 discovery panel、冻结的 observation protocol 和普通 likelihood model 下，保留跨块 realization dependence 提供了可重复的增量 source evidence signal。

不能说：

- 已经证明完整 plume path distribution 可辨识；
- 已经证明 ≥143-source dense candidate ranking 会改善；
- 已经证明真实 VOC UAV 数据有该机制；
- 已经有论文主创新；
- 已经完成 2026 remote-field theory transfer。

GO 后必须停止，等待负责人决定 fresh dense confirmation。

---

## 6. 禁止 rescue

如果结果失败：

- 不改 B；
- 不增加 PCA components；
- 不换 neural sequence model；
- 不删“坏 source”；
- 不调 shrinkage；
- 不提高/降低 encounter threshold；
- 不从 raw ppm 换另一套 observable；
- 不换 source subset；
- 不引入 source coordinates；
- 不追加 seeds 直到负责人裁决。

失败就是有价值结论。

---

## 7. 最终回报必须给出

1. branch
2. base commit
3. final commit
4. exact decision label
5. input audit PASS/FAIL
6. n_sources
7. n_realizations/source
8. FULL mean NLL
9. median SHUFFLED mean NLL
10. relative NLL improvement
11. empirical null p-value
12. four-fold ΔNLL
13. positive-source count / 18
14. FULL vs null median truth rank
15. FULL vs null top-3
16. leave-one-source-out sign stability
17. evidence directory
18. ZIP path + SHA256
19. explicit statement that no closed loop / no dense expansion was run

不要只回“完成了”。
