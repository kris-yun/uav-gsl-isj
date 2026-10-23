# V7科学问题、失败机制与可验证边界

日期：2026-10-23。依据本轮冻结的PMFS/物理独立审计、信息论独立报告、第四轮代码复查、OCB静态pilot与最终L1控制矩阵。文中将源码事实、数学反例、已执行结果和仍待验证的物理假说分开。本文不改写原冻结结果，也不把模型内测试称为真实气体性能保证。

## 1. 实际科学问题与当前答案

需要解决的问题是：**在有限飞行、驻留与传感器预算下，哪些合法观测能够排除错误源，并且其区别不能被未知强度、局地传输、源高度或传感器响应解释掉？**浓度预测更准、源概率更尖、重捕获气味更快都可能有用，但每一项都需要再证明怎样改善候选源排序与错误确认。

本轮完成了可执行的M1联合通道、M2动作提议与M3成本分配/新数据审计，以及真实旧物理导出的静态开发pilot。最新13变体 × 6控制世界 × 两种先验的156个L1 episode全部运行完毕；raw-joint/EIG、母算法、各独立消融与full在最终top-1端点均为6/6。静态pilot中raw-joint Gaussian为40/40，静态M1为31/40。因此，**工程链完成，但M1、M2、M3独立科学收益尚未建立**。native连续物理与合法UAV闭环资格仍HOLD。[E1–E3]

这不是证明所有候选机制无效。它规定了下一次实验必须区别什么，并排除了“只胜过弱方差参照就已证明三个新模块”的解释。

## 2. PMFS的真实执行链：首先纠正问题归因

### 2.1 固定源码版本与测量语义

本轮审计固定在`MAPIRlab/GasSourceLocalization@4e141e162551e674f2f30ddb8859136c72139aac`。源码逐文件SHA、行数与运行能力见`SOURCE_RUNTIME_RECEIPT.json`及物理审计。不能把其他分支、论文中的抽象描述和该提交实际执行的代码混为一谈。[S1–S5, E4]

|环节|该固定版本的实际行为|对源判别的含义|
|---|---|---|
|停留读出|`StopAndMeasureState`默认收集2 s，平均浓度、风速并计算圆周平均风向|一次读出具有有限时长和实际滤波语义|
|二值测量|`processGasAndWindMeasurements`对窗口平均浓度阈值化，然后刷新风、更新地图/候选并移动|观测是“窗口均值过阈”，不能直接当长期hit frequency|
|地图反演|`EstimateHitProbabilities`将一次hit/no-hit按风核和可见区域传播，累计log-odds与距离相关confidence|多个受影响地图单元共享同一原始事件，不是多次独立观测|
|候选前向模型|二维风加高斯速度扰动移动filament，以每步格内有无filament累计长期占据频率|这个读出算子与实际窗口平均浓度过阈不同|
|源评分|`sourceProbFromMaps`从`total=1`开始，乘自由格的当前兼容因子|它是地图兼容评分；没有自动成为原始窗口的完整测量似然|
|源分布更新|`updateSourceProbability`重算、归一化并覆写源评分|不是每轮把旧源posterior再乘一次；历史依赖主要进入累计地图|
|主动动作|`chooseGoalAndMove`按当前地图、候选响应与可达目标主动选点|PMFS本身已经是主动方法，不能把它说成固定航线|
|停止|`checkSourceFound`使用源分布方差阈值|尖锐的错误峰也可触发成功标志；真值距离另用于日志|

在当前编译分支，单格兼容因子可写作

\[
f_i(s)=1-c_i D\,|p_i-h_i(s)|,\qquad
\widetilde\pi_t(s)=\prod_{i\in\mathcal F}f_{i,t}(s),\qquad
\pi_t(s)=\widetilde\pi_t(s)/\sum_j\widetilde\pi_t(j),
\]

其中\(p_i\)为当前反演地图、\(h_i(s)\)为该源模拟的占据频率，\(c_i,D\)来自该评分规则。这里没有额外的\(\pi_{t-1}(s)\)乘因子。可审查的是相关地图信息经许多兼容因子相乘、读出算子失配和累计地图的历史依赖；不能用“递归重复乘旧后验”作为本版本的既定根因。[S1–S3, E4]

### 2.2 实际选点使用方差启发式

