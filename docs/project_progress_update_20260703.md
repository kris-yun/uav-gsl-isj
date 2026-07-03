# CP-SBD-GSL 项目进度更新

**更新日期**: 2026-07-03
**更新人**: AI Agent (多Agent专家审查后)

---

## 一、当前状态总览

### 方法: CP-SBD-GSL (Conformal Prediction-guided Sequential Bayesian Design)
- **三个核心模块**: DDM-Stopping, W-RAIG, CP-Stopping
- **目标期刊**: IEEE Sensors Journal (ISJ, Q2, IF~3.4)

### 实验数据现状

#### 原始消融 (3 seeds × 3 houses)
| Config | Median | Mean | Std | n |
|--------|--------|------|-----|---|
| Full | 1.333 | 1.431 | 0.307 | 9 |
| NoDDM | 1.635 | 1.757 | 0.725 | 9 |
| NoWRAIG | 1.610 | 1.688 | 0.585 | 9 |
| Baseline | 1.646 | 1.639 | 0.758 | 9 |

#### 经典基线 (3 seeds × 3 houses)
| Method | Median | House01 | House02 | House03 |
|--------|--------|---------|---------|---------|
| CP-SBD-GSL | 1.333 | 1.0-1.6m | 1.6-2.0m | 1.2-1.3m |
| SensorAwareSurgeCastPF | ~0.75 | 2.9-3.9m | 0.3-0.5m | 0.8-1.5m |
| GrGSL | 4.178 | 3.7-4.2m | 3.6-7.3m | 2.2-7.6m |
| PMFS | 5.242 | 3.0-3.1m | 5.2-6.8m | 5.5-6.3m |

---

## 二、多Agent专家审查结果 (2026-07-03)

### 审查专家
1. **Kepler** (ISJ副主编视角) — 评分 4.5/10
2. **Euclid** (审稿人视角) — 评分 5.5/10

### 一致结论: 当前不可投稿

### 致命问题 (5个)
1. **SurgeCast在2/3场景优于我们** — House02差距4-6x
2. **统计功效严重不足** — 3 seeds无法支撑任何声明, p=0.89 (Full vs Baseline)
3. **CP Exchangeability假设被违反** — 序贯贝叶斯更新破坏i.i.d.假设
4. **CPonly > Full消融矛盾** — 模块间存在负协同效应
5. **模块是"浅层移植"** — 缺乏GSL特有理论贡献

### 统计检验结果 (3 seeds)
- Full vs Baseline: p=0.89, Cliff's δ=0.000 → **完全不显著**
- Full vs NoDDM: p=0.48 → 不显著
- Full vs NoWRAIG: p=0.26 → 不显著
- House03: Baseline(0.805m) **优于** Full(1.294m) → 模块在简单场景有害

### ISJ投稿可行性评估
| 维度 | 当前状态 | 要求 |
|------|---------|------|
| 创新性 | 4.5-5.5/10 | ≥7/10 |
| 实验充分性 | ❌ | 10+ seeds, 2+ datasets |
| 超越SOTA | ❌ | 所有场景持平或优于 |
| 理论贡献 | ❌ | GSL-specific理论 |
| 统计检验 | ❌ | Wilcoxon + CI |

---

## 三、正在执行的修复

### Phase 1: 数据扩充 (进行中)
- [x] 恢复扩展消融map_dist数据
- [ ] 10 seeds × 8 configs × 3 houses = 240 runs (正在跑)
- [ ] 统计检验: Wilcoxon + bootstrap CI

### Phase 2: 问题诊断 (待完成)
- [ ] CPonly > Full问题: 分析停止时序
- [ ] 数据泄露检查: 已确认无泄露 ✅
- [ ] CP coverage实测

### Phase 3: 方法改进 (待决策)
- [ ] 重新定位: "risk-controlled" vs "precision improvement"
- [ ] 修复模块负协同
- [ ] 补GADEN数据集

---

## 四、代码仓库

- **GitHub**: https://github.com/kris-yun/cp-sbd-gSL (私有)
- **VM代码**: /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/
- **本地代码**: D:\ZYC\A-gas\src\

---

## 五、下一步行动

1. 等待10-seed实验完成 (~3小时)
2. 运行统计分析
3. 根据结果决定方法改进方向
4. 更新开题报告Word
