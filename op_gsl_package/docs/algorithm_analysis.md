# OPGSL 算法分析与创新点

## 一、当前算法架构

OPGSL = Optimized Particle-based Gas Source Localization

### 核心流程
1. 无气体检测时：黄金角螺旋探索 (Golden-Angle Spiral)
2. 检测到气体后：化学趋向导航 (Chemotaxis Navigation)
   - 计算加权质心 (Weighted Centroid)
   - 向质心方向移动
3. 收敛条件：conc > 0.4 && dist < 1.5m && time > 15s && hits >= 2

### 包含的模块
1. **WR-SFE** (Wind-Relative Spatial Field Estimator)
   - 核密度估计 (KDE) 构建气体场
   - 风场相对坐标系
   - 自适应带宽

2. **WA-IG** (Wind-Aware Information Gain)
   - 黄金角螺旋探索
   - 风场偏置
   - 不确定性加权

3. **Chemotaxis Navigation**
   - 加权质心估计
   - 梯度跟随
   - 导航感知回退

## 二、当前结果分析

### 为什么比基线好？

| 方法 | H01 | H02 | H03 | 问题 |
|------|-----|-----|-----|------|
| OPGSL | 1.06m | 1.12m | 1.36m | - |
| PMFS | 6.32m | FAIL | FAIL | 确定性、H02/H03失败 |
| GrGSL | 1.70m | 3.64m | 7.80m | 超时 |

**关键原因：**
1. PMFS 是确定性算法，不适应不同场景
2. GrGSL 超时，探索效率低
3. OPGSL 的化学趋向导航有效利用气体检测信息

### 但是...没有创新模块！

当前 OPGSL 的改进来自：
- 修复了状态机流程（之前 chooseGoalAndMove 从未被调用）
- 使用了官方包的 WR-SFE 和 WA-IG 模块

**这不是论文级别的创新。** 需要添加创新模块。

## 三、需要的创新点

### 主创新：Bout-Level Bayesian Inference（事件过程推断）

**来源：** 随机点过程 (Stochastic Point Process) - 金融/生物领域

**核心思想：**
- 不是用"气体浓度"作为观测
- 而是用"气味事件过程"作为基本观测单位
- 建模 bout (气体检测批次) 的统计特性

**公式：**
```
观测模型：
  z_t = {
    bout_event, if gas > threshold for duration > min_bout
    no_event,   otherwise
  }

似然函数：
  P(z_t | s) = lambda(s) * exp(-lambda(s) * dt)

其中 lambda(s) = 源位置 s 的 bout 到达率
```

**为什么是 A 级创新：**
- 改变了观测空间定义（从信号估计到随机事件推断）
- 有严格的数学基础（点过程理论）
- 在 GSL 领域没有被使用过

### 辅助创新 1：Sensor Delay as Latent State（传感器延迟隐变量）

**来源：** 隐马尔可夫模型 (HMM) - 语音识别领域

**核心思想：**
- 不是"补偿"传感器延迟
- 而是把延迟作为隐变量去估计

**公式：**
```
状态空间：
  x_t = [source_pos, sensor_latency, sensor_recovery]

状态转移：
  x_t = f(x_{t-1}) + w_t

观测模型：
  z_t = h(x_t) + v_t
```

**为什么是 A 级创新：**
- 从 PF over source 升级为 PF over joint system
- 统一处理延迟和间歇性
- 在气体溯源领域没有被使用

### 辅助创新 2：Information-Theoretic Active Sensing（信息论主动感知）

**来源：** 贝叶斯实验设计 (Bayesian Experimental Design) - 医学诊断领域

**核心思想：**
- 控制策略不是规则（如 surge-cast）
- 而是最大化期望信息增益

**公式：**
```
控制目标：
  u_t = argmax E[KL(P(s|z_{1:t+1}) || P(s|z_{1:t}))]

近似：
  u_t ≈ argmax H[P(s|z_{1:t})] - E_z[H[P(s|z_{1:t+1})]]
```

**为什么是 A 级创新：**
- 从启发式控制升级为贝叶斯最优决策
- 有严格的理论基础（信息论）
- 在 UAV 气体溯源领域没有被使用

## 四、消融实验设计

### 实验矩阵

| 配置 | WR-SFE | Chemotaxis | Bout-Inference | Delay-State | Info-Gain |
|------|--------|------------|----------------|-------------|-----------|
| A0 (基线) | ✓ | ✓ | ✗ | ✗ | ✗ |
| A1 | ✓ | ✓ | ✓ | ✗ | ✗ |
| A2 | ✓ | ✓ | ✗ | ✓ | ✗ |
| A3 | ✓ | ✓ | ✗ | ✗ | ✓ |
| A4 (完整) | ✓ | ✓ | ✓ | ✓ | ✓ |

### 验收标准

1. **A1 vs A0**: final_error 降低 >= 15%，否则 Bout-Inference 不能作为主创新
2. **A2 vs A0**: timeout 不增加，否则 Delay-State 无效
3. **A3 vs A0**: path_length 减少或 success_rate 增加，否则 Info-Gain 无效
4. **A4 vs A0**: 所有指标优于 A0，且每个模块都有贡献

## 五、下一步行动

1. 实现 Bout-Level Bayesian Inference 模块
2. 实现 Sensor Delay Latent State 模块
3. 实现 Information-Theoretic Active Sensing 模块
4. 跑消融实验
5. 完善理论公式
6. 准备论文

## 六、当前代码结构

```
OPGSL/
├── OPGSL.cpp          # 主算法
├── OPGSL.hpp          # 头文件
├── WATS_GSL.hpp       # WR-SFE + WA-IG 模块
└── CMakeLists.txt     # 编译配置
```

### 关键修复

1. Override `OnCompleteNavigation` → 导航到 `StopAndMeasureState`
2. 在 `processGasAndWindMeasurements` 后设置 `need_next_goal_` 标志
3. 在 `OnUpdate()` 中延迟调用 `chooseGoalAndMove()`
4. 避免嵌套 spin 冲突