该版本虽然计算`calculateMutualInformationGas()`，实际`informationValue`中读取MI的语句已注释，执行的是

\[
\operatorname{interest}(x)\propto
\operatorname{varianceOfHitProb}(x)\,[1-\operatorname{confidence}(x)]
\]

及其邻域距离权重组合。邻域循环没有把方差索引移到邻点。MI函数本身假想知道某点hit frequency并把confidence置1，使用五个频率桶；这也不是已标定的有限驻留测量通道。源码还计算了距离惩罚后的`evaluation`，但插入候选集合的是`interest`，故该固定提交的排序未使用该距离惩罚。修正这种实现缺陷是公平基线工作，不应包装成研究创新。[S5, E4]

### 2.3 B4明确证明了什么

原B4末次源更新的方差为0.3290678238，MAP位置误差5.0316647345 m，均值误差5.0988983923 m，真源1 m区域质量约0.00041262。错误候选W与真源代表T的原始兼容分数约为\(7.71713\times10^{-6}\)和\(5.18813\times10^{-10}\)，比值14874.5987。[F1–F2]

已有控制没有支持一个过于简单的修复：统一源释放面积为相同1×1单元后，两个控制W/T仍约17547.0359与20180.7108；更窄的DIRECT10单元控制仍约8.1535与8.3833。删除部分传播地图因素、统一面积或调温度可能减小过度自信，但尚无证据表明会翻转错误排序。[F2–F3, E4]

B4因此是“停止准则与位置正确性脱节”的实际反例，也与观测/模型兼容评分出错相容。**这些记录没有唯一识别出源高度、局地风、时间相关、传感器还是哪一项物理误差主导B4。**本轮的构造性反例只证明机制可以发生，不能替代物理归因实验。

## 3. 统一观测模型与真正的源可辨性

设\(s\)为有限合法候选源，\(\eta\)包括排放强度、传播参数、源高度和传感器参数，动作\(a_t\)包含路径、双点几何和驻留时间。真实可采原始块应写为

\[
X_t=\mathcal H_{\mathrm{sensor}}
\bigl(\{c(x_a(u),u;s,\eta)\}_{u\in W_t},\text{sensor state}\bigr)+\epsilon_t.
\]

所有候选都应条件化于同一个已经发生的过去\(\mathcal F_{t-1}\)，而不是分别虚构“如果该源为真它本应走过的历史”：

\[
p_t(x\mid s,r,a_t,\mathcal F_{t-1}).
\]

这里\(r\)是实现中有限nuisance状态。真正随时间变化的随机过程必须由条件状态或合法联合律表示；不能一边把源率/响应常数称为固定未知量，一边每个窗口重新抽一个最有利值。有限表是可实施接口，并不保证连续物理\(\eta\)被有限网格精确覆盖。[E5–E6]

给定一组动作，若某两个源及其允许nuisance使全部可得观测律相同，则任何推断器都不能用这些观测区分它们。更强网络、稀疏先验、低维潜变量或新名称不能越过这个边界。建设性的修正是寻找确有区别且代价可接受的测量几何/窗口，或准确报告仍相容的源集合。

## 4. 六类失败机制、解析反例与最小修正

### 4.1 浓度MSE改善主要来自共模，源差并未改善

令\(X_s(t)=m(t)+\delta_s(t)+\epsilon(t)\)。共同项\(m(t)\)可能远大于不同源之间的\(\delta_s(t)\)。更准确地预测\(m(t)\)可显著降低整体MSE，但若\(\delta_s\)仍被平滑掉、方向预测错误或可被nuisance吸收，源似然比就不会改善。这是一种数学上明确的机制，与“预测更准但源排序不改善”相容。[E4–E5]

**最小修正：**除场误差外，逐源对报告正确方向的留出对数似然比、相容集大小和给定预算下的错误确认；与共同增益/背景扰动一起测源差的稳定性。不能只在训练场上看特征距离变大。

### 4.2 源地图方差大，不代表有限读出信息多

下表是两个等先验源的解析高斯测量反例，由160点Gauss–Hermite积分计算；它不是plume仿真。[E7]

|动作|两源预测均值|测量扰动标准差|源间均值方差|\(I(S;Y)\)，nat|
|---|---|---:|---:|---:|
|A|−2，+2|10|4|0.01961017|
|B|−0.5，+0.5|0.2|0.25|0.67594258|

