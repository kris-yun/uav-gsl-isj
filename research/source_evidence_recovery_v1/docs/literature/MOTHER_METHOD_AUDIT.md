# V6 母算法核验与可迁移算子

审查日期：2026-10-23 UTC。本文是独立文献审查笔记，不是这些论文的复现报告；未运行作者代码。主结论：接受“特权物理教师 → 可部署学生”的方向，但不能直接蒸馏单个真状态的动作、后验或浓度场。保持 V1 的 M1/M2/M3 主线。推荐的实际目标见 `PROJECTED_SOURCE_EVIDENCE_OPERATOR.md`。

## 1. 资格与访问记录

| 编号 | 正式题录与年份 | DOI / 官方标识 | 全文访问与代码事实 | 本项目角色 |
|---|---|---|---|---|
| P1 | He et al., **Bridging the Sim-to-Real Gap from the Information Bottleneck Perspective**, 第8届 CoRL **2024**，PMLR 270:473–495 **2025出版** | 出版 DOI 未在官方页提供；预印本 DOI `10.48550/arXiv.2305.18464` | 已读 arXiv v2 方法§4–5、实验§6、局限§7、实现附录；作者仓库 `tinnerhrhe/HIB_Policy` 仅 README/许可证，声明代码待发布 | 历史表征的基线；不能称 CoRL2025，也不能称已复现 |
| P2 | Feng et al., **Learning Task-Sufficient World Models by Synergizing Agentic Exploration and Structured Modeling**, **ICML2026**, PMLR306:30616–30641 | 出版 DOI 官方页未提供；arXiv `2607.04409` | 正式 PMLR 页存在；已读方法§3、实验§5、附录A/B/C；未核实到可下载实现 | 任务充分表征、成对轨迹采样、主动探测的直接母机制 |
| P3 | Hou et al., **Learning Neural Operators from Partial Observations via Latent Autoregressive Modeling**, **AAAI2026**, 40(1):390–398；2026-03-14 | **10.1609/aaai.v40i1.37001** | 已读正式9页PDF：§3方法、§4结果/消融；正文引用的附录不在此PDF，不宣称附录已读；`Kingyum-Hou/LANO` 实际包含 `src/` | 部分场补全基线/教师备选，不作为源判别创新的直接证据 |
| P4 | Cai et al., **Provable Partially Observable Reinforcement Learning with Privileged Information**, **NeurIPS2024** | **10.52202/079017-2038**；arXiv2412.00985 | 已读正式PDF Proposition3.1、Definition3.2、§4–6、Algorithms1/2部分；不宣称通读68页全部证明；未核实作者代码 | 特权蒸馏的正确性边界和 belief 加权原则 |
| P5 | Yamada et al., **TWIST: Teacher-Student World Model Distillation for Efficient Sim-to-Real Transfer**, **ICRA2024**, 9190–9196；预印本2023 | IEEE DOI检索到 **10.1109/ICRA57147.2024.10610450**，正式venue由作者/牛津页面核对；未直接读取IEEE落地页 | 已读全文§III–VI；作者项目页明确 `Code (Coming soon)` | 世界模型蒸馏及同动作想象 rollout 基线，不能算2025/26新母算法 |
| E1 | Gloeckler et al., **Compositional simulation-based inference for time series**, **ICLR2025** | arXiv DOI `10.48550/arXiv.2411.02728`，出版DOI未核实 | 已读v2 §3、§4、§5.2；官方 `mackelab/markovsbi` 含实现和notebooks | 时间分解推断的强基线与 Markov 假设排雷 |
| E2 | Kim et al., **Distilling Realizable Students from Unrealizable Teachers**, **IROS2025**, 8103–8110 | DOI索引 `10.1109/IROS60139.2025.11247406`；作者主页和IEEE目录核对venue，IEEE DOI落地页未读 | 已读预印本§III两个算法、§IV实验和局限；作者项目可访问，未见代码链接 | 可恢复探索训练的参考，非本轮主线替换 |
| E3 | Wehenkel et al., **Addressing Misspecification in Simulation-based Inference through Data-driven Calibration**, **ICML2025**, PMLR267:65949–65980 | arXiv DOI `10.48550/arXiv.2405.08719`；出版DOI官方页未提供 | 已读§2.3–3公式、§5.1消融、§6局限；未核实完整作者代码 | 真实域校准的比较基线；不是新M1或新M2的贡献 |

注意：出版 DOI、arXiv DOI 和“未提供/未查到”必须分栏，不补造 DOI。上述 P1/P5 的源码缺口是真实核查结果，不等于永久没有代码。

## 2. 方法级笔记（各篇只摘取与迁移直接相关的机制）

### P1 HIB：历史信息瓶颈

**原失败**：特权策略/普通历史模仿在动力学变化下退化。输入局地状态历史 (H_t) 和仅训练可见的特权参数 (S_t^p)。TCN 得到随机表示 (Z_t)，特权自编码器得到目标表示；两个投影头用余弦正样本对齐，目标头 EMA 更新，另加高斯瓶颈和任务损失。输出供控制器使用的历史表示。正文 Eq.(10) 是 (-I(Z;S^p)+\alpha I(H;Z))；Eq.(12) 是归一化向量的负余弦。消融比较无瓶颈、无RL、无投影头、使用负样本；实机为A1机器人。§7承认复杂高维特权模态困难。

**迁移判断**：作为“历史编码器+特权目标”的直接迁移基线合理。其任务目标是控制回报，未保证保留源似然比。不能把普通余弦对齐重新命名为源证据创新。额外数学审查：Eq.(7)中 `argmin TV = argmin KL` 并非由 Pinsker 不等式推出；在受限模型类中极小点可以不同。我们只可使用 TV 被 KL 上界控制的结论。

### P2 MIST-WM：任务门控与因子条件轨迹对

**原失败**：通用图像潜变量保留大量与控制无关因素。Dreamer潜变量经过可学习门控 (m\odot z)；Eq.(2)预测奖励，Eq.(3)最大化任务描述互信息并惩罚门控大小；Eq.(5)以“同一因子值、不同 rollout”为正样本，“不同因子值”为负样本做 InfoNCE，同时训练 probing skill。输出紧凑任务表示与探测技能。门控/MI/充分性/探索/课程均有消融。原文明确门控只是DBN充分状态的实践代理；实验只在仿真，静态不可干预因素、细小线索未可靠识别。

**迁移判断**：气源位置通常不能由无人机干预改变；可干预的是观测位置。应把“因子标签直接区分”改成**学生信息下投影后的源条件轨迹可分性**；不可分源对不得硬拉开。对同源独立羽流 realization 构造正对，对具有可分辨性证据的竞争源构造负对，才避免学到风场seed/几何编号。

### P3 LANO：按已知边界逐层传播部分观测

**原失败**：连续缺测区域造成输入输出位置不一致和监督空缺。输入坐标、历史场值及观测mask；Eq.(4) (S=\mathrm{softmax}(\mathrm{MLP}(Y)/\tau)\odot M, Z=S^TY/(\|S\|_1+\epsilon))；Eq.(5)用部分卷积更新注意力与mask，再以复用注意力解码。MPT额外遮蔽已观测输入但保留可用输出监督。输出下一时刻场。NS/反应扩散/ERA5实验；Table3删除边界先行和MPT明显退化。Theorem3.1是低秩积分算子表示，不是守恒定律或逆问题可辨识保证。

**迁移判断**：可作为部分风/浓度场补全基线；移动UAV轨迹极稀疏且非整齐栅格，需新离散算子。不能将其MSE收益推断为源定位收益。

### P4 特权POMDP：belief加权而非oracle动作复制

**原失败**：历史仍不能唯一确定隐状态，teacher在观测等价状态给出冲突动作。Proposition3.1构造即使无限数据、最优蒸馏仍次优的例子。确定性滤波条件是完整历史可唯一解码状态；一般情形先学习 (b(z|H))，再用 

\[
\overline Q(H,a)=\sum_z b(z|H)Q(z,H,a)
\]

更新actor。Theorem5.1控制值误差 (O(\epsilon+T^2\epsilon_{belief}))。有有限POMDP数值实验，不是气源实验。

**迁移判断**：支持先把教师预测投影到学生历史，再生成规划目标；不支持声称间歇气体满足确定性滤波。将低后验合法源删除也不能援引其低访问状态截断证明：两者的风险对象和前提不同。

### P5 TWIST：教师/学生同动作想象轨迹对齐

输入仿真状态和配对随机化图像；教师RSSM冻结后，学生按图像编码；Eq.(3)匹配确定状态、prior/posterior分布；Eq.(4)让两模型沿**同一动作序列**想象并匹配prior及确定状态。输出可替代教师潜变量的视觉学生模型。DMC与Panda推/提方块验证；删除想象蒸馏影响较大。

**迁移判断**：可以借同动作 rollout 配对避免动作混杂；不能复制老师看到真风/真源后的oracle轨迹。我们的新目标应是历史条件预测分布，允许同一历史对应多种物理状态。TWIST原始latent-MSE/KL须作为直接迁移基线。

### E1 Compositional SBI：单步分解不适用于原始气体观测

输入独立于待估参数的状态proposal及模拟器单步转移；训练local posterior-score，再组合成全序列posterior。Eq.(3)：

\[
\nabla_\theta\log p(\theta|x_{0:T})=\sum_{t=0}^{T-1}\nabla_\theta\log\widetilde p(\theta|x_t,x_{t+1})-(T-1)\nabla_\theta\log p(\theta).
\]

训练状态proposal需覆盖支持且独立于参数。§3.2.2警告加噪参数后的score不能直接相加；§5.2明确**HMM不在方法范围**。实验含生态、流行病、Kolmogorov流；proposal过窄/过宽都退化。

**迁移判断**：可用于完整物理教师transition建模，不能把局地浓度序列当可观测Markov状态后相乘。正好为我们使用过滤隐状态的联合观测生成器提供边界。

### E2 CritiQ/ReTRy：可恢复状态的数据课程

