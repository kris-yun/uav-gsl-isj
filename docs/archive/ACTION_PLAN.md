# CP-SBD-GSL 投稿执行计划

**科学问题**: 当plume未到达UAV起始位置时，现有upwind-tracking和plume-model方法失效
**核心贡献**: Posterior-based搜索不依赖plume接触，在弱信号环境中一致工作
**目标期刊**: IEEE Sensors Journal

---

## Phase 0: 立即执行 (今天-明天)

### 0.1 验证科学问题
- [ ] 画出"起始气体浓度 vs 定位误差"散点图 (所有方法×所有house)
- [ ] 计算source-start距离 (House01/02/03各多少m?)
- [ ] 确认: 弱信号环境(House01) vs 强信号环境(House02)的差异是否由距离决定

### 0.2 检查VM实验进度
- [ ] 10-seed实验完成多少? (ssh检查ablation_10seeds.csv行数)
- [ ] 是否需要修复脚本让实验继续?

---

## Phase 1: 修复方法Bug (第1周)

### 1.1 修复DDM的LLR计算
**问题**: DDMonLy在step=1就停止 (LLR在初始阶段产生虚假正信号)
**修复**:
- 用posterior entropy变化率替代当前LLR
- 增加冷静期: step < 25时不积累evidence
- 验证: DDMonLy不再在step=1停止

### 1.2 修复CP的假收敛
**问题**: CPonly在某些seed下停在4.5m外 (MAP暂时稳定在错误位置)
**修复**:
- 增加stable_req (需要更多连续步数确认收敛)
- 增加min_cal (需要更多calibration样本)
- 验证: CPonly的worst-case从4.5m降到<3m

### 1.3 修复级联停止协议
**问题**: DDM先于CP触发 → 搜索被截断
**修复**:
- CP是硬约束, DDM是软辅助
- DDM只有在CP width < 2×threshold时才允许触发
- 验证: Full的性能 >= max(CPonly, DDMonLy)

---

## Phase 2: 深化理论 (第2周)

### 2.1 Adaptive CP实现
- 实现Gibbs & Candès (2021)的adaptive alpha
- 设计GSL-specific nonconformity score (posterior KL散度)
- 验证: coverage table (target 90% → actual X%)

### 2.2 Proposition 1证明
**Statement**: 在bounded posterior drift下，adaptive CP的coverage ≥ 1-α
- 证明Bayesian update的drift有界
- 引用Gibbs & Candès 2021 Theorem 1
- 给出explicit bound

### 2.3 DDM理论桥接
- 证明: DDM停止 ⟹ 后验已收敛 (KL散度意义)
- 用posterior entropy变化率作为LLR的理论依据

---

## Phase 3: 实验补强 (第3-5周)

### 3.1 10-seed实验完成
- 确保所有8方法×3house×10seed = 240 runs完成
- 修复map_dist缺失问题
- 统计检验: Wilcoxon + bootstrap CI + Cohen's d

### 3.2 Coverage Table
- 在每个run中记录: source是否在CP confidence region内
- 报告: target 80%/90%/95% → actual coverage

### 3.3 起始气体浓度分析
- 画出每个house的gas readings时间序列
- 计算每个house的"有效plume接触时间比例"
- 证明: House01 plume接触比例 << House02

### 3.4 Anytime Performance Curve
- 画出每一步的累积regret
- 证明: CP-SBD-GSL在任何时刻t的累积风险更低

### 3.5 GADEN数据集 (如果时间允许)
- 编译GADEN bridge
- 至少3个不同wind condition
- 验证方法的泛化性

---

## Phase 4: 论文写作 (第5-7周)

### 4.1 论文结构
1. **Introduction**: UAV GSL的实际需求 + 现有方法的局限
2. **Problem**: 弱信号环境下的搜索失败 (数据驱动)
3. **Method**: CP-SBD-GSL的posterior-based框架
4. **Theory**: Adaptive CP coverage guarantee (Proposition 1)
5. **Experiments**: 
   - 强信号 vs 弱信号环境对比
   - Ablation study
   - Coverage table
   - Anytime performance
6. **Discussion**: 与SurgeCast的坦诚对比 + 局限性

### 4.2 标题候选
1. "Beyond Plume Contact: Bayesian Posterior Monitoring for Robust UAV Gas Source Localization"
2. "Consistent Gas Source Localization in Weak-Signal Environments via Posterior Stability Monitoring"
3. "When the Plume Doesn't Reach the UAV: Distribution-Free Source Localization"

### 4.3 审稿人回应预案
- Q: "SurgeCast在House02更好?" → 承认, 但强调弱信号环境的优势
- Q: "CP exchangeability?" → Adaptive CP + bounded drift proof
- Q: "3 seeds不够?" → 10-20 seeds + 统计检验
- Q: "单数据集?" → GADEN (如果完成)

---

## 关键里程碑

| 周 | 里程碑 | 验证标准 |
|----|--------|---------|
| 1 | Bug修复完成 | DDM不再step=1停止, Full > CPonly |
| 2 | 理论完成 | Proposition 1 LaTeX + coverage table |
| 3 | 10-seed实验完成 | 240 runs + 统计检验 |
| 4 | 补充实验完成 | Anytime curve + 起始气体分析 |
| 5 | 论文初稿完成 | 完整8页ISJ格式 |
| 6 | 论文修改 | 根据自查修改 |
| 7 | 投稿 | 提交到ISJ |

---

## 立即行动 (今天)

1. 检查VM上10-seed实验进度
2. 画起始气体浓度 vs 定位误差散点图
3. 计算House01/02/03的source-start距离