confidence相同时，均值方差代理偏向A，实际源信息在B约高34.5倍。因而“模型的均值分歧大”不能普遍替代“机器人在此时长和噪声下能辨源”。

另一个有限窗反例直接对应观测算子：两个离散时刻，机制A产生\((Z,Z)\)，机制B产生\((Z,1-Z)\)，\(Z\sim\mathrm{Bernoulli}(1/2)\)。每个时刻的hit概率均为1/2，但窗口平均超过3/4的概率分别为1/2和0。长期单点占据率不足以决定窗口均值过阈的概率。

**最小修正：**对每个可执行窗口用与实际读出相同的时钟、平均、阈值和响应核生成源条件重复样本；在一个联合通道中表达其分布。若只能估计有限数据表，动作价值也是估计诊断，不能把估计KL当精确物理信息率。

### 4.3 派生cue相乘与相关地图扩散会制造过量证据

对同一左右原始块\(X=(L,R)\)，sum、gradient、MNM与motion cue通常相关，且都是同一块的函数。应估计一次

\[
p(E,H_1,\ldots,H_K\mid s,r,a),
\]

不能把它替换为\(p(E\mid s)p(H_1\mid s)\cdots p(H_K\mid s)\)，除非有经过验证的条件独立性。完整可逆变换\((L,R)\leftrightarrow((L+R)/2,(L-R)/2)\)不会增加源信息；确定性压缩还满足数据处理不等式

\[
I(S;f(X)\mid a)\le I(S;X\mid a).
\]

当前M1保留的是与even-only基线相同的一位共同浓度码，不能称“全部原始浓度信息无损保留”。源对cover可能改善受限样本/模型/通信下的压缩，但这要与同特征数、同总平滑质量的固定选择和raw-joint比较。[E5–E6]

固定nuisance也必须整段共享：

\[
w_{sr,t}\propto\pi_s\omega_{sr}\prod_{k\le t}p_k(o_k\mid s,r,a_k),
\]

而非每步重新边缘化同一个先验。解析例中，源0的两种Bernoulli机制为0.1/0.9，源1均为0.5；观测1、0的共享机制证据分别0.09和0.25，等源先验后验为\((0.264705882,0.735294118)\)。每步重积分会错得\((0.5,0.5)\)。本轮`JointPosterior`通过了这个检查。根据既有历史计算下一步条件nuisance预测不构成重复更新；再次把该历史因子乘入每个状态才会重复计数。[E6]

**最小修正：**唯一事件ID、原始块只编码一次、posterior单次更新；audit为决策另行计算且不回乘posterior；重叠窗口要显式建条件律。共同不可达padding符号保留零，不为“数值稳定”制造假可达观测。源独有结构零与所有模型共同支持失败须分别处理。

### 4.4 未知幅度或传播时延可以吞掉位置差

若两个候选响应模板满足\(h_j=c h_i\)，源率未知且允许\(q_j=q_i/c\)，则\(q_i h_i=q_j h_j\)。给每个标量观测一个完全自由幅度会更严重地消除位置约束。精确枚举、block-SBL与GLRT都不能凭算法名称恢复这个丢失的辨识性。[E5, R1]

一维匀速对流模型

\[
c(x,t)=q\bigl(t-(x-s)/u\bigr)
\]

中两传感器时延差是\((x_1-x_2)/u\)，与源位置\(s\)无关。它可给流速/传播结构信息，却没有自动提供释放点距离。GCC/TDOA是经典运算，不应被表述为2026新源定位机制。

**最小修正：**使用跨窗口共享的低维释放过程，保留多维空间/时间响应，检验候选差在nuisance可解释方向以外是否非零。线性高斯幅度/基线可被积分，但完整证据需要均值、协方差与\(\log|\Sigma_s|\)，不是只比较残差或归一化SBL的gamma。沿候选差最大的合法方向采样可能产生新观测；再编码已有相同数据不会产生新观测。

### 4.5 假motion、几何记忆和源高度混淆

同一真实浓度信号经不等传感器延迟形成\(L(t)=c(t-\tau_L)\)、\(R(t)=c(t-\tau_R)\)，即使没有真实空间运动，也会产生时差/反对称响应。不同高度源在同一观测平面的场差，还可能被误记成纯XY距离作用。返回气味边界与确定释放点也是不同目标：若所有候选在管内分布一致，精确重捕获边界不会改变源赔率。[E4–E6]

