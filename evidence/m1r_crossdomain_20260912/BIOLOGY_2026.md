# 2026 生物物理思想与 PMFS 源响应别名：两篇原文核验

核验日期：2026-09-12。范围为正式 2026 生物／生物物理论文，只深入两篇；未使用 bank、VM、训练或新 forward。工作区事实来自本轮实际读取的 [M1R_CAUSAL_IMPLEMENTATION_STATUS_20260912.md](../../docs/M1R_CAUSAL_IMPLEMENTATION_STATUS_20260912.md)，没有用历史记忆替代当前状态。

**结果：找到两项有实质对应的大思想，未找到当前观测条件下可直接修复 PMFS 源别名的现成方法。** 第一项让我们区分“物理上不可辨识”和“内部表示抹掉了信息”；第二项说明，差分能改变判断方向的原因是响应通道具有不同的物理传播核。当前数据只确认原始序列可用，尚未证明所需的源特异动态信息存在。

## 1. 信息瓶颈可能在感知系统内部，而不是环境本身

**Henry H. Mattingly, Keita Kamino, Jude Ong, Rafaela Kottou, Thierry Emonet, Benjamin B. Machta. _E. coli chemosensing accuracy is not limited by stochastic molecule arrivals_. Nature Physics 22, 123–130 (2026).**

正式期刊页明确标注 Article / Published 08 January 2026；DOI 中的 `025` 不是发表年份。[正式全文](https://www.nature.com/articles/s41567-025-03111-4)，[期刊 PDF](https://www.nature.com/articles/s41567-025-03111-4.pdf)。核对位置：正文 Eqs. (1)–(3)，Fig. 2 及 “Relevant information encoded in kinase activity” 部分。

论文区分外部浓度变化、分子到达和内部激酶活动。任务相关信号是 $s(t)=d\log c(t)/dt$。它用条件互信息率量化可恢复信息：

$$\dot I^*_{s\to r}=\lim_{dt\to0}\frac{I(r(t+dt);s(t)\mid\{r\})}{dt}.$$

内部响应模型为

$$a(t)=a_0-\int_{-\infty}^{t}K_r(t-t')[r(t')-r_0]dt'+\eta_n(t),$$

$$K_r(t)=G_r\left[\tau_1^{-1}e^{-t/\tau_1}-\tau_2^{-1}e^{-t/\tau_2}\right]\Theta(t).$$

其积分为零，体现适应性响应。通过受控浓度阶跃和单细胞 FRET 分离响应核与内部噪声，论文发现内部编码的信息远低于分子到达物理极限。定量推导依赖浅梯度、近似线性高斯、可忽略的行为反馈及特定噪声模型；它没有证明任意环境下 $d\log c/dt$ 都是充分统计量。“causal Wiener filtering”在此指仅使用过去数据，不等于 SCM 因果识别。

### 借什么：用相同估计目标逐层定位信息丢失

以下为 PMFS 迁移推导，不是论文中的 PMFS 结论。

现有链路可写为：物理时序 $Y_{1:T}$ → 聚合命中表示 $B=T(Y_{1:T})$ → 候选事件响应 → M1R 对比 → posterior。已知 H01/H02 的别名发生在当前候选事件表示上；这只证明该层不能区分，不证明物理时序也不能区分。

对冻结的动作与环境记录 $C$，若新增量 $Z=K*Y$ 仍只是现有原始观测的确定性变换，则有

$$I(S;Z\mid B,C)\le I(S;Y\mid B,C).$$

因此新模块应该先回答：**被 hit/miss 聚合删除的浓度幅值、响应相位、持续时间或恢复过程里，是否仍有源相关、且校准失配不能复制的信息？** 零积分响应可作为一种观测表示，用于消除常数偏置；“快慢差分”及零积分核本身是旧信号处理结构，不是从这篇 2026 论文自动取得的主创新。

### 当前可用与缺口

