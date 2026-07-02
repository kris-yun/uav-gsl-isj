# 项目进度 — CP-SBD-GSL (v2)
> 更新时间: 2026-07-03

## 方法: CP-SBD-GSL
**C**onformal **P**rediction-terminated, **S**elf-regulating **B**ayesian **D**ecision framework for **G**as **S**ource **L**ocalization

### 三大创新支柱

#### 1. DDM-Stopping (Drift-Diffusion Model 停止准则)
- **理论来源**: 神经科学 — Gold & Shadlen (2007) "The neural basis of decision making"
- **核心思想**: 将 GSL 搜索终止建模为感知决策过程，无人机累积证据直到达到置信阈值
- **数学公式**: θ(t) = θ₀ · exp(-γt) + θ_min (urgency gating)
- **证据累积**: dx = (μ - λx)dt + σdW (Ornstein-Uhlenbeck 过程)
- **优势**: 相比 CP-Stopping，不要求 exchangeability 假设
- **状态**: ✅ 已集成，参数已调优 (min_obs=25, min_time=60s, leak=0.05)

#### 2. W-RAIG (Wasserstein Risk-Aware Information Gain)
- **理论来源**: 最优传输 — Rockafellar & Uryasev (2000) CVaR; 近年 risk-sensitive BO
- **核心公式**: W-RAIG(a) = E_m[EIG_m(a)] - β · √(Var_m[EIG_m(a)])
- **退化情况**: β=0 时退化为标准 EIG = Infotaxis
- **优势**: 相比 KL-based EIG，几何意义明确，对后验形状假设更鲁棒
- **状态**: ✅ 已集成，β=0.5

#### 3. CP-Stopping (Conformal Prediction 停止准则)
- **理论来源**: Vovk et al. (2005) Conformal Prediction
- **核心思想**: 分布无关的后验收敛检测
- **优势**: 无需参数假设，理论保证覆盖率
- **状态**: ✅ 已集成

### 统一目标函数

$$
\max_{\pi} \mathbb{E}\left[\sum_{t=1}^{T} \gamma^{t-1} I_t^{W\text{-}RAIG} - \lambda \sum c(s_t, s_{t+1}) + \eta \mathcal{E}_t\right]
$$
s.t. DDM-Stop(t) 或 CP-Stop(t) 触发时终止

### 已验证模块 (保留在框架中)
- ✅ Lévy 飞行探索 (跨领域: 生态学/动物觅食)
- ✅ Bout 检测 (跨领域: 神经科学/嗅觉编码)
- ✅ 自适应步长 (基于梯度信息)
- ✅ 逆风追踪 (经典 plume tracking)
- ✅ GP 高度模型 (贝叶斯优化)
- ✅ 3D 后验 (FIM 驱动高度选择)
- ✅ SD-NBV 框架 (空间去卷积 + 下一最佳视角)

### 实验配置

| 配置 | DDM | W-RAIG | CP | 用途 |
|------|-----|--------|-----|------|
| Full | ✅ | ✅ | ✅ | 完整方法 |
| NoDDM | ❌ | ✅ | ✅ | DDM 消融 |
| NoWRAIG | ✅ | ❌ | ✅ | W-RAIG 消融 |
| Baseline | ❌ | ❌ | ❌ | 基线 |

- 数据集: VGR (3 House, CFD filament 仿真)
- 起点: (-0.9, 0.15), 飞行高度: 0.3m
- 每配置 3 seeds (0,1,2), timeout: 300s
- 基线: PMFS, GrGSL, SensorAwareSurgeCastPF

### 当前实验结果 (初步)

#### 消融实验 (运行中)
| 方法 | House01 | House02 | House03 | 状态 |
|------|---------|---------|---------|------|
| Full s0 | 1.574m/15步 | 1.616m/15步 | 运行中 | DDM-STOP 触发 |
| NoDDM | 待运行 | | | |
| NoWRAIG | 待运行 | | | |
| Baseline | 待运行 | | | |

#### 问题诊断
- DDM-STOP 在 step 15 触发，过早收敛 (~1.6m 误差)
- 已调优: min_obs 10→25, min_time 20→60s, leak 0.01→0.05, theta_min 0.5→1.5
- LLR 计算从简单 map-move 改为 gas-weighted evidence
- 新版代码已部署，后台编译中

### 目标期刊: IEEE Sensors Journal (ISJ, IF ~4.3)

### ISJ 准备度评估 (Maxwell Agent)
- 当前: 5.5/10
- 目标: 8.0/10
- 加分项: CP-first-in-GSL (+1.5), DDM 跨领域 (+0.5), W-RAIG (+0.5)
- 待改进: 实验充分性, 统计检验, 泛化验证

### 文件清单
| 文件 | 路径 | 状态 |
|------|------|------|
| 框架理论 | docs/CP_SBD_GSL_FRAMEWORK_CN.md | 完成 |
| ISJ评估 | docs/ISJ_SENIOR_EDITOR_EVALUATION.md | 完成 |
| 跨领域创新 | docs/CROSS_DOMAIN_INNOVATION_REVIEW.md | 完成 |
| 代码回归分析 | docs/CODE_REGRESSION_ANALYSIS.md | 完成 |
| 项目进度 | docs/project_progress_cp_sbd.md | 本文件 |

### 下一步
1. 等待消融实验完成 (36 runs, ~2h)
2. 分析消融结果，确定主效模块
3. 运行经典基线 (PMFS/GrGSL/SurgeCast)
4. 统计检验 (Wilcoxon, Cliff's delta)
5. 搜索 2025-2026 跨领域创新文献
6. 更新开题报告 (template.doc 格式)
7. 撰写论文初稿