# CP-SBD-GSL 完整实验报告 (v3 — 最终版)
> 日期: 2026-07-03 | 目标: IEEE Sensors Journal

## 一、方法概述

CP-SBD-GSL: Conformal Prediction-terminated, Self-regulating Bayesian Decision for GSL
三大跨领域创新支柱:
1. DDM-Stopping (神经科学, Gold & Shadlen 2007)
2. W-RAIG (最优传输, Rockafellar & Uryasev 2000)
3. CP-Stopping (统计学习, Vovk et al. 2005)

## 二、经典基线对比

| 方法 | 中位数(m) | 均值(m) | 标准差(m) | vs CP-SBD-GSL |
|------|----------|---------|----------|---------------|
| **CP-SBD-GSL** | **1.333** | **1.431** | **0.307** | — |
| SurgeCast | 1.476 | 1.474 | 1.220 | +11% |
| GrGSL | 4.178 | 5.213 | 2.071 | +213% |
| PMFS | 5.242 | 4.944 | 1.500 | +293% |

### 分场景对比 (中位数)

| House | CP-SBD-GSL | PMFS | GrGSL | SurgeCast |
|-------|-----------|------|-------|-----------|
| House01 | 1.130m | 3.094m (2.7×) | 4.178m (3.7×) | 3.054m (2.7×) |
| House02 | 1.690m | 5.242m (3.1×) | 6.532m (3.9×) | 0.439m (0.3×) |
| House03 | 1.294m | 6.269m (4.8×) | 7.646m (5.9×) | 1.476m (1.1×) |

### 关键发现
1. CP-SBD-GSL 在 3/3 House 上优于 PMFS 和 GrGSL (3-6×)
2. SurgeCast 在 House02 表现极好，但在 House01/03 较差
3. CP-SBD-GSL 方差最低 (0.307)，是最可靠的方法
4. 收敛速度: CP-SBD-GSL ~45s vs PMFS/GrGSL ~300s (6× faster)

## 三、消融实验

| 方法 | 中位数(m) | 均值(m) | 标准差(m) | vs Full |
|------|----------|---------|----------|---------|
| **Full** | **1.333** | **1.431** | **0.307** | — |
| NoDDM | 1.635 | 1.757 | 0.725 | +23% |
| NoWRAIG | 1.610 | 1.688 | 0.585 | +21% |
| Baseline | 1.646 | 1.639 | 0.758 | +23% |

### 模块贡献
- DDM-Stopping: 移除后精度下降 23%, 方差增加 136%
- W-RAIG: 移除后精度下降 21%, 方差增加 91%
- 模块间存在正向交互效应: 单独移除任一模块都破坏协同

### 核心洞察
**稳定性 > 精度**: Full 方法的核心贡献是尾部风险控制
- 方差降低 84% (0.307 vs 0.758)
- 最差情况降低 31% (1.983 vs 2.863)
- 一致性提升 53% (极差 0.968 vs 2.058)

## 四、论文叙事框架

### 标题
"Risk-Controlled Bayesian Decision Framework for UAV Gas Source Localization 
with Formal Stopping Guarantees"

### 核心故事
1. **问题**: GSL 有三个耦合决策 (探索/利用/停止)，现有方法各自为政
2. **洞见**: 三个决策从同一约束贝叶斯序贯决策目标函数的条件最优解涌现
3. **贡献**: 
   - (a) 统一目标函数 + 约束贝叶斯序贯决策
   - (b) DDM 停止准则 (首次用于 GSL)
   - (c) W-RAIG 风险感知信息增益
   - (d) CP 分布无关终止保证
4. **实验**: 
   - 消融证明完整性最优 + 尾部风险控制
   - 比 PMFS 4× better, 比 GrGSL 3× better
   - 收敛速度快 6×

### 审稿人回应预案
**Q: "n=9 做统计检验?"** → 增加到 10+ seeds
**Q: "PMFS 为什么崩?"** → 用官方 launch 文件，结果已修正
**Q: "CP exchangeability?"** → 正面讨论 violation 有界性
**Q: "DDM 和 CP 为什么都要?"** → 展示互补性 (待扩展消融)

## 五、待完成

- [ ] 扩展消融 (NoCP, DDM-only, WRAIG-only, CP-only) — watcher 已部署
- [ ] 增加种子数到 10+
- [ ] 统计检验 (Wilcoxon + Cliff's δ)
- [ ] 第二个数据集 (GADEN)
- [ ] 开题报告更新