**最小修正：**同步时钟、校准双侧响应或以固定共享响应状态建模；把高度、局地风、速度和实际行进方向明确纳入输入。M2保存实际进入方向的因果记忆，不能把机头朝向或未来真值当进入向量。返回管只限制普通利用动作，付费coverage与合法challenger须能访问管外；方向不确定管不是未经校准的“95%置信管”。

### 4.6 低后验源恢复不能由高置信或容错码名称保证

若真源初始质量为\(10^{-6}\)，仅恢复到0.95就需要新增赔率约\(1.9\times10^7\)，即约16.76 nat的对数证据。每块期望只有0.05 nat时，约335块是证据量级，并非任何有限样本保证。若真源被结构零删除，后续正likelihood乘法也不能恢复其概率；这必须与“小而正的错误先验”分开。[E5]

“五次观测预测最多错一位”也不直接等于可以辨认16源。仅在五次观测真的是五个二元符号、要求对任意单bit错误保证恢复且每源一个码字时，Hamming球界给出\(16(1+5)=96>2^5=32\)，该要求不可能成立。连续值、多符号或随机误差模型不受这个特定五bit反例直接裁决，应按其真实联合观测律评估。这个反例不能反过来冒充对既有15.7/16经验结果的精确生成解释。

**最小修正：**完整保留合法源，源独立付费覆盖，模型内新后缀检验，以及只影响后续动作的challenger反馈。有限相关burst可通过联合error channel表示；每步独立error kernel不等于整段任意至多k次错误的容错保证。只改预测表而不对环境符号施加相同错误机制，会造成新失配。[E5–E6]

## 5. M3具体能保证什么，不能保证什么

### 5.1 非等成本分配和不被posterior关闭的探索

给定当前incumbent \(i\)，对所有合法竞争源\(j\)计算候选条件预测KL \(D_{ij}(a)\)，按单位成本观测率求解

\[
\max_{y\ge0,v}v,
\quad c^\top y=1,
\quad \sum_a y_aD_{ij}(a)\ge v\ (j\ne i),
\quad \lambda_a=\frac{y_a}{\sum_b y_b}.
\]

这是非等成本Chernoff结构的可实施形式；KL、LP和Chernoff不是本轮新发明。若两个动作的竞争源信息为\((1,0)\)、\((0,9)\)，成本为1、9，则最优抽样频率为0.9、0.1，单位成本最坏信息率0.5；误把均分资源份额0.5、0.5当抽样频率只得到0.1。[R2–R3, E5]

实现再混合\(\rho_t=(1-\epsilon)\lambda_t+\epsilon\nu\)，其中\(\nu\)与源后验无关。若一个可辨动作集合B在整个比较阶段均合法、可负担且\(\nu(B)>0\)，则无论当前posterior多么偏，单次选择它的条件概率至少\(\epsilon\nu(B)\)；前n次完全不访问它的概率不超过\((1-\epsilon\nu(B))^n\)。这证明探索概率不被低posterior消除，**没有证明B真的可辨、有限预算必恢复或估计KL正确**。预算尾段动作不可负担时，保证只针对当时可负担集合；代码重新解子问题并记录实际分布。[E5–E6]

所有源对min值为0时，输出未可分诊断并使用指定/轮换合法challenger的pair分配与coverage，不回退为EIG来掩盖机制失效。不可达或全局等价的源对仍不能被强制探索解决。

### 5.2 固定共享nuisance的新数据审计

在审计起点\(t_0\)之后，给每个待检验源\(s\)准备一个只使用过去信息、事先归一化的备择预测\(q_{s,t}\)。定义

\[
E_{s,t}=\frac{\prod_{k=t_0+1}^{t}q_{s,k}(O_k)}
{\sup_{r\in\mathcal R_s}\prod_{k=t_0+1}^{t}p_k(O_k\mid s,r,A_k,\mathcal F_{k-1})}.
\]

分母是**整段固定一个r后再取上确界**，不是每个时刻选不同r再相乘。准备预测在观察前完成并冻结；旧错误source posterior不作为排除低概率源的依据。真实源与真实固定r若属于准确的条件族，动作只依赖实际过去，所有预测与时间依赖均正确，则

