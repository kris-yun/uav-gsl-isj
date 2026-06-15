# 科学问题定义

## 问题标题
低风速环境下PMFS概率地图收敛失败导致UAV气体源定位误差增大

## 问题描述
在低风速（<0.5 m/s）室内/半封闭环境中，PMFS（Particle-based Mapping with Forward Simulation）算法的概率地图难以收敛：
- Gas hit信息因低风速下羽流扩散kernel过小而传播不足
- GMRF风场估计在稀疏传感器数据下发散
- 搜索陷入局部最优，最终定位误差>3m

## 可检验假设
H1: 在低风速条件下，PMFS的概率地图方差在300s搜索预算内无法收敛到<1.0
H2: 基于气体命中分布的空间统计特征可以提供额外的距离估计信息
H3: 基于风向的后验校正可以改善源位置估计

## 控制变量
- 风速: 由GADEN仿真器控制（House01/02/03各有不同风场）
- 随机种子: 控制UAV探索路径
- 源位置: 由VGR数据集固定
- 起始位置: 由VGR数据集固定
- 搜索预算: maxSearchTime=300s（统一）

## 评估指标
1. **error**: 最终源位置估计与真实源的欧氏距离(m)
2. **errorAll**: 全局最优估计与真实源的距离(m)
3. **searchTime**: 搜索耗时(s)
4. **iterations**: 搜索迭代次数
5. **variance**: 概率地图方差（收敛度量）
6. **success@2m**: 误差<2m的成功率
7. **success@3m**: 误差<3m的成功率

## 数据集
- VGR (Virtual Gas Rendering) 仿真数据集
- House01: source=(-0.4, -2.9), 低风速室内环境
- House02: source=(0.0, -1.0), 不同布局
- House03: source=(8.2, 5.0), 更大空间
