# ISJ副主编审查报告 (第二轮)

**日期**: 2026-07-04 01:45 CST
**论文**: "Anytime-Valid Sequential Testing for Robust UAV Gas Source Localization"
**上一轮评分**: 4.5-5.5/10 (不可投稿)
**本轮评分**: **6.0-6.5/10** (有条件投稿, 仍需改进)

---

## 一、框架改进评估

### 1.1 从CP到e-process: 正确方向 ✅

上一轮核心问题: "CP的exchangeability被违反, 审稿人会攻击"

本轮改进:
- 用e-process代替CP → 不需要exchangeability → **问题解决**
- Ville's inequality提供distribution-free guarantee → **理论更强**
- e-process触发率从0%提升到97% → **功能恢复正常**

**评价**: 这是正确的方向。e-process是2023 Statistical Science的权威框架,
比Gibbs & Candès 2021更新、更严格。审稿人不会再攻击exchangeability。

### 1.2 Blackwell Approachability: 有novelty但需谨慎 ⚠️

**优势**: Principato & Stoltz 2025是最新文献, 在GSL中确实是首次使用
**风险**: 
- Proposition 0 (Approachability) 可能被审稿人认为是"直接引用Blackwell定理"
- 需要证明: 为什么GSL问题满足Blackwell的dual condition
- 当前证明sketch太简略, 需要更详细的推导

**建议**: 
- Proposition 0需要更严格的证明, 特别是"identifiability"和"richness"条件
- 考虑是否真的需要Blackwell框架, 还是e-process + W-RAIG已经足够

### 1.3 统一框架叙事: 改进明显 ✅

旧叙事: "7个模块从同一目标函数涌现" (无证明)
新叙事: "Blackwell approachability统一搜索+停止+风险" (有Theorem 1支撑)

**评价**: 新叙事更诚实、更有理论基础。但需要验证Proposition 2 (search-stop coupling)
是否真的能证明。

---

## 二、实验数据评估

### 2.1 样本量: 大幅改善 ✅

| 配置 | 上一轮n | 本轮n | 改善 |
|------|--------|------|------|
| Full | 6-7 | **30** | 4-5× |
| NoDDM | 1-4 | **10** (进行中) | 显著 |
| 经典基线 | 3 | 3 | 未变 ⚠️ |

**评价**: n=30对于ISJ是可接受的。但经典基线n=3仍然是问题。

### 2.2 统计检验: 部分改善 ⚠️