\[
\mathbb P_{s,r_*}\{\exists t:E_{s,t}\ge1/\alpha\}\le\alpha.
\]

证明依赖\(E_{s,t}\)被对真实r的非负似然比检验超鞅支配；\(E\)本身不必是超鞅。存在精确支持零时，不能一概把似然比称为均值1鞅。有限样本估计表、遗漏真实nuisance、错误的块独立性或任意从已有数据启动的新审计，均不会自动获得实际气体风险保证；多次重启须安排相应错误预算。18项M3单元测试核验了上述实现性质和有限模型枚举风险，没有证明真实家族包含性。[E5–E6]

`compatible_now={s:E_s(t)<1/alpha}`允许重新进入；`not_rejected_since_start={s:max_{u≤t}E_s(u)<1/alpha}`不允许重新进入。两者在准确模型条件下都受上述anytime事件控制，但语义不同。它们均不是后验概率图，也不能被归一化再作为新的likelihood。若全模型状态对观测后缀均为零，代码在改变证据前报告支持失败，不以0/0产生假置信。

最新engine在incumbent被current list拒绝时，从仍compatible的其他源选最小log-e者作规划challenger。合法全源集继续保留，audit不乘回posterior。此规则执行成功只证明决策接口工作；是否改善独立恢复必须由no-audit-feedback消融裁决。[E2, E6]

## 6. 当前控制后端的两个关键限制

### 6.1 同时间预算不等于同信息利用

engine在travel期间每0.1 s生成双点浓度供M2边界检测/记忆使用，而source likelihood更新paired dwell块。各episode现在记录`travel_scalar_samples`、`dwell_scalar_samples`、`posterior_scope`与公平性限制。准确说法是“基于dwell块的工作概率”；它不是包含所有旅行观测的完整源后验。[E2, E6]

M3政策消融必须共享相同M2/travel条件。完整链与不使用travel的joint-EIG比较时，差异同时含不同的原始信息利用方式，不能把任何优势全归给新的成本分配。更强比较需要给各法同一可用原始流，或建立travel和dwell的联合条件模型并将其计入强基线。按路径付费解决资源公平性，仍未独自解决信息公平性。

这不自动否定audit的条件定理：若给定固定真实\((S,R)\)后，新dwell服从正确条件律，动作可以使用其他过去side-channel。问题是当前经验条件表是否准确，以及“完整Bayes后验”这一表述是否成立，不能混为一谈。

### 6.2 均匀phase使该运动相位不含额外源身份

控制后端含移动波形

\[
\sin\{3t+\phi-(x-s)^\top n_r\},\qquad
\phi\sim\mathrm{Uniform}(-\pi,\pi).
\]

令\(\phi'=\phi+s^\top n_r\pmod{2\pi}\)。固定机制r后，\(\phi'\)仍均匀，因此去掉空间幅度\(\mu_s(x)\)后的整个移动波形分布与源位置无关。源信息可以来自空间均值、幅度、噪声尺度或其联合结构；该构造不能验证“运动相位本身新增源定位信息”。这是模型对称性的严格反例，不是从弱实验结果猜测。[E6]

该L1后端还在每个块重采相位/共享扰动并初始化传感器状态，不跨travel、dwell和下一块连续继承真实传感器状态。0.1 s时钟与显式成本是有用的工程合同，不能将其升级成native plume连续动力学证据。

## 7. 物理数据资格：已取回什么，尚缺什么

### 7.1 OCB-R2 / X00的实际字节与允许结论

本轮从`kris-yun/uav-gsl-isj@005ba6a34d95fdfe340050df96fe30a688fa71bf`取回并核验八个已开放DISCOVERY世界；不能把原元数据中的64条全部写成已经拥有的物理世界。[D1–D3, E4]

