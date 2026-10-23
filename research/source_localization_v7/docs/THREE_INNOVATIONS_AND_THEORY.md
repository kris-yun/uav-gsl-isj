# V7 三模块创新身份证与条件理论

版本：2026-10-23。本文按当前源码、M3 的 [THEORY.md](../src/gsl_discrimination/m3_audit/THEORY.md)、冻结静态 pilot 和冻结 L1 控制矩阵整理。**“三模块”指三个可检查的机制设计，不表示三项独立创新已经由真实气源实验验证。**

## 0. 当前结论和证据边界

| 层面 | 已完成 | 尚不能声称 |
|---|---|---|
| M1 | 物理受限镜像滤波 bank、源对覆盖选通道、一次联合符号、固定总 Dirichlet 平滑、公平 best-one | 相同原始观测的信息被确定性特征增加；精确复现原论文自由训练 MNM；动态主机制已经胜出 |
| M2 | 因果相对方向记忆、不确定管、源响应差双点动作与管外复测、21 项目标测试 | 记忆是独立源证据；恢复羽流即识别源；已完成 native UAV 闭环 |
| M3 | 成本分配、付费持续覆盖、新后缀审计、18 项目标测试及条件性风险证明 | 估计通道天然等于真实 plume 条件律；五次采样必恢复；已实现 ISIT2025 全套分簇算法 |
| 静态 OCB | raw-joint 与可逆 EO 均 40/40，新静态 M1 为 31/40 | 新静态编码优于强联合基线 |
| 冻结 L1 矩阵 | 13 变体、156 episodes；完整流程及各分支能运行 | 强基线和主要消融均饱和时，full 具有独立性能增益 |

本文证明的是结构性质及明确模型下的结论。应用新颖性需要独立、同资源、物理合格的实验；数学正确性不能代替该证据。正式来源、阅读深度与迁移链见 [CROSS_DOMAIN_DISCOVERY_AND_TRANSFER.md](CROSS_DOMAIN_DISCOVERY_AND_TRANSFER.md)。

## 1. 统一符号、信息边界和观测所有权

研究标签沿用用户约定：**A=PMFS/气源定位原任务与方法，B=母算法原领域，C=第三领域；A′=同资源的强联合统计基线，B 对照=母算法迁入 A 的必要适配，B′=针对 A 故障的二次改造。**本轮 `A_adapted_variance` 并非 native PMFS 复现，B 对照也不表示全部母论文已经精确复现。详细消融映射见 [跨域文档 §5](CROSS_DOMAIN_DISCOVERY_AND_TRANSFER.md)。以下复杂度公式中的数学量 \(A\)（动作数）、\(B\)（校准块数）是计数符号，与上述研究标签不同。

设源集 \(\mathcal S=\{1,\ldots,S\}\)，合法配对动作集大小为 \(A\)，共享 nuisance 有 \(R\) 个值。一块同步双侧窗口有 \(L\) 个真实时间样本，校准集每个动作/源/nuisance 有 \(B\) 个块；候选滤波器数为 \(F\)，选中通道最多 \(K\)，联合字母表大小为 \(O\)。M2 另有 \(N\) 个中心、\(D\) 个间距、\(U\) 个方向，几何合法动作数至多 \(NDU\)。

用 \(\alpha_D\) 表示直方图的**总平滑质量**，用 \(\alpha_A\) 表示审计错误阈值。两者不是同一个量。代码中分别是 `calibrate_source_contrast(..., alpha=...)` 和 `AuditLedger(..., alpha=...)`，不得混用其解释。

\(\mathcal F_{t-1}\) 包含策略真正已见的全部过去信息，包括用于动作建议的行进期观测。第 \(t\) 个动作及其预测必须在新结果 \(Z_t\) 到达之前确定。理想观测表的语义为

\[
P_t(a,s,r,z)=\Pr(Z_t=z\mid \mathcal F_{t-1},A_t=a,S=s,R=r).
\tag{1}
\]

每个假设面对同一条**实际发生的观测历史**。可以有不同假设条件下的隐状态滤波，但不能为不同源换成不同的已见历史，亦不能读未来真风或测试世界未观测的整幅浓度场。

实现载体是 [FiniteChannel / JointPosterior](../src/gsl_discrimination/channel.py)，表形状为 `[A,S,R,O]`。nuisance 在一段 episode/audit 内共享，不能每步重新积分为一个独立新值。固定表只代表 memoryless 通道或已合理证明条件独立的块；更一般的历史依赖必须给出正确条件增量。数据有时间戳、窗口不重叠，均不自动证明这些条件。

**一块物理观测只编码一次、只进入源后验一次。**M2 的 memory、M1 派生特征、审计 e-value 都不是新物理观测。审计可以对同一原始事件做独立的决策计算，但不能把其结果再作为似然回乘源后验。[原始记录账本](../src/gsl_discrimination/ledger.py) 拒绝重复 ID、重叠/倒序窗口和部署块内的真源标签；事件 ID 本身不能识别被客户端换名后重复提交的数据。

## 2. M1 身份证：源对覆盖的物理受限镜像通道

### 2.1 问题、母机制与二次设计

**针对故障：**浓度标量/均值相近的候选可能在双点联合时序中有差异；单一中心线侧别任务却不一定保留区分纵向距离、释放条件和其他源对所需的信息。

