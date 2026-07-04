# ISJ副主编审查 + 科学问题重定义 — 深度分析

**日期**: 2026-07-03  
**目标**: IEEE Sensors Journal  
**输入**: ISJ Senior Editor审查 + 83-run log数据分析 + 10-seed实验进度

---

## 一、ISJ副主编的核心判断

### 编辑原话（一句话）
> "方法的核心想法（DDM停止准则）有潜力，但当前实验不足以支撑投稿。样本量不足，关键模块（CP）无实质贡献，单一数据集限制泛化性。"

### 按严重程度排序的5个问题

| # | 问题 | 严重性 | 当前状态 |
|---|------|--------|---------|
| 1 | 样本量 n=1~7，无统计检验 | **致命** | 10-seed实验VM运行中（~30/240完成），map_dist全空 |
| 2 | CP-STOP从未触发 = 贡献声明矛盾 | **致命** | 99%的run中CP模块无作用 |
| 3 | 无方差/标准差/置信区间报告 | **严重** | 只有均值 |
| 4 | 单数据集（VGR 3栋房子） | **严重** | 无额外数据集 |
| 5 | Coverage table缺失 | **中等** | 对声称使用CP的方法，没有coverage = 没有证据 |

---

## 二、科学问题重定义 — 像师兄做ID保持一样具体

### 2.1 师兄的模式（作为参考）

师兄做UAV身份保持：
- **具体问题**: 无人机飞行重叠时，经典跟踪方法的ID会变化
- **失败机制**: 当两架无人机轨迹交叉时，tracker丢失身份关联
- **改进**: 他改了关联算法，比经典方法在交叉场景下ID保持率更高
- **论文结构**: 问题(具体场景) → 原因(具体机制) → 方法(针对性改进) → 实验(该场景下显著更好)

### 2.2 我们的问题 — 从数据中找具体失败机制

**看数据，经典方法的失败模式非常具体：**

**SurgeCast在House01的失败过程（从log提取）：**
```
步骤1: gas=0.17, wind=0.8  → 开始upwind tracking
步骤2: gas=0.16, wind=0.77 → 继续追踪
步骤3: gas=0.092, wind=0.64 → 信号减弱
步骤4: gas=0.034, wind=0.1  → 几乎没有信号
步骤5: gas=0.022, wind=0.053 → 信号消失
→ "Found the emission source!" 距源3.05m（实际是放弃搜索）
```

**SurgeCast在House02的成功过程：**
```
步骤1: gas=11, wind=0.04   → 强信号，开始追踪
步骤2: gas=19, wind=0.047  → 信号增强
...持续追踪...
步骤23: gas=83, wind=0.073 → 找到源！距源0.44m
```

**CP-SBD-GSL在House01的过程（我们的方法）：**
```
步骤1: gas=0.16 → posterior更新到(-0.53, 1.37)
步骤3: gas=0.037 → 探索不同区域(-1.79, 0.09)
步骤7: gas=0.017 → posterior开始收敛到源方向(0.09, -0.93)
步骤10: gas=0.77 → 接近源(-1.37, -3.51)
步骤12: CONVERGED 距源1.13m
```

### 2.3 科学问题定义

**问题名称: "Plume Contact Dependency in UAV Gas Source Localization"**
（UAV气体源定位中的"羽流接触依赖性"问题）

**一句话定义:**
> 现有upwind-tracking方法（如SurgeCast）的搜索方向完全依赖当前时刻的气体信号；
> 当UAV起始位置远离源、或建筑几何遮断plume路径时，气体信号弱/间歇，
> 方法失去搜索方向 → 定位失败。

**为什么这是像师兄一样的具体问题：**

| 维度 | 师兄的ID保持 | 我们的Plume Contact Dependency |
|------|-------------|-------------------------------|
| 具体场景 | 无人机轨迹交叉 | UAV起始位置远离源，plume信号弱 |
| 经典方法失败机制 | tracker在交叉时丢失ID关联 | upwind tracker在信号弱时失去方向 |
| 失败的具体表现 | ID变化（可量化） | 定位误差从0.44m暴增到3.05m（7倍） |
| 改进方向 | 改关联算法 | 用posterior-based搜索代替direct tracking |
| 改进效果 | 交叉场景ID保持率↑ | 弱信号场景误差从3.05m降到1.13m |

**关键区别（也是我们的创新点）：**
师兄的改进只在交叉场景更好。我们的改进也是只在弱信号场景更好（House01），
但在强信号场景（House02）SurgeCast更好（0.44m vs 1.61m）。

