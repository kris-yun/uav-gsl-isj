# 用于气体源定位的置换等变全历史比值图

**方法名称：** Permutation-Equivariant Whole-History Ratio Map (PE-WHRM)

## 研究动机
稀疏移动气体测量使浓度场重建与源点定位之间出现结构性错位。模型可以为浓度场给出经过校准的不确定性，却丢失区分一个源点位置与固定错误候选所需的、有顺序且相对于候选的证据。因此，需要研究的对象不只是当前测量处的场值，而是每个候选源点与完整自适应测量历史之间的似然比。

物理引导的稀疏反演把确定性的 Green-function surrogate 放入神经稀疏反演流程（semanticscholar:c930ca69d5ed8553c0638ebe60205fe9c1845e58），而 probabilistic neural operator 对输出函数的分布进行评分（dblp:journals/corr/abs-2502-12902）。XIT 假设一个后验均值-方差场，并用它进行规划（dblp:journals/corr/abs-2602-13739）。这些方法都没有询问：每个连续的历史前缀是否让真实源点相对于同一个错误候选获得更多证据。PE-WHRM 针对的正是这个缺失的、有顺序且相对于源点的量，同时保留冻结的 PMFS 源网格和 updater interface。

这个缺口之所以现在值得检验，是因为 2026 年的工作已经把后验场与 XIT 的主动气体分布制图决策结合起来（dblp:journals/corr/abs-2602-13739），并比较了稀疏自主重建中的校准不确定性方法（dblp:journals/corr/abs-2604-06387）；但两者仍围绕场重建或给定的场后验来组织推断。现有的 source-labelled PMFS 轨迹包含估计 joint-versus-product density ratio 所需的完整前缀和反源点配对。对源网格重标记保持等变的 shared scoring 提供了保留源网格对称性的具体工具。结合起来，这些条件允许直接检验相对于源点的证据，而不是把场校准当作定位的代理。

EUSIPCO 2024 的方法把 Poisson 和 Green-function 结构嵌入分布式气体源定位的神经稀疏反演流程（semanticscholar:c930ca69d5ed8553c0638ebe60205fe9c1845e58）。它没有为每个候选源点学习全历史似然比，也没有显露逐前缀的真实源点相对于固定错误候选的证据。它的推断对象仍是确定性的候选响应 surrogate，因此缺少在自适应历史下测量源点相对证据的量。

Probabilistic neural operator 使用 proper field-space scoring rule 学习输出函数的校准分布（dblp:journals/corr/abs-2502-12902）。它没有把 joint source-history 与 product 配对转换为先验归一化的源点概率或固定候选的前缀增量。它的目标是函数不确定性，而不是候选源点识别，所以有顺序的源点标签不在其 estimand 中。

XIT 使用给定的后验均值-方差场，在主动气体分布制图中权衡探索与利用（dblp:journals/corr/abs-2602-13739）。它没有用相对于源点的全历史图替换后验 updater，也没有检验测量是否改善固定错误候选的定位 margin。规划把后验作为输入，因此后验的证据语义不在该方法的范围内。

2026 年的不确定性研究比较了面向重建的不确定性估计器，用于稀疏自主车辆观测（dblp:journals/corr/abs-2604-06387）。它没有训练有顺序的历史源点比值估计器，也没有检验保留边际测量的破坏性置换。它的评价对象是场重建和校准，因此缺少能够识别定位证据的 source-pair intervention。

缺口闭合后，可以得到一个可审计的概率图更新：其增量可归因于一个源点相对于固定错误候选的有顺序证据，而不只是场校准。由后验驱动的规划器，例如 XIT（dblp:journals/corr/abs-2602-13739），可以使用具有明确定位语义的概率图；同时，源点识别问题也会与 probabilistic neural operator 的函数不确定性目标区分开（dblp:journals/corr/abs-2502-12902）。因此，得到的主张更窄但具有因果性：破坏历史与源点之间的关系，必须破坏定位 margin。

## 方法
### M0_data_setup
*从冻结的 PMFS 数据准备有顺序的源点-历史配对及 product-of-marginals control。*

1. 把每条轨迹前缀编码成固定字段记录：源点坐标、有序的位置和时间戳、风场或上下文变量、有效性掩码，以及截至当前时刻的气体读数。matched example 保留生成该前缀的轨迹源标签。negative example 从同一 context stratum 的另一条轨迹抽取源点与该前缀配对，禁止自配对，并保存 split、stratum、trajectory、prefix 和 pairing type 等标识。对 matched 和 negative 等量抽样，将表格作为 scorer 的训练输入。
   - _为什么：_ 缺失的信息是源点如何与有顺序的历史发生关系。把 matched dependence 与保持源点和历史边际不变的 control 进行对比，就能针对这层关系。