**母机制：**PNAS 2026 的双侧时间滤波、ReLU 与镜像相减。原论文的重要证据是任务训练得到的低阶结构、环境依赖性及行为对应，不能把经典 Reichardt/Barlow–Levick 家族重新当作 2026 新发明。当前代码使用有限指数核族，是该算子族的受限实现，不是原论文自由滤波系数的精确复现。[PNAS 原文](https://emonet.biology.yale.edu/assets/papers/2026/2026_brudner-et-al-PNAS-fly-navigational-responses-exploit-plume.pdf)

**二次设计 B′：**按动作和竞争源对的联合符号分离选择少量通道，保留偶部强度，一次输出 \(P(z\mid s,r,a)\)。目标由单侧别输出改为覆盖多个源对；JS、贪心选择和直方图本身不声称新。

源码：[operator.py](../src/gsl_discrimination/m1_opponent/operator.py)、[calibration.py](../src/gsl_discrimination/m1_opponent/calibration.py)。

### 2.2 输入、状态、输出

| 阶段 | 输入 | 状态/输出 |
|---|---|---|
| 校准 | `raw[A,S,R,B,L,2]`、真实 `times[L]`、`SamplingContract`、源/动作标识、成本、bank | 每动作选中通道、偶/奇阈值、一个 `[A,S,R,O]` 联合表和训练诊断 |
| 在线 | 动作编号、完整原始双侧窗口、同一相对采样时钟及资格 | `SourceContrastModel.encode` 返回一个联合符号 |
| 共享后验 | 一个动作、一个符号、唯一事件 ID | 更新所有 `(source,nuisance)` 权重，再对 nuisance 求源边缘 |

`encode(times=None)` 可使用冻结重播时钟；原生适配器必须显式传入实际时钟。改变窗口时长或相对采样间隔需要重校准通道。`SamplingContract` 是调用方承诺加结构检查，不是传感器标定实验本身。

### 2.3 实际预处理与非均匀时钟

双侧原值先作

\[
y_{n,i}=\log\left(1+\frac{\max(x_{n,i}-b_0,0)}{s_0}\right),\qquad s_0>0.
\tag{2}
\]

设 \(t_0<\cdots<t_{L-1}\)。当 \(L>1\) 时梯形权重为

\[
\tilde w_0=\frac{t_1-t_0}{2},\quad
\tilde w_n=\frac{t_{n+1}-t_{n-1}}2,\quad
\tilde w_{L-1}=\frac{t_{L-1}-t_{L-2}}2,
\quad w_n=\frac{\tilde w_n}{t_{L-1}-t_0}.
\tag{3}
\]

单张静态快照的权重为 1。当前偶部及 gradient 分支为

\[
E=\sum_nw_n\frac{y_{n,L}+y_{n,R}}2,
\qquad G=\sum_nw_n\frac{y_{n,L}-y_{n,R}}2.
\tag{4}
\]

式 (3) 正是对分段线性插值的时间积分平均；它避免密集采样区域被按帧数过度加权。它不恢复缺失的高频数据，也不证明稀疏快照适合动态滤波。

MNM 核当前使用另一项明确的因果离散求积：\(\Delta_0=t_1-t_0\)，\(\Delta_n=t_n-t_{n-1}\)；对终点 \(T\)、滞后 \(\ell\) 与衰减 \(\gamma>0\)，

\[
w_n^{(\ell)}\propto
\mathbf1\{t_n\le T-\ell\}\exp[(t_n-(T-\ell))/\gamma]\Delta_n,
\qquad \sum_n w_n^{(\ell)}=1.
\tag{5}
\]

这里的截断指数核是代码的求积定义，**不是声称所有核都使用式 (3) 的梯形权**。没有足够历史支持时拒绝该滞后，不向未来插值。

### 2.4 镜像整流与联合编码

当前受限 bank 用

\[
f_{1k}=w^{(0)}-\eta_k w^{(\ell_k)},\quad f_{2k}=-w^{(0)},
\]
\[
q_k(L,R)=\operatorname{ReLU}(\langle f_{1k},L\rangle+\langle f_{2k},R\rangle+b_k),
\quad h_k(L,R)=q_k(L,R)-q_k(R,L).
\tag{6}
\]

默认动态 bank 为一个静态 gradient 加六个延迟/抑制组合；这些时间尺度是研究配置，不能称已由 UAV 测得。非 gradient 分支要求连续资格、已标定带宽、足够样本及最大采样间隔；正滞后还要求时钟误差与传感器差分延迟之和小于该滞后的三分之一。资格不满足时不能仅通过改布尔值将 X00 快照升级成 motion。

每动作的偶部阈值为训练中位数，奇部阈值为训练绝对响应的 0.4 分位数并设数值下限。选中通道集合 \(F_a=(k_0,\ldots,k_{K_a-1})\) 后，

\[
e=\mathbf1\{E>\theta_E\},\qquad
q_k=1+\mathbf1\{h_k>\theta_k\}-\mathbf1\{h_k<-\theta_k\},
\]
\[
z=e+2\sum_{j=0}^{K_a-1}3^j q_{k_j},\qquad O_a=2\cdot3^{K_a}.
\tag{7}
\]

零附近为三值码的中间值。不同动作的较短字母表补不可到达的零概率单元以形成统一张量；这不是增加新结果的平滑质量。

### 2.5 固定总平滑质量与源对覆盖

每个源/nuisance 的训练块计数为 \(n_{sr}(z)\)，总块数为 \(B\)。当前默认

\[
\widehat P_F(z\mid s,r,a)=
\frac{n_{sr}(z)+\alpha_D/O_a}{B+\alpha_D}.
\tag{8}
\]

`legacy_per_cell` 只保留给冻结 pilot 的追溯，不能在新增通道时让总先验质量随字母表成倍变化而将该变化算作信息增益。

定义

\[
\psi_{ij}(F,a)=\min_{r,r'}\operatorname{JS}\big(\widehat P_F(\cdot\mid i,r,a),\widehat P_F(\cdot\mid j,r',a)\big),
\]
\[
J_a(F)=\sum_{i<j}\min\{\psi_{ij}(F,a),\kappa\}.
\tag{9}
\]

每轮选使 \(J_a(F\cup\{k\})-J_a(F)\) 最大的未选通道。增益不超过门槛、达到数量上限或所有源对达到目标时停止。最坏 nuisance 比较属于训练覆盖准则；它没有将 nuisance 的物理值在 episode 中改成逐步重抽。

当前公平对照为：

- `mother`：同 bank、同 TRAIN 目标的 best-one，而不是固定取第 0 项静态梯度。
- `fixed_two`：预先固定索引 0 与 `min(3,F-1)`，去重并受 `max_filters` 限制，不用开发结果选索引。
- `even`：仅保留偶部位。
- `raw_joint`：对完整双侧时间窗口作无监督向量量化，默认 18 个符号、同总平滑质量，见 [raw_joint.py](../src/gsl_discrimination/m1_opponent/raw_joint.py)。这是一项强同窗口基线，仍不是原始观测的理想 Bayes 上限。

### 2.6 性质与证明

**命题 1：镜像反对称。**任意相同左右共享的滤波器与偏置下，\(h_k(R,L)=-h_k(L,R)\)，而 \(E\) 不变。

**证明。**交换两输入只交换式 (6) 中两个整流项，直接相减得负号。式 (4) 的和项不变。对称三值阈值还给出 \(q_k(-h)=2-q_k(h)\)。这保证算子及编码的变换结构，不自动保证有限训练数据拟合的整个源概率表具有空间镜像对称。∎

