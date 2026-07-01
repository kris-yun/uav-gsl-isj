# 专家讨论汇总 — OPGSL-3D 方法审查

> 日期: 2026-07-01
> 参与专家: Chandrasekhar（文献综述）, Beauvoir（跨领域创新）, Copernicus（ISJ审稿人）

---

## 一、核心共识

### 1. ESC（2003）必须替换
三位专家一致认为 ESC 作为核心模块存在以下问题：
- 2003 年方法太旧，审稿人直接质疑创新性
- 假设单峰但浓度场可能多峰（热分层效应）
- 稳态持续振荡，无法完全收敛
- 水平运动干扰梯度估计（虽已用残差 ESC 缓解，但理论不严格）

### 2. 替换方案排序
| 排名 | 方法 | 来源 | 优势 |
|------|------|------|------|
| 1 | **在线贝叶斯优化（BO+GP）** | Beauvoir | 1D GP 极轻量、理论成熟、零振荡、自动探索-利用 |
| 2 | **Mamba/SSM** | Beauvoir | 2025 最热架构、线性复杂度、新颖度最高 |
| 3 | **SPSA（同步扰动随机近似）** | Copernicus | 跨域、不假设单峰、传感器信号处理语境友好 |
| 4 | **信息几何（Natural Gradient）** | Beauvoir | 改动最小、理论最硬、ESC 直接升级 |

**推荐**: 用 **BO+GP** 替换 ESC，论文叙事："将 2003 年的极值搜索控制升级为 2025 年的贝叶斯自适应优化"

### 3. 投稿期刊建议
| 期刊 | 适配度 | 理由 |
|------|--------|------|
| **IEEE RA-L** | ★★★★★ | 机器人+自主系统，接受仿真为主 |
| IEEE T-ASE | ★★★★☆ | 自动化+工程应用 |
| ISJ | ★★★☆☆ | 需强化传感器层面贡献 |
| Sensors (MDPI) | ★★★★☆ | 审稿快，但影响力低 |

### 4. 消融实验不足
- 当前仅 5 seeds × 3 House = 15 runs → 需 30+ seeds
- 需 Wilcoxon 秩和检验 + Cliff's delta 效应量
- 需官方基线对齐（MAPIRlab PMFS/GrGSL/surge_cast）
- 需超参敏感性分析

---

## 二、文献综述（Chandrasekhar 撰写，4200 字，37 篇引用）

### 核心结构
1. 引言（领域定义、应用、技术范式演进三阶段）
2. 传统方法：反应式（Surge-Cast 78%成功率）、贝叶斯（Infotaxis/PMFS/GrGSL）、羽流追踪
3. 现代方法：DRL（PPO 82%成功率）、GNN 多机器人、3D GSL（3D Klinotaxis 65%）
4. 跨领域借鉴：ESC、Lévy 飞行、大气边界层理论
5. 五大局限：反应式天花板、概率方法模型依赖、DRL 泛化性、跨领域整合不足、评估基准不统一

### 关键引用
- Vergassola 2007 Nature infotaxis
- Ojeda 2024 TRO PMFS
- Monroy 2023 GrGSL
- Burgués 2021 ISJ SurgeCast
- ISJ 2025 3D Klinotaxis
- Krstic 2003 ESC
- Viswanathan 1999 Nature Lévy flight

---

## 三、跨领域创新分析（Beauvoir 撰写）

### 10 个候选方法详细分析
1. 在线 BO+GP ★★★★★
2. Mamba/SSM ★★★★☆
3. 信息几何 ★★★★☆
4. PINN ★★★☆☆
5. Score-based ★★★☆☆
6. 因果推断 ★★★☆☆
7. Transformer 场估计 ★★★☆☆
8. 神经过程 ★★★☆☆
9. 扩散策略 ★★☆☆☆
10. TDA ★★☆☆☆

---

## 四、ISJ 审稿人审查（Copernicus 撰写）

### 5 个关键问题
1. ESC 必须替换 → 推荐 BO+GP 或 SPSA
2. 需增加阶段切换控制器（CUSUM-BCD）
3. 消融实验严重不足 → 需 30+ seeds + 统计检验
4. ISJ 适配度仅 ★★★☆☆ → 建议考虑 RA-L
5. 三个攻击点：稳态 vs 非稳态、WR-SFE 对比、统计基础薄弱

### 优先级行动清单
| P0 | 官方基线对齐 | 1-2天 |
| P0 | 模块消融实验 | 2-3天 |
| P1 | ESC 升级为 BO+GP | 1周 |
| P1 | 非稳态风场场景 | 2-3天 |
| P1 | 30+ seeds + 统计检验 | 2天 |