|事实|已核验内容|研究边界|
|---|---|---|
|源与seed|两替代释放位置，各四个不同master seed，共八世界|不是两源同时释放；同r编号也不是共同随机数配对|
|三维源位置|A=(-0.6,1.95,0.4)m；B=(-0.4,-2.9,-0.3)m|同时改变XY和z，不能称纯XY扰动；高度相差0.7m|
|浓度切片|每世界`cube`为(10,87,114) float32，轴time/x/y，观测平面z=0.2m|三维传播的二维切片，不是完整三维状态|
|池化探针|每世界`pooled`为(10,30) float64，原探针为2×2 native cells平均|八件全部bit-exact重算；不是理想点传感器|
|物理时间|首帧50.2998047s、末帧499.821289s；间隔49.700897–50.003052s|同帧空间同步成立；连续短窗、高频时差与动态边界运动不成立|
|风|native wind index与bundle hash|未获得可调用局地(u,v,w)字节，不能写局地风已到位|
|传感器|GADEN理想molar ppm导出|没有真实延迟、噪声、饱和或旋翼扰动校验|
|划分|每源r01/r02训练，r03/r04开发；整世界分组|40个开发快照只来自4个独立世界；历史已开discovery不是新盲确认|
|运动资格|同期平面空间选点可回放|未证明飞行可达、避障或同步硬件几何合法|

House01 occupancy实际字节尚未恢复，源体素与出生扰动邻域是否free继续HOLD。source B的负z坐标本身不足以判无效；已有hash和`scientific_sanity_pass`也不足以判合法。必须读取实际occupancy并给出坐标到体素及邻域检查收据。新H03/confirmation未解封；50秒间隔不能靠插值获得未观测的连续气味运动。[D2–D3, E4]

原元数据记录8 contexts × 2 sources × 4 seeds共64个discovery导出，完整native filament世界仍在用户既有本地归档。本轮读出的16个NPY共3,195,008 bytes，只覆盖X00八条。原生成器版本/补丁与当前本地upstream core也不等价，不能以重新运行不同版本替代原资产资格。

### 7.2 其他既有资产不能越级使用

|资产|可用范围|不能据此声称|
|---|---|---|
|House02 18源×16旧实现|原定义固定探针的离线源判别|record index是真秒；未取回局地风；test响应可作为在线候选模板|
|O24六世界、48 unique frames/240 queries|按原tick绑定的旧脚本机制筛查|240个独立物理样本或任意新策略的反事实闭环|
|Cross-house H07/H14 FAST/SLOW|H14原回放，H07 receptor-domain故障可作错误检测|四任务等于四独立seed，或故障数据为正常源辨识证据|
|B4原轨迹|一个已知失败episode的归因与执行链审查|独立训练分布或任意双点连续场|
|CH4 S2 DAY/NIGHT|0.1s tick、20s短窗及局地三维风的读出smoke|多替代源、独立实现、未见源泛化或完整UAV搜索|

这些资格来自逐资产审计，不因模块接口能够读取数据而升级。普通原始观测修正和时钟检查是必要基础，不能单独充作新方法创新。[E4]

## 8. 已冻结实测：必须一起展示强基线与负结果

### 8.1 OCB静态开发pilot

协议先冻结，在训练四世界的435个原探针对中选择probe12/17，随后评估四开发世界共40快照。两点约相距7.003m；尚未成为已合法UAV基线。结果如下。[E1]

|方法|正确快照/40|本次允许解释|
|---|---:|---|
|mean-only Gaussian|31|单一均值摘要丢失部分空间联合区别|
|raw-joint Gaussian|40|该二源开发数据的同期空间joint有用|
|可逆even/odd Gaussian|40|与raw-joint理论等价；最大后验差4.5102810375396984e-17|
|冻结静态M1 joint histogram|31|没有超过mean，更没有超过raw-joint|

原始结果使用当时版本，后续固定总Dirichlet平滑修复没有回写该分数；复现保留`legacy_per_cell=0.5`。40/40既不是40个独立世界，也不证明输出概率已校准。没有native PMFS head-to-head，没有时序MNM测试，两候选也不能检验多竞争源需要混合动作的max–min结构。协议SHA256为`a469f14ee1de56183669ae0b7f4e054697334d6d5c74b4bd58c97a9ca2e3c08e`。[E1]

### 8.2 完成的156个L1控制episode

矩阵配置SHA256为`25d5d047a238c3c846179c3098e2f848ce5fd0d8df28b67cba37082d5053d303`；13变体、6控制世界、普通/错误两种先验，每episode上限300s。下面均为最终top-1，不将终点饱和改写成未报告的时间曲线优势。[E2]

