# 可部署信息集上的源证据微分算子

状态：**二次创新候选的可实施定义**。以下恒等式是概率微分和条件期望的已知性质；不是原创定理。将其用于“源条件过滤 + 联合未来观测 + 源对证据路径监督”的组合设计是本项目提案，尚无House/湖岸正收益证明。本文不修改V1，也不声称任何学习器已达到理论前提。

## 1. 为什么单个特权状态教师会错

记 (s\in\mathbb R^2) 为源位置，(m) 为机制，(H) 为部署可见历史，(Q) 为**提前确定**的合法动作块，(Z) 为只在训练或教师仿真中可见的风场/传播状态。统一省略已知几何 (G)。历史不能唯一恢复 (Z)，所以合法预测目标是

\[
\bar p_{s,m}(y\mid H,Q)=\int p_T(y\mid z,s,m,H,Q)b_T(dz\mid H,s,m).
\tag{1}
\]

不能使用 (p_T(y\mid Z=z_*,s,m,Q)) 代替，也不能对每个测试源挑选最匹配的未来真实风场。对未见源 (s)，历史过滤仍须重新计算；不能复用只在真源下构造的 (b_T(z|H,s_*))。

反例：隐藏二元状态 (z\sim\mathrm{Bernoulli}(1/2))。源a时 (Y=z)，源b时 (Y=1-z)。知道 (z) 的oracle总能区分源，部署可见历史不含 (z) 时，两源都给 (Y\sim\mathrm{Bernoulli}(1/2))，真实可辨识信息为零。复制oracle老师会制造不存在的源差异。

## 2. 可执行的双项边缘差分教师

定义完整资料密度 (r_{s,m}(H,y,z\mid Q))，及合法历史边缘 (r_{s,m}(H,z))。两者均由同一个传感器观测模型和传播模型生成。令

\[
J_{s,m}(H,y,Q)=\log\int r_{s,m}(H,y,z\mid Q)dz,\quad
B_{s,m}(H)=\log\int r_{s,m}(H,z)dz.
\]

于是

\[
\ell^T_{s,m}(y|H,Q)=J_{s,m}-B_{s,m},\qquad
g^T_{s,m}=\nabla_sJ_{s,m}-\nabla_sB_{s,m}.
\tag{2}
\]

这一步避免把“历史已过滤过的latent”和“未来观测”重复计数。若学生提供完整历史 `log_prob(H,s,m)`，应计算完整链式likelihood；若提供未来块conditional likelihood，只增加相应后缀一次。

### 粒子/潜状态bank实现

训练teacher bank采样 (z_k\sim q(z))。要求q覆盖完整资料分布支持；优先使用不依赖候选源的公共base noise，便于不同源公平比较和自动微分。定义

\[
u_k(s)=\log r_{s,m}(H,y,z_k|Q)-\log q(z_k),\quad
v_k(s)=\log r_{s,m}(H,z_k)-\log q(z_k).
\]

\[
\widehat\ell^T=\operatorname{LSE}_k u_k-\operatorname{LSE}_k v_k,
\qquad
\widehat g^T=\sum_k\alpha_k\nabla_su_k-\sum_k\beta_k\nabla_sv_k,
\tag{3}
\]

其中 (\alpha=\mathrm{softmax}(u),\beta=\mathrm{softmax}(v))。共享的 (1/K) 因子相消。两组责任度必须分别计算，不能把alpha当beta。有效样本数、最大权重、不同bank的误差必须记录。有限粒子下log估计有偏，不可写成无偏似然梯度；收敛要求可积性及足够覆盖。

等价的条件形式是

\[
\nabla_s\log\bar p_s(y|H,Q)
=E_{z|H,y,s,Q}\left[\nabla_s\log p_T(y|z,H,s,Q)+\nabla_s\log b_T(z|H,s)\right].
\tag{4}
\]

直接平均teacher观测score会漏掉第二项。先预测一个均值风场再算score也一般不等价。

**源坐标支持边界**：Eq.(2–4)假定可交换微分/积分且积分支持不随源坐标变化。若碰到障碍、羽流命中硬阈值等不连续，应保留V1的边界项处理路线或改用明确的有限源对证据；不能宣称简单autograd已算出真实边界导数。