### M1_shared_ratio_map
*估计共享的源点-历史比值，并把它们转换为先验归一化的源点概率图。*

2. 构造一个对所有候选共享的 scorer：用独立编码器处理候选坐标和带 mask 的有序历史，再用双线性或拼接 head 融合；所有源点必须共用同一组权重。训练使用平衡二元交叉熵；只有在记录到采样失衡时才使用逆源频率权重。用独立 calibration split 拟合单调校准映射，并为每个候选-前缀输出 logit 与校准诊断。禁止 candidate-index embedding 和 source-specific output head。

*用平衡二分类损失区分匹配的源点-历史前缀与独立重配的前缀。*
$$ \mathcal{L}_{\mathrm{ratio}}(\theta)=-\mathbb{E}_{p(s,H_t)}\log D_\theta(s,H_t)-\mathbb{E}_{p(s)p(H_t)}\log\!\left(1-D_\theta(s,H_t)\right) \tag{1} $$


*在类别先验平衡时，分类器 logit 估计源点与历史之间的密度比。*
$$ \ell_\theta(s,H_t)=\log\frac{D_\theta(s,H_t)}{1-D_\theta(s,H_t)}\approx\log\frac{p(s,H_t)}{p(s)p(H_t)} \tag{2} $$

   - _为什么：_ joint-versus-product 对比针对候选源点与完整历史之间的依赖，而参数共享使源网格重标记始终经过同一套 scoring rule。
3. 先在未参与拟合的 product-control 表上评估校准后的 scorer。对数值稳定的 logit 计算 exponential ratio moment，并在把 logit 解释成 ratio 之前保存估计值和不确定性。对每个完整前缀，在 log 空间加入冻结的 PMFS 先验，用完整冻结源网格上的 log-sum-exp 归一化，保存概率图、归一化残差、先验版本和 split 标识。

*用 PMFS 先验归一化候选源点的密度比 logit，得到冻结源网格上的概率图。*
$$ q_\theta(s\mid H_t)=\frac{\pi_0(s)\exp\ell_\theta(s,H_t)}{\sum_{u\in\mathcal{S}}\pi_0(u)\exp\ell_\theta(u,H_t)} \tag{3} $$

   - _为什么：_ 分类器分数本身不是概率图。moment check 检验 density-ratio interpretation，而 prior normalization 保留预期的 Bayesian source support。

### M2_fixed_rival_evidence
*把连续前缀的 ratio logits 转换为针对固定错误候选的逐次及累计证据。*

4. 由轨迹标签确定真实源点，并在查看预测前按预注册规则选择错误候选：最近的错误网格点和先验最高的错误网格点，平局按网格顺序处理。保存每个前缀的 logit，计算相邻前缀差分，用真实源点增量减去每个 rival 增量，从第一个前缀开始累加。报告每次更新 margin、累计 margin、最终 rank，以及按轨迹 bootstrap 得到的区间。

*前缀差分提取新增的全历史证据，并比较真实源点与固定错误候选。*
$$ \Delta_{\theta,t}(s)=\ell_\theta(s,H_t)-\ell_\theta(s,H_{t-1}),\qquad \delta_{\theta,t}(s^*,r)=\Delta_{\theta,t}(s^*)-\Delta_{\theta,t}(r) \tag{4} $$

   - _为什么：_ 定位改善需要相对于持续存在的错误候选的证据；只有真实源点增量为正，并不能说明这种区分已经出现。

### M3_validation
*检验源网格等变性，以及破坏性置换是否移除有顺序的源点相对证据。*

5. 对等变性检查，给候选源网格施加一一重标记，在不重新训练的情况下运行同一个 scorer，再把输出逆置换，记录最大绝对残差和 rank 是否一致。两个破坏性 control 都保持读数和边际计数不变：一个把读数重新分配到不同的时间-位置槽位，另一个在同一 stratum 内把源点与其他轨迹历史重新配对。冻结模型和 split，重新执行完整评分与证据计算，保存 intact/control 轨迹以及预注册的通过/失败阈值。

*精确源网格置换等变要求候选源点重标记后，概率图以相同方式重排。*
$$ \mathbf{q}_\theta(H_t;\Pi\mathcal{S})=\Pi\,\mathbf{q}_\theta(H_t;\mathcal{S}) \tag{5} $$

   - _为什么：_ 贡献所声称的是有顺序的源点相对机制，因此 control 应该破坏这层关系，同时让边际场信息仍然可用。

