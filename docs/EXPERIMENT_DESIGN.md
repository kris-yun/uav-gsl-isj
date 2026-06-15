# 实验设计

## 实验矩阵

### 主实验: 消融研究
| 条件 | PWC | PSDE | SDR | 目的 |
|------|-----|------|-----|------|
| baseline | OFF | OFF | OFF | PMFS原始性能 |
| pwc | ON | OFF | OFF | PWC单独贡献 |
| mac | OFF | ON | OFF | PSDE单独贡献 |
| pwc_mac | ON | ON | OFF | PWC+PSDE协同 |
| sdr | OFF | OFF | ON | SDR单独贡献 |
| full | ON | ON | ON | 完整方法 |

### 数据集
- House01: source=(-0.4, -2.9), config=2,4-1_fast
- House02: source=(0.0, -1.0), config=3,5-1_fast
- House03: source=(8.2, 5.0), config=1-2,5_fast

### 种子与统计
- 每条件每场景: ≥10 seeds (0-9)
- matched seeds: 所有条件用相同种子
- 统计检验: Wilcoxon配对检验 (p<0.05)
- 效应量: Cohen's d
- 置信区间: Bootstrap 95% CI (1000 resamples)

### 统一参数 (所有条件共享)
```
maxSearchTime: 300.0
wccThreshold: 0.001
explorationProbability: 0.05
initialExplorationMoves: 2
minExplorationIterations: 3
useWCC: true
useWRSD: true
```

### 输出指标
1. error: 最终估计与源的欧氏距离(m)
2. errorAll: 全局最优估计距离(m)
3. searchTime: 搜索耗时(s)
4. iterations: 迭代次数
5. variance: 概率地图方差
6. converged: 是否在300s内收敛

### 停止条件
- 单次实验: maxSearchTime=300s
- 如果某条件在所有seed上都比baseline差，分析原因后决定是否替换模块