|变体|普通先验|错误先验|
|---|---:|---:|
|A adapted variance|4/6|3/6|
|A′ joint EIG|6/6|6/6|
|M1 direct best-one|6/6|6/6|
|M1 fixed-two|6/6|6/6|
|M1 raw-joint strong|6/6|6/6|
|M2 off|6/6|6/6|
|M2 geometry without memory|6/6|6/6|
|M2 boundary-only|6/6|6/6|
|M3 joint EIG|6/6|6/6|
|M3 direct cost|6/6|6/6|
|M3 no coverage|6/6|6/6|
|M3 no audit feedback|6/6|6/6|
|full|6/6|6/6|

adapted variance在错误先验组有一个最终错误高置信episode；所有其他变体该计数为零。full错误先验组合计触发七次audit challenger反馈，普通先验组为零。no-audit-feedback触发零次，仍全对；no-coverage也全对。因此这组结果证明反馈路径可以运行，没有证明它是成功的独立原因。强基线饱和使三个模块的独立收益在该端点无法确立。

该结果亦不支持用速度优势替代精度优势：full平均规划约2.8–3.0ms，两个EIG变体约0.47–0.52ms。不同实际付费用时有尾段剩余差，必须使用同一预算规则和逐episode实际成本；不能把数秒均值差直接叫显著样本效率提升。结果文件明确`native_improvement_verified=false`。[E2]

## 9. 能改变裁决的最小下一步

下一步首先提取已有native资产中合法连续窗口，而不是扩建网络或重跑大量新世界。固定三项基础合同：源体素和出生邻域合法；浓度/局地风/位置/时钟同步；物理sensor state与窗口、路径成本一致。缺项保持HOLD，不用50秒插值或另一个解析后端代替。

|待检验主张|必须同等的条件|直接判据|失败后的研究决策|
|---|---|---|---|
|M1源对cover有独立价值|同raw block、同even边缘、同feature数量和总平滑质量、只用TRAIN选择|留出整世界的源排序、对数分数、仍相容源对；必须有强raw-joint|定位为受限压缩，不声称新增物理信息|
|M2记忆/方向有独立价值|同可用travel流、同预算/动作合法性、相同源模型|去记忆、纯几何、普通返回、固定方向的独立消融|只保留有效动作提议；不把重捕获当定位成功|
|M3分配/覆盖能帮助错误信念恢复|同channel、观测流、先验、成本；至少三候选及互补动作|与joint-EIG、直接成本Chernoff、no-coverage/no-audit比较恢复曲线和错误确认|保留结构性探索机制，撤回未证实性能贡献|
|audit控制真实错误率|真实条件族包含性、依赖与共享nuisance正确、新数据起点|按独立world评估覆盖与错误确认；形式保证另需包含证明|继续标conditional/model-relative；不标真实alpha保证|
|时间运动cue超出静态幅度|合法连续native原始流、同步和响应校准、完整联合参照|相同资源下存在不能被静态幅度或共享nuisance解释的源差|停止用当前phase模型或静态切片支持该主张|

普通错误先验且正确模型，与真源不在候选集/物理机制失配必须分开测试。前者检验探索和证据恢复，后者检验模型支持失败与不确定集合；不能通过数值floor恢复了一个正数就宣布解决后者。当前已打开的X00与L1数据都不能充当新的盲确认集。

最终状态为：**实现PASS；若干精确有限模型性质PASS；静态物理开发pipeline PASS；连续动态与合法UAV物理资格HOLD；三模块独立定位收益NOT ESTABLISHED。**该状态由实测强基线、反例和数据资格共同决定，不以论文层级、模块数量或人为评分门槛替代。

## 10. 来源与可追查收据

### 官方源码与B4原证据

