# 气体源定位方法综述：经典方法与跨领域可迁移方法

> 日期: 2026-06-09
> 项目: D:\ZYC\A-gas (UAV GSL SCI3)
> 目的: 系统梳理GSL领域经典方法和可跨领域迁移的方法，为DQA-AS创新模块提供理论支撑

---

## 一、经典气体源定位方法

### 1.1 Particle Filter (粒子滤波) 用于气体源定位

**核心数学框架:**
- 状态空间: 源位置 s = (x, y)，可能扩展到源强度 Q
- 粒子集: {s_i, w_i}_{i=1}^N，每个粒子代表一个候选源位置
- 预测步: s_i^k ~ p(s^k | s^{k-1})，通常为随机游走扩散
- 更新步: w_i^k ∝ w_i^{k-1} · p(z_k | s_i)，其中 z_k 为气体浓度观测
- 似然模型: 通常采用高斯或逆距离模型 p(z|s) ∝ exp(-||x_uav - s||^2 / σ^2)
- 重采样: 当有效粒子数 N_eff < 阈值时执行系统重采样

**关键文献:**
- Vergassola et al., Nature 2007 (Infotaxis中的隐式粒子方法)
- MAPIRlab GasSourceLocalization 中的 particle_filter 实现
- Lilienthal et al., "Statistical gas distribution modelling with the kernel DM+VW" (2009)

**已有气体溯源应用:**
- ✅ 直接应用于GSL，MAPIRlab ROS2实现可用 (particle_filter action server)
- 在VM上已测试运行，属于baseline之一
- 项目中已有自实现版本 (simple_planners.py)

**迁移到UAV GSL的可行性: ★★★★★ (已实现)**
- 已经是GSL标准方法之一
- 适合作为baseline对照
- 可以通过改进似然模型(引入风向信息)提升性能

**潜在优势:**
- 天然处理多峰后验(多粒子表示)
- 可以融合任意复杂似然模型
- 计算开销可通过粒子数调节
- 与DQA-AS的后验估计可以互补

**局限:**
- 粒子退化问题(在高维或稀疏观测下)
- 预测模型依赖先验(扩散步长敏感)
- 没有显式的空间平滑约束(正是MEMP要解决的问题)

---

### 1.2 Surge-Cast / Spiral / Zigzag (反应式方法)

**核心数学框架:**
- 无需显式概率模型，基于即时传感器反馈的有限状态机(FSM)
- **Surge-Cast**: 两个状态
  - SURGE: 沿上风方向移动 (方向 = -wind_unit_vector)
  - CAST: 横向搜索，当丢失烟羽时展开(几何扩展: cast_amplitude *= expand_factor)
  - 状态切换: 连续N次miss → CAST; 检测到hit → SURGE
- **Spiral**: 对数螺旋线搜索，r = a + b·θ
- **Zigzag**: 固定角度的横向扫描模式

**关键文献:**
- Hayes et al., "Distributed chemical plume mapping" (2002) — 原始Surge-Cast
- Russell et al., "A comparison of reactive and bug-inspired search strategies" (2003)
- MAPIRlab实现: surge_cast, surge_spiral, spiral action servers

**已有气体溯源应用:**
- ✅ GSL标准基线方法
- MAPIRlab C++实现: surge_cast ~120-178s/run
- 项目自实现有3个bug (baseline audit发现):
  - 翻转频率错误(每步vs每10次miss)
  - 线性扩展vs几何扩展
  - 缺少向最近hit点漂移

**迁移到UAV GSL的可行性: ★★★★☆ (已实现但需修正)**

**潜在优势:**
- 计算极轻(无需维护后验)
- 不依赖环境模型(reactive, model-free)
- 在有风条件下表现合理
- 适合在线实时执行

**局限:**
- 无记忆性(不积累历史信息)
- 在复杂室内环境(多房间、气流紊乱)表现差
- 无法声明源位置(只是跟踪，不估计源)
- House03上表现极差(零分化)

---

### 1.3 Infotaxis (信息论方法)