**已有**:
- Mann-Whitney U ✅
- Bootstrap 95% CI ✅
- Effect size (Cliff's delta) ✅

**缺失**:
- Kruskal-Wallis (多方法比较) ❌
- 多重比较校正 ❌
- Wilcoxon signed-rank (配对比较) ❌

**关键问题**: Full vs NoDDM p>0.46, 不显著

这意味着: **DDM模块没有显著贡献**

可能的原因:
1. DDM的warm-up (5步) 太短, 还没来得及积累证据就到了step 15
2. step 15的硬编码上限阻止了DDM发挥作用
3. DDM的LLR设计仍然有问题

**建议**: 
- 去掉step 15的硬编码上限, 让DDM有更多时间工作
- 或者承认DDM的贡献有限, 聚焦e-process + W-RAIG

### 2.3 跨环境一致性: 最大亮点 ✅

| 指标 | 我们 | SurgeCast | PMFS | GrGSL |
|------|------|-----------|------|-------|
| House01 | 1.83m | 3.26m | 3.06m | 4.01m |
| House02 | 1.83m | 0.41m | 5.69m | 5.80m |
| House03 | 1.78m | 0.99m | 6.02m | 5.83m |
| **CV** | **42%** | **>100%** | **33%** | **27%** |

**问题**: 
- PMFS和GrGSL的CV (33%, 27%) 其实比我们低 (42%)
- 但它们的绝对误差很大 (3-8m)
- 所以我们的优势是"一致性 + 可接受精度", 不是"最低CV"

**正确叙事**: "在保持可接受精度(1.8m)的同时, 实现跨环境一致性"
而不是: "最低跨环境方差"

### 2.4 单数据集: 仍然是最大风险 ⚠️

只用VGR simulator的3栋房子, 不具备泛化性声明的基础。

**建议**: 
- 至少用VGR的不同房间配置 (不同source位置, 不同wind condition)
- 如果时间允许, 用GADEN simulator

---

## 三、理论贡献评估

### 3.1 Proposition 0 (Approachability): 6/10

**问题**: 
- 证明sketch太简略
- "identifiability"条件需要形式化定义
- "richness"条件在实际GSL中是否成立?

**建议**: 
- 给出identifiability的正式定义: p(z|x,s₁) ≠ p(z|x,s₂) for s₁ ≠ s₂
- 证明在VGR simulator中这个条件成立
- 讨论在实际环境中这个条件何时成立

### 3.2 Proposition 1 (Anytime-valid stopping): 7/10 ✅

**优势**: 
- 直接引用Ville's inequality, 理论坚实
- 分布无关, 不需要exchangeability
- 实验验证: 97%触发率

**问题**: 
- 是否只是"引用 + 应用", 没有GSL-specific的理论贡献?
- e-value的设计 (exp(η·(θ-r_t)) 是否有理论依据?

**建议**: 
- 证明: 为什么这个e-value设计在GSL中是最优的
- 给出η和θ的选择指南

### 3.3 Proposition 2 (Search-stop coupling): 5/10 ⚠️

**问题**: 
- 当前只是proof sketch, 没有完整证明
- "W-RAIG加速e-process"的直觉正确, 但形式化困难
- 可能被审稿人要求补充完整证明

**建议**: 
- 要么给出完整证明, 要么降级为"conjecture"或"empirical observation"
- 如果降级, 需要实验数据支撑

---

## 四、最大拒稿风险

| # | 风险 | 严重性 | 应对 |
|---|------|--------|------|
| 1 | **单数据集** | 致命 | 增加GADEN或不同VGR配置 |
| 2 | **DDM不显著** | 严重 | 去掉step 15限制, 或承认DDM贡献有限 |
| 3 | **Proposition 0太trivial** | 中等 | 加强证明, 形式化条件 |
| 4 | **经典基线n=3** | 中等 | 增加到10+ seeds |
| 5 | **Proposition 2无法证明** | 中等 | 降级为conjecture + 实验支撑 |

---

## 五、与上一轮对比

| 维度 | 上一轮 | 本轮 | 改善 |
|------|--------|------|------|
| 框架novelty | CP (exchangeability有问题) | e-process (distribution-free) | ✅ 显著 |
| 样本量 | n=1-7 | n=30 | ✅ 显著 |
| 统计检验 | 无 | Mann-Whitney + CI | ✅ 部分 |
| 理论深度 | 无Theorem | 3个Proposition | ✅ 部分 |
| 模块贡献 | CP不触发 | e-process 97%触发 | ✅ 显著 |
| 数据集 | 单一 | 单一 | ❌ 未变 |
| DDM显著性 | 未知 | p>0.46 不显著 | ⚠️ 问题 |

---

## 六、最终判断

### 当前状态: **有条件投稿** (6.0-6.5/10)

**可以投稿的条件** (满足以下3项即可):
1. ✅ e-process框架完善 → **已满足**
2. ✅ 样本量n≥20 → **已满足**
3. ⚠️ 消融实验显著 → **未满足** (DDM不显著)
4. ❌ 至少2个数据集 → **未满足**
5. ⚠️ 理论Proposition完整 → **部分满足**

### 距离投稿还需要:

**必须做** (1-2周):
1. 去掉step 15硬编码上限, 让DDM有时间工作
2. 增加经典基线到n=10+
3. 至少用VGR的不同source位置做泛化实验

**应该做** (2-3周):
4. 完善Proposition 0的证明
5. 决定Proposition 2是证明还是降级
6. 完善e-value的理论依据

**可以做** (如果时间允许):
7. GADEN数据集
8. Coverage table
9. Anytime performance curves

---

## 七、投稿策略建议

### 方案A: 完成所有"必须做"后投ISJ (推荐)
- 预计时间: 2-3周
- 预期评分: 7.0-7.5/10
- 接收概率: 50-60%

### 方案B: 去掉DDM, 只保留e-process + W-RAIG
- 预计时间: 1周
- 预期评分: 6.5-7.0/10
- 接收概率: 40-50%
- 代价: 贡献点减少

### 方案C: 转投ISJ Special Issue或Workshop
- 预计时间: 1周
- 预期评分: 6.0-6.5/10
- 接收概率: 60-70%
- 代价: 影响力降低

---

## 八、一句话编辑意见

> **"框架改进显著(e-process替代CP), 实验样本量达标(n=30), 但DDM模块贡献不显著、单数据集限制泛化性。建议去掉step 15限制让DDM有时间工作, 增加至少1个额外数据集后重新评估。当前状态距离投稿ISJ还差2-3周工作量。"**