- **S1** 固定提交的[Simulations.cpp](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp)：模拟占据频率、源兼容评分与归一化更新。
- **S2** 固定提交的[PMFS.cpp](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp)：阈值化、地图/风/候选更新调度。
- **S3** 固定提交的[PMFSLib.cpp](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp)：地图反演与传播。
- **S4** 固定提交的[StopAndMeasureState.cpp](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/Common/States/StopAndMeasureState.cpp)：有限驻留平均。
- **S5** [固定官方源码树](https://github.com/MAPIRlab/GasSourceLocalization/tree/4e141e162551e674f2f30ddb8859136c72139aac)：`MovingStatePMFS.cpp`与`PMFS_utils.cpp`；逐文件定位、行号和SHA见E4及`SOURCE_RUNTIME_RECEIPT.json`。
- **F1** [B4官方终止判定原记录](https://github.com/kris-yun/uav-gsl-isj/blob/c2aacbac7fb2ef7be4be3c9c7dcfce20c11f823c/research/pmfs_reproduction/b4_official_terminal_resumed_20261010/B4_OFFICIAL_TERMINAL_DECISION_zh.md)。
- **F2** [B4 M0证据归因原记录](https://github.com/kris-yun/uav-gsl-isj/blob/17c48958f9d7eda98dd61b8e656a8c52205cb7d7/research/pmfs_reproduction/b4_m0_offline_attribution_20261010/B4_M0_EVIDENCE_ATTRIBUTION_zh.md)。
- **F3** B4 M1源表示控制：原仓库`research/pmfs_reproduction/b4_m1_source_representation_20261010/review/M1_A_RESULT.json`；physics已读原结果，具体数值和出处保留于E4。未在本文杜撰新的源码提交URL。

### 本轮实测、审计与数据

- **E1** `results/ocb_static_v1/STATIC_PILOT_RESULT.json`及当时`code_at_run`：静态协议、冻结选择、逐世界/逐快照结果与旧平滑语义。
- **E2** `results/control_matrix_v7_frozen/CONTROL_MATRIX_RESULT.json`及`episodes/*/CONTROL_RESULT.json`：156个L1 episode、实际成本、动作、travel/dwell数量与方法限制。
- **E3** 本目录`EXPERT_MEETING_AND_DECISION.md`：四轮、七视角由root和三个真实代理承担，独立冻结SHA与披露X的先后顺序。
- **E4** 工作证据`evidence/discovery/pmfs_physics_independent.md`、`SOURCE_RUNTIME_RECEIPT.json`、`data_qualification_v7.json`：底层独立诊断与明确标注的第二轮物理裁决。
- **E5** 工作证据`evidence/discovery/radar_independent.md`、`radar_round2.md`；实现证明`src/gsl_discrimination/m3_audit/THEORY.md`。
- **E6** 工作证据`evidence/discovery/redteam_round4.md`、`REDTEAM_ROUND4_CHECKS.json`；代码`channel.py`、`engine.py`、`m1_opponent/calibration.py`、`m3_audit/`；对应标准库unittest。
- **E7** 工作证据`evidence/discovery/FINITE_WINDOW_COUNTEREXAMPLE.json`：解析高斯反例，不是新物理实验。
- **D1** [OCB固定仓库提交](https://github.com/kris-yun/uav-gsl-isj/tree/005ba6a34d95fdfe340050df96fe30a688fa71bf)；下载来源、blob与逐件SHA见`evidence/discovery/ocb_r2/REMOTE_FETCH_RECEIPTS.json`。
- **D2** `evidence/discovery/ocb_r2/RETRIEVAL_FREEZE.json`、`RETRIEVAL_VERIFICATION.json`：预先选择X00及字节/池化核验。
- **D3** `evidence/discovery/ocb_r2/metadata/`中的原时间映射、source manifests、比较合同与occupancy审计摘录。

### 算法母模块的原始来源

- **R1** FUSION2025多参数化字典block-SBL：[作者全文](https://arxiv.org/html/2503.12913v2)，DOI [10.23919/FUSION65864.2025.11124160](https://doi.org/10.23919/FUSION65864.2025.11124160)。共享支持结构是迁移依据，单源精确枚举是本任务适配，不是原论文声称的气源后验算法。
- **R2** TIT2025主动多假说检验：[作者全文](https://arxiv.org/html/2405.06554v3)，DOI [10.1109/TIT.2025.3588527](https://doi.org/10.1109/TIT.2025.3588527)。
- **R3** 非等成本ASHT：[作者全文](https://arxiv.org/html/2509.11632v3)，[ICASSP2026官方条目](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)。其渐近结果不能升级成本任务五次观测或有限预算必恢复保证。

经典的Bayes、KL/JS、GLRT、GCC、数据处理、Chernoff、似然比和Ville不等式均按经典工具使用。PNAS/Nature新生物模块与本任务适配边界详见配套会议文档及`THREE_INNOVATIONS_AND_THEORY.md`，不把基础工具重新归为2026原创。
