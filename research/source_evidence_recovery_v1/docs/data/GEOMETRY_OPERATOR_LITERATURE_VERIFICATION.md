# V6 几何迁移文献核验与具体可借算子

核验日期2026-10-23。以下区分可访问全文与仅正式题录/摘要，不把母论文性能当气源定位性能。当前主框架不需要把这五篇都组合进去。

## 1. 指定的两篇论文

### 1.1 GFNO

Yanyu Ke, Yifan Wang, Gang Hu, K. T. Tse. **GFNO: A generalized Fourier neural operator framework for wind flow field reconstruction from sparse observations.** Building and Environment 304 (Part B), 115143, 2026；DOI **10.1016/j.buildenv.2026.115143**。出版社卷期入口注明2026-10-01；预印本DOI为10.2139/ssrn.6764764，不能混为正式DOI。

正式题录由出版社文章页/卷期及作者机构研究记录交叉支持；本次出版社全文返回403，SSRN交付PDF亦403。因此**未完成全文公式/消融核验，不作为已精读的主创新母算子**。公开摘要所支持的是“稀疏观测嵌入到latent grid，再经Fourier operator重构风场”，不是已证明的气源可辨识性提升。四种embedding和三种kernel的具体定义、全部损失权重、代码许可目前不可核实，不能自行补出。

- 出版社：https://www.sciencedirect.com/science/article/abs/pii/S0360132326009467
- 正式卷期：https://www.sciencedirect.com/journal/building-and-environment/vol/304/part/PB
- 作者机构题录：https://scholar.hit.edu.cn/en/publications/gfno-a-generalized-fourier-neural-operator-framework-for-wind-flo/
- 预印本：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6764764
- 官方可执行代码：本次未找到可确证链接。

**本领域裁决：**若以后取得全文，可作为合法局地风→教师隐传播状态的强基线。不得先把稀疏风补全替代M1源证据监督；更小风MSE不必改善源margin。

### 1.2 Nature Communications / Gen4Turbulence

Vivek Oommen, Siavash Khodakarami, Aniruddha Bora, Zhicheng Wang, George Em Karniadakis. **Learning turbulent flows with generative models for super resolution and sparse flow reconstruction.** Nature Communications 17, 3707，2026-03-09；DOI **10.1038/s41467-026-70145-4**。

已访问17页正式PDF，检查任务定义、Methods式(5)–(8)、条件GAN/EDM任务区分、消融与数据代码来源。adv-NO使用time-conditioned UNet，预测未来/高分辨率场，训练由L1、固定感知特征、RaGAN相对真假损失组合。判别器训练时参与、推断时丢弃。稀疏重构Task3是另一个条件GAN/EDM实验，不能把它与adv-NO混称同一模块。论文明确其网格依赖；“zero-shot”指同一几何内新掩码。单轨迹多snapshot的数据效率不能换算成多世界泛化。

- 正式PDF：https://www.nature.com/articles/s41467-026-70145-4.pdf
- 代码：https://github.com/vivekoommen/Gen4Turbulence
- 作者数据：https://doi.org/10.5281/zenodo.17088765

**本领域裁决：**其“全局平均误差忽略细节”的失败解释与本项目可类比，但源证据任务敏感方向不等于高频。用它作全场重建/谱保真辅助基线；主训练目标仍须观察源对证据。不能仅换成GAN就声称有物理源判别能力。

## 2. 更直接的几何/算子迁移来源

### 2.1 RIGNO（NeurIPS2025）

Sepehr Mousavi等，**RIGNO: A Graph-based Framework For Robust And Accurate Operator Learning For PDEs On Arbitrary Domains**。正式NeurIPS2025论文；arXiv:2501.19205v2，2025-10-14。

全文已检查Methods、Appendix A/B、F.8/F.9、局限。输入为不规则点坐标、场值、系数、当前时刻与lead time；按局部密度构造覆盖全域的regional节点/支撑半径，输入点聚合到区域网格，经多尺度消息传递，再解码到查询点。每层随机edge masking降低依赖固定连边；fractional pairing用模型中间态训练未见小时间步。监督是完整解轨迹。它具可实现接口与开源JAX代码，但主体基准为2D，OOD源团中心大位移在Smooth Transport明显退化。