- **可用观测：** 240 s 内同步 gas、pose、wind、移动状态和时间；状态文件已验证三 House 均有 14 个合格静止段。可检查变化是否在阈值化、聚合或后续源映射阶段被删除。
- **最小前提：** 先固定所要辨认的是源位置，而不是上升／下降或 plume 接触状态。能够预测这些状态，不等于能分开两个源。
- **缺失证据：** 源特异原始时序响应及传感核／内部噪声的独立校准。目前真实浓度不可作为部署输入，单条移动 gas 序列不能把输运波动和 sensor 内部噪声自动分开。
- **不可移植：** 不能照抄细菌的响应时间常数、分子 Poisson 噪声或浅梯度信息率，也不能从 1200 个相关帧估计一个数字就宣称源可辨识。若所有原始候选响应也相同，任何共同 $K$ 的输出仍相同。

本篇可支持**信息损失定位与测量结构设计**，还不能支持一个新的源 likelihood。新的理论义务是说明 PMFS 的表示如何保留其自身的源辨别统计量，并把这一增量与普通 raw-input Bayes 区分开。

## 2. 差分有效的关键，是两条通道具有不同的物理传播核

**Blox Bloxham, Hyunseok Lee, Jeff Gore. _Repulsion from slow-diffusing nutrients improves microbial chemotaxis towards moving sources_. Nature Communications 17, 4872 (2026).**