## 3. 源对证据监督，而非全场重建

学生只输入 (H,G,s,m,Q)，通过归一化自回归头输出

\[
p_\theta(y_{1:L}|H,G,s,m,Q)=\prod_{j=1}^L
p_\theta(y_j|H,G,s,m,Q_{1:j},y_{<j}).
\tag{5}
\]

若采用持久隐变量混合，须先对每条轨迹采样一次隐变量，再生成整段，不可每个时刻独立重采样。未来联合采样与历史likelihood来自同一个模型；不得使用两个互不一致的heads。

对于竞争源a,b及合法连续路径 (s(u))，有

\[
\Lambda^T_{a,b}(y;H,Q)
=\ell^T_a-\ell^T_b
=\int_0^1 g^T_{s(u)}(y;H,Q)^T\dot s(u)du.
\tag{6}
\]

当a,b跨不连通可行区域，改用端点差 (\ell_a-\ell_b)，不可强行穿越墙体积分。学生生成器的log-prob自动诱导 

\[
\Lambda^\theta_{a,b}=\log p_\theta(y|H,a,m,Q)-\log p_\theta(y|H,b,m,Q).
\]

采用NLL锚点保证归一化预测语义，并加入投影证据监督：

\[
L=L_{NLL}+\lambda_{pair}E_{a,b,Q,y\sim(\bar p_a+\bar p_b)/2}
\rho(\Lambda^\theta_{a,b}-\Lambda^T_{a,b})
+\lambda_{dir}E\|\dot s^T(\nabla_s\log p_\theta-\widehat g^T_s)\|^2.
\tag{7}
\]

有限源bank不能提供可靠连续坐标导数时，必须关闭directional项并明确“pair evidence版本”，不可伪造源微分teacher。单纯Eq.(7)不是充分的创新主张；论文应评价**生成/过滤/积分次序、轨迹联合性、源对监督与其可部署接口形成的实际机制**相对普通联合NLL、直接teacher蒸馏和未投影差分的独立收益。

### 信息瓶颈和采样改造

从MIST-WM借鉴可学习gate与同因子独立rollout成对采样；我们把待保留目标换成一组合法动作上的投影证据 

\[
T_{task}(H)=\{\bar p_{s,m}(Y_Q|H):s,m,Q\in\mathcal Q_{train}\}.
\]

gate压缩表示必须经过源对likelihood误差约束；压缩失败即增维，不靠增大loss权重掩盖。若原始合法观测已不可分，禁止用源标签硬造间隔。训练课程可以优先覆盖已有模型证据误差大、但投影teacher可分性稳定的源对；不能按测试真源/未来实测响应选pair或Q。

## 4. 可检验的充分条件与不能保证之处

### 4.1 投影分布是正确监督目标

在同一合法历史H下，若teacher预测条件分布正确，则任意student密度q满足

\[
E_{Z|H,s}E_{Y|Z,H,s}[-\log q(Y|H,s)]
=H(\bar p_s)+D_{KL}(\bar p_s\|q).
\]

所以teacher样本级NLL的总体最优是投影混合，而不是每个样本的oracle密度。这里只说明正确目标；有限容量/样本/域偏移下不保证达到它，也不保证源差分监督比NLL更好。

### 4.2 源对margin误差

若对相关H,Q,y沿路径的方向导数误差上界为 \(\epsilon\)，路径长为 \(d\)，数值积分误差 \(\delta_{quad}\)，则由基本微积分定理

\[
|\Lambda^\theta_{a,b}-\Lambda^T_{a,b}|\le d\epsilon+\delta_{quad}.
\tag{8}
\]

若teacher真实源相对竞争源的margin大于此误差，student保留其排序。不能由平均导数MSE直接推统一上界；必须在冻结留出源/动作/机制上报告tail误差，或仅给概率型界。

若仅有每源 \(|\log p_\theta-\log\bar p_T|\le\eta\)，则源对误差至多 \(2\eta\)。必须再计入teacher相对真实物理分布的偏差。不存在“梯度更准因此MAP必更准”的无条件定理。

### 4.3 学生信息上限