- 全文：https://arxiv.org/html/2501.19205v2
- 正式论文：https://papers.nips.cc/paper_files/paper/2025/file/dcb91f43033bb1d367d1848806dee98d-Paper-Conference.pdf
- 代码：https://github.com/camlab-ethz/rigno （MIT）

**适配算子（我们的提案，非母论文结果）：**以可得局地history token和3D几何点作物理点，条件源坐标参与区域消息，查询端输出观测分布参数；原生区域构图只解决不规则几何输入。是否保留源方向导数依靠M1任务监督与同容量基线验证。禁止把random edge masking产生的波动直接称校准后验。

### 2.2 Schwarz Neural Inference / SNI（ICLR2026）

Jianing Huang, Kaixuan Zhang, Youjia Wu, Ze Cheng. **Operator Learning with Domain Decomposition for Geometry Generalization in PDE Solving**。ICLR2026正式论文，28页；arXiv:2504.00510v2。

已检查主算法、附录C/D/G和实验。原问题是新几何不落在训练形状分布。母算法先在随机基本多边形及多样边界上训练局部算子，再把新域分解成重叠子域，以当前全局解作人工边界，局部预测与Schwarz–Richardson迭代拼接全局解。输入包括几何、全局/人工边界、系数和源项；输出局部/全局PDE解。理论重点为自伴强制椭圆算子，非线性/非自伴湍流平流不自动适用；论文明列Navier–Stokes未覆盖。

- 正式全文：https://proceedings.iclr.cc/paper_files/paper/2026/file/710445227fa8c1b6a9ceada902dd4741-Paper-Conference.pdf
- HTML：https://arxiv.org/html/2504.00510v2
- 代码：https://github.com/questionstorer/sni

母迭代可写为

\[
u^{n+1}=u^n+\tau\sum_k R_k^T[\widetilde S_k(u^n,B,H)-R_ku^n].
\]

**适配边界：**可研究已知边界辅助扩散场或小区域教师拼接，不能把未知界面风当已知真值。若用于本项目，要另证学习迭代收缩/稳定性；仅有局部误差界只可直接导出邻域误差递推，不能在未知非线性系统里宣称收敛。此路线本轮不加入主M1以免改变研究目标。

### 2.3 Transolver++（ICML2025）

Huakun Luo等，**Transolver++: An Accurate Neural Solver for PDEs on Million-Scale Geometries**。PMLR267:41432–41449（ICML2025）。正式PMLR页面及全文方法、Table3消融已核对。

输入为网格点物理/坐标特征；学习每点局部温度，使用Gumbel重参数化形成point-to-state分配，聚合为少数物理state tokens，在token间计算信息，再回传原网格。母公式的自适应温度和slice reparameterization比泛称“Transformer”具体。多GPU通信只聚合state而非整网格。论文证据针对已监督场预测和工业几何，未给源位置似然；soft token不是已识别真实传播机制。

- 正式题录：https://proceedings.mlr.press/v267/luo25o.html
- 全文：https://arxiv.org/html/2502.02414v1
- 代码：https://github.com/thuml/Transolver_plus

**本领域裁决：**作为几何压缩强基线可行，但不优先用于本项目。其随机soft slicing不天然保留微弱源对证据，复杂度优化也不是当前小数据主瓶颈。若使用必须同预算与RIGNO/普通稀疏聚合比较，不作为新增第四创新。

## 3. 二次创新应该落在哪里

真正可主张的候选不在“我们使用3D几何算子”，而在：几何可迁移的合法history编码，经训练期3D教师提供任务条件信息，只保留能解释竞争源观测似然差的方向；部署时对未观测传播自由度边缘化，既不使用未来真风，也不人为制造源间差异。

几何算子的主要验收应是：相同观测权限与相同样本预算下，未见源/未见几何的源对证据误差减少；M1增益不能被普通条件生成器、标准knowledge distillation或相同几何编码轻易替代。最终主创新由根任务的M1推导决定，本文仅提供迁移层的可审查依据与边界。