[正式期刊页](https://www.nature.com/articles/s41467-026-71148-x)标注 Published 04 April 2026；[正式 PDF](https://www.nature.com/articles/s41467-026-71148-x.pdf)第 1 页标注 Accepted 9 March 2026。原文方法核对位置：PDF 第 4 页 Eq. (1)，第 9 页 Eqs. (2)–(5)，第 10 页 Eq. (10)。[作者固定版本代码](https://github.com/Blox-Blox/Differential-Chemotaxis/tree/704de055009a3470ee612546b0c5cfe27c044b64)由原文 Code availability 给出；本轮没有运行。

同一移动源释放快、慢扩散物质，产生非平行浓度梯度。异质受体结合模型得到

$$X=n_A\log(1+c_A/K_A)-n_R\log(1+c_R/K_R).$$

在点源近似下，$\rho=\sqrt{r^2+z^2}$，

$$c_i(r,z)=\frac{q_i}{4\pi D_i\rho}\exp\left[-\frac{v_p(\rho-z)}{2D_i}\right].$$

由于 $D_A\ne D_R$，慢通道更偏向尾迹，二者相减可形成原先单梯度没有的方向。论文通过模拟及已有氨基酸响应数据支持该机制；其主要点源模型依赖近似均匀扩散、定速源和小 Péclet 数，并另用有限元检查部分情形。它不是任意输运失配下的源位置识别定理，也不证明差分在所有参数下获益。

### 借什么：共享环境下，寻找不能相互替代的机制响应

以下为本报告迁移推导。若两个可观测通道满足

$$y_1=\mathcal G_1(S,U),\qquad y_2=\mathcal G_2(S,U),$$

且两个候选在第一通道相同、第二通道不同，则联合观测可以打破第一通道的等价类。差分可以压低两通道共享的背景分量，同时保留机制差异；但前提是共享分量及差异来自可说明的物理结构。论文的额外信息不是一个负权，而是 $D_A\ne D_R$ 导致的新梯度方向。

这对 M1R 的对应是：已有 source/context 相减已经起作用，但如果两个候选的 source 响应相同，继续优化公共背景相减不会把它们分开。需要的二次创新是得到不同的候选条件响应通道，说明它怎样在共同环境中区分源与尾迹／其他 nuisance；把权重改成生物学术语没有完成这一点。

### 当前可用与缺口

- **现有输入不是论文的两条通道。** 单路 gas 与 wind 分别是浓度响应和局部环境观测，不能将 wind 当第二种扩散物质的浓度；两者不满足上述共同源释放的结构。
- **同路 gas 的任意快慢滤波不等于两种物理传播核。** 如果原始候选轨迹 $Y_s=Y_{s'}$，则任意相同滤波 $K_1Y$、$K_2Y$ 仍对两候选相等；不存在由复制观测创造独立信息的途径。
- **可保留的前提门：** 对已存在且部署可得的响应量，先证明至少一条通道在允许的传感／输运变换下仍区分别名候选，再考虑通道组合。必须冻结共同 nuisance 范围，不能给真源更宽的解释空间。
- **不可移植：** 本轮不新增化学传感器、不生成不同扩散系数 forward，也不把论文受体数比例作为 planner／likelihood 权重。其均匀流参考系对应不能推广为任意障碍环境、局部测风或湍流干预。

本篇可支持**物理通道多样性如何解除单通道歧义**这一设计原则。当前没有证据表明现有记录已经具备所需的第二条源特异响应，因此不批准为新增 PMFS 源修复模块。

## 3. 两篇合起来能形成什么研究问题

值得推进的表述是：**当前 PMFS 是否把仍可辨别源的动态响应压缩成同一个事件模板；若是，哪些基于测量物理的响应分量能保留源信息，同时消除共享背景？**

这不是要求凭空引入第二传感器，也不是把已有两个滤波器当成独立观测。第一篇告诉我们先定位损失发生在哪一层；第二篇告诉我们只有物理响应差异真实存在，差分才有可能改变歧义。两篇都没有替 PMFS 证明源干预机制，也没有把新分数校准成 likelihood。

在既定只读范围内，下一门是核对 raw → 聚合 → source mapping 的信息删除位置及已有候选响应对象的粒度。若原始层有真实差异但事件模板合并了它们，可研究保留该差异的观测算子；若原始层没有源条件响应，或允许的 nuisance 已能复制差异，则当前数据不足，不能用论文年份补齐。

最终状态：`BIOLOGY_2026_SUBSTANTIVE_DESIGN_INSIGHT_NO_DEPLOYABLE_SOURCE_REPAIR`。未产生新的 3/3、主创新 PASS 或闭环结果。

## 4. 旧用史、检索及文件 provenance

- 已对以下两个目录执行 `rg -n -i`，搜索两篇 DOI 后缀 `03111-4`、`71148-x`、题名片段 `chemosensing accuracy`、`Repulsion from slow`、作者 `Mattingly`、`Bloxham` 和 `differential chemotaxis`：`D:\ZYC\CSTAR_M1R_CAUSAL_REPAIR_20260912\docs`、`D:\ZYC\A-gas\docs`。两次均 exit 1、无命中。此结果仅说明所查 docs 未命中，不宣称全会话／全硬盘历史首次使用。
- 技能：`D:\ZYC\UAV\.codex\skills\paper_search\SKILL.md`；脚本：同目录 `scripts/search_papers.py`。脚本版本不支持说明中的 `--json`，本轮直接调用已核实的 `search_papers()` API，将含摘要结果保存到 `biology_search_raw.json`。这是本报告之外唯一新增文件。
- 一次多源查询：`biological perturbation dynamics identifiability`，年份 2026，每源最多 3 篇；返回 arXiv 3、OpenAlex 3、Crossref 3、其余 0。检索结果的年份／venue 未直接作为发表证据；最终两篇由期刊官方网页、正式 PDF 和具体方法核验确定。
- 原始错误：DBLP `Expecting value: line 1 column 1 (char 0)`；Semantic Scholar `429 Client Error`。Nature 部分页面在 web 工具发生 cookie 重定向或 Internal Error，已通过可访问的官方全文、期刊 PDF，以及 requests 在内存读取正式公开 PDF 核验；未绕过付费或登录限制，未保存 PDF。
- 仅深入上述两篇。早年 DL-MRA 不因搜索结果混入 2026 而计入；新检索的相邻 review、预印本和需要训练的通用模型没有被当作这两篇的替代理论。此前 DML-IL、FANS、ACI 没有作为本轮新贡献提交。
- 文件使用 UTF-8、LF；无算法／配置改动。