**命题 2：固定总平滑在嵌套字母表下边缘一致。**若新增一个三值通道、既有阈值与编码分区不变，则对新码边缘化恰得旧估计表。

**证明。**对旧单元 \(z\)，新计数满足 \(\sum_{q=0}^{2}n(z,q)=n(z)\)，且

\[
\sum_{q=0}^{2}\frac{n(z,q)+\alpha_D/(3O)}{B+\alpha_D}
=\frac{n(z)+\alpha_D/O}{B+\alpha_D}.
\tag{10}
\]

若每格固定 \(\alpha\)，分母会从 \(B+O\alpha\) 变成 \(B+3O\alpha\)，旧边缘随之改变。当前修复消除了这一混淆。∎

**推论：嵌套通道的训练覆盖目标不因正规边缘化而下降。**在命题 2 条件下，JS 的数据处理不等式说明每个 nuisance 对的联合 JS 不小于其边缘 JS；取最小、截断和求和都保持单调。因此 \(J_a\) 单调。浮点误差和实际重新定义分区不在此代数结论内。

**单调不等于次模或贪心最优。**例如两个二元特征 \(U,V\) 各自与源 \(S\) 无关，但 \(U\oplus V=S\)。单个特征的分离为零，联合却完全可分。这种协同信息反例说明联合分布覆盖目标没有一般的边际收益递减保证；正增益门槛下的贪心还可能停在空集合。当前不声称最小通道集、全局最优或总体可辨识证书。

**命题 3：同一原始观测的确定性编码不能增加源信息。**条件于冻结训练集、动作和实际过去，令 \(Z=f(W)\)，则

\[
I(S;Z\mid C)\le I(S;W\mid C).
\tag{11}
\]

**证明。**由 \(Z\) 是 \(W\) 的函数，\(I(S;W,Z\mid C)=I(S;W\mid C)\)；链式法则又给出左式等于 \(I(S;Z\mid C)+I(S;W\mid Z,C)\)，后一项非负。∎

所以可能收益应是有限样本估计/通信约束下的表示效率，或动作改变后取得了新的 \(W\)，不能称确定性滤波创造信息。

**命题 4：静态 EO 可逆换基不产生信息。**对同一对值 \(x=(L,R)^\top\)，

\[
z=T x,\quad T=\tfrac12\begin{bmatrix}1&1\\1&-1\end{bmatrix},\quad
L=E+O,\ R=E-O.
\tag{12}
\]

**证明。**\(\det T=-1/2\ne0\)。密度变换中的 Jacobian 对所有源相同，Bayes 比值不变。Gaussian 的均值与协方差应一致变换为 \(T\mu_s,T\Sigma_sT^\top\)；若在两种坐标另加不一致 ridge，就不再是同一个模型。冻结 pilot 按一致变换得到数值等价。量化、裁剪、仅保留奇部或重新拟合模型均可能丢失信息，不在可逆结论内。∎

### 2.7 复杂度与未解决问题

预处理全部校准块与 bank 约为 \(O(ASRBFL)\)，另有阈值 quantile 开销。贪心至多 \(AKF\) 次候选评估，每次计数约 \(O(SRBK)\)，全源对/干扰对 JS 约 \(O(S^2R^2O_{\max})\)。一个保守界为

\[
O\{ASRBFL+AKF[SRBK+S^2R^2(2\cdot3^K)]\}.
\tag{13}
\]

当前代码限制 \(K\le3\)；字母表指数增长仍是实际样本需求限制。最终表存储 \(O(ASRO_{\max})\)。当前在线 `extract` 会计算整个 bank，故为 \(O(FL)\)，不能写成只算选中 \(K\) 项的复杂度；后验更新为 \(O(SR)\)。

该有限表只覆盖训练时列出的源和 nuisance。没有解决未见源位置、连续源参数泛化或校准分布外的传感器机制。训练 JS 变大不保证留出排名改善。

## 3. M2 身份证：相对返回方向管与源响应差编队

### 3.1 母机制、修改与接口