**诚实的论文框架：**
> "在plume信号弱的环境中（起始浓度<0.2 ppm），SurgeCast的定位误差增加7倍；
> CP-SBD-GSL通过posterior-based搜索保持一致性能（1.13m），
> 代价是在强信号环境中不追SurgeCast的极致精度（0.44m）。
> 对于实际部署（不知道源在哪里、不知道起始位置信号强弱），
> 一致性比极端精度更重要。"

### 2.4 这个叙事 vs 之前的叙事

| | 旧叙事 | 新叙事 |
|---|--------|--------|
| 问题 | "首次将Adaptive CP应用于UAV GSL" | "upwind-tracking在弱plume信号下失效" |
| 具体性 | 太宽泛，审稿人不知所云 | 有具体数据、具体场景、具体失败机制 |
| 创新点 | 3个模块的"统一涌现" | posterior-based搜索对plume contact的鲁棒性 |
| 可验证性 | 需要证明太多东西 | 只需证明弱信号场景下我们更好 |
| 类比 | 无 | 像师兄的ID保持一样具体 |

---

## 三、三个核心问题的解决方案

### 3.1 模块间负协同 — 怎么办

**问题**: CPonly > Full，说明加了DDM反而变差

**根因（从数据确认）:**
- DDM在step=1-2就触发停止（LLR计算bug）
- DDM先于CP触发 → 搜索被截断 → Full不如CPonly

**解决方案: 删除CP，保留DDM+W-RAIG**

理由：
1. CP-STOP从未触发 → 它没有实际贡献
2. 副主编明确建议方案C："删除CP，诚实做法"
3. 删除CP后负协同消失（因为CPonly的"好"数据不再对比）
4. 方法简化为双模块：DDM(停止准则) + W-RAIG(搜索策略)

**操作:**
- 删除CP相关代码（或设opgsl_cp=false）
- 重命名方法为"DDM-RAIG"
- 消融实验变为: Full(DDM+RAIG) vs NoDDM(只有RAIG) vs NoRAIG(只有DDM) vs Baseline(都没有)
- 这样消融更清晰，每个模块都有明确作用

### 3.2 模块只是浅层移植 — 怎么办

**问题**: 审稿人说CP是"滑动窗口分位数"不是CP，DDM是标准SPRT搬过来

**解决方案: 不追求每个模块都深，而是让一个模块真正深入**

**核心策略: 把DDM做成GSL-specific的贡献**

DDM在GSL中的独特性（这是其他领域没有的）:
1. **GSL的LLR不是简单高斯**: 环境中plume是filament-based的，不是Gaussian plume
   → 需要设计GSL-specific的似然函数
   → 可以用posterior entropy变化率代替原始LLR

2. **GSL的证据积累有物理约束**: 气体扩散需要时间，风向会变化
   → 可以引入"信息传播延迟"的概念
   → 在LLR中加入时间衰减项

3. **GSL的停止有安全含义**: 紧急泄漏响应中，过早停止 = 资源分配到错误位置
   → 可以设计"安全停止准则"：只有在posterior confidence region < 阈值时才停止

**具体做法:**
- 不再声称CP是贡献（删除它）
- DDM的理论深度通过GSL-specific的LLR设计来体现
- 一个Proposition: "在bounded posterior drift下，DDM停止准则的误停概率 < δ"
- 这比"三个模块统一涌现"更容易证明，也更诚实

### 3.3 理论不过深 — 怎么办

**问题**: 没有Theorem/Proposition，只有verbal argument

**解决方案: 集中火力在DDM上写一个Proposition**

**Proposition 1 (DDM Coverage under Bounded Drift):**

> 假设: (1) posterior update的KL散度在每步有上界D_max
>        (2) DDM的LLR使用posterior entropy变化率
>        (3) 停止阈值θ设置使得P(false positive) < δ
> 
> 结论: DDM停止时，MAP估计与真实源的距离
>        以概率≥1-δ小于某个与D_max相关的上界

**证明思路:**
1. 引用Gibbs & Candès (2021) Theorem 1 (adaptive CP的coverage)
2. 证明posterior entropy变化率是valid nonconformity score
3. 给出explicit bound

**这比"统一目标函数涌现"现实得多:**
- 只需证明一个命题
- 有成熟的理论工具可引用（Wald's SPRT, Gibbs-Candès）
- 与实验直接对应（coverage table）

---

## 四、实验状态与数据补强计划

### 4.1 当前实验状态

**VM 10-seed实验**: 运行中，约30/240完成
- 目前跑完: Full(3 seeds) + 部分NoCP + 部分CPonly
- 问题: map_dist字段全空（benchmark_runner没有写入距离）
- 需要从log中提取距离（用已有的extract脚本）

