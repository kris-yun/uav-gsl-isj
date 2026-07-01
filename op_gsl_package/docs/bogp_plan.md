# BO+GP 替换 ESC 实现计划

## 改动范围
1. OPGSL.hpp: 添加 GPState 结构体，替换 ESCState
2. OPGSL.cpp: 替换 ESC update/getZ 逻辑为 BO+GP 逻辑

## GP 数学公式（1D Matérn 5/2）

核函数:
k(z, z') = σ_f² * (1 + √5*r/l + 5*r²/(3*l²)) * exp(-√5*r/l)
其中 r = |z - z'|, l = 长度尺度, σ_f² = 信号方差

均值预测:
μ(z*) = k(z*, Z)^T * (K + σ_n² * I)^{-1} * y

方差预测:
σ²(z*) = k(z*, z*) - k(z*, Z)^T * (K + σ_n² * I)^{-1} * k(Z, z*)

UCB 采集函数:
z_next = argmax[μ(z) + sqrt(β) * σ(z)]
其中 β = 2 * log(t) （渐近最优）

## 实现细节

### GPState 结构体
- observations: deque of (z, concentration) pairs
- max_window: 50 (滑动窗口)
- l: 0.5m (长度尺度)
- sigma_f: 1.0 (信号方差)
- sigma_n: 0.1 (噪声方差)
- beta: 2.0 (UCB 探索参数)

### 核心函数
1. addObservation(z, c): 添加观测到滑动窗口
2. predict(z): 返回 (μ, σ) 对
3. getNextZ(): 用 UCB 选择下一个高度
4. fit(): 计算 (K + σ_n² I)^{-1} * y (缓存)

### 与现有代码的接口
- 替换 esc_.update(c) → gp_.addObservation(z, c)
- 替换 esc_.getZ() → gp_.getNextZ()
- 保留其他模块（Lévy、层扫描、后验）不变
