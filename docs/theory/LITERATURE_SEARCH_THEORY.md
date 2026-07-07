# Literature Search for UAV Gas Source Localization Theory

检索日期：2026-07-04  
范围：2020-2026 年优先；少数主题若直接证据不足，仅在“启示”中引用经典或相邻理论。  
核心结论先行：未找到严格证明“同一传感器、同一采样预算下，事件/二值观测在信息增益上本质优于连续观测”的论文。按数据处理不等式，若二值事件只是连续读数的确定性或随机量化，原始连续读数不会更少信息。二值/事件驱动模型的可辩护优势主要来自成本归一化、低信噪比阈值检测、通信/能耗约束、时效性、异常鲁棒性、以及主动采样策略把观测集中到后验方差大的区域。

---

## 主题1：自纠正性质在主动推理/贝叶斯主动学习中的应用

### 主题描述

本主题关注“后验方差越大 → 采样信息增益越大 → 策略自动回到不确定区域并纠正后验偏差”的机制。直接命中“self-correcting + Bayesian + active inference”的 2020-2026 顶会文献较少；最贴近的是 Bayesian optimization/active learning 中显式学习超参数和主动推理中以 epistemic value 驱动探索的工作。

### Top-3 相关论文

1. **Carl Hvarfner, Erik Hellsten, Frank Hutter, Luigi Nardi. 2023. “Self-Correcting Bayesian Optimization through Bayesian Active Learning.” NeurIPS 2023.**  
   DOI: [10.52202/075280-3465](https://doi.org/10.52202/075280-3465); arXiv: [2304.11005](https://arxiv.org/abs/2304.11005)  
   关键发现：指出 GP-based BO 对核超参数高度敏感，并提出以 Bayesian active learning 显式优先学习超参数的 acquisition，使 BO 在超参数误设时具备 self-correcting 行为。  
   与 GSL 的关系：可作为“模型错配/先验偏差可被主动信息采样纠正”的直接论据，尤其适合支撑 UAV GSL 中对源位置、扩散尺度、风场扰动参数的联合后验校正。

2. **Yingke Li, Anjali Parashar, Enlu Zhou, Chuchu Fan. 2026. “Pragmatic Curiosity: A Unified Framework for Hybrid Learning and Optimization via Active Inference.” arXiv preprint.**  
   arXiv: [2602.06104](https://arxiv.org/abs/2602.06104)  
   关键发现：把 Bayesian optimization 与 Bayesian experimental design 统一到 active inference/expected free energy 框架，在目标优化和不确定性消减之间进行连续权衡。  
   与 GSL 的关系：可支撑“GSL 不是单纯 exploitation，而是 hybrid learning-and-localization”的问题定义；UAV 轨迹可解释为同时最小化定位损失和后验熵。

3. **Yingke Li, Anjali Parashar, Enlu Zhou, Chuchu Fan. 2026. “Curiosity is Knowledge: Self-Consistent Learning and No-Regret Optimization with Active Inference.” arXiv preprint.**  
   arXiv: [2602.06029](https://arxiv.org/abs/2602.06029)  
   关键发现：用 active inference 连接 curiosity、self-consistent learning 与 no-regret optimization，强调 epistemic drive 对长期性能的作用。  
   与 GSL 的关系：可用于论证 UAV 在 plume patchy/weak-signal 条件下需要保留探索项，否则会被早期假阳性或假阴性锁定到错误后验。

### 对我们论文的启示

- 引用方式：把 Hvarfner et al. 作为“Bayesian active learning 具有 self-correcting acquisition 机制”的核心文献；把 Li et al. 作为 active inference 与信息采样的现代框架。
- 理论补强：可定义信息增益项 `IG(x)=H[p(theta|D)]-E_y H[p(theta|D,y,x)]`，并证明在近似高斯后验下，候选点预测方差越大，观测对后验熵下降的上界/近似值越大。
- 对比边界：不要声称事件观测无条件优于连续观测；应声称“在能耗/通信/采样频率固定、低 SNR 且阈值事件触发可提高有效样本密度时，事件策略可获得更高单位成本信息增益”。

### ISJ 说服力

**8/10**。self-correcting 的顶会证据较强，但“事件驱动 vs 连续观测”的直接信息论证明仍是空白，需要我们自己给出 cost-normalized 或 weak-signal 条件下的定理。

---

## 主题2：Minimax 下界在主动学习/自适应采样中的应用

### 主题描述

本主题关注如何在自适应观测下使用 Fano/Assouad/Le Cam 技巧证明 minimax 下界。关键难点是观测分布依赖历史策略，因此 KL 或 mutual information 必须沿时间展开，并对所有自适应策略统一上界。

### Top-3 相关论文

1. **Fan Chen, Dylan J. Foster, Yanjun Han, Jian Qian, Alexander Rakhlin, Yunbei Xu. 2024. “Assouad, Fano, and Le Cam with Interaction: A Unifying Lower Bound Framework and Characterization for Bandit Learnability.” NeurIPS 2024.**  
   DOI: [10.52202/079017-2407](https://doi.org/10.52202/079017-2407); arXiv: [2410.05117](https://arxiv.org/abs/2410.05117)  
   关键发现：给出交互式决策中的 Assouad/Fano/Le Cam 统一框架，专门处理 bandit/RL 这类数据由算法交互采集的下界问题。  
   与 GSL 的关系：最适合借鉴为“自适应 UAV 路径也不能绕开某些信息瓶颈”的理论模板。

2. **Jayadev Acharya, Clément L. Canonne, Ziteng Sun, Himanshu Tyagi. 2022. “The Role of Interactivity in Structured Estimation.” COLT 2022 / arXiv.**  
   arXiv: [2203.06870](https://arxiv.org/abs/2203.06870)  
   关键发现：研究交互性在结构化估计中的样本复杂度作用，使用信息论方法刻画交互数据采集何时有帮助、何时帮助有限。  
   与 GSL 的关系：可用于区分“自适应路径规划”与“非自适应扫描”的理论差异，并说明交互性必须与结构假设匹配才产生收益。

3. **Raghav Bongole, Amirreza Zamani, Tobias J. Oechtering, Mikael Skoglund. 2026. “Minimax Quantile Lower Bounds for Interactive Statistical Decision Making with Privacy.” arXiv preprint.**  
   arXiv: [2606.23096](https://arxiv.org/abs/2606.23096)  
   关键发现：面向 interactive statistical decision making 给出 minimax quantile lower bounds；虽然主题含 privacy，但证明技巧仍是自适应交互观测下控制信息流。  
   与 GSL 的关系：可借鉴其“逐轮交互 + 风险分位数”视角，为 UAV GSL 的 high-probability 定位误差下界提供技术参考。

### 对我们论文的启示

- Fano 证明模板：构造一组难区分源位置集合 `{theta_1,...,theta_M}`；用链式法则把自适应观测 KL 写成 `sum_t E KL(P_{theta_i}(Y_t|H_{t-1},X_t), P_{theta_j}(Y_t|H_{t-1},X_t))`；再用传感器模型给出单步 KL 上界。
- 对比策略：若连续观测和二值事件观测使用同等“每步成本”，连续观测的下界不会更差；若二值事件允许更高频率或更大覆盖，则应以总通信/能量预算归一化后比较。
- 理论补强：建议在论文中给出一个 Fano-based theorem：在弱信号、有限飞行时间和传感器噪声下，任意自适应策略的源定位误差存在下界，且下界由累计可分辨 KL 控制。

### ISJ 说服力

**9/10**。Chen et al. 2024 是交互式下界的强支撑；若我们补上 GSL 专属 KL 计算，将显著增强理论严谨性。

---

## 主题3：相变在后验收缩中的应用

### 主题描述

本主题关注 posterior contraction rate 从快到慢的相变，尤其是在空间/图/流形参数估计中由平滑性、观测类型、维度或干预比例改变导致的速率变化。直接“指数速率 → 多项式速率”的空间 GSL 文献较少，但 Bayesian graph/manifold smoothing 和 causal posterior concentration 已提供可迁移论据。

### Top-3 相关论文

1. **Arkaprava Roy, Shubhashis Ghosal. 2022. “Optimal Bayesian Smoothing of Functional Observations over a Large Graph.” Journal of Multivariate Analysis.**  
   DOI: [10.1016/j.jmva.2021.104876](https://doi.org/10.1016/j.jmva.2021.104876); arXiv: [2104.10335](https://arxiv.org/abs/2104.10335)  
   关键发现：研究大图上函数观测的 Bayesian smoothing 和 posterior contraction，收缩速率由函数平滑性、图结构和样本规模共同决定。  
   与 GSL 的关系：可把 UAV 搜索区域离散成空间图，用图 Laplacian prior 表示 plume/source field 平滑性，并分析空间结构导致的速率变化。

2. **Paul Rosa, Slava Borovitskiy, Alexander Terenin, Judith Rousseau. 2023. “Posterior Contraction Rates for Matérn Gaussian Processes on Riemannian Manifolds.” NeurIPS 2023.**  
   DOI: [10.52202/075280-1477](https://doi.org/10.52202/075280-1477); arXiv: [2309.10918](https://arxiv.org/abs/2309.10918)  
   关键发现：给出 Riemannian manifold 上 Matérn GP prior 的 posterior contraction rates，说明几何结构和 prior smoothness 会直接影响非参数贝叶斯收缩。  
   与 GSL 的关系：适合支撑复杂地形/障碍物约束下的空间先验，不必把 plume field 简化为欧氏平面上的各向同性 GP。

3. **Valentinian Lungu, Anish Dhir, Mark van der Wilk, Ioannis Kontoyiannis. 2026. “The Relative Value of Interventional and Observational Samples in Bayesian Causal Linear Gaussian Models.” arXiv preprint.**  
   arXiv: [2603.26460](https://arxiv.org/abs/2603.26460)  
   关键发现：发现 posterior concentration 在观测样本和干预样本比例上存在相变；某些区域可出现指数型集中，而另一些区域退化为较慢的多项式型行为。  
   与 GSL 的关系：虽不是空间 GSL，但可作为“观测类型比例导致后验收缩速率相变”的最新贝叶斯证据；可类比为连续读数、二值事件、主动确认观测之间的比例相变。

### 对我们论文的启示

- 引用方式：Roy & Ghosal、Rosa et al. 用于空间/图/流形后验收缩；Lungu et al. 用于“观测机制改变会导致 posterior concentration phase transition”。
- 理论补强：可在 UAV GSL 中定义临界覆盖/事件率 `rho_c`：当有效命中事件或高 KL 观测比例超过 `rho_c`，后验源位置方差快速收缩；低于 `rho_c` 时仅多项式收缩或停滞。
- 对比边界：需要说明这是我们从相邻 Bayesian contraction 理论作出的迁移，而不是已有 GSL 文献已经证明的定理。

### ISJ 说服力

**7/10**。空间后验收缩文献扎实，但“指数到多项式相变 + UAV GSL”的直接证据不足；适合作为提出新理论的动机。

---

## 主题4：二值观测 vs 连续观测的信息论比较

### 主题描述

本主题关注 binary/event observation 和 continuous observation 的 Fisher information、CRB、KL 信息量比较。严格地说，在同一连续测量先生成、二值观测只是其量化版本时，连续观测按数据处理不等式不弱于二值观测；二值观测的优势通常来自低比特硬件、传输预算、采样频率、时延或阈值检测与弱信号匹配。

### Top-3 相关论文

1. **Petre Stoica, Xiaolei Shang, Yuanbo Cheng. 2022. “The Cramér-Rao Bound for Signal Parameter Estimation from Quantized Data.” IEEE Signal Processing Magazine.**  
   DOI: [10.1109/MSP.2021.3116532](https://doi.org/10.1109/MSP.2021.3116532); arXiv: [2209.13182](https://arxiv.org/abs/2209.13182)  
   关键发现：系统讨论量化数据下信号参数估计的 CRB，给出低比特/量化观测的信息损失与设计原则。  
   与 GSL 的关系：可作为二值事件传感器 Fisher information/CRB 分析的直接理论基础。

2. **Guoxin Zhang, Wei Yi, Michail Matthaiou, Pramod K. Varshney. 2024. “Direct Target Localization With Low-Bit Quantization in Wireless Sensor Networks.” IEEE Transactions on Signal Processing.**  
   DOI: [10.1109/TSP.2024.3411672](https://doi.org/10.1109/TSP.2024.3411672)  
   关键发现：研究无线传感器网络中低比特量化的直接目标定位，分析量化观测对定位性能的影响。  
   与 GSL 的关系：与 UAV GSL 的“有限通信 + 空间定位 + 低比特观测”高度同构，可借鉴其低比特定位误差界。

3. **Ahmed Arafa, Karim Banawan, Karim G. Seddik, H. Vincent Poor. 2021. “Sample, Quantize and Encode: Timely Estimation Over Noisy Channels.” IEEE Transactions on Communications.**  
   DOI: [10.1109/TCOMM.2021.3092413](https://doi.org/10.1109/TCOMM.2021.3092413); arXiv: [2007.10200](https://arxiv.org/abs/2007.10200)  
   关键发现：在 noisy channel 和时效性约束下联合考虑采样、量化和编码，说明低比特策略在时效/通信受限条件下可提升系统级估计性能。  
   与 GSL 的关系：支撑“事件观测不是点态信息更多，而是单位时间/单位通信成本更有效”的论证。

### 对我们论文的启示

- 可成立表述：在同等原始观测条件下，连续浓度读数信息不少于二值事件；但在低 SNR、漂移噪声强、通信/能耗受限时，阈值事件可通过更高频率、更低延迟和鲁棒似然获得更高单位成本信息增益。
- 弱信号条件：若连续读数的幅值估计被基线漂移和校准误差主导，而二值事件只需检测超过阈值的 plume hit，则二值模型可降低模型错配风险。
- 理论补强：建议写成 cost-normalized Fisher information 或 KL rate：`I_binary / cost_binary > I_continuous / cost_continuous`，避免违反数据处理不等式。

### ISJ 说服力

**8/10**。低比特信号处理和目标定位文献很强；但需要谨慎措辞，优势必须绑定成本、时效或鲁棒性条件。

---

## 主题5：UAV GSL 最新进展（2024-2026）

### 主题描述

本主题检索 UAV/robot gas source localization、odor source localization 的 2024-2026 最新论文，重点关注 IEEE RA-L、IEEE Sensors Journal、TRO/ISJ 相关方向。结果显示：最新工作多采用连续气体浓度、信息论搜索、深度强化学习、多机器人协作或生物混合传感；直接采用“二值事件模型”作为核心理论模型的 2024-2026 顶刊论文很少。

### Top-3 相关论文

1. **Seunghwan Kim, Jaemin Seo, Hongro Jang, Changseung Kim, Murim Kim, Juhyun Pyo, Hyondong Oh. 2025. “Gas Source Localization in Unknown Indoor Environments Using Dual-Mode Information-Theoretic Search.” IEEE Robotics and Automation Letters.**  
   DOI: [10.1109/LRA.2024.3511375](https://doi.org/10.1109/LRA.2024.3511375)  
   关键发现：提出 dual-mode information-theoretic search，在未知室内环境中进行 GSL，强调信息论策略和模式切换。  
   与 GSL 的关系：RA-L 高相关基线；可与我们的事件驱动 Bayesian/Fano 理论形成直接对比。

2. **Chihiro Fukui, Tomoya Uchida, Sakito Koizumi, Yuta Murayama, Hao Liu, Toshiyuki Nakata, et al. 2025. “Advanced Bio-Hybrid Drone for Superior Odor-Source Localization: High-Precision and Extended-Range Detection Capabilities.” npj Robotics.**  
   DOI: [10.1038/s44182-025-00020-9](https://doi.org/10.1038/s44182-025-00020-9)  
   关键发现：展示 bio-hybrid drone 的高精度、远距离 odor-source localization 能力，强调硬件传感能力对无人机嗅觉定位的决定性作用。  
   与 GSL 的关系：可用于最新 UAV odor source localization 背景，说明硬件进展之外仍需要强理论路径规划和不确定性控制。

3. **Meh Jabeen, Qing-Hao Meng, Hui-Rang Hou, Hong-Yue Li. 2024. “Odor Source Localization in Outdoor Building Environments through Distributed Cooperative Control of a Fleet of UAVs.” Expert Systems with Applications.**  
   DOI: [10.1016/j.eswa.2024.123332](https://doi.org/10.1016/j.eswa.2024.123332)  
   关键发现：研究户外建筑环境中 UAV fleet 的分布式协同 odor source localization，突出多 UAV 协作和复杂环境适应。  
   与 GSL 的关系：可作为多 UAV/户外复杂环境最新对比；我们若是单 UAV，可强调理论可扩展到多智能体信息增益分配。

### 额外高相关文献

- **Hui Li, Jie Yuan, Hao Yuan. 2024. “An Active Olfaction Approach Using Deep Reinforcement Learning for Indoor Attenuation Odor Source Localization.” IEEE Sensors Journal.** DOI: [10.1109/JSEN.2024.3373610](https://doi.org/10.1109/JSEN.2024.3373610)。适合作为 IEEE Sensors Journal 最新 DRL-GSL 对比。
- **Yuhan Cheng et al. 2026. “SniffySquad: Patchiness-Aware Gas Source Localization with Multi-Robot Collaboration.” ACM Transactions on Sensor Networks.** DOI: [10.1145/3786599](https://doi.org/10.1145/3786599); arXiv: [2411.06121](https://arxiv.org/abs/2411.06121)。适合支撑 patchy plume 与多机器人协作。

### 对我们论文的启示

- 引用方式：Kim et al. 作为信息论 GSL 直接对比；Fukui et al. 作为 UAV odor localization 最新硬件进展；Jabeen et al. 作为多 UAV 户外协作对比；Li et al. 作为 IEEE Sensors Journal DRL baseline。
- 二值事件模型空白：最新 GSL 文献普遍没有把 binary event observation 与 continuous observation 做严格信息论比较，这是我们论文的潜在创新点。
- 对比实验建议：至少加入 continuous concentration GP/Bayesian update、thresholded event update、DRL active olfaction、information-theoretic search 四类 baseline。

### ISJ 说服力

**9/10**。最新应用文献支撑充足；若理论部分能解释二值事件模型为何在弱信号和成本约束下有效，会明显区别于现有 GSL 工作。

---

## 主题6：Conformal Prediction / e-process 在机器人中的应用

### 主题描述

本主题关注 conformal prediction、runtime risk control、anytime-valid/e-process 在机器人、UAV 或停止规则中的应用。结论：机器人领域已有 conformal prediction 用于安全规划和不确定性规划；e-process/anytime-valid RCPS 在 NeurIPS 2024 已成熟，但直接落到机器人/UAV stopping 的论文仍较少，是可创新结合点。

### Top-3 相关论文

1. **Jiankai Sun, Yiqi Jiang, Jianing Qiu, Parth Nobel, Mykel J. Kochenderfer, Mac Schwager. 2023. “Conformal Prediction for Uncertainty-Aware Planning with Diffusion Dynamics Model.” NeurIPS 2023.**  
   DOI: [10.52202/075280-3521](https://doi.org/10.52202/075280-3521)  
   关键发现：将 conformal prediction 用于 diffusion dynamics model 的 uncertainty-aware planning，为机器人规划提供分布无关的不确定性校准。  
   与 GSL 的关系：可用于说明 CP 已进入机器人规划顶会；我们的 stopping/localization confidence 可采用类似校准思想。

2. **Lars Lindemann, Matthew Cleaveland, Gihyun Shim, George J. Pappas. 2023. “Safe Planning in Dynamic Environments using Conformal Prediction.” IEEE Robotics and Automation Letters.**  
   DOI: [10.1109/LRA.2023.3292071](https://doi.org/10.1109/LRA.2023.3292071); arXiv: [2210.10254](https://arxiv.org/abs/2210.10254)  
   关键发现：把 conformal prediction 用于动态环境安全规划，提供碰撞/风险相关的统计保证。  
   与 GSL 的关系：可支撑“机器人系统中可接受分布无关统计保证”的审稿人说服点。

3. **Ziyu Xu, Nikos Karampatziakis, Paul Mineiro. 2024. “Active, Anytime-Valid Risk Controlling Prediction Sets.” NeurIPS 2024.**  
   DOI: [10.52202/079017-1920](https://doi.org/10.52202/079017-1920); arXiv: [2406.10490](https://arxiv.org/abs/2406.10490)  
   关键发现：将 risk-controlling prediction sets 扩展到 sequential/adaptive 数据收集，使用 wealth/e-process 思想获得 anytime-valid 风险保证。  
   与 GSL 的关系：虽然不是机器人论文，但最适合为 UAV GSL 的 anytime stopping rule 提供理论基础：飞行过程中任意时刻停止都保持置信有效。

### 额外高相关文献

- **Yiqi Zhao, Bardh Hoxha, Georgios Fainekos, Jyotirmoy V. Deshmukh, Lars Lindemann. 2024. “Robust Conformal Prediction for STL Runtime Verification under Distribution Shift.” ICCPS 2024.** DOI: [10.1109/ICCPS61052.2024.00022](https://doi.org/10.1109/ICCPS61052.2024.00022); arXiv: [2311.09482](https://arxiv.org/abs/2311.09482)。可作为 CPS/runtime verification 场景的 conformal 支撑。

### 对我们论文的启示

- 引用方式：Sun et al. 和 Lindemann et al. 证明 CP 已被机器人顶会/RA-L 接受；Xu et al. 证明 adaptive/anytime-valid 风险控制可在序贯采样中成立。
- 理论补强：可设计 e-process stopping：当源位置 credible set 半径、误定位风险或 posterior false localization risk 的 e-value 通过阈值时停止，并保证任意停止时间下错误率受控。
- 创新定位：目前机器人 GSL 中少见 “Bayesian posterior + conformal/e-process anytime stopping” 组合，可作为 ISJ 理论亮点。

### ISJ 说服力

**8/10**。CP 机器人证据强，e-process 机器人直接证据弱；把 Xu et al. 的 anytime-valid 框架迁移到 UAV GSL stopping 是合理且有新意的。

---

## 总体建议：如何把文献转化为论文理论支撑

1. **避免绝对化命题**：不要写“二值观测比连续观测信息更多”。建议写“在成本归一化、低 SNR、事件稀疏和通信受限条件下，事件驱动观测可获得更高单位资源信息增益”。
2. **主理论链条**：Bayesian active learning 的 self-correction → interactive Fano lower bound → posterior contraction phase transition → low-bit/event observation cost-normalized information → UAV GSL empirical gap → conformal/e-process anytime stopping。
3. **建议新增定理**：
   - 定理 A：弱信号阈值事件模型下的单步 Fisher information/KL rate。
   - 定理 B：自适应 UAV 采样的 Fano minimax 下界。
   - 定理 C：当有效事件率超过临界值时 posterior contraction 进入快速收缩区；低于临界值时为慢速收缩。
   - 定理 D：基于 e-process 的任意时刻停止规则控制误定位风险。
4. **最适合 ISJ 的卖点**：不是“事件观测天然更优”，而是“事件触发 + Bayesian self-correction + anytime-valid stopping”构成一个资源受限 UAV GSL 的完整统计决策框架。

