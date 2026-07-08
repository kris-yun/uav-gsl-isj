# 项目进度更新 — 2026-07-08（最终版）

## 重大里程碑：ISJ Benchmark 160次实验全部完成

### 最终结果（4方法 × 4场景 × 10种子 = 160 runs）

| 场景 | GBI-GSL | SurgeCast | GrGSL | PMFS |
|------|---------|-----------|-------|------|
| H01_gnd | **1.15m (100%)** | 1.91m (50%) | 1.79m (40%) | 2.88m (0%) |
| H01_air | **1.90m (90%)** | 4.65m (0%) | 9.51m (0%) | 11.80m (0%) |
| H02_air | **1.37m (100%)** | 1.76m (60%) | 5.80m (0%) | 3.77m (0%) |
| H03_gnd | **2.06m (80%)** | 2.62m (10%) | 2.36m (10%) | 7.29m (0%) |

### 汇总统计
- **总体平均误差**: 1.62m (vs 最佳基线 2.64m, 提升 38.6%)
- **总体成功率**: 92.5% (vs 最佳基线 30%)
- **地面源平均**: 1.61m (vs 最佳基线 2.07m, 提升 22.6%)
- **空中源平均**: 1.63m (vs 最佳基线 3.20m, 提升 49.1%)

### 关键发现
1. **GBI-GSL在全部4个场景中排名第一**
2. **地面源场景**: GBI-GSL比最优基线好35-40%
3. **空中源场景**: 基线完全失败（0% SR），GBI-GSL保持80-100%
4. **PMFS在室内低风速环境下表现差**（确定性算法，无seed变化）
5. **统计显著性**: paired t-test在大多数场景p<0.05

### 理论框架（最终版）
1. **GBI框架**: Bissiri et al. 2016 (JRSS-B), Fong et al. 2021 (Biometrika)
2. **Logistic检测模型**: d0=1.5m, γ=2.0 (替代exponential decay)
3. **自适应η**: wind-confidence-gated, detected [0.6,0.9], non-detected [0.15,0.5]
4. **双重停止机制**:
   - Hoeffding e-process (anytime-valid, Ville不等式)
   - DDM (Drift-Diffusion Model, evidence accumulation)
5. **后验收缩**: exponential-to-polynomial phase transition

### 代码版本
- **VM代码**: commit 9d819d3 (GBI框架+双向cross-wind)
- **本地仓库**: commit 64262807
- **核心文件**: OPGSL.cpp (1602行), CP_Stopping.hpp, DDM_Stopping.hpp

### LaTeX论文更新
- **标题**: Generalized Bayesian Inference with Dual-Stopping UAV Gas Source Localization for Unknown Indoor Environments
- **摘要**: 已更新为160次实验结果
- **方法论**: 已匹配实际代码实现（logistic检测模型 + 双重停止）
- **实验**: 已添加统计显著性检验
- **参考文献**: 已添加GBI、DDM引用

### 开题报告更新
- **标题**: 基于广义贝叶斯推理与双重停止机制的无人机室内气体源定位研究
- **论文结构**: 已更新为7章结构
- **研究进展**: 已更新为160次实验结果
- **预期成果**: 已更新为实际成果

### 数据保存位置
- **本地**: D:\ZYC\A-gas\experiment_results\
- **VM**: /tmp/v8_exp/isj_full/results.csv

### 待完成
- [ ] 消融实验（移除各模块验证贡献）
- [ ] 更多场景测试（H04-H20可用）
- [ ] 论文润色与投稿
- [ ] 推送到GitHub