对确定性历史压缩 (R=f(H)\)，数据处理给出 \(I(S;R)\le I(S;H)\)。若合法动作集合中任意Q均满足 \(\bar p_a(Y_Q|H)=\bar p_b(Y_Q|H)\)，任何student/planner都无法可靠区分a,b；训练只能恢复模型丢失信息，不能创造传感器未提供的信息。

有限假设下，若所有相对于某参考源的likelihood比仅依赖统计量R，则R对该源假设族充分；这是标准充分性结论。对未来动作是否充分还需对所有会被选中的Q成立，不能只在固定路线成立。

## 5. 直接进入工程的张量与接口

- `history`: `[B,T,F]`；局地气体/局地风/位置/动作/时间及mask；禁止真源标签、未来观测、未来全场风。
- `source_xy`: `[B,S,2]`，连续物理坐标；不得只学训练源ID embedding。
- `mechanism`: `[B,S,M,...]` 或离散m索引；若机制未知，M2维护联合posterior。
- `action_block`: `[B,A,L,D_a]`；计划时仅允许事前合法动作。
- teacher `log_joint_weights`: `[B,S,M,A,K,2^L]`（二元短块时）；长期/连续响应用采样，不指数展开。
- student `log_prob`: 历史总log-density或明确标记的conditional后缀；M2回放用相同冻结模型版本重新算。
- `sample_future`: `[B,S,M,A,N,L,D_y]`；共享latent确保联合性。
- `pair_evidence`: `[B,E,A,N]`，E为源对数；只能由相同normalized density相减，不能另加自由pairhead造成循环不一致。

teacher bank为研发资产，部署调用不能读取bank真实标签或真实未来库。在线学生预算应单独测量CPU/显存，不把teacher离线时间隐藏。

## 6. 与M2/M3的统一闭环

1. 新观测写不可变账本；M1按候选源与机制计算本次增量。
2. M2的诊断仅提出机制/变点候选；先撤销旧后缀，再用M1按新机制重算完整后缀。诊断预测不能作为另一份观测likelihood相乘。
3. 当前联合posterior保留低概率合法源；M3向M1请求每个合法动作块的联合样本，建立相关软码本。
4. M3按功效/风险约束选反证动作，保证恢复列表有检查机会；无足够分离度时记录证据不足，比较同模型的联合EIG。
5. 执行动作得到新气体/局地风观测，回到步骤1。teacher不在部署链内。

## 7. 最小决定性消融

| 标签 | teacher目标 | student/联合头 | 可回答问题 |
|---|---|---|---|
| A | 原PMFS | 原PMFS | 原生任务基线 |
| A′ | 无特权teacher | 同容量合法历史AR-NLL | 结构适配是否足够 |
| A′+B-HIB | 配对特权latent余弦+瓶颈 | 同容量头 | 普通历史特权蒸馏 |
| A′+B-TWIST | 配对latent与同动作imagined rollout | 同容量头 | 直接母方法是否足够 |
| B′-oracle | 单个真状态未来响应/score | 同容量头 | 不合法目标的高估幅度，仅诊断 |
| B′-unweighted | 不经过源条件过滤或忽略filter导数 | 同容量头 | 投影与微分次序的必要性 |
| B′-project-NLL | 正确projected joint，只有NLL | 同容量头 | teacher和正确积分本身的收益 |
| B′-pair | projected joint + 源对端点证据 | 同容量头 | 源判别监督的独立收益 |
| B′-full | projected joint + 合法源方向teacher + pair | 同容量头 | 连续源证据微分的附加收益 |

模型参数量、realization数量、动作训练覆盖、优化预算固定；全体在相同冻结未见源/风/几何集合上评测。若B′只比PMFS好但不比A′或project-NLL好，不能称二次创新已成立。若有M1独立收益再测M2恢复事件和M3在同一M1下的EIG对照，不能以换更强M1解释M3收益。

## 8. 状态判定

该算子可在已知连续概率模型上编写数值恒等式测试，证明工程算对；但测试通过不等于真实物理teacher合格。原生GADEN/House缺少source-conditioned independent-realization teacher bank、可靠观测算子或连续source derivative时，相关能力必须保持BLOCKED，其他已运行模块可以交付。