**核心数学框架:**
- **核心思想**: 在每个时间步选择使期望信息增益(EIG)最大的移动方向
- 后验: P(s|z_{1:t})，源位置s在网格上的概率分布
- 熵: H_t = -Σ_s P(s|z_{1:t}) · log P(s|z_{1:t})
- 候选动作: a ∈ {8个方向 + 原地停留}
- 碰撞概率模型(物理核心): p_hit(x, s) 基于扩散-对流方程
  - 静止流体: p_hit ∝ 1/(4πD·t) · exp(-||x-s||^2/(4Dt))
  - 有风: p_hit ∝ 1/(4πD·t) · exp(-||x-s-vt||^2/(4Dt))，v为风速
- EIG: EIG(a) = H_t - E_{z_{t+1}}[H_{t+1}]
  - = H_t - [p_hit·H_hit + (1-p_hit)·H_miss]
- 选择: a* = argmax_a EIG(a)

**关键文献:**
- Vergassola, Villermaux, Shraiman, "Infotaxis as a strategy for searching without gradients" Nature 2007
- Loisy & Eloy, "Infotaxis and its variants" 2022
- MAPIRlab实现 (MAPIRlab/GasSourceLocalization)

**已有气体溯源应用:**
- ✅ GSL标志性方法，2007年Nature论文
- MAPIRlab C++实现可用
- 项目自实现有关键简化(无物理烟羽模型、无风向集成、miss更新有任意0.1缩放)

**迁移到UAV GSL的可行性: ★★★★☆ (理论最优但实际受限)**

**潜在优势:**
- 理论保证: 在扩散模型正确时，信息增益最优
- 自动平衡探索-利用(explore-exploit tradeoff)
- 不需要预设搜索模式

**局限:**
- 依赖精确的扩散-对流物理模型(室内环境难以满足)
- 计算开销: 每步需对所有候选方向计算EIG(涉及后验更新)
- 在项目测试中: House01 BestErr=3.93m, 仅1/2成功@2m
- 产生与KLD完全相同的结果(实现bug待确认)

**与DQA-AS的关系:**
- DQA-AS的Q因子可以看作Infotaxis EIG的改进版
- DQA-AS的核心问题: Q因子是"cosmetic"(记忆中的诊断结论)
- Infotaxis的问题: 后验太模糊导致EIG区分度低

---

### 1.4 Bayesian Inference / Gaussian Process 方法

#### 1.4a 贝叶斯网格方法 (PMFS风格)

**核心数学框架:**
- 网格后验: 将空间离散为网格 G，维护 P(s ∈ cell_i | z_{1:t})
- 似然模型: p(z_t | s) 基于气体扩散模型
  - PMFS: 使用advection-diffusion核 K(x, s, wind)
  - 网格更新: P(s|z_{1:t}) ∝ P(z_t|s) · P(s|z_{1:t-1})
- PMFS特有: Particle-based, 在网格上沉积"质量"
  - 每次hit: 在上风方向沉积概率质量
  - 每次miss: 降低当前位置附近的概率质量
- 声明: 当最大后验概率 > 阈值，或后验熵 < 阈值时声明源

**关键文献:**
- Monroy et al., "A new approach for gas source localization in indoor environments" (PMFS, 2017)
- MAPIRlab实现: PMFS ~30s/run, 效果最好的baseline

**已有气体溯源应用:**
- ✅ MAPIRlab主要方法之一，项目中有实现
- PMFS在VM上测试: 效果最好的baseline

**潜在优势:**
- 直觉清晰: 维护源位置的概率地图
- 可以融合多源信息(气体+风+占用网格)
- 声明机制灵活

**局限:**
- 声明时机不准(项目诊断: 0.6m处就声明，最佳距离可达3.65m)
- 假源锁定(posterior MAP锁定在错误位置)
- 间歇性烟羽处理差(固定阈值对filament plume不鲁棒)

#### 1.4b 高斯过程方法 (GP Gas Mapping)

