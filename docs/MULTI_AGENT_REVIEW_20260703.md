# CP-SBD-GSL 多Agent专家审查综合报告

**审查日期**: 2026-07-03
**审查专家**: ISJ副主编(Kepler) + 审稿人(Euclid)
**当前状态**: 不可投稿 (4.5-5.5/10)

---

## 一、核心问题汇总

### 致命问题 (Must Fix)

#### 1. SurgeCast在2/3场景优于我们
| House | CP-SBD-GSL | SurgeCast | 差距 |
|-------|-----------|-----------|------|
| House01 | 1.0-1.6m | 2.9-3.9m | 我们好2x |
| House02 | 1.6-2.0m | 0.3-0.5m | 他们好4-6x |
| House03 | 1.2-1.3m | 0.8-1.5m | 相当 |

**两位专家一致认为**: 这是审稿人必问的第1个问题。"稳定性"叙事(Std 0.307)站不住脚，因为方差低但均值高=稳定地差。

#### 2. 统计功效严重不足 (3 seeds)
- 9 runs/config无法支撑任何统计声明
- 无Wilcoxon/Mann-Whney/bootstrap CI
- Kepler: "3 seeds is instant reject"
- Euclid: "置信区间宽度 > 中位数本身"

#### 3. CP Exchangeability假设被违反
- 标准CP要求i.i.d./exchangeable
- UAV GSL中：传感器漂移、风场时变、自适应轨迹 → 分布持续变化
- 必须用adaptive CP (Gibbs & Candès 2021)或证明drift有界
- 当前代码中CP是naive split conformal，严格意义上覆盖保证不成立

#### 4. CPonly > Full 消融逻辑矛盾
- CPonly在House02达0.19m，但Full在House02是1.6-2.0m
- 说明加入DDM和WRAIG反而降低了性能 = 负协同效应
- 消融实验的逻辑基础被动摇

#### 5. 模块是"浅层移植"，缺乏GSL特有理论贡献
- DDM本质 = 带时间衰减的SPRT变体 (Cisek 2009已有robotics应用)
- W-RAIG = 信息增益 × Wasserstein权重 (理论创新不足)
- CP = 直接套用Angelopoulos 2023 (无domain adaptation)
- Kepler: "每个模块都是浅层移植，没有从源领域带来真正的理论深度"

### 严重问题 (Should Fix)

#### 6. 单数据集 (VGR)
- ISJ要求2-3个独立数据集
- VGR的3个house只是同一数据集的不同配置，不算3个独立环境

#### 7. 方法名演变 (SAISC-PF → CP-SBD-GSL)
- Kepler发现仓库中有SAISC-PF版本，现在改名CP-SBD-GSL
- 模块名也完全变了 (SDBE→DDM, IASC→WRAIG, PCR-D→CP)
- 审稿人可能搜索到GitHub，需要透明说明版本演变

#### 8. 数据一致性问题
- Kepler发现呈现数据与仓库日志存在矛盾
- 需要统一数据口径，确保可复现

---

## 二、两位专家评分对比

| 维度 | Kepler (ISJ副主编) | Euclid (审稿人) |
|------|-------------------|----------------|
| 跨领域迁移新颖度 | 6/10 | 6/10 |
| 理论贡献深度 | 3/10 | 5/10 |
| 实验支撑强度 | 4/10 | 4/10 |
| 总分 | **4.5/10** | **5.5/10** |
| 判断 | 不可投稿 | 勉强大修 |

---

## 三、审稿人必问的6个问题

### Q1: "Why is your method outperformed by SurgeCast in 2/3 environments?"
**回应策略**: 不要回避。引入CP coverage metric(SurgeCast没有)和anytime performance curve。证明在resource-constrained场景下CP-SBD-GSL的cumulative risk更低。

### Q2: "CP的exchangeability假设在序贯贝叶斯设置下如何保证?"
**回应策略**: 引用adaptive CP (Gibbs & Candès 2021)，给出empirical coverage table(target 90% → actual X%)，或证明drift速率有界。

### Q3: "With only 3 seeds, how can you claim statistical significance?"
**回应策略**: 必须增加到至少20 seeds，报告bootstrap 95% CI + Wilcoxon signed-rank test。

### Q4: "CPonly achieves 0.19m but Full achieves 1.6-2.0m. Explain."
**回应策略**: 分析每个模块的停止触发时机。可能是DDM过早触发停止，阻止了CP的充分收敛。需要提供step-by-step stopping time analysis。

### Q5: "You only validate on VGR. Generalization?"
**回应策略**: 补充GADEN数据集实验。

### Q6: "Three modules from three frameworks — theoretical justification?"
**回应策略**: 必须提供Proposition/Theorem证明组合的合理性和coverage guarantee。

---

## 四、紧急修复路线图

### Phase 1: 立即修复 (今天)
1. ✅ 恢复扩展消融的map_dist数据 (已完成)
2. 修复扩展消融缺失数据(超时未走FAST EXIT的runs)
3. 检查数据泄露问题(GT source位置是否在决策中被使用)

### Phase 2: 本周完成
4. 增加seeds到10个(先10个，后续补到20)
5. 添加统计检验脚本(Wilcoxon + bootstrap CI)
6. 修复CPonly > Full的问题：分析DDM和CP的停止时序冲突

### Phase 3: 2周内完成
7. 补GADEN数据集实验
8. 补多起点敏感性实验(3-5个起始位置)
9. CP coverage实测表(target vs actual)

### Phase 4: 方法改进(决定性)
10. 如果SurgeCast仍然全面优于我们，考虑:
    - 方案A: 重新定位为"risk-controlled"论文，强调coverage guarantee
    - 方案B: 重新设计模块交互(修复负协同)
    - 方案C: 降级投稿目标(workshop paper / 更低IF期刊)

---

## 五、关键决策点

### 决策1: SurgeCast更好怎么办?
- **选项A**: 承认并重新定位 → "CP-SBD-GSL provides formal coverage guarantees that SurgeCast lacks"
- **选项B**: 修复方法使我们在所有场景都更好 → 需要重新设计模块
- **选项C**: 更换基线对比 → 不诚实，不推荐

### 决策2: 模块堆砌vs统一理论?
- Kepler认为模块是"浅层移植"，需要GSL-specific理论贡献
- 候选: CP在spatially correlated plume下的coverage修正
- 候选: Wasserstein距离在plume posterior上的closed-form approximation

### 决策3: ISJ还是降级?
- 当前状态4.5-5.5/10，ISJ大修是最好情况
- 如果6-8周密集工作后仍无法解决核心问题，考虑Sensors(Q3)或RAL workshop

---

**下一步行动**: 立即检查代码中的数据泄露问题，然后修复扩展消融缺失数据。