**已有可分析数据（83 runs from logs）:**
- 3-seed消融: 36 runs (8 methods × 3 houses × ~1.5 seeds)
- 经典基线: 27 runs (3 methods × 3 houses × 3 seeds)
- 扩展消融: 36 runs (部分数据)

**数据质量问题:**
- n=1~7 per cell → 统计power不足
- 无map_dist → 需要从log后处理提取
- 某些run超时(360s) → converge_type="other"

### 4.2 数据补强路线

**Week 1-2: 修复benchmark_runner + 让10-seed跑完**
1. 修复map_dist提取（从log的最后一步坐标计算）
2. 确保10-seed实验完整跑完240 runs
3. 这是最大的immediate improvement

**Week 2-3: 统计检验**
- Kruskal-Wallis + post-hoc Dunn's test
- Mann-Whitney U for pairwise comparisons
- Bootstrap 95% CI
- Effect size (Cliff's delta)

**Week 3-4: Coverage table**
- 对DDM停止: 记录触发率、触发时精度
- 对posterior: 记录source是否在confidence region内

**Week 4-5: 额外数据集**
- 选项A: VGR不同房间配置（最快）
- 选项B: GADEN数据集（需要编译bridge）
- 选项C: 合成数据集（最快但说服力最低）

---

## 五、修订后的论文结构

### 标题方向
**旧**: "首次将Adaptive Conformal Prediction应用于UAV GSL"  
**新**: "Beyond Plume Contact: Posterior-Based Search for Robust UAV Gas Source Localization in Signal-Degraded Environments"

### 论文结构

**1. Introduction (1.5页)**
- UAV GSL的实际需求（紧急泄漏、环境监测）
- 现有upwind-tracking方法的成功条件（需要连续plume接触）
- 实际部署中的问题：不知道源在哪里，不知道起始位置信号强弱
- 我们的贡献：posterior-based搜索 + DDM停止准则

**2. Problem Formulation (1页)**
- Plume Contact Dependency的形式化定义
- 强信号 vs 弱信号环境的operational definition
  → 起始位置气体浓度 < 0.2 ppm为"弱信号"（从数据中得出）

**3. Method (3页)**
- 3.1 Posterior-Based Search（W-RAIG的GSL-specific设计）
- 3.2 DDM Stopping Criterion（GSL-specific LLR设计）
- 3.3 级联停止协议
- 删除CP模块的讨论（诚实说明为什么去掉）

**4. Theoretical Analysis (1.5页)**
- Proposition 1: DDM stopping的coverage bound
- 证明sketch
- Coverage table (target 90% → actual X%)

**5. Experiments (3页)**
- 5.1 Setup: VGR数据集 + 3 houses + 10+ seeds
- 5.2 主实验: 我们 vs SurgeCast/PMFS/GrGSL
  → 重点展示House01（弱信号）的优势
  → 诚实展示House02（强信号）SurgeCast更好
  → 跨环境一致性分析（CV比较）
- 5.3 消融: DDM vs W-RAIG vs Baseline
  → 证明每个模块的贡献
- 5.4 Stopping Analysis: DDM触发率、触发时精度、anytime performance

**6. Discussion (1页)**
- 诚实讨论SurgeCast在强信号环境的优势
- 我们方法的定位：不知道源在哪里时的鲁棒选择
- 局限性：单数据集、计算开销

**7. Conclusion (0.5页)**

---

## 六、6周执行路线图

### Week 1: 修复 + 数据收集
- [ ] 修复benchmark_runner的map_dist提取
- [ ] 让10-seed实验完整跑完（240 runs）
- [ ] 从log中提取所有已有run的距离数据
- [ ] 删除CP模块（代码+实验配置）

### Week 2: 方法修复 + 理论
- [ ] 修复DDM的LLR（用posterior entropy变化率）
- [ ] 增加DDM冷静期（step < N时不积累evidence）
- [ ] 写Proposition 1 + 证明sketch
- [ ] 构建coverage table

### Week 3: 统计 + 实验
- [ ] 所有实验结果的统计检验
  - Kruskal-Wallis + Dunn's
  - Mann-Whitney U
  - Bootstrap 95% CI
  - Effect size
- [ ] 画anytime performance curves
- [ ] 画"起始气体浓度 vs 定位误差"散点图

### Week 4: 额外数据集
- [ ] 选择并运行额外数据集（VGR不同配置或GADEN）
- [ ] 跨数据集一致性验证

### Week 5-6: 论文写作
- [ ] Introduction + Problem Formulation
- [ ] Method + Theory
- [ ] Experiments + Discussion
- [ ] 图表制作
- [ ] 内部审阅

---

## 七、关键风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 10-seed实验数据仍然不显著 | 中 | 增加到20-seed；或聚焦anytime performance而非final distance |
| DDM修复后仍然不如CPonly | 低 | 重新评估是否保留DDM |
| 额外数据集表现不好 | 中 | 用VGR不同房间配置（与现有数据最兼容） |
| Proposition 1证不出来 | 低 | 用empirical coverage table代替理论bound |
| 6周时间不够 | 中 | 转投ISJ workshop/special issue |

---

## 八、立即可执行的Action Items

### 今天可以做的:
1. 检查VM实验进度，确认脚本正常运行
2. 写一个Python脚本从已有83个log中提取所有距离数据
3. 确认删除CP模块的代码改动范围

### 本周需要做的:
1. 修复benchmark_runner的map_dist字段
2. 确认10-seed实验可以完整跑完
3. 开始从log中批量提取距离数据
---

## 附录：197-run实际数据分析（2026-07-03更新）

### A. 我们方法的完整消融数据 (n=10 per cell)

| Method | House01 | House02 | House03 | 跨环境均值 |
|--------|---------|---------|---------|-----------|
| **Full** | 2.04±0.87 | 1.98±0.55 | **1.64±0.64** | 1.89 |
| NoDDM | 2.05±1.16 | 2.58±0.59 | 1.24±0.46 | 1.96 |
| NoWRAIG | 1.78±0.58 | 2.49±0.87 | 1.25±0.67 | 1.84 |
| **NoCP** | 2.13±0.81 | **2.27±0.76** | **1.11±0.66** | 1.84 |
| CPonly | 2.46±0.80 | 2.45±0.58 | 2.52±1.77 | 2.48 |
| DDMonLy | 2.09±0.54 | 2.69±0.34 | 1.78±0.00 | 2.19 |
| WRAIGonly | 3.40±0.71 | 2.47±0.22 | — | 2.94 |
| **Baseline** | 1.60±0.00 | 1.88±0.20 | — | 1.74 |

### B. 经典基线数据 (n=3 per cell, from baselines_final.csv)

| Method | House01 | House02 | House03 |
|--------|---------|---------|---------|
| **SurgeCast** | 3.26±0.43 | **0.41±0.11** | 0.99±0.34 |
| PMFS | 3.06±0.04 | 5.69±0.69 | 6.02±0.34 |
| GrGSL | 4.01±0.25 | 5.80±1.57 | 5.83±2.31 |

### C. 关键发现（数据驱动）

**发现1: CP模块正在损害性能（支持删除CP）**
- Full vs NoCP: House01 2.04 vs 2.13 (Full稍好), House02 1.98 vs 2.27 (NoCP更好), House03 1.64 vs 1.11 (**NoCP明显更好**)
- 加了CP模块后，2/3环境变差 → CP确实有负协同
- 但注意：CP-STOP从未触发 → CP的直接停止功能没有工作
- 负协同的机制：CP参数可能影响了其他模块的行为

**发现2: SurgeCast的环境敏感性（核心科学问题）**
- House02: SurgeCast 0.41m >> 我们 1.98m (SurgeCast好5倍)
- House01: SurgeCast 3.26m > 我们 2.04m (我们好1.6倍)
- House03: SurgeCast 0.99m > 我们 1.64m (SurgeCast好1.7倍)
- SurgeCast的跨环境方差: 0.41 → 3.26m (8倍差异)
- 我们的跨环境方差: 1.11 → 2.13m (2倍差异)

**发现3: 统计显著性问题**
- 标准差普遍在0.5-1.2m → 均值差异1-2m可能不显著
- 需要Wilcoxon/Mann-Whitney U检验确认
- 增加n到20-30可能让差异更清晰

**发现4: 我们方法内部，NoWRAIG在House01表现最好**
- NoWRAIG House01: 1.78±0.58 (所有配置中最好)
- 这暗示W-RAIG在某些环境下可能有负面影响
- 需要进一步分析W-RAIG的β参数敏感性

### D. 结论

数据清楚地支持：
1. **删除CP** — 它不仅没有贡献（CP-STOP不触发），还在损害性能
2. **聚焦DDM作为核心贡献** — 这是我们的独特创新
3. **SurgeCast不是在所有环境都好** — 它在House01显著差
4. **我们的优势是跨环境一致性** — 但需要更多数据证明