原问题是同观测不同隐状态给出不相容teacher动作。CritiQ只在缺恢复数据状态查询teacher；ReTRy从学生到达状态启动teacher恢复rollout，并把恢复状态加入下一轮reset集合。输出学生策略与扩充训练分布。三类机器人任务，实机抽屉搜索；CritiQ长时误差积累，ReTRy训练成本更高。原文Algorithm1的判别器阈值方向与Eq.(1)标签描述需实现前额外核对，不能盲抄。

**迁移判断**：可在离线仿真重启中加入“错误高置信后的恢复历史”；真机不可reset风场。不能把teacher真源动作投入部署规划。适合作训练集覆盖基线。

### E3 RoPE：仿真—真实观察的软耦合

输入少量真实参数标签、仿真样本和已有posterior网络；对齐任务统计后，以半平衡熵正则OT求耦合 (P\)，输出 

\[
\tilde p(\theta|x_o^i)=\sum_j(n_oP_{ij})\tilde p(\theta|x_s^j).
\]

正文Eq.(3)假设 (x_o\perp\theta|x_s)；§5.1有仅OT/仅微调消融，§6指出维度和校准域支持问题。熵过大会回退先验。六类实验含真实风洞。

**迁移判断**：可用于真实域对照和校准，前提是有独立真实源标签；不能用冻结测试源做校准。不能修复模拟器根本缺失的源条件依赖，不能承担M1主创新。

## 3. 对建议的裁决

1. **执行**：训练期允许物理特权，部署期显式限制输入；teacher目标先在合法历史信息下积分；可实现完整未来联合分布；M1接口保持V1。
2. **执行并改造**：用任务充分表示聚焦竞争源证据，同时保留几何、动作和机制解释；成对样本必须跨独立realization、来源可审计。
3. **保留为基线**：HIB正对齐、TWIST想象蒸馏、LANO场补全。直接搬到气源上不自动构成三项贡献。
4. **不直接执行**：teacher单点真风→student确定真风；把静态源当可干预latent；把原始浓度视为Markov；把题录出版年当会议年；将源码未发布写成可复现。
5. **本轮推荐**：源条件过滤后的“未来联合—历史边缘”双项证据微分算子，与竞争源路径积分监督。它与已有M1源差分主旨一致，补上V1欠缺的teacher信息集投影；M2/M3继续消费同一个归一化联合生成器。它仍是待验证候选，不能据文献声称≥10%定位提升。

## 4. 一手来源清单

- HIB正式题录：<https://proceedings.mlr.press/v270/he25a.html>
- HIB全文：<https://arxiv.org/html/2305.18464v2>
- HIB代码状态：<https://github.com/tinnerhrhe/HIB_Policy>
- MIST正式题录：<https://proceedings.mlr.press/v306/feng26aa.html>
- MIST全文：<https://arxiv.org/html/2607.04409v1>
- MIST项目：<https://sites.google.com/view/mist-wm/home>
- LANO正式题录/DOI：<https://ojs.aaai.org/index.php/AAAI/article/view/37001>
- LANO全文：<https://ojs.aaai.org/index.php/AAAI/article/view/37001/40963>
- LANO代码：<https://github.com/Kingyum-Hou/LANO>
- 特权POMDP：<https://proceedings.neurips.cc/paper_files/paper/2024/hash/74d188c51d97fcfbc0269f584d6a53b7-Abstract-Conference.html>
- 特权POMDP全文：<https://proceedings.neurips.cc/paper_files/paper/2024/file/74d188c51d97fcfbc0269f584d6a53b7-Paper-Conference.pdf>
- TWIST项目/代码状态：<https://twist-sim2real.github.io/>
- TWIST全文：<https://arxiv.org/html/2311.03622v1>
- TWIST大学正式存档：<https://ora.ox.ac.uk/objects/uuid%3A60cf65aa-acc3-4362-8edf-216dc22c32a4>
- Compositional SBI正式题录：<https://proceedings.iclr.cc/paper_files/paper/2025/hash/aa539a128dc8653408dab242f6042c84-Abstract-Conference.html>
- Compositional SBI全文：<https://arxiv.org/html/2411.02728v2>
- Compositional SBI源码：<https://github.com/mackelab/markovsbi/>
- CritiQ/ReTRy项目：<https://portal-cornell.github.io/CritiQ_ReTRy/>
- CritiQ/ReTRy全文：<https://arxiv.org/html/2505.09546v1>
- RoPE正式题录：<https://proceedings.mlr.press/v267/wehenkel25a.html>
- RoPE全文：<https://arxiv.org/html/2405.08719v2>
- RoPE机构确认：<https://machinelearning.apple.com/research/addressing-misspecification>

## 5. 可供主报告引用的检索编号

正式题录：HIB `turn221view0`；MIST `turn221view1`；LANO `turn221view2`；POMDP `turn222view0`；TWIST作者页 `turn243view1`；SBI `turn234search2`；RoPE `turn241view0`。方法全文：HIB `turn229view0`；MIST `turn228view1`；LANO `turn222view6`；POMDP `turn224view2`；TWIST `turn228view3`；SBI `turn238view0`；CritiQ `turn236view1`；RoPE `turn245view0`。根代理正式引用前应自行open对应源。