**核心数学框架:**
- 浓度场建模: c(x) ~ GP(μ(x), k(x, x'))
- 核函数: 通常使用RBF + 白噪声
  - k(x, x') = σ_f^2 · exp(-||x-x'||^2/(2l^2)) + σ_n^2 · δ(x,x')
- 预测: c(x*) | D ~ N(μ_post, σ_post^2)
  - μ_post = K(x*, X) · [K(X,X) + σ_n^2·I]^{-1} · y
  - σ_post^2 = k(x*, x*) - K(x*,X)·[K(X,X)+σ_n^2·I]^{-1}·K(X,x*)
- 源定位: 找 argmax_x μ_post(x) 或 argmax_x acquisition_function(x)
- 采集函数: UCB, EI, PI 等

**关键文献:**
- Lilienthal et al., "Gas distribution modelling with the kernel DM+VW" (2009)
- Reggente & Lilienthal, "Using wind information for gas distribution" (2009)
- smueller18/TDKernelDMVW (时变核密度+风向加权)

**已有气体溯源应用:**
- ✅ 广泛用于气体分布建模
- KernelDMVW是MAPIRlab/tdkdm_vw的核心
- 项目中有ec_kdmv_package

**迁移到UAV GSL的可行性: ★★★☆☆**

**潜在优势:**
- 不确定性量化: 自然给出预测方差
- 可以融合风向信息(各向异性核)
- 连续空间表示(不需要离散化)

**局限:**
- 计算复杂度 O(n^3) (矩阵求逆)
- 超参数敏感(长度尺度l、噪声σ_n)
- 对非平稳场(室内复杂流动)建模困难
- 主要用于建模(事后分析)，不直接指导在线搜索

---

### 1.5 GrGSL (梯度-based GSL)

**核心数学框架:**
- 估计气体浓度梯度: ∇c ≈ (c(x+δ) - c(x-δ)) / (2δ)
- 沿梯度方向移动: x_{t+1} = x_t + η · ∇c(x_t)
- 变体: 结合wind信息的加权梯度
- 声明: 当梯度趋近于零且浓度足够高时

**关键文献:**
- MAPIRlab implementation: GrGSL action server
- 物理直觉: 气体从源扩散，浓度梯度指向源方向

**已有气体溯源应用:**
- ✅ MAPIRlab实现可用，VM上运行 ~120-136s/run
- 属于标准baseline

**迁移到UAV GSL的可行性: ★★★★☆ (已实现)**

**潜在优势:**
- 直觉简单: 沿浓度上升方向走
- 计算轻量
- 在平滑浓度场上快速收敛

**局限:**
- 梯度估计噪声大(传感器精度有限)
- 局部最优陷阱(多个局部极大值)
- 在间歇性烟羽中梯度方向不可靠
- 需要多步采样估计梯度(增加时间成本)

---

## 二、跨领域可迁移方法

### 2.1 脑源定位 (EEG Source Localization) → MEMP

**核心数学框架:**
- **前向模型**: V = L · J + ε
  - V: 头皮电位 (m个传感器)
  - L: 导联场矩阵 (m × n, n为候选源点数)
  - J: 源电流密度 (n维)
  - ε: 噪声
- **逆问题 (病态)**: 从V估计J，m << n (传感器远少于源)
- **主要方法族**:
  - **等效偶极子**: 参数化为少量偶极子 (1-3个)
  - **分布式方法**: 
    - **LORETA** (Low Resolution Electromagnetic Tomography)
      - min ||V - LJ||^2 + λ||∇^2 J||^2
      - 空间平滑约束: 假设相邻源点活动平滑
    - **MNE** (Minimum Norm Estimate)
      - min ||J||^2 s.t. ||V - LJ||^2 ≤ ε
    - **Beamformer** (LCMV, SAM)
      - w = R^{-1} · l / (l^T · R^{-1} · l)
      - 空间滤波器，逐点扫描
  - **稀疏方法**: 
    - L1正则化: min ||V - LJ||^2 + λ||J||_1
    - 游戏组LASSO: ||J||_{2,1}
- **关键数学工具**: Tikhonov正则化、SVD分解、图拉普拉斯

**关键文献:**
- Pascual-Marqui et al., "Low resolution electromagnetic tomography" (LORETA, 1994/2002)
- Hämäläinen & Ilmoniemi, "Interpreting magnetic fields of the brain" (MNE, 1994)
- Grech et al., "Review on solving the inverse problem in EEG source localization" (2008)
- Baillet et al., "Electromagnetic brain mapping" (2001)

**已有气体溯源应用:**
- ⚠️ 直接应用: 无 (文献中未找到)
- ✅ 项目中已有: **MEMP模块** (Medical Evidence Mass Processing)
  - 从LORETA提取图拉普拉斯平滑思想
  - P(s|z) ∝ P(z|s) · P(s) · exp(-λ·||L·s||^2)
  - 已实现于 workspace/uav_diagsense/src/memp/

**迁移到UAV GSL的可行性: ★★★★★ (已在项目中实现)**

**类比映射 (项目中的MEMP设计)**:
| EEG域 | GSL域 |
|-------|-------|
| 头皮传感器 | 气体传感器 |
| 脑偶极子 | 气体源 |
| 导联场L | 扩散传播核 |
| 电流密度J | 源概率分布 |
| 空间平滑 | 烟羽连续性 |

**潜在优势 (已验证):**
- 消除后验中的孤立虚假峰值
- 强制空间一致性(气体不会"瞬移")
- 计算开销低(拉普拉斯矩阵预先构建)
- 超参数少(仅平滑权重λ)

**进一步可迁移但尚未利用的EEG方法:**
- **Beamformer思想**: 构造空间滤波器逐点扫描源 → 可设计"浓度波束形成器"
- **多偶极子模型**: 假设有多个源 → 多气体源定位
- **时变源模型**: EEG中用Kalman跟踪移动偶极子 → 跟踪移动气体源

---

### 2.2 流行病学溯源 → BPFM

**核心数学框架:**
- **网络传播模型**: SIR/SIS模型在图G=(V,E)上传播
  - 感染概率: p_ij = 1 - (1-β)^{A_ij} (A为邻接矩阵)
- **Rumor Centrality** (Shah & Zaman 2011):
  - 在树状网络上，rumor centrality = 节点到所有感染节点的距离之和
  - 最大rumor centrality的节点 = 最可能的传播源
- **Jordan Center** (Luo et al. 2013):
  - source = argmin_v max_{u∈infected} d(v,u)
  - 在感染子图的中心
- **后验方法** (Altarelli et al. 2014):
  - P(source=v | infection_set) ∝ Π_{paths from v} p(infection|tree)
  - 使用Belief Propagation计算
- **反向追踪** (Comin & da Fontoura Costa 2011):
  - 从感染节点反向追踪传播路径
  - 沿网络传播方向回溯 → 类似于沿风向上溯

**关键文献:**
- Shah & Zaman, "Rumors in a network: Who's the culprit?" (IEEE TIT, 2011)
- Luo et al., "Finding the infection source of a network epidemic" (2013)
- Altarelli et al., "Bayesian inference of epidemics on networks" (2014)
- Riley, "Large-scale spatial-transmission models of infectious disease" (2007)
- Wallinga & Teunis, "Different epidemic curves for SARS" (2004) — 代际间隔法

**已有气体溯源应用:**
- ⚠️ 直接应用: 无 (文献中未找到)
- ✅ 项目中已有: **BPFM模块** (Bayesian Particle Flow Mapping)
  - 从流行病学"接触追踪"提取"沿风向反向追踪"思想
  - 粒子沿风场流动: hit时上溯(朝源)，miss时扩散(探索)
  - 已实现于 workspace/uav_diagsense/src/bpfm/

**迁移到UAV GSL的可行性: ★★★★★ (已在项目中实现)**

**类比映射 (项目中的BPFM设计)**:
| 流行病学域 | GSL域 |
|-----------|-------|
| 传播网络 | 风场(气流网络) |
| 感染链 | 烟羽轨迹 |
| 接触追踪 | 沿风向上溯 |
| 超级传播者 | 高浓度区域 |
| 感染概率 | 检测概率 |

**潜在优势:**
- 粒子自然集中到证据强的区域
- 风驱动流动比随机扩散更快收敛到源
- 天然处理多模态后验

**进一步可迁移但尚未利用的流行病学方法:**
- **Jordan Center**: 在离散化的空间网格上找最小最大距离中心 → 可用于粗定位
- **代际间隔法** (Wallinga-Teunis): 从多个检测点反推"第一代" → 多次encounter的时间反演
- **SIR传播模型**: 将烟羽传播建模为感染过程 → 概率传播图

---

### 2.3 DOA估计 (Direction of Arrival) → 空间谱方法

**核心数学框架:**
- **信号模型**: x(t) = A(θ)·s(t) + n(t)
  - x(t): m个传感器的观测向量
  - A(θ): 导向矩阵 [a(θ_1), ..., a(θ_K)]
  - a(θ): 导向向量 (传感器阵列对方向θ的响应)
  - s(t): K个源信号
  - n(t): 噪声
- **MUSIC算法** (Schmidt 1986):
  - 信号子空间: 由Rx = E[xx^H]的K个最大特征向量张成
  - 噪声子空间: 由m-K个最小特征向量张成
  - 空间谱: P_MUSIC(θ) = 1 / ||a^H(θ)·E_n||^2
  - 源方向 = P_MUSIC的K个峰值
- **ESPRIT算法** (Roy & Kailath 1989):
  - 利用阵列的平移不变性
  - 不需要扫描，直接估计
  - Φ = E_s1^{-1} · E_s2 (两个子阵列的信号子空间旋转矩阵)
- **Cramér-Rao下界**: 给出DOA估计的理论精度极限
- **稀疏贝叶斯学习**: 将DOA视为稀疏恢复问题

**关键文献:**
- Schmidt, "Multiple emitter location and signal parameter estimation" (MUSIC, 1986)
- Roy & Kailath, "ESPRIT" (1989)
- Stoica & Nehorai, "MUSIC, maximum likelihood, and Cramér-Rao bound" (1989)
- Malioutov et al., "A sparse signal reconstruction perspective for source localization" (2005)

**已有气体溯源应用:**
- ⚠️ 直接应用: 非常有限
  - 声学DOA用于UAV声源定位 (区别于气体)
  - 少数论文将阵列信号处理思想用于无线传感器网络源定位
- ❌ 未见用于气体源定位

**迁移到UAV GSL的可行性: ★★★☆☆ (理论潜力大，实际挑战多)**

**类比映射:**
| DOA域 | GSL域 |
|-------|-------|
| 传感器阵列 | UAV多个采样点(时序采集) |
| 导向向量a(θ) | 扩散模型对源位置的响应 |
| 信号子空间 | "源信号"子空间 |
| 噪声子空间 | 噪声/干扰子空间 |
| 空间谱P(θ) | 源位置概率图 |

**潜在优势:**
- 超分辨率: MUSIC/ESPRIT可以分辨比Rayleigh极限更近的源
- 子空间分解: 将"源信号"与"噪声"分离 → 区分真实源和干扰
- 统计效率高: 接近Cramér-Rao下界

**挑战:**
- DOA假设远场(平面波)，气体扩散是近场(球面波衰减)
- DOA需要同时多传感器采集，UAV是时序单传感器
- 需要对扩散场建模"导向向量" → 物理模型依赖
- 可能需要多次轨迹的数据积累才能构造"等效阵列"

**可探索方向:**
- 将UAV多次采样视为"虚拟阵列"，用MUSIC思想扫描源位置
- 用子空间分解思想将"信号"(源贡献)从"噪声"(湍流/干扰)中分离
- 与MEMP结合: EEG方法族本身就包含beamformer变体

---

### 2.4 压缩感知 (Compressed Sensing) → 稀疏源定位

**核心数学框架:**
- **稀疏信号模型**: y = Φ·x + n
  - y: m维观测 (m << N)
  - Φ: m×N感知矩阵
  - x: N维信号，K稀疏 (仅K个非零)
  - n: 噪声
- **恢复条件**:
  - RIP (Restricted Isometry Property): (1-δ)||x||^2 ≤ ||Φx||^2 ≤ (1+δ)||x||^2
  - 不相干性: 感知矩阵与稀疏基不相关
- **恢复算法**:
  - **BP (Basis Pursuit)**: min ||x||_1 s.t. ||y - Φx||_2 ≤ ε
  - **OMP (Orthogonal Matching Pursuit)**: 贪心选择最相关的列
  - **ISTA/FISTA**: 迭代收缩阈值
  - **BP denoising**: min ||x||_1 s.t. ||y-Φx||_2 ≤ ε
- **稀疏贝叶斯学习 (SBL)**: x ~ N(0, Γ), Γ对角，自动确定稀疏模式

**关键文献:**
- Candès, Romberg & Tao, "Robust uncertainty principles" (2006)
- Donoho, "Compressed sensing" (2006)
- Malioutov et al., "A sparse signal reconstruction perspective for source localization" (2005) — DOA+CS
- Wipf & Rao, "An empirical Bayesian strategy for solving simultaneous sparse approximation" (SBL, 2007)

**已有气体溯源应用:**
- ⚠️ 非常有限
  - Matthes et al., "Source localization in sensor networks using sparse Bayesian learning" (2005)
  - 少数无线传感器网络论文
- ❌ 未见直接用于UAV气体源定位
- ✅ 项目中已有: **SDM模块** (Sparse Deconvolution Mapping)
  - 从图像去模糊提取L1稀疏反卷积思想
  - min ||K*s - b||^2 + λ||s||_1 (ISTA算法)
  - 已实现于 workspace/uav_diagsense/src/sdm/

**迁移到UAV GSL的可行性: ★★★★☆ (SDM已部分实现)**

**类比映射:**
| CS域 | GSL域 |
|------|-------|
| 稀疏信号x | 源分布(通常1-2个点源 → 极度稀疏) |
| 感知矩阵Φ | 扩散传播核K |
| 观测y | 采集到的后验(被风模糊的) |
| L1正则化 | 源稀疏先验 |

**潜在优势:**
- 源定位问题天然是稀疏的(少量点源) → CS理论保证
- SDM已验证: L1反卷积可以去除风导致的后验模糊
- 与贝叶斯框架自然融合

**进一步可利用的CS技术:**
- **SBL (Sparse Bayesian Learning)**: 自适应确定稀疏度，比固定λ的L1更鲁棒
- **Group Sparsity**: 如果有多源，可以用group LASSO
- **Adaptive CS**: 根据已有观测自适应选择下一个采样点 → 指导UAV路径

---

### 2.5 概率图模型 (Bayesian Network, MRF) → 结构化后验

**核心数学框架:**
- **贝叶斯网络 (BN)**:
  - 有向无环图 G=(V,E)，P(X_1,...,X_n) = Π_i P(X_i | Parents(X_i))
  - 推理: 变量消元、信念传播、Junction Tree
- **马尔可夫随机场 (MRF)**:
  - 无向图，P(x) = 1/Z · Π_{cliques c} ψ_c(x_c)
  - 势函数ψ_c编码局部一致性
  - 全局条件: P(x_i | x_{-i}) = P(x_i | neighbors(x_i))
- **条件随机场 (CRF)**:
  - P(y|x) = 1/Z(x) · Π_t ψ_t(y_t, y_{t-1}, x_t)
  - 用于序列标注 → 可用于时序气体观测
- **推断方法**: 
  - 精确: 变量消元、Junction Tree
  - 近似: Loopy BP、Mean Field、MCMC

**关键文献:**
- Koller & Friedman, "Probabilistic Graphical Models" (2009, 教科书)
- Kindermann & Snell, "Markov Random Fields" (1980)
- Bishop, "Pattern Recognition and Machine Learning" (2006, Ch 8)

**已有气体溯源应用:**
- ⚠️ 有限应用
  - MRF用于气体分布图重建 (3D气体场的正则化)
  - BN用于多传感器融合
- ❌ 未见直接用于GSL源定位
- MEMP模块中的图拉普拉斯实际上是一种MRF先验(隐式)

**迁移到UAV GSL的可行性: ★★★☆☆ (理论框架好，实用化需大量工作)**

**类比映射:**
| PGM域 | GSL域 |
|-------|-------|
| 图节点 | 空间网格点 |
| 边 | 空间邻接关系 |
| 势函数 | 烟羽连续性/浓度相似性 |
| 推断 | 后验计算 |

**潜在优势:**
- 可以建模复杂的依赖关系(风向、障碍物、多房间拓扑)
- MRF的局部一致性天然适合烟羽的平滑假设
- BN可以编码因果关系(源→烟羽→传感器→观测)
- CRF可以建模时序观测的转移关系

**挑战:**
- 模型设计复杂(需要定义合理的图结构和势函数)
- 推断计算量大(精确推断在大图上不可行)
- 需要大量数据训练参数

---

### 2.6 控制理论中的自适应搜索策略

**核心数学框架:**
- **源搜索控制问题**:
  - 状态: x_t = (UAV位置, 后验状态)
  - 控制: u_t = 下一步移动方向/距离
  - 目标: 最小化到达源的时间/距离
- **Extremum Seeking Control (ESC)**:
  - 实时估计梯度: ∂J/∂x ≈ [J(x+δ·sin(ωt)) - J(x-δ·sin(ωt))] / (2δ)
  - 更新: x_{t+1} = x_t + α · sign(∂J/∂x)
  - 不需要模型，纯反馈驱动
- **Model Predictive Control (MPC)**:
  - min_{u_{0:H}} Σ_{t=0}^H cost(x_t, u_t) + terminal_cost(x_H)
  - s.t. x_{t+1} = f(x_t, u_t) (动力学约束)
  - 滚动时域: 每步重新优化
- **Reinforcement Learning (RL)**:
  - Q(s,a): 状态-动作值函数
  - 策略π: 状态→动作映射
  - 可以学习复杂的搜索策略

**关键文献:**
- Krstić & Wang, "Stability of extremum seeking feedback for general nonlinear dynamic systems" (2000)
- Scheideman, "A survey of source seeking algorithms" (2005)
- Various: Bayesian Optimization for source seeking (Gutmann & Corander, 2006)
- Zhang et al., "Robot odor source localization using bio-inspired and Bayesian strategies" (2019)

**已有气体溯源应用:**
- ✅ ESC已用于简单的气味源搜索机器人
- ✅ Bayesian Optimization用于自适应采样
- ⚠️ MPC和RL在GSL中应用较少

**迁移到UAV GSL的可行性: ★★★★☆**

**类比映射:**
| 控制理论域 | GSL域 |
|-----------|-------|
| 性能指标J | 负后验熵/浓度倒数 |
| 控制输入u | UAV移动指令 |
| 系统动力学f | UAV运动模型 |
| 干扰 | 湍流、风变化 |

**潜在优势:**
- ESC: 无需模型，纯反馈，适合未知环境
- MPC: 可以预测性规划(考虑未来多步)
- RL: 可以学习复杂的室内搜索策略(需要训练数据)

**与DQA-AS的关系:**
- DQA-AS的Q因子本质上是一种extremum seeking的变体
- 可以将DQA-AS框架化为MPC: 目标函数 = Q因子，约束 = UAV动力学
- RL可以学习DQA-AS中需要手动调优的超参数

---

## 三、方法对比与DQA-AS创新定位

### 3.1 已有创新模块在方法谱系中的位置

| 模块 | 源领域 | 解决的核心问题 | 方法类别 |
|------|--------|---------------|---------|
| **MEMP** | EEG脑源定位 | 后验孤立峰值 | 空间正则化 |
| **BPFM** | 流行病学 | 粒子效率低 | 粒子流动 |
| **SDM** | 图像去模糊 | 风模糊后验 | 稀疏反卷积 |
| **DQA-AS** | 自身设计 | 声明时机 | 决策质量因子 |

### 3.2 经典方法的共同弱点 (DQA-AS的攻击面)

1. **后验模糊问题**: 所有贝叶斯方法在风存在时后验都向下游延伸
   - SDM直接解决: L1反卷积去模糊
   
2. **空间一致性缺失**: 网格后验有孤立虚假峰
   - MEMP直接解决: 图拉普拉斯平滑
   
3. **粒子效率低**: 粒子滤波在稀疏观测下退化
   - BPFM直接解决: 风驱动流动
   
4. **声明时机不准**: 阈值方法在后验模糊时误判
   - DQA-AS解决: Q因子决策质量评估

### 3.3 未被利用的跨领域方法 (潜在SCI3创新方向)

| 方法 | 源领域 | 潜在GSL应用 | 创新性 | 实现难度 |
|------|--------|------------|--------|---------|
| **Beamformer** | DOA/EEG | 空间滤波扫描源 | ★★★★ | ★★★ |
| **SBL** | 压缩感知 | 自适应稀疏源估计 | ★★★★ | ★★★ |
| **Jordan Center** | 流行病学 | 网格上快速粗定位 | ★★★ | ★★ |
| **MPC** | 控制理论 | 预测性路径规划 | ★★★ | ★★★★ |
| **CRF** | 概率图模型 | 时序观测结构化推理 | ★★★★ | ★★★★ |

### 3.4 与SCI3论文的关联

**论文叙事线索:**
- 问题: UAV GSL中Bayesian posterior在风场下模糊→声明失败
- 现有方法: PMFS/GrGSL/Infotaxis都有此问题但未解决
- 创新: 从3个非机器人/嗅觉领域引入3个互补模块
  - MEMP (EEG) → 空间平滑
  - BPFM (流行病学) → 风驱动粒子
  - SDM (图像处理) → 稀疏反卷积
- 核心贡献: **Observation-Planning-Coupling-Gap** — 没有现有方法将传感器动力学集成到贝叶斯后验更新中

---

## 四、关键参考文献汇总

### 经典GSL
1. Vergassola et al., "Infotaxis as a strategy for searching without gradients", Nature, 2007
2. Monroy et al., "A new approach for gas source localization in indoor environments", 2017 (PMFS)
3. Lilienthal et al., "Statistical gas distribution modelling with the kernel DM+VW", 2009
4. Hayes et al., "Distributed chemical plume mapping", 2002 (Surge-Cast)
5. MAPIRlab/GasSourceLocalization, https://github.com/MAPIRlab/GasSourceLocalization

### 跨领域 - EEG/脑源
6. Pascual-Marqui et al., "Low resolution electromagnetic tomography: a new method", Brain Topography, 1994
7. Hämäläinen & Ilmoniemi, "Interpreting magnetic fields of the brain", Medical & Biological Engineering, 1994
8. Grech et al., "Review on solving the inverse problem in EEG source localization", Clinical Neurophysiology, 2008
9. Baillet et al., "Electromagnetic brain mapping", IEEE Signal Processing Magazine, 2001

### 跨领域 - 流行病学
10. Shah & Zaman, "Rumors in a network: Who's the culprit?", IEEE TIT, 2011
11. Luo et al., "Finding the infection source of a network", IEEE ISIT, 2013
12. Altarelli et al., "Bayesian inference of epidemics on networks via Belief Propagation", PRL, 2014
13. Wallinga & Teunis, "Different epidemic curves for SARS reveal similar impacts", PNAS, 2004

### 跨领域 - DOA/信号处理
14. Schmidt, "Multiple emitter location and signal parameter estimation", IEEE TAP, 1986
15. Roy & Kailath, "ESPRIT", IEEE TASSP, 1989
16. Malioutov et al., "A sparse signal reconstruction perspective for source localization", IEEE TSP, 2005

### 跨领域 - 压缩感知
17. Candès et al., "Robust uncertainty principles: exact signal reconstruction", IEEE TIT, 2006
18. Donoho, "Compressed sensing", IEEE TIT, 2006
19. Wipf & Rao, "An empirical Bayesian strategy for solving simultaneous sparse approximation", 2007

### 跨领域 - 控制理论
20. Krstić & Wang, "Stability of extremum seeking feedback", Automatica, 2000
21. Zhang et al., "Robot odor source localization using bio-inspired and Bayesian strategies", 2019
