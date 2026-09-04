# G2-M2 重新设计：神经算子分裂的 bank-free 输运预测（跨领域借鉴 2026 文献）

## 一、为什么旧 M2 失败（一句话）

旧 M2 的"增量"是「F11 最近 wind vs F10 历史 max」——这是**工程 hack，不是科学思想**，所以两次 screen 结果相反（2胜1负 ↔ 1胜2负），是 ±5% 的噪声。M2 缺的是：一个**可跨环境泛化的输运预测机制**，而不是一个 wind 选取技巧。

## 二、2026 年可借鉴的跨领域思想（文献）

### 主线 1：神经算子分裂 + 组合泛化（Neural Operator Splitting）

| 文献 | 出处 | 核心思想 |
|---|---|---|
| **Origo** | ICML 2026 | 把 PDE 演化分解为「全局谱线性算子（扩散/输运）+ 局部本构算子库（非线性）」，用 **Strang splitting** 组合。学的是"物理字母"（advection/diffusion/reaction 原子算子），遇到**未见过的新 PDE** 时用正确组合激活——**compositional generalization** |
| **Test-time Neural Operator Splitting** | 2026 | 训练一个"算子字典"（Euler 对流 + 扩散），test-time 用 **Lie/Strang splitting** 组合，**zero-shot** 泛化到训练外的新物理（比 MPP/Zebra/GEPS 等基础模型低一个数量级 NRMSE） |
| **CompNO** | arXiv 2601.07384, 2026 | 先学 **Foundation Blocks**（每个是专门的 FNO，学 convection / diffusion / nonlinear convection），再用 Adaptation Blocks 组装成任务特定 solver |

**借鉴点**：M2 的 bank-free 输运不该"端到端学一个黑箱浓度场"，而该学**两个物理原子算子**（advection + diffusion），在任何 House 上**组合复用**——这直接实现「held-out House 不查 bank」的泛化要求。

### 主线 2：Committor 函数（稀有事件/过渡路径理论，从化学统计物理借来）

| 文献 | 出处 | 核心思想 |
|---|---|---|
| **Following the Committor Flow** | JCTC 2026 | 用 NN 学 **committor 概率 q(x)** = 轨迹从 x 出发先到达目标 B 的概率，是最 informative 的一维反应坐标。迭代式：初始猜测 → 偏置采样 → 训练 NN → 提取主导通道 → 增强采样 → 收敛 |
| **DASTR** | JCP 2026 | 用**变分损失**（而非残差损失，只需一阶导）估计高维 committor，深度自适应采样解决稀有事件数据稀缺 |

**借鉴点**：M2 的 `p(O_future)` 本质是一个 committor——「气团从源 S 出发，未来到达观测点 a 邻域的概率」q(源位置 | wind, geometry)。这给出了 M2 的**后向（backward Kolmogorov）数学形式**，与 forward 的 operator splitting 互补。

### 主线 3：Non-myopic 主动实验设计（对 M3，但 M2 的预测要支撑它）

| 文献 | 出处 | 核心思想 |
|---|---|---|
| **Sequential BOED via Policy Gradient RL** | arXiv 2601.05868, 2026 | SBOED 表述为 MDP，policy-gradient 学 amortized 设计策略，用 active-subspace 降维 + LANO 神经算子代理。学出的策略是**「上游（upstream）追踪」** |
| **Actively inferring methane sources with drones** | Environmental Data Science 2026 | Bayesian + RL：**non-myopic（多步前瞻）一致优于 myopic（贪心）**；「精确定位需要在**源附近、包括略上游**采样」 |

**借鉴点**：直接印证了之前诊断的「探索-利用困境」——M3 需要 non-myopic（多步前瞻），而多步前瞻**依赖 M2 提供可靠的未来观测预测**。这确立了 M2 → M3 的依赖关系。

### 主线 4：生成式算子（湍流高频结构）

