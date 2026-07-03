# 重新思考：从经典方法的问题出发，而不是我们的bug

## 一、用户的关键提醒

DDM step=1停止、CP假收敛 — 这是我们方法的实现问题，不是经典方法的通病。

经典方法 (SurgeCast/PMFS/GrGSL):
- 没有CP/DDM，只有timeout
- 不会"过早停止"，它们一直跑到超时
- 所以"过早停止"不是经典方法的问题，是我们在尝试做智能停止时引入的新问题

## 二、经典方法的真正问题是什么？

看数据:

| 方法 | House01 | House02 | House03 | 跨环境行为 |
|------|---------|---------|---------|-----------|
| SurgeCast | 3.05m (差) | 0.44m (极好) | 0.75m (好) | 在House01崩溃 |
| PMFS | 3.09m | 5.24m | 6.27m | 全面差 |
| GrGSL | 4.18m | 6.53m | 7.65m | 全面差 |
| CP-SBD-GSL | 1.0-2.4m | 1.6-2.0m | 0.7-3.1m | 稳定在1-2m |

### 经典方法的真正问题:

**1. SurgeCast: 环境敏感性**
- House02 (简单几何): 0.44m — 极好
- House01 (复杂几何): 3.05m — 比我们差2倍
- 原因: SurgeCast依赖连续的upwind tracking
  → 在复杂建筑中，plume被障碍物打断
  → upwind方向不准 → 搜索方向错误
  → 但算法不知道自己错了，继续按错误方向跑

**2. PMFS/GrGSL: 全面差**
- 所有环境都在3-8m
- 原因: 这些方法依赖plume model (Gaussian plume等)
  → VGR数据集是filament仿真，不是Gaussian plume
  → 模型假设错误 → 后验不准 → 搜索方向错误

**3. 共同问题: 不知道自己对不对**
- SurgeCast在House01差3m，但算法不知道
- PMFS在所有环境都差5-7m，但算法不知道
- 没有任何机制告诉算法"你可能在错误的方向上搜索"

## 三、我们方法的真正优势

CP-SBD-GSL在所有环境稳定在1-2m。为什么?

看代码:
- 用的是posterior-based搜索 (不直接依赖plume model)
- 用的是wind-relative spatial field estimation (WATS_GSL)
- 用的是ensemble-based uncertainty estimation

**核心洞察: 我们的方法通过posterior monitoring来适应不同环境**

- SurgeCast: 直接追踪plume → plume断了就迷失
- CP-SBD-GSL: 监控posterior分布 → plume断了但posterior还在积累信息

## 四、真正的科学问题 (待确认)

### 候选A: 复杂环境中的一致性源定位

**问题**: 现有UAV GSL方法在不同建筑几何中性能差异巨大
  - SurgeCast: House02 0.44m vs House01 3.05m (7倍差异)
  - 没有方法能保证在未知环境中也能工作

**原因**: 经典方法依赖plume接触 (upwind tracking, plume model)
  → 当建筑几何改变plume结构时，方法失效

**方案**: Posterior-based搜索 + 稳定性监控
  → 不直接依赖plume，而是通过posterior积累信息
  → 在所有环境中一致工作

### 候选B: UAV GSL中的环境自适应问题

**问题**: UAV在执行气体源搜索时，不知道会进入什么样的建筑
  → 需要一个在所有环境中都合理工作的方法
  → SurgeCast需要环境"恰好适合"才能工作

### 候选C: 需要更多数据来确认

也许10-seed实验完成后，数据会告诉我们更清晰的故事。

## 五、下一步建议

1. 先修复DDM/CP的bug (让方法本身工作正确)
2. 等10-seed实验完成 (获得更可靠的数据)
3. 从完整数据中找经典方法的具体失败模式
4. 定义科学问题

核心原则: 科学问题必须是经典方法也有的问题，不是只有我们方法才有的bug
