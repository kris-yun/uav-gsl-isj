# V7 跨领域发现与迁移：方法证据、候选比较及原创边界

版本：2026-10-23。与当前 `source_localization_v7` 实现对应。本文是研究决策记录，不把文献的期刊层级、算法已能运行或条件性证明等同于真实气源定位性能。

## 1. 结论及本次发现解决的具体问题

**建议继续验证“源对覆盖的双点时序观测 + 源响应差决定的测量几何 + 不被旧高置信关闭的反证采样”。**研究对象是竞争源的可分性，不是更准确的浓度拟合、中心线跟随或更持久的历史记忆。

任务背景中，PMFS 的 B4 有错误高置信，浓度预测改善未带来真源排序改善，五位观测在一位容错下仍留下接近全部 16 个候选。由此要问：不同源在**可实际取得的观测**上是否产生可区分的联合分布；若没有差别，重新编码和更尖的后验不能补出信息。若有差别，策略是否真的取得相应观测，并在传感器、时间相关和成本限制下保留它。

当前实现的三部分是待验证的机制设计：

1. **M1：源对覆盖的镜像滤波通道。**在有限物理合法算子库中，按训练源对的联合分布分离选择少量通道，输出一次联合符号。
2. **M2：相对返回方向管与响应差双点编队。**方向记忆提出候选区域；竞争源的均值和响应梯度差决定双点基线；管内不可分时允许管外复测。
3. **M3：成本正确的完整候选分配与新后缀审计。**全部合法源保留，付费覆盖不随源后验消失，审计使用新观测，不把审计量回乘为另一份似然。

一次冻结的 OCB 静态 pilot 中，M1 静态联合直方图为 **31/40**，原始双点 joint Gaussian 为 **40/40**。随后完成的 156 episode L1 控制矩阵中，强联合基线、best-one、各主要消融与 full 的最终 Top-1 均饱和，**未证明 B′ 独立增益**。动态机制和原生闭环仍需合格连续数据。对应公式、证明和接口见 [THREE_INNOVATIONS_AND_THEORY.md](THREE_INNOVATIONS_AND_THEORY.md)。

## 2. 证据等级与独立性

阅读范围采用明确标签：

- **F：正式正文方法与实验已读。**不等于所有补充材料、原始数据和代码都已复现。
- **M：作者预印本的方法、关键公式或理论段已读。**正式出版信息另行核对，不能假定预印本与终稿逐字一致。
- **A：正式摘要、书目或原文图注已读。**不作全文公式核验的替代。
- **C：作者代码有实读。**另写明读到文件还是仅确认仓库入口；“有代码”不等于“运行复现”。

上述字母只在“阅读范围”语境表示证据等级；§5 的 A/B/C 是用户指定的研究领域标签，两者分开解释。

下表的 10 篇包括主候选、正式先验工作与迁移链证据，**并非 10 篇都具备相同正式资格或阅读深度**。方法来源只使用原论文、作者稿、作者代码和出版/作者机构元数据；未由综述替代原方法。

生物学独立阶段先冻结了 PNAS 双侧时序机制和线虫 staPAW；随后才收到 X1–X3。独立 PNAS 与 X1 重合是独立汇合，不能反写成事前指定。并行的雷达/统计方向独立冻结了 FUSION 2025 的共享位置、多参数化字典候选，以及成本主动检验方向；它们不是生物学代理在冻结前已知的候选。第二轮用 X2 替换 staPAW 的辅助主模块地位，第三/四轮结合成本 ASHT 与可预测似然审计完善 M3。原始记录见 [生物独立稿](../evidence/discovery/bio_independent.md)、[第二轮](../evidence/discovery/bio_round2.md)、[第四轮](../evidence/discovery/bio_round4_review.md) 与 [雷达独立稿](../evidence/discovery/radar_independent.md)。冻结稿中的 staPAW 混合公式漏写加号，已在第二轮登记勘误，未改写冻结文本。

## 3. 十篇方法级资格矩阵

| ID | 原论文及正式资格 | DOI / 版本 | 已读范围 | 代码、数据及复现状态 |
|---|---|---|---|---|
| D1 | Brudner 等，*Fly navigational responses exploit plume-specific odor motion and gradient cues*；PNAS 2026 | [10.1073/pnas.2608896123](https://doi.org/10.1073/pnas.2608896123) | F：作者保存的正式 PDF，方法及主要实验；C：复现说明；未取得完整 SI | [作者仓库](https://github.com/emonetlab/GradientMotionMultiplePlumes) 已读数据形状、预处理与符号说明；未训练/重跑 |
| D2 | Siliciano 等，*A vector-based strategy for olfactory navigation in Drosophila*；Nature 2026 | [10.1038/s41586-026-10827-7](https://doi.org/10.1038/s41586-026-10827-7) | F：曾成功读终稿方法与自然羽流部分；M：2025 作者稿；C：关键模拟及预处理文件 | [作者仓库](https://github.com/rutalaboratory/Edge-Tracking-Model)，所读提交 `225dc7d...`；数据 DOI `10.5281/zenodo.20751812` 仅核对入口。没有复现终稿全部自然羽流实验 |
| D3 | Chen、Pillow、Leifer，*State-switching navigation strategies in Caenorhabditis elegans are beneficial for chemotaxis*；PNAS 2026 | [10.1073/pnas.2519999123](https://doi.org/10.1073/pnas.2519999123)；[作者稿 v1](https://arxiv.org/html/2508.00191v1) | A：正式书目/摘要；M：作者稿结果、方法和公式；未取得终稿 PDF | [MATLAB 仓库](https://github.com/Kevin-Sean-Chen/Chemotaxis_function) 与数据 DOI `10.6084/m9.figshare.25996498` 已确认入口，未执行 |
| D4 | Vershinin、Cohen、Gurewitz，*Multi-Stage Active Sequential Hypothesis Testing with Clustered Hypotheses*；ISIT 2025 | [10.1109/ISIT63088.2025.11195532](https://doi.org/10.1109/ISIT63088.2025.11195532)；[作者稿](https://arxiv.org/html/2501.11459v1) | M：模型、分组/阶段机制及条件；正式会议信息经作者机构库核对；非终稿全公式审读 | 本轮未确认可直接运行的作者代码；不能写“无代码” |
| D5 | Hsu、Wang，*Tradeoffs Among Action Taking Policies Matter in Active Sequential Multi-Hypothesis Testing: The Optimal Error Exponent Region*；IEEE TIT 71(9):6546–6565，2025 | [10.1109/TIT.2025.3588527](https://doi.org/10.1109/TIT.2025.3588527)；[作者稿 v3](https://arxiv.org/html/2405.06554v3) | M：模型、可分性/有界 LLR 条件、探索策略和定理段；正式资格经作者机构记录核对 | 本轮未核实可执行作者实现；V7 不宣称复现其完整最优误差指数区域 |
| D6 | Vershinin、Cohen、Gurewitz，*Active Sequential Hypothesis Testing with Non-Homogeneous Costs*；2025 作者稿，ICASSP 2026 官方议程确认 | [作者稿 v3](https://arxiv.org/html/2509.11632v3)；[正式会议条目](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1) | M：模型、成本比值目标及 adapted Chernoff；正式 proceedings DOI 本轮未核实 | 未确认作者代码入口；不把官网议程当作代码复现 |
| D7 | Zecchin、Simeone、Ramdas，*Quantum Sequential Universal Hypothesis Testing*；2025 作者预印本 | [arXiv:2508.21594v1](https://arxiv.org/html/2508.21594v1)；本轮未核实正式期刊/会议 DOI | M：顺序 split likelihood、可预测替代分布、复合零假设及定理/数值实验设置；**不列作已核实正式高水平期刊论文** | 本轮未确认代码；量子数值实验不是气体实机验证 |
| D8 | Shigaki 等，*Insect-inspired adaptive behavioral compensation strategy against olfactory sensory deficiency for robotic odor source localization*；npj Robotics 4:12，2026 | [10.1038/s44182-026-00080-5](https://doi.org/10.1038/s44182-026-00080-5) | F：正式 12 页 PDF 方法、室内/室外实验及局限 | 数据 DOI `10.5281/zenodo.17596675`；原文代码声明为向作者索取；本轮未取回或运行 |
| D9 | Möderl、Westerkam、Venus、Leitinger，*A Block-Sparse Bayesian Learning Algorithm with Dictionary Parameter Estimation for Multi-Sensor Data Fusion*；FUSION 2025 | [10.23919/FUSION65864.2025.11124160](https://doi.org/10.23919/FUSION65864.2025.11124160)；[作者全文 v2](https://arxiv.org/html/2503.12913v2) | M：雷达独立审读覆盖信号模型、证据优化、参数更新、Algorithm 1 及单/多雷达实验；定稿再核对上述关键段。正式资格由作者软件存档的会议/DOI 记录交叉核对 | 定稿新确认 [TU Graz 公开 Python 存档](https://doi.org/10.3217/kcn0n-03509)，含 SBL、NOMP 和演示；已读目录/说明，未读源码或执行。保留独立稿当时“未找到代码”的历史状态 |
| D10 | Mordad 等，*Bio-Inspired Event-Based Visual Servoing for Ground Robots*；IEEE Control Systems Letters 10:889–894，2026 | [10.1109/LCSYS.2026.3703887](https://doi.org/10.1109/LCSYS.2026.3703887)；[作者稿](https://arxiv.org/html/2603.23672v1) | M：传感模型、主动控制及实验装置；A：正式元数据/图注；未逐项核对终稿全部公式 | [作者代码与实验入口](https://github.com/SiamiLab/BioInspiredEBVS) 已确认，未执行 |

“未确认”只描述此次核验范围，不表示作者没有提供某资源。

## 4. 输入—状态—算子—输出矩阵

以下是原论文机制的压缩记录。V7 的数学细节另见理论文档，不能把下列所有方法归入同一个“注意力”或“记忆”概念。

| ID | 原始输入与状态 | 方法级计算及输出 | 有效条件、实验或直接限制 |
|---|---|---|---|
| D1 | 双侧有限历史；滤波缓冲 | 两时间滤波器、ReLU、镜像相减形成侧别判定。诊断的延迟乘减与最小网络不是同一算子 | 原目标是中心线侧别；环境影响梯度/运动线索效用；固定线索平滑组合也能解释行为。动物尺度不能照搬 UAV |
| D2 | 运动方向、气味进入/退出事件；两方向记忆 | `m ← a m + b vhat`，返回/离开状态调节运动；退出有风门控 | 相对方向而非固定边界坐标。事件需足够持续，方向不相干会抵消；作者离线平滑不应当作实时输入 |
| D3 | 浓度历史、横向差、运动历史；两个持续状态 | 感觉历史核驱动状态转移 softmax；状态决定转向/微调混合分布 | 观察与光遗传扰动支持状态进入/退出；目标是趋化效率，不是离散候选源排名 |
| D4 | 已知的动作条件假设分布；阶段及候选簇 | 按分布参数分离选动作，阶段内重复测量并排除/合并接近假设 | 独立观测、已知分布和跨动作可分性是关键；不能直接给相关 plume 数据套有限样本结论 |
| D5 | 全部假设下的联合观测分布及资源约束；全对 LLR | 根据当前估计与探索策略选择动作，分析成对错误指数的权衡 | 原最优性为渐近结论，探索率设计与 V7 固定覆盖不同；不支持五步物理恢复保证 |
| D6 | 动作分布、成对 KL、不同正成本；当前引导假设 | 优化“期望信息/期望成本”；更正把资源比例当抽样频率的问题 | 分布已知、条件独立的设置。不是先逐动作做 `KL/c` 再把这些数直接当抽样概率 |
| D7 | 顺序量子测量结果；过去估计与复合零假设 | 替代密度在下一结果前确定，除以共享零假设参数的整段最大似然；阈值测试 | 方法提供经典 universal-inference 思路进入量子复合检验的实际应用；V7 仅借鉴统计结构，不引入量子硬件 |
| D8 | 双侧人工触角读数和转动情境；surge/zigzag/loop 等控制状态 | 触角接触位置及运动情境影响控制；检查嗅觉缺损补偿 | 有实际地面机器人；室外比较未形成完整算法×缺损因子设计；非多源候选分布判别 |
| D9 | 多雷达内部的相干向量响应；共享位置/稀疏支持、各站幅度、噪声参数 | 多字典边缘证据最大化，交替更新连续位置、共享精度和噪声；输出位置及幅度条件分布 | 雷达间可不相干，域内多维形状仍须存在。单雷达与 NOMP、不同检测阈值及多雷达比较；不能把稀疏精度归一化成源后验 |
| D10 | 异步事件流；结构化亮度与机器人运动 | 固定空间核的事件通量分离速度及位置×速度，主动小幅运动维持可观测性 | 1D 地面机器人和可控制视觉图样；不能直接假设自然气味场有同样解析可观测结构 |

## 5. A/B/C 迁移矩阵：什么已发生，什么仅为本项目设计

按用户约定，**A 是 PMFS/气源定位任务及原方法，B 是母算法的原领域，C 是第三领域**。例如 D1 的 B 是动物嗅觉，A 是候选气源判别；视觉到嗅觉的结构先例可以支撑迁移判断，但不是精确 2026 模块已经完成 B→C→A 的证据。经典计算家族的迁移也不等于精确新模块已经完成二次迁移。

为避免与实验命名混淆，本文的消融标签统一如下。**A′** 是在 A 上采用相同观测资源的强联合统计基线；**B 对照**是将母算法直接接到 A 的必要接口/尺度适配；**B′** 才是为 A 的具体故障增加的二次设计。这里 B 对照不意味着原动物尺度和实验参数原样照搬。

| 比较层 | 含义与本项目对应 | 资格边界 |
|---|---|---|
| A | native PMFS 的原方法/原问题 | 当前 L1 的 `A_adapted_variance` 只借其方差选点思想，不是 native PMFS 复现 |
| A′ | 同资源的完整 raw-joint 与联合信息选点；矩阵中 `Aprime_joint_eig` | 强基线必须保留；使用有限训练估计的联合模型，不等于理想 Bayes 上界 |
| B 对照 | M1 同 bank、同 TRAIN 选出的 best-one；M2 普通边界返回；M3 直接成本分配 | 其余模块固定的控制有助归因，但属于母结构适配，不能统称精确复现全部原论文 |
| B′ | 源对覆盖多滤波、响应差编队及管外复测、完整候选覆盖及新后缀挑战审计 | 尚未取得相对强 A′/公平 B 的独立物理收益 |

| 来源（B） | 迁入 A 的实际修改 | 已确认的 C 证据 | 缺口及取舍 |
|---|---|---|---|
| D1 | 侧别分类改成源条件联合符号分布；不同源对覆盖决定多通道选择；保留偶部强度 | 论文 ref 57 与兔视网膜 Barlow–Levick 延迟抑制作明确计算结构比较；嗅觉任务中实际训练/检验类似结构 | 仅能称跨模态结构复现/汇合，不能称精确 MNM 已在 UAV 应用。保留 M1 母结构 |
| D2 | 相对方向只约束动作候选；加入不确定管、响应差基线及管外复测 | 本轮没有找到其精确 2026 事件记忆模块的独立 C 实机迁移 | B′ 为新工程设计；记忆不是源证据。保留为 M2 辅助机制 |
| D3 | 退出依据由浓度变好改为完成候选验证/发现无信息 | D10 支持主动运动改变可观测性的家族原则，但不是 staPAW 规则迁移 | 不足以成为第二个主模块；降为有限状态控制参考 |
| D4 | 候选关系按动作可分性处理，避免全局最坏源对为零就停止 | 本轮未确认该版本独立 C 实机应用 | 启发全源对输出与显式挑战；当前 M3 **没有复现整套 ISIT 分簇算法** |
| D5–D6 | 完整合法源集、正确成本分配、对后验不敏感的付费覆盖 | 有理论及指定分布数值实验；本轮未确认气体或其他 C 实机迁移 | 采用可复核数学结构，不借其渐近结论宣称本项目有限步最优 |
| D7 | 对每个源建立新后缀审计，共享整段 nuisance；替代混合预测先冻结 | 经典复合检验/可预测似然结构进入量子假设检验，作者稿给出数值验证 | 这是统计构造的跨任务先例；不证明拟合气体通道正确。未核实正式 venue，不能冒充新顶刊母算法 |
| D8 | 作为机器人双侧嗅觉和故障恢复的直接 A 领域先例 | 原任务本身已是机器人嗅觉；不另包装为第三领域 C | 排除“首次双侧嗅觉/首次丢失恢复”说法，不采用其行为状态作为 M1 创新 |
| D9 | 多目标稀疏求解改为单源候选枚举；跨几何共享排放 nuisance，比较不能被幅度吸收的响应形状 | 本轮未确认该精确 FUSION 算子的 C 实迁移；母文列出的声学可扩展方向不能写成已完成实验 | 保留 nuisance/非比例形状诊断；当前不作为主模块。若所有源仅有尺度差，自由源强会消去可分性 |
| D10 | 仅借“通过实际运动获得原来缺失的观测”原则 | 生物感觉适应 → EJC 2025 主动感知理论 → 2026 地面机器人事件视觉闭环，有原论文与代码链 | 明确真实工程迁移，但属于计算家族；气体无可控亮度图样，不能直接移植其控制律 |

D10 上游方法为 Biswas、Sontag、Cowan 的 *An exact active sensing strategy for a class of bio-inspired systems*，EJC 2025，DOI [10.1016/j.ejcon.2025.101361](https://doi.org/10.1016/j.ejcon.2025.101361)，方法读取自 [作者原稿](https://arxiv.org/html/2411.06612v1)。其不可稳定到孤立点及低幅周期强迫构造是有明确条件的系统理论，不能泛化成“所有主动摆动都会改善气源定位”。

## 6. 独立候选与 X 的最终比较

| 阶段/候选 | 原判断 | 经方法与数据约束后的裁决 |
|---|---|---|
| 独立候选 1：D1 双侧时序 | 结构清楚，可解释；缺源排名与精确 C 迁移 | 与 X1 独立汇合。采用镜像整流算子族，但主 B′ 必须是源对覆盖，不是单一 side classifier |
| 独立候选 2：D3 staPAW | 持续探索与退出机制有因果证据 | 不再争第二项主贡献。没有证据表明学习另一状态网络解决当前源混淆 |
| 雷达独立候选：D9 共享位置、多参数字典 | 可将未知幅度与向量响应形状分开，直接形成源条件比较 | 保留其可辨识性检查；纯幅度差会被自由源强吸收，16 个互斥源也不需要多目标 SBL。当前不选作主创新 |
| 雷达独立候选：D5/D6 全对/成本主动检验 | 对应错误高置信后的动作分配与覆盖 | 与 X3 的阶段分簇方向比较后用于 M3；严格区分成本目标、持续覆盖和审计三个作用 |
| X1：D1 | 与独立候选一致 | 保留；禁止把经典 Reichardt 乘减叫 2026 新发明，禁止丢弃源判别可能需要的强度偶部 |
| X2：D2 | 精确事件记忆与运动方向可检查 | 作为 M2 更合适：相对方向能形成几何候选区，但需要响应差与管外复测才面向源判别 |
| X3：D4 | 动作条件簇适合解释部分候选不可分 | 保留思想；实现改由 D5/D6 的成本分配、完整源集与挑战覆盖，加 D7 相关的独立审计构造支撑 |

### 6.1 D9 的算子、气体改写及排除理由

原文式 (1)、(8) 的核心为

\[
y^{(l)}=\sum_k\psi^{(l)}(\theta_k)\alpha_k^{(l)}+v^{(l)},\qquad
\mathcal L=\sum_l\{-y^{(l)H}C_l^{-1}y^{(l)}-\log|C_l|\}+\mathrm{const},
\]
\[
C_l=\Psi^{(l)}(\Theta)\Gamma^{-1}\Psi^{(l)}(\Theta)^H+
(\lambda_l\Lambda_v^{(l)})^{-1}.
\]

位置 \(\Theta\) 和稀疏精度 \(\Gamma\) 跨站共享，幅度可按站变化。原贡献是多参数化字典融合及连续参数估计，不是 SBL 或幅度消去本身；\(\gamma_k\) 不是源概率。[作者稿 §II–IV](https://arxiv.org/html/2503.12913v2)

**以下是本项目的迁移设计推论，并非原文已有气体实验。**对于 16 个互斥单源，先精确枚举 \(s\)，采用

\[
y=F_s(\eta,\tau)a+H\beta+\epsilon,\qquad
F_s=R_\tau G_s(\eta)\Phi .
\]

\(\Phi a\) 为跨多个几何读数共享的低维排放过程，\(R_\tau\) 是按真实时间间隔计算的传感器响应，\(H\beta\) 为基线/漂移，\(\eta\) 为有限输运不确定性。对可独立校准的 nuisance 用整段一致的积分或条件递推；Gaussian 积分须保留 \(\log|\Sigma_s|\)。不能让每个标量读数各有一个自由排放率，也不能把未知传播路径的风当成已知局部真风。

**自由源强反例：**若 \(y=q h_s+\epsilon\)、\(h_j=c h_i\)，且 \(c>0\)、幅度域允许 \(q/c\)、噪声律相同，则 \((s=i,q)\) 与 \((s=j,q/c)\) 给出完全相同的观测分布。任意更多的同类读数不能打破这种混淆。固定某个源强先验可能产生证据差，但该差来自先验约束，不是新增的响应形状。每站一个标量且每站自由幅度时，问题更严重。

另一个反例是 \(c(x,t)=q(t-(x-s)/u)\) 的无耗散匀速对流：两站到达时差只依赖站间距与速度，源平移能被未知释放波形的平移吸收。因此相关峰本身不定位源。该候选只有在跨几何、经传感器卷积后仍有**不能被允许 nuisance 模仿的非比例响应形状**时值得实测；这正是保留诊断而暂不列为主创新的实质理由。完整推导与候选接口保留在 [雷达独立稿](../evidence/discovery/radar_independent.md)。

### 6.2 直接先例：Bio-Nav 与 Bee-Nav 不可混写

Xu 等的 **Bio-Nav** 为 *A Bumblebee-Inspired Spatial Memory Navigation Framework for Robotic Odor Source Localization*，Biomimetics 11(5):350，2026，DOI [10.3390/biomimetics11050350](https://doi.org/10.3390/biomimetics11050350)。本轮阅读等级 **A**：已读 [正式摘要、原文完整图注和元数据](https://pubmed.ncbi.nlm.nih.gov/42187417/)，未取得正文公式；MDPI 429、PMC 验证码及 EuropePMC 未返回正文，不称全文核验。已读部分确认 POMDP-HMM、STM 访问抑制、LTM 方向参考、fuzzy 融合、value iteration，以及无记忆/STM/双记忆消融；代码开放性未核实。它属于 A 的直接先例，足以要求避免“首次引入记忆”说法；不足以补写其算子或断言它缺少某项能力。

另一篇 **Bee-Nav** 为 Nature 2026 *Efficient robot navigation inspired by honeybee learning flights*，DOI [10.1038/s41586-026-10461-3](https://doi.org/10.1038/s41586-026-10461-3)，是视觉学习飞行/归巢；本轮只读官方摘要与 [作者 README](https://github.com/tudelft/Bee-Nav)，未读完整方法。它不能替代 Bio-Nav 的先验工作审查，也不能被写成未知气源定位验证。

## 7. 三个二次创新设计的身份证

### M1：源对覆盖的联合观测通道

母算子是双侧时间滤波、整流与镜像相减。当前实现是有限指数核族，不是 PNAS 自由训练系数的精确复现。二次设计根据每个动作下的源对联合分布分离选择通道，并保留一个偶部强度位和少量三值奇部通道，整块观测只产生一次联合符号。

具体改变的是**把有限通道资源放在剩余源对的区分需求上**。公平母算法基线必须是同 bank、同训练目标选出的 best-one；固定等数量通道和整块 raw-joint 对照也必须保留。若最佳单通道已完成全部覆盖，不能再以多通道本身宣称必要贡献。

M1 不改变数据处理不等式。同一原始窗口的确定性压缩不能增加理想信息；可能的收益是有限标定样本/通信预算下的可靠表示，或让后续策略取得更有价值的原始观测。这两个主张需分开实验。

### M2：返回方向管内的源响应差编队

母记忆为进入事件的方向累积。当前工程层从当前位置生成带不确定度的返回管，使用候选均值及响应梯度预测两个端点的偶/奇差，输出全源对几何分数。管内没有有用源对差异时，释放合法管外复测候选。

源坐标与机器人位置不变而响应梯度差旋转时，最佳基线应随之旋转；这是区分本机制与普通朝向/距离规则的可检验性质。反例是管内所有源预测相同：重捕获不能变成判别，必须换观测或承认当前不可辨识。

### M3：成本分配、持续覆盖与新证据审计

母方法提供全对比较、成本比值与可预测似然构造。二次设计将全部合法源保留为约束，避免旧错误后验关闭挑战；将正常搜索限制与全局合法覆盖分开；以一次新后缀审计检查候选排除，审计量不作为额外观测。

其理论是**安装通道正确时的条件结论**。已估计的直方图或 Gaussian 表不会因只用 TRAIN 拟合就自动满足真实 plume 的条件分布。新后缀不依赖旧先验能避免继承旧置信，但不能修复模型漏真源、未覆盖 nuisance 或传感器错误模型。

## 8. 数据与实际试验对主张的约束

冻结 OCB pilot 见 [STATIC_PILOT_RESULT.json](../results/ocb_static_v1/STATIC_PILOT_RESULT.json) 与同目录协议、探针冻结和代码快照：

| 比较 | 冻结结果 | 合法解释 |
|---|---:|---|
| mean-only Gaussian | 31/40 | 双点均值压缩在这些开发世界中不足 |
| raw-joint Gaussian | 40/40 | 已选双点保留了区分两源的联合信息 |
| 可逆 EO Gaussian | 40/40；后验最大差约 `4.51e-17` | 可逆换基保持信息，非新滤波收益 |
| M1 static joint histogram | 31/40 | 当前新静态编码未胜过 raw-joint；不作事后调参挽救 |

探针在 TRAIN 的 435 对中选择后冻结，为原编号 12/17，间距约 7.003 m。开发样本为四个独立世界各十张快照，不是 40 个独立 seed。约 50 s 帧间隔只支持同步静态空间比较；没有连续运动、局部风、真实传感器带宽或机载同步采样资格。两释放源同时改变 x/y/z，不能把它当作纯 XY 干预。当前结果不证明 16 候选、未见源、native PMFS 同场胜出或 UAV 闭环。

### 冻结 L1 控制矩阵：强基线饱和，无独立增益证据

[控制矩阵配置](../configs/control_matrix.yaml) 与 [CONTROL_MATRIX_RESULT.json](../results/control_matrix_v7_frozen/CONTROL_MATRIX_RESULT.json) 已完成：13 个变体 × 6 个指定源/机制/seed 世界 × 正常/错误先验 = 156 episodes；每轮为两个虚拟测量平台、300 s 模拟预算。六个世界是配置列出的六组组合，不是源×机制×seed 的完整交叉设计。

| 变体组 | 正常先验最终 Top-1 | 错误先验最终 Top-1 | 解释 |
|---|---:|---:|---|
| `A_adapted_variance` | 4/6 | 3/6 | 有限通道中的适配方差参考，不是 native PMFS 复现 |
| 其余 12 个变体：raw-joint EIG、best-one、fixed-two、raw-joint 强对照、M2/M3 消融及 full | 各 6/6 | 各 6/6 | 强基线已饱和，不能从最终正确率证明任何 B′ 独立收益 |

full 的六个错误先验 episodes 合计触发 7 次显式 audit challenger 反馈，说明该控制分支实际执行；`M3_no_audit_feedback` 同样最终 6/6，所以不能把触发次数当作该机制必要或优越的证据。

该后端的标定与评估共享解析构造；均匀随机相位会吸收源相关的共同相位移，因此不支持“新气味运动相位携带源信息”的验证。后验只使用 dwell 双点块，而 M2 还读取 travel 流；日志已分别计数，真实性能主张还需给强基线同等全流数据。此矩阵是 Level 1 集成/条件机制试验，不能升级为真实 plume、旋翼传感器或未见源位置验证。其他资源指标和运行细节以原始 JSON 与项目审计为准，本文不事后挑选次指标宣称胜出。

## 9. 下一轮判定门槛

先取得原生连续数据、真实时钟、两端点位置、传感器与管路延迟、同步误差、响应/恢复带宽及相关时间/长度，再冻结尺度。未经量测不能指定最佳毫秒、米数或“独立观测数”，不能插值稀疏快照制造气味运动。

应执行的最小比较是：同一整块双侧时序下的偶部、best-one 母结构、固定等数量通道、源对覆盖、多维 raw-joint；同一资源下的普通返回、无 memory 响应差规划、方向管及管外复测。主指标是真源排序、错误排除、相容集、校准和达到同一可靠程度的成本，羽流命中是辅助指标。

必须明确两类失败：单通道已经足够时不夸大覆盖；memory 仅提高重捕获而不改善相同资源的源判别时不强称第二贡献。所有合法动作都不能区分某些源/干扰组合时，应报告不可辨识，而不是继续增加后端网络或后验尖锐度。

## 10. 可长期复查的第一手来源

代码只读不等于运行；正式资格和阅读深度以矩阵记录为准。

- **D1：** [作者终稿 PDF](https://emonet.biology.yale.edu/assets/papers/2026/2026_brudner-et-al-PNAS-fly-navigational-responses-exploit-plume.pdf)、[作者代码](https://github.com/emonetlab/GradientMotionMultiplePlumes)。ref 57 为 Barlow–Levick，[DOI](https://doi.org/10.1113/jphysiol.1965.sp007638)，仅书目核对，未复读扫描全文。
- **D2：** [正式终稿 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558081)、[作者预印本](https://pmc.ncbi.nlm.nih.gov/articles/PMC11844514/)。终稿曾读取成功，后续重开受验证码阻挡。代码实读 `simulation_agent.py`、`simulation_envs.py`、`data_preprocess.py` 和 `sssm.py` 前 150 行：[固定提交](https://github.com/rutalaboratory/Edge-Tracking-Model/tree/225dc7ddbebb30d5f092f7144db02216fd1271b6)。代码不自动覆盖终稿全部自然羽流实验。
- **D3：** [正式 DOI](https://doi.org/10.1073/pnas.2519999123)、[作者稿](https://arxiv.org/html/2508.00191v1)、[代码入口](https://github.com/Kevin-Sean-Chen/Chemotaxis_function)。
- **D4：** [作者稿](https://arxiv.org/html/2501.11459v1)、[作者机构正式记录](https://cris.bgu.ac.il/en/publications/multi-stage-active-sequential-hypothesis-testing-with-clustered-h/)。
- **D5：** [作者稿](https://arxiv.org/html/2405.06554v3)、[作者机构期刊/DOI 元数据](https://scholars.lib.ntu.edu.tw/entities/publication/8b20458e-d251-4daa-b7d8-53db935563cd)。
- **D6：** [作者稿模型及算法](https://arxiv.org/html/2509.11632v3)、[官方会议条目](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1)。
- **D7：** [作者稿方法与定理](https://arxiv.org/html/2508.21594v1)；未核实正式发表资格。
- **D8：** [正式 PDF](https://www.nature.com/articles/s44182-026-00080-5.pdf)。
- **D9：** [FUSION 作者全文](https://arxiv.org/html/2503.12913v2)，覆盖模型、证据与参数更新、算法和实验；[TU Graz 作者软件存档](https://repository.tugraz.at/records/kcn0n-03509)，原文脚注 4 直接给出链接。此次新确认入口不回写冻结独立稿。
- **D10：** [作者稿](https://arxiv.org/html/2603.23672v1)、[正式元数据与图注](https://pubmed.ncbi.nlm.nih.gov/42577742/)、[上游 EJC 作者稿](https://arxiv.org/html/2411.06612v1)。
- **Bio-Nav 直接先例：** [正式期刊页](https://www.mdpi.com/2313-7673/11/5/350)、[PMC 正文入口](https://pmc.ncbi.nlm.nih.gov/articles/PMC13204904)。本轮仅成功读取正式摘要/原文图注，未取得正文，明确不称全文核验。

本文不以人为分数替代这些条件。当前交付可审计的机制、代码与证伪路径；是否形成有竞争力的气源定位贡献，取决于后续独立且同资源的物理实验。