| 文献 | 出处 | 核心思想 |
|---|---|---|
| **Learning turbulent flows with generative models** | Nature Communications 2026 | 神经算子 + 对抗训练克服 L2 过平滑，能量谱误差降 15× |

## 三、M2 新设计：算子分裂的时变输运预测

### 3.1 数学形式

目标：`(geometry, online wind, S, a, M_t) → p(O_future)`，bank-free。

把输运建模为 **advection-diffusion 的算子分裂数值解**：

$$\frac{\partial C}{\partial t} = \underbrace{-\nabla\cdot(\mathbf{u}\,C)}_{\text{advection}} + \underbrace{D\,\nabla^2 C}_{\text{diffusion}} + \underbrace{q\,\delta(x-S)}_{\text{source}}$$

用 **Strang splitting** 分解为两个原子算子，多步推进：

$$\boxed{C_{t+\Delta t} = \mathcal{A}_{\Delta t/2}\,\mathcal{D}_{\Delta t}\,\mathcal{A}_{\Delta t/2}\,C_t}$$

- **Advection 算子 $\mathcal{A}$**：沿 online wind 场 $\mathbf{u}(x,t)$ 平流。**纯物理，不需要学**——直接读真实 wind 数据（Lagrangian 位移或半拉格朗日）。
- **Diffusion 算子 $\mathcal{D}$**：湍流扩散，$D$ 从 bank 数据**标定一次**（用一个 House 的浓度场反推等效 $D$），此后在**任何 House 复用**。

### 3.2 为什么这是「跨领域思想」，而不是又一个 hack

| 维度 | 旧 M2（hack） | 新 M2（算子分裂） |
|---|---|---|
| 机制 | 选一个 wind（最近 vs 历史 max） | 组合两个物理原子算子（advection ∘ diffusion） |
| 泛化 | 无（依赖单 House 的 bank） | **compositional**：算子与 House 无关，新 House 只需新 wind + geometry |
| 时变性 | 稳态 plume（抹掉风向） | **时变**：splitting 多步推进真实时变 wind |
| 科学依据 | 无 | Strang splitting（数值分析）+ operator bank（Origo/CompNO）+ committor（JCTC） |

### 3.3 与 committor 的对偶（后向视角）

Forward（浓度场推进）的对偶是 **committor**：q(x) 满足 backward Kolmogorov 方程，q(源 S) 就是「源 S 的羽流未来到达观测点 a」的概率。两者共享同一个 advection-diffusion 算子，M2 可以：
- **Forward**：给 M3 做 non-myopic 前瞻（预测"去 a 会采到什么浓度"）。
- **Backward（committor）**：给 M1 做似然（P(观测点 a 被源 S 的羽流覆盖)）。

这使 M1/M2/M3 共享**同一个输运算子**，而不是各自维护一套 bank 查询。

## 四、落地路径（分阶段，每步可 falsify）

1. **L0（离线验证，最快）**：用真实时变 wind，operator splitting 求解 advection-diffusion（数值实现 advect + diffuse），对比旧 Gaussian plume 在下游观测的定位 rank。判据：**splitting 应显著优于稳态 plume（rank 197/94 → 逼近 36 的瞬时场）**。
2. **L1（committor 形式）**：用变分损失学 backward Kolmogorov 的 committor，验证「源 S → 观测点 a」概率与 forward 一致性。
3. **L2（held-out 泛化）**：在 H01 标定 D，直接迁移到 H02/H03（不重训、不查 H02/H03 bank），验证跨 House 的 bank-free 泛化——**这是 M2 真正的承重点，也是当前 screen 完全没测的能力**。

## 五、判据（预注册）

- M2 承重 = **F11 vs F10 在 held-out House 上的 downstream 增量 ≥ 预注册阈值**（而非 240s 单 House 的 ±5% 噪声）。
- bank-free = **H02/H03 上不查询该 House 的 bank**，只用 H01 标定的 D + online wind + geometry。