母来源为 Nature 2026 的进入/退出方向记忆，DOI [10.1038/s41586-026-10827-7](https://doi.org/10.1038/s41586-026-10827-7)。其记忆目标是方向，不是最后一次边界的固定坐标。代码版本和阅读资格见跨域文档。V7 新增的不确定管、响应梯度选择与管外复测，不归为原论文已给出的算法。

源码：[memory.py](../src/gsl_discrimination/m2_boundary/memory.py)、[formation.py](../src/gsl_discrimination/m2_boundary/formation.py)、[接口 README](../src/gsl_discrimination/m2_boundary/README.md)。

| 子接口 | 必需输入 | 输出与权限 |
|---|---|---|
| `CausalBoundaryMemory.update` | 真实秒数、位置、实际 travel heading、合格 crossing event；风版另需当下局部风 | 进入/退出方向状态及诊断；不接收源后验或真源 |
| `make_return_tube` | 当前合法位置、方向记忆、长度、定位/延迟/漂移不确定量 | 相对当前点的有限方向管；不是源似然或未经校准的“95% 管” |
| `score_paired_formations` | `center[N,2]`、均值 `[N,S]`、梯度 `[N,S,2]`、联合协方差 `[N,S,2,2]` 或 `[N,D,U,S,2,2]`、间距/方向/成本/几何 | 合法双点动作，全源对 contrast 矩阵、偶奇差、管内外标志与候选索引 |

### 3.2 因果方向更新与延迟处理

对合格进入事件，

\[
m_{k+1}=a\,m_k+b\,\widehat v_k.
\tag{14}
\]

不强行设 \(b=1-a\)。\(\widehat v_k\) 来自已观测运动窗口中按重叠时长加权的速度平均，再归一化；速度由位置差/时间差确定，方向由对应运动段的 travel heading 给定，不能用飞机机头 yaw 代替。

事件检测器必须用已发生的稳定 off/on 历史确认 crossing，并校正采样到传感/管路输出的已知延迟。方向窗口结束时刻为 crossing 加最短 post 确认时间；物理记忆年龄从该时刻计，不因较晚收到确认而变年轻。静止时羽流自身扫过传感器不能建立运动方向记忆。

`entry_only` 是明确的无风改版，只保留进入记忆。`wind_gated` 需当下且不过期的局部风，初始化退出上风偏置并对退出方向门控。接口风向表示空气流动的下风方向，上风取负号。当前实现没有复现 Nature 的全部负二项驻留与随机速度动力学。

方向散布含窗口内方向差、相邻进入方向不一致及调用方给出的方向噪声。工程协方差更新为 \(P_m\leftarrow a^2P_m+b^2V_k\)。设 \(u=m/\|m\|\)，归一化的一阶 Jacobian 为

\[
J_m=\frac{I-uu^\top}{\|m\|},\qquad P_u=J_mP_mJ_m^\top.
\tag{15}
\]

方向抵消、采样间隙过大、当前运动陈旧、未来事件/风、时间倒序或位置越过运动上界均拒绝。该不确定量是工程估计，尚未取得概率覆盖校准。

### 3.3 相对方向管

以当前位置 \(x_t\) 为起点，\(n\perp u\)，定义

\[
\mathcal T_t=\{x_t+s u+r n:0\le s\le L_t,\ |r|\le R_t(s)\},
\]
\[
R_t(s)=r_0+k\sqrt{n^\top[P_x+q\,\mathrm{age}\,I+(v_{\max}\sigma_\tau)^2I+s^2P_u]n}.
\tag{16}
\]

代码的漂移输入 \(q\) 为标量 variance rate；\(k\) 是保守程度，不默认某个置信分位数。管约束双点中心；两个端点可以横跨其边界，但另过合法性与局部半径门。

**命题 5：平移等变与给定历史的源无关性。**将整条位置轨迹和当前位置平移同一常量，不改变时间、运动 heading 和事件，则记忆不变，返回管仅同量平移。给定相同历史与配置，不同的外部源编号不会改变记忆。

**证明。**速度与窗口方向只依赖位置差，式 (14)–(15) 不含绝对位置或源编号；式 (16) 只有原点随当前位置平移。∎

这里“源无关”指算子在给定同一观测历史下不读取源标签，**不表示统计上 \(m\) 与真实源独立**。气味事件本身可能含源信息；memory 是历史的派生量，不能因此再乘一份“记忆似然”。

### 3.4 候选响应决定双点基线

动作 \(a=(q,d,u)\) 的端点为 \(q\pm du/2\)。调用方从训练 ensemble 或因果可得模型提供 \(\mu_s(q)\)、\(g_s(q)=\nabla\mu_s(q)\) 及完整偶奇联合协方差，绝不从未来测试全场获取梯度。

\[
\bar z_s(a)=\begin{bmatrix}\mu_s(q)\\(d/2)u^\top g_s(q)\end{bmatrix},\quad
\delta_{ij}(a)=\bar z_i(a)-\bar z_j(a),
\]
\[
D_{ij}^{\rm geom}(a)=\delta_{ij}^\top
[\Sigma_i(a)+\Sigma_j(a)+\lambda I]^{-1}\delta_{ij}.
\tag{17}
\]

协方差须对称半正定、合并后正定；ridge 必须由调用方明确给出，默认 0。完整 2×2 协方差使用一次，不能把相关的原始双点、偶部、奇部再独立相乘。\(D^{\rm geom}\) 是设计距离，**不是 M3 的 KL、源概率或检验统计量**。

局部一阶近似忽略曲率。`FormationGeometry.linearization_radius` 是调用方声明的有效范围；代码会检查 \(d/2\) 不超过该范围，却没有从数据证明某个 Hessian 上界。较长基线应另提供精确端点预测模型；不能把 7 m 静态探针对直接塞入短基线线性化并称其合格。

**命题 6：局部近似误差。**若半径 \(d/2\) 内 \(\|\nabla^2\mu_s\|\le M_s\)，则精确双点偶部与 \(\mu_s(q)\) 之差、奇部与 \((d/2)u^\top g_s\) 之差，绝对值均不超过 \(M_s d^2/8\)。若沿基线三阶导有界 \(T_s\)，奇部误差可进一步界为 \(T_s d^3/48\)。

**证明。**令 \(v=du/2\)，Taylor 余项 \(r_\pm\) 满足 \(\mu(q\pm v)=\mu(q)\pm g^\top v+r_\pm\)、\(|r_\pm|\le M_s\|v\|^2/2\)。取和或差后除 2 得第一组界。三阶展开中二阶项在奇部抵消，余项界为 \(T_s\|v\|^3/6\)。∎

这是附加光滑条件下的数学界，当前项目没有测出 \(M_s,T_s\)，不能据此宣布实际误差已受控。

**命题 7：同幅源的最优基线由响应梯度差决定。**若 \(\Delta\mu=0\)，合并协方差在比较方向间固定且正定，间距相同，则

\[
D_{ij}^{\rm geom}(u)=\frac{d^2}{4}(u^\top\Delta g)^2
\,[\Sigma_{ij}^{-1}]_{22}
\]

当 \(\Delta g\ne0\)、\(\|u\|=1\) 时，由 \(u=\pm\Delta g/\|\Delta g\|\) 最大化；当 \(\Delta g=0\) 时，所有方向得分均为零并列。

**证明。**式 (17) 此时差向量仅第二项非零，正定矩阵逆的第二对角元为正；由 Cauchy–Schwarz，\(|u^\top\Delta g|\le\|\Delta g\|\)，等号方向如上。∎

因此响应梯度差旋转、源坐标不变时，最佳基线也旋转。这是代码测试的机制性质，不依赖“朝最近源”或固定横风规则。若协方差、合法性或成本随方向变化，最优方向还要考虑这些因素，不能套用该简化结论。

### 3.5 管外复测、零分数与真正不可辨识的区别

当前输出包括全部动作×源对矩阵和 `gate_pair_indices` 可选的关注源对。默认只要求至少一个源对得分超过阈值，避免全源对 maxmin 为零就把所有局部有用动作丢弃。

- 管内有合格动作：`inside_tube`。
- 管内没有而管外有：`out_of_tube_retest`。
- 只给了无用管内候选：`need_outside_proposals`。
- 给定合法集合均未超过判别阈值：`no_discriminating_action`。
- 几何筛完没有动作：`no_legal_actions`。

均值/梯度相同只意味着式 (17) 的均值型分数为零；不同协方差、更高阶统计或动态结构仍可能区分源。**这不是完整观测分布不可辨识的证明。**M2 不排除源，也不把阈值以下得分改写为总体零信息结论。

真正的不可能性条件更强：若两个源在每个可到达历史和每个合法动作下的完整条件观测分布都相同，则任何仅依赖已见历史的策略都无法从这些观测区分它们。证明可按时间归纳：历史律相同，策略的动作条件律相同，新观测律相同，故下一历史律仍相同。该结论同时说明为何换动作有时有用，以及为何不可能时不能靠更尖后验补救。

### 3.6 复杂度与模块边界

枚举最多 \(NDU\) 动作，输出 \(\binom S2\) 个源对距离，每项为固定 2×2 线性代数，故时间约 \(O(NDU\,S^2)\)，结果存储 \(O(A S^2)\)，另加调用方地图合法性检查成本。参考 `rank_by_maxmin` 还需 \(O(A S^2+A\log A)\)；它不是 M3 的成本分配算法。

设保存运动样本数为 \(H\)。当前 Python 列表实现每次复制/扫描约 \(O(H)\)，若同时前端删除 \(q\) 个过期样本，则为 \(O(H+qH)\)，最坏可达 \(O(H^2)\)；不能因记忆向量只有二维就宣称整个更新为常数时间。存储为 \(O(H)\)。这是实现复杂度，不是新的理论下界。

M2 不证明飞行路径无碰撞或两平台同步到达；端点 bounds/callback 只是几何门。真实成本应包括到位、恢复、稳定和双点采样。没有这些量时只报告声明的查询预算。

## 4. M3 身份证：完整源对成本分配、覆盖与独立审计

本节与实现作者的 [THEORY.md](../src/gsl_discrimination/m3_audit/THEORY.md) 一致，补上等价变换和审计证明的完整步骤。源码为 [planner.py](../src/gsl_discrimination/m3_audit/planner.py)、[ledger.py](../src/gsl_discrimination/m3_audit/ledger.py)。

母来源分别是 TIT2025 的全对探索/错误指数框架、2025 作者稿/ICASSP2026 的非均匀成本 ASHT，以及经典可预测似然/复合零假设审计在 2025 QSUT 作者稿中的具体应用。当前固定 \(\epsilon\)、对称挑战评分、M2 管外挑战与软件审计接口是本项目选择；不归为这些母论文已经证明的新公式或精确复现。

### 4.1 I/O 与状态

| 接口 | 输入 | 输出/状态 |
|---|---|---|
| `CoveragePlanner.plan` | `channel[A,S,R,O]`、`predictives[A,S,O]`、`source_posterior[S]`、步数；可选 `exploit_mask`、`challenger` | 动作概率、可选抽样动作、完整 KL/资源份额/成本/零对/覆盖诊断 |
| `AuditLedger.prepare` | 将执行的动作；可选同形状、同 nuisance 语义的下一步条件表 | 在结果前复制并冻结预测；不允许并存两个未完成 prepare |
| `AuditLedger.update` | 动作、联合结果、唯一事件 ID | 各源 log e-value、当前可相容集、从未排除集、计数与成本 |

`source_posterior` 只选择正常分配的 incumbent，不用其小质量删候选或缩小覆盖。`predictives` 可由 `JointPosterior.predict()` 对共享 nuisance 的当前条件权重边缘化。该 KL 是安装预测模型中的量，不是自动校准的真实世界 KL 下界。M2 的式 (17) 不被直接当作这些 KL。

### 4.2 成本比值与正确抽样频率

对当前 incumbent \(i\)，所有其他合法源 \(j\ne i\) 都进入约束，

\[
D_{ij}(a)=\sum_zp_i^a(z)\log\frac{p_i^a(z)}{p_j^a(z)}.
\tag{18}
\]

目标为

\[
\max_{\lambda\in\Delta_A}
\frac{\min_{j\ne i}\sum_a\lambda_aD_{ij}(a)}{\sum_a\lambda_a c_a},
\quad c_a>0.
\tag{19}
\]

**命题 8：式 (19) 等价于线性规划**

\[
\max_{y\ge0,v}v,\quad c^\top y=1,\quad
\sum_ay_aD_{ij}(a)\ge v\quad\forall j\ne i,
\quad \lambda_a=\frac{y_a}{\sum_by_b}.
\tag{20}
\]

**证明。**从任意 \(\lambda\) 定义 \(y=\lambda/(c^\top\lambda)\)，则 \(c^\top y=1\)，目标变为 \(\min_jD_{ij}^\top y\)。反之由可行 \(y\) 定义 \(\lambda=y/(\mathbf1^\top y)\)，其成本均值为 \(1/(\mathbf1^\top y)\)，恢复相同目标。引入最小值下界 \(v\) 得 LP。∎

实现内部解资源比例 \(z_a=c_ay_a\)，因此 \(\sum z_a=1\)；实际抽样概率是 \(\lambda_a=(z_a/c_a)/\sum_b(z_b/c_b)\)，不是 \(z_a\)。系数先归一化再调用 HiGHS，避免很小的正 KL 被绝对求解容差当零。

**可复核成本反例。**若

\[
D=\begin{bmatrix}1&0\\0&9\end{bmatrix},\qquad c=(1,9),
\]

最优资源份额为 \((1/2,1/2)\)，抽样频率为 \((0.9,0.1)\)。其最小证据/成本为 \(0.9/1.8=0.5\)；误把资源比例当频率时只有 \(0.5/5=0.1\)。这验证成本算法而不依赖有利的 plume 实例。

两源时只有一个约束，最优值退化为最大 \(D/c\) 动作。因此两源静态 pilot 不能证明多候选的分配机制。

### 4.3 付费覆盖、零源对与管外挑战

执行分布为

\[
\rho_t=(1-\epsilon)\lambda_t+\epsilon\nu,
\tag{21}
\]

其中 \(\nu\) 在当前合法动作域上事先指定、与后验独立，默认均匀；\(\epsilon=0\) 是显式无覆盖消融。`exploit_mask` 只限制正常 LP，不能限制全局合法覆盖。真正禁止的动作必须在调用前移出全局动作域；M2 方向管不是安全边界。

若完整对手 LP 为零、mask 为空、存在支持奇异的无限 KL，或调用者显式指定 challenger，代码可转入全局源对挑战，评分为

\[
\mathrm{score}_{ij}(a)=\frac{\min\{D_{ij}(a),D_{ji}(a)\}}{c_a}.
\tag{22}
\]

可选择管外动作；完全没有有效挑战时执行覆盖并报告不可分。当前零判定有明确数值容差，不能把弱于容差的差别说成数学上严格相同。无限 KL 保留支持差异，不悄悄加平滑，也不将其送入有限系数 LP；该 fallback 不声称原完整 LP 最优。正常与 fallback 分支都没有暗换成 EIG。

覆盖成本每决策的期望为 \(\epsilon\nu^\top c\)，总期望成本为 \(\rho_t^\top c\)。它不是免费的随机动作，也不是逐路径总预算保证。当前 engine 会在预算末端移除已付不起的动作；此时无限期全动作覆盖前提不再成立。

**命题 9：固定动作域上的覆盖不会被错误后验关闭。**若 \(\epsilon\nu_a>0\)，每步执行概率至少为它；在持续执行 \(T\) 步、动作域不变时，

\[
\Pr\{N_a(T)=0\}\le(1-\epsilon\nu_a)^T.
\tag{23}
\]

**证明。**条件于任何尚未执行该动作的过去，下一步不选它的概率至多 \(1-\epsilon\nu_a\)；反复取条件期望得乘积界，不需要动作独立。∎

**命题 10：简单准确通道下的正信息漂移。**若真实源为 \(s_*\)、假源为 \(j\)，观测条件律正确，则

\[
\mathbb E_{s_*}\left[\Delta\log\frac{L_{s_*}}{L_j}\mid\mathcal F_{t-1}\right]
=\sum_a\rho_t(a)D(p_{s_*}^a\Vert p_j^a)
\ge\epsilon\sum_a\nu(a)D(p_{s_*}^a\Vert p_j^a).
\tag{24}
\]

**证明。**给定动作，正确条件律下的期望 LLR 就是 KL；对动作随机化取平均，再用 KL 非负与式 (21)。∎

当每个假源都有严格正的覆盖信息、初始真源先验正，并有合适的有界增量或鞅大数条件，累计 LLR 可以超过任意有限初始赔率劣势。复合有限 nuisance 时，要对每个错误 `(source,nuisance)` 状态满足相应分离或另证明累计散度条件。式 (24) 不保证五步恢复，不保证模型错误时恢复，不保证被物理删除或初始恰为零的真源恢复，也不等于当前复合预测 LP 的渐近最优性证明。

### 4.4 新后缀审计：不是第二个后验

在只依赖过去的时刻 \(t_0\) 开始审计，所有源/nuisance 的后缀似然初始化为 1，不继承旧源后验。定义

\[
L_{sr}(t)=\prod_{k=t_0+1}^{t}P_k(a_k,s,r,z_k),\qquad
A_{sr}(t)=\log L_{sr}(t).
\tag{25}
\]

对每个待审计源 \(s\)，事先给所有 \(j\ne s,r\) 正的归一化权重 \(w^{(-s)}_{jr}\)，默认均匀。替代路径混合和统计量为

\[
Q_{-s}(t)=\sum_{j\ne s,r}w^{(-s)}_{jr}L_{jr}(t),\qquad
E_s(t)=\frac{Q_{-s}(t)}{\max_rL_{sr}(t)}.
\tag{26}
\]

`prepare` 实际冻结下一步替代预测

\[
q_{-s,t}(z)=
\frac{\sum_{j\ne s,r}w^{(-s)}_{jr}L_{jr}(t-1)P_t(a_t,j,r,z)}{Q_{-s}(t-1)}.
\tag{27}
\]

在分母非零时它正规化，且 \(\prod_kq_{-s,k}(z_k)=Q_{-s}(t)\) 由连乘望远镜消去得到。若替代路径质量已经为零，代码选择任一正规下一步预测并保持路径质量为零。日志用 logsumexp，避免把很小的概率误成零。

零假设使用 \(\max_r\prod_kP_k\)，不是 \(\prod_k\max_rP_k\)。例如两个固定 Bernoulli nuisance 为 0.1 和 0.9，观测顺序为 1、0，则各整段似然都是 0.09；逐步换 nuisance 会得到 0.81，已经变成另一模型。替代概率恒为 0.5 时，正确式 (26) 为 \(0.25/0.09\)。

### 4.5 审计风险定理及证明

**定理 11（模型相对的 anytime 真源覆盖）。**假定：

1. 真源 \(s\) 与一个固定真 nuisance \(r_*\) 均包含在安装族中，整个后缀保持其物理含义；
2. 所用表是给定同一实际过去和当前动作的真实正规条件律；独立块只是满足该条件的一种方式；
3. 替代预测正规、可预测，在当前结果前冻结；动作和审计起点仅依赖过去及允许的独立随机化；
4. 原始数据不重复，或增量使用正确的依赖条件律。

则对于 \(0<\alpha_A<1\)，

\[
\Pr_{s,r_*}\{\exists t\ge t_0:E_s(t)\ge1/\alpha_A\}\le\alpha_A.
\tag{28}
\]

**证明。**真 nuisance 在零假设族中，故 \(\max_r L_{sr}(t)\ge L_{sr_*}(t)\)，从而

\[
E_s(t)\le M_t:=\frac{Q_{-s}(t)}{L_{sr_*}(t)}.
\]

条件于过去及已选动作，每一步 LR 因子的条件均值为

\[
\sum_{z:P_t(z\mid s,r_*)>0}P_t(z\mid s,r_*)
\frac{q_t(z)}{P_t(z\mid s,r_*)}
=\sum_{z:P_t(z\mid s,r_*)>0}q_t(z)\le1.
\]

因此 \(M_t\) 是非负检验超鞅，起始为 1；全支持/绝对连续时为通常的均值一 LR 鞅。由 Ville 不等式，\(\Pr(\sup_t M_t\ge1/\alpha_A)\le\alpha_A\)。点态支配使 \(E_s\) 越界事件包含于该事件，得式 (28)。随机审计起点可先条件于其过去，再取期望。∎

**注意：**\(E_s\) 自身不必是超鞅；保证来自被真实 LR 检验超鞅支配。不能仅对 \(E_s\) 写未经证明的乘积超鞅递推。经典 likelihood ratio 与 Ville 工具不被列作 V7 新定理发明。

定义

\[
\mathcal C_t=\{s:E_s(t)<1/\alpha_A\},\qquad
\mathcal C_t^{\rm ever}=\{s:\max_{u\le t}E_s(u)<1/\alpha_A\}.
\tag{29}
\]

前者对应 `compatible_now`，允许重新进入；后者对应 `not_rejected_since_start`，单调缩小。两者均非概率分布。任意时刻若用预先声明的 singleton-list 规则宣布某源，错误 singleton 必然已排除唯一真源，因此在这些条件下错误概率至多 \(\alpha_A\)，无需额外乘源个数。这个结论是“唯一真源的 anytime 覆盖”，不是任意多个真零假设的通用多重检验结论。

重复启动新审计需要 alpha spending 或其他有效组合。空列表必须报告失败/模型疑问，不能归一化 inverse e-values 得出“认证赢家”。全安装族对整个后缀均为零时，代码在变更证据前抛出 `ImpossibleObservationError`。

### 4.6 估计通道、误差模型和实际反馈

用 TRAIN 拟合的直方图、Gaussian 或任意学习条件律都不自动满足定理 11。当前 `guarantee_scope` 明确为 **model-relative**。有限 nuisance 网格没有包含真实连续参数时，附近有一个网格点并不构成覆盖证明。若另有以概率至少 \(1-\beta\) 同时覆盖真实条件律的外部族，并在审计中对该族有效最大化，才可在相应条件下结合为 \(\alpha_A+\beta\)；四个 seed 本身不建立这种保证。

有限错误可以进入完整联合符号通道，例如两比特一起翻转的相关掩码。它不能被改写成两个独立错误，也不能由此宣称对任意物理污染稳健。一次错误掩码模型与“五位允许一位错”的集合规则不是同一件事。

当前 [engine.py](../src/gsl_discrimination/engine.py) 的 full 分支还有可执行反馈：若旧后验的 incumbent 不在 `audit.compatible_now`，从相容替代中选择 log e-value 最小者作为显式 challenger，随后再做合法源对挑战/成本分配。该反馈只用过去审计，不回写源概率；`no_audit` 消融关闭反馈但仍记录审计。控制矩阵中该分支已触发，但还没有独立性能增益证据。

### 4.7 复杂度

完整 pairwise KL 为 \(O(AS^2O)\)，内存若显式保存为 \(O(AS^2)\)。有限 LP 有至多 \(A+1\) 个变量、\(S-1\) 个对手约束和成本等式；实际使用 HiGHS，复杂度应写为对应 LP 求解成本，不能无条件称线性时间。挑战扫描为 \(O(AS)\)，不含已经算出的 KL。

audit `prepare` 为每个零源混合其余 `(source,nuisance)` 的结果分布，当前实现约 \(O(S^2RO)\)；若外部提交整张新表，还需 \(O(ASRO)\) 的验证。`update` 为 \(O(SR+S)\)，另写事件日志。状态包括 \(O(SR)\) 累计似然、\(O(S^2R)\) 替代权重和安装表，审计事件日志约 \(O(tS)\)。它不是与源数无关的常数成本审计。

## 5. 三模块实际集成与代码中仍然存在的边界

### 5.1 实际数据流

```python
# 所有条件表与 action mapping 已在 TRAIN 冻结。
predictives = posterior.predict()
formation = score_paired_formations(...)  # 训练预测 + 已见方向记忆
plan = planner.plan(channel, predictives, posterior.source, step,
                    exploit_mask=proposal_mask, challenger=challenger)
action = sample(plan.probabilities)
audit.prepare(action)                     # 在新结果之前
raw_block = backend.observe(action)        # 真源只由环境/评估器拥有
raw_ledger.append(raw_block, action)
z = model.encode(action, raw_block.values, actual_times, contract)
posterior.update(action, z, event_id)       # 一次源后验更新
snapshot = audit.update(action, z, event_id) # 单独审计，不回乘后验
```

此段是接口语义示意，`backend` 的实际 raw-block 字段应依数据 schema 接入，不是一个额外可直接运行脚本。当前 `run_control` 已按同一所有权顺序运行。

M2 输出支持完整源对矩阵；当前控制 engine 用其参考排名形成约前三分之一动作的 proposal mask，boundary-only 则按管内合法中心和成本排序。M3 的 KL 来自 M1/原始联合观测表，不是把 M2 的 Mahalanobis 分数硬改成 likelihood。当前实现未执行 ISIT 的完整分簇与分阶段排除算法。

审计允许可预测条件表接口，但默认 `JointPosterior.update` 与演示 engine 使用冻结表。若真实 plume 需要隐状态条件滤波，不能只替换 audit 表就宣称源后验也已经实现正确历史依赖；原生适配需使整个条件模型一致。

当前动作成本在对应表/账本初始化时给出，控制后端采用回到共同起点的已声明 excursion 成本。真实连续飞行的位移成本会随当前位置变化，必须统一规划、执行和审计的成本记账；当前固定成本演示不是一般时变航路规划的证明。

### 5.2 原生数据门

动态 M1 需要真实连续双点记录及可分辨的传感器响应；M2 需要实际运动与因果事件；M3 需要正确的条件观测模型。某个模块通过输入格式检查不能代替另外两项资格。

关键量包括实际采样间隔、同步误差、差分管路/传感器延迟、恢复时间、空间/时间相关尺度、两平台位置和完整动作成本。数值未知时留空或阻断动态分支，不按动物的 0.46 mm、0.017 s 尺度照搬。50 s 快照只可作静态比较，不能以插值赋予原生运动资格。

## 6. 实验现状及两项重要反证

### 6.1 静态 pilot：新编码未胜出

[冻结结果](../results/ocb_static_v1/STATIC_PILOT_RESULT.json)：从 TRAIN 435 个探针对中选定原编号 12/17，约 7.003 m，四个开发世界各十张快照。

| 观测/模型 | 正确数 |
|---|---:|
| mean-only Gaussian | 31/40 |
| raw-joint Gaussian | 40/40 |
| 一致变换的 EO Gaussian | 40/40 |
| 静态 M1 joint histogram | 31/40 |

raw-joint 与 EO 后验最大差约 `4.51e-17`，对应命题 4。应保留“联合观测有用、当前新编码未胜出”这两个同时成立的结论。四个世界不是四十个独立实验；两源、不同 z 的释放、未验证飞行资格以及缺少 native PMFS 同场比较均限制外推。三项校准正确性修复不追改该冻结结果。

### 6.2 L1 控制矩阵：强基线饱和

[配置](../configs/control_matrix.yaml) 与 [完整结果](../results/control_matrix_v7_frozen/CONTROL_MATRIX_RESULT.json) 包含 13 个变体、6 个指定源/机制/seed 组合、正常与错误先验，共 156 episodes，两个虚拟平台和 300 s 模拟预算。

`A_adapted_variance` 为正常 4/6、错误先验 3/6；其余 12 个变体，包括 raw-joint EIG、best-one、fixed-two、raw-joint 强对照、所有主要 M2/M3 消融和 full，最终 Top-1 都各为 6/6。**这组结果没有证明 M1 覆盖、M2 memory 或 M3 反馈的独立性能增益。**适配方差参考也不是原生 PMFS 复现。

full 在六个错误先验 episodes 中合计 7 次显式 audit challenger 触发，证明工程分支执行；无反馈版本也最终 6/6，不能将触发数当因果收益。固定源候选和解析构造与校准共享，也不能证明未见源或真实 plume 泛化。

后验只使用 dwell 双点块，M2 另读取 travel 流；日志分别记录其 scalar samples。当前匹配策略消融共享该流程，但 native 科学比较还应给全流 raw-joint 强基线同样可见数据。不同策略改变动作，也改变花费及实际可见流；“同样 300 s”不能省略数据量与观测权限报告。

### 6.3 控制后端的源相位不可辨识

当前 [control_backend.py](../src/gsl_discrimination/evaluation/control_backend.py) 中 moving 项为

\[
\sin[3t+\Phi-(x_i-s)^\top d_r],\qquad
\Phi\sim\mathrm{Unif}(-\pi,\pi).
\tag{30}
\]

**命题 12：给定相同动作/机制，源位置引起的共同相位移被均匀相位吸收。**

**证明。**写成 \(\sin[3t+(\Phi+s^\top d_r)-x_i^\top d_r]\)。模 \(2\pi\) 后 \(\Phi+s^\top d_r\) 仍均匀，且两传感器的相位差只依赖 \((x_1-x_2)^\top d_r\)。所以该相位过程本身不含源位置差异。∎

均值/幅度项仍随源变化，故整个后端并非全源不可分；但不能用它证明“气味运动相位提供了新的源信息”。这正是需要另一套真实或经独立物理验证连续数据的具体原因。

### 6.4 原五位容错问题的必要条件

若把原任务明确限制为固定长度五位二元码，并要求任意一位错误后仍唯一识别 16 个源，则半径一的 Hamming 球各含 \(1+5=6\) 个词；唯一纠错要求这些球互不相交，必要条件为 \(16\times6\le2^5\)，显然不成立。该短证明只针对这个二元编码/最坏错误合同，不能一概套在实值观测、概率错误控制或改变动作后的新数据上。它说明为什么不能只让原五位的后验更尖，而必须检查新的可分观测。

## 7. 测试、主张与下一步实验的对应关系

| 性质 | 代码验证 | 不能由该测试代替的证据 |
|---|---|---|
| 镜像变号、静态退化、非均匀时间平均、总平滑投影、共享 nuisance、相关错误 | [M1 tests](../tests/test_m1_operator.py) | PNAS 原模型精确复现或真实运动信息收益 |
| 梯度旋转驱动基线、同幅区分、偶部保留、联合协方差、时钟/风/几何/延迟门、管外复测 | [M2 tests](../tests/test_m2_boundary.py)，21 项已通过 | 连续气体的返回事件有效性与源判别提升 |
| 成本反例、弱 KL、零对/管外挑战、固定 nuisance、预测冻结、有限路径 anytime 风险枚举、重复数据/全族零支持 | [M3 tests](../tests/test_m3_audit.py)，18 项已通过 | 拟合通道对真实 plume 的校准及有限五步恢复概率 |
| 原始时间、稀疏不能升级动态、缺风、字节/seed 资格 | [数据资格 tests](../tests/test_data_qualification.py) | 传感器与飞行动力学的实测资格 |

测试通过数按各模块既有运行记录引用；本文没有修改代码或重新挑选开发参数。项目总测试与矩阵审计以最终运行日志为准。

可发表性能主张至少需要：真正连续且传感器合格的新数据；多个源对需要不同通道的正例；同窗口 best-one/固定通道/raw-joint 比较；记忆与响应差几何的分离消融；前瞻冻结的独立世界/布局；真源覆盖、错误排除、排名与完整实际成本。若只改善有限样本估计或航程，就将贡献明确收窄到该结果。

当前未解决：未见源位置、连续 nuisance 的统一覆盖、真实传感器失配下的风险、原生 PMFS 同场比较、旋翼/湖面等目标场物理，以及多个模块在强基线之上的独立增益。没有任何一项由文献层级、单元测试或人为评分自动补足。

## 8. 理论来源与归属

- M1 生物结构：[PNAS 2026](https://doi.org/10.1073/pnas.2608896123)。本文件中的有限 bank、源对目标、平滑一致性检查与代码接口为项目实现；DPI、JS 数据处理及线性可逆换基为标准数学性质。
- M2 事件记忆：[Nature 2026](https://doi.org/10.1038/s41586-026-10827-7)，[作者代码](https://github.com/rutalaboratory/Edge-Tracking-Model)。方向不确定管、响应梯度评分、管外复测及工程门为本项目设计；Taylor 与 Cauchy–Schwarz 证明不作为新数学工具。
- 全对/探索来源：[Hsu–Wang 作者稿 v3](https://arxiv.org/html/2405.06554v3)，正式 DOI [10.1109/TIT.2025.3588527](https://doi.org/10.1109/TIT.2025.3588527)。不沿用其渐近最优误差指数作为本项目五步保证。
- 成本比值来源：[Non-Homogeneous Costs 作者稿](https://arxiv.org/html/2509.11632v3)，[ICASSP2026 正式会议条目](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)。当前挑战 fallback 与固定覆盖不是其完整算法复现。
- 可预测替代/复合零假设的近期应用：[Quantum Sequential Universal Hypothesis Testing 作者稿](https://arxiv.org/html/2508.21594v1)。本项目用有限替代混合和共享 nuisance 的条件证明；经典 universal inference、likelihood ratio 和 Ville 不归为 2025/2026 新发明。
- 实现作者的 M3 全部条件、反例与验证记录：[m3_audit/THEORY.md](../src/gsl_discrimination/m3_audit/THEORY.md)。本文件以该内容与源码为准，不扩大其物理适用范围。
