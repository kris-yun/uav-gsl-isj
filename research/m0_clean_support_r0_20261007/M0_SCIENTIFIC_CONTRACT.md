# M0 R0：干净支撑的 matched-error 机制箱合同

设计版本：`M0_R0_V1`。本轮为 **静态设计，0 次 GADEN、OpenFOAM、PMFS 运行**。40 行 runlist 仅供审查，全部 `launch_authorized=False`。冻结完成后停止；执行需要后续明确指令。

继承 `research/pro-handoff-20261007` 的 `4e7e1ce16f7c6db3c68214c984337375c8d09e26`，保持旧判定 **`W0C_STAGE0_NO_CLEAN_BASE_HOLD`** 及原门槛。W0-PRE/PRE2 仅为 *positive exploratory signal, but boundary-confounded*。旧 House 数据和 frozen runner 均不改动。

## 1. 问题、估计对象与结论边界

固定源、gas、几何、release、RNG、时钟和 source-blind route，比较两种 **全 simulation Free 区和固定 ROI 内都匹配 vector RMSE** 的风误差，是否产生稳定不同的前向羽流损伤和源后验损伤。

这是一个 prescribed-flow 机制筛查：一个无内部障碍的开放三维箱、一个解析 wind context、两个已知候选位置、四个配对 seed。它不能确认复杂湖岸、稀疏气象恢复、未知连续源空间或闭环 UAV/原生 PMFS 性能。四个 seed 在两个源之间复用，因此独立随机区组数仍为 **4**，不能写成 8 个独立环境。M0_PASS 仅允许把 surviving contrast 提交 FSR pilot；`PRIMARY_GO` 和最终湖岸确认仍需要 FSR。

令 `C[s,r,m]` 为源 s、seed r、wind m 的模拟浓度。每个测试 fold 的真实观测固定为：

`y[s,r] = route_sample(C[s,r,U0])`。

源反演使用错误 wind 的候选预测字典，而非把真实观测也替换为 `C[s,r,m]`。配对 plume/sensor 差异 `C[s,r,m]−C[s,r,U0]` 是前向损伤；固定 y 下的 posterior 变化是错误 transport evidence 造成的推断损伤。两者分别计算，不能互相代替。

## 2. Domain、ROI 和真正的 guard

| 对象 | x / m | y / m | z / m |
|---|---:|---:|---:|
| Simulation domain | −16 至 44 | −20 至 20 | −8 至 16 |
| Analysis ROI | −2 至 18 | −8 至 8 | 1 至 9 |
| 真正 outlet 的内侧平面 | −15.75 至 43.75 | −19.75 至 19.75 | −7.75 至 15.75 |

原生 cell size 0.25 m，240×160×96；六面一层 cell 是 `Outlet=2`，内部是 `Free=0`。无地板、天花板、建筑或湖岸；z 是相对垂向坐标，负值不代表地下。ROI 至有效 outlet 的最小净 guard 为 **6.75 m**。两个源均在上游 x=0、高度 z=5，y=−1/+1，最小 outlet clearance **10.75 m（上方）**。

静态尺寸只能证明几何 guard；尚未证明随机羽流被容纳。Native 使用循环 Gaussian 表，不能用 IID 随机游走假设给出已经通过的随机 containment 结论。

未来先资格审查 8 条 U0 baseline，两源各自 **4/4** 全通过：

- 20–120 s 的 51 个对齐 frame：六个 simulation 面内侧 **1 m** 带的 Gaussian mass fraction mean ≤0.05，q95 ≤0.10；q95 使用线性分位数。
- 0–140 s 的每一个 native saved record：每个 filament 的 3σ 支撑至任何有效 outlet 平面净距 ≥1 m；centroid clearance ≥1 m；source clearance ≥10 m。
- 全时段零 filament 删除、零位置/RNG 异常；逐 tick 计数或结合固定释放与 outlet 控制流的不变式证书证明，不能只检查保存时刻的 log。

六面 mass 带用 box Gaussian CDF 积分，三维并集不重复计角部；详见 domain JSON。未截断 Gaussian 尾部积分是保守的支撑风险诊断，不能称为实际流出质量。更强的 3σ 支撑门和零删除门同时强制。

记录 all-side centroid、源 clearance、total/ROI/outside-ROI mass、支撑净距和删除计数。ROI 出界是任务观测变化，simulation 出界会破坏因果资格。32 条干预也必须满足同一支撑门，否则 HOLD。

任一 baseline 不通过 -> `M0_BASE_SUPPORT_HOLD`，停止。不得选择有利 seed、改源、缩短窗口或扩域后自动重跑。新的 domain/build 需要单独审查和新冻结，旧证据保留。新箱的 20–120 s 窗口和物理 1 m 带在结果前定义，不用于修改旧 W0C 的窗口、3-bin 带和 5%/10% 门。

## 3. 平滑三维 base wind 与两组干预

`U0(x,y,z) = [0.08+0.04*tanh((z−5)/1.5), 0, 0.005] m/s`。

解析场 C∞、divergence=0，水平速度 0.04–0.12 m/s；任务高度 shear 为 0.02667 s⁻¹，非零 w=0.005 m/s。开放六面的净通量平衡。它是物理含义明确的 shear-advection 运动学场，没有求解 Navier–Stokes，也没有实测/CFD/turbulence/lakeshore 真实性主张。Native wind 为 cell-centre float32，故原生输运读取的是该解析场的离散近似。

只冻结以下两组；禁止增加 remove-w、wake、NN 等 family：

- **A_on / A_off**：相同 C∞ compact streamfunction 的 discrete curl，中心 y=0 / 5.5 m，相差恰好 22 个 cell；x/z 中心相同，幅度和含导数 halo 的支撑体积完全相同。是 corridor 循环/方向误差与离开 corridor 的相同误差。
- **B_shear / B_speed**：相同 z∈(2,8) 支撑；前者局部取消任务高度的 along-wind shear，后者加入普通正水平 speed bias，保留任务高度 shear。均不改变 w。不能称为“整个计算域所有 shear 都消除”。

所有公式、gain、native 字节预期 hash、物理门在 perturbation JSON。A mask 只用 ROI、解析流朝向和固定几何偏移，无 true source identity 或 plume；同一 mask 作用于两候选源。这是实验者给出的 **干预位置**，尚无估计 transport relevance 的算法贡献。

为验证 A 实际形成 on/off contrast，在 8 条 oracle baseline 上预先要求：每源每 seed 的 nominal on-box Gaussian mass overlap mean ≥0.30，off-box mean ≤0.01 且 q95 ≤0.05，另报 derivative halo overlap。失败 -> `PAIR_A_RELEVANCE_HOLD`，不移动 mask，也不继续 32 条干预。

| pair | arm | Free-domain RMSE / m·s⁻¹ | ROI RMSE / m·s⁻¹ |
|---|---|---:|---:|
| A | A_on | 0.0009048415322 | 0.0042028462775 |
| A | A_off | 0.0009048415322 | 0.0042028462775 |
| B | B_shear | 0.0074849027370 | 0.0128284769706 |
| B | B_speed | 0.0074849029041 | 0.0128284772569 |

不是只靠大 guard 稀释 global error：两个 audit volume 都要匹配。绝对差 ≤1e−7 m/s **且**相对差 ≤1e−4；分母 `max(E1,E2)`，两者必须非零。Pair A 和 B 彼此的误差大小不要求相等。当前表来自静态 float32 代数，B 最大差约 2.86e−10 m/s，不是 plume 实验结果。

Native field 还须全部 finite、u≥0.02、speed≤0.20 m/s、vector error≤0.0500001 m/s、max/RMS discrete divergence≤1e−6/1e−7 s⁻¹。所有 wind 覆盖完整 guard，无零 padding。实际 wind 的 native decoder readback、occupancy 语义和 runtime hash 门尚未执行。

## 4. Gas、随机配对、route 和运行计数

Native gas 12（carbonMonoxide，SG=0.967）仅为近空气密度 preset。Point source 固定释放 10 filaments/s；σ0=10 cm，growth γ=15 cm²/s，legacy noise=0.01，初始中心 10 ppm。原生 buoyancy、噪声和 σ Euler 公式全部保持。参数详见 source JSON，禁止结果后改 gas 或 release。

时钟 140 s，dt=0.1 s，保存请求 0.5 s；原生以 `currentTime > lastSaveTime + saveDelta` 保存，实际序列应记录而非假设 281 条。评分请求 t=20,22,…,120 s，选择内置时间不晚于请求的最近 frame，lag≤0.61 s。相同源/seed 的全部 arms 必须具有相同输出时间和 record index 序列。

四个 seeds `2026100701` 至 `2026100704`，每源、每 arm 相同；每 run 新进程、OMP 1 thread。Seed equality 不足以证明 CRN：PointSource.Emit 必须无 RNG/retry，release count、filament 顺序、σ age 序列相同，零异常/零 outlet 删除；在已审阅的 native 控制流下每个 live filament 每 tick 恰好三个 Gaussian draw。所有相关原生源码/二进制 hash 和 call-assignment 不变式在执行前及配对后复核。不能证明 -> `M0_RNG_HOLD`，不声称 causal pairing。

Route 函数不接收 candidate coordinates、true source、wind 或 plume，只使用 ROI 和固定 insets。ROI-only 7 行 lawnmower：x=2–14，y=−3 至 3，z=ROI 中点 5；90 m，总时长 100 s，51 个观测。每个 segment 起终速度为 0，内部转角停留 0.4 s，冻结 trapezoid/triangle profile，v≤1.2 m/s，a≤1 m/s²，0.25 m vehicle clearance。连续几何和有界速度/加速度已静态检查；不是 airframe/controller 验证，jerk/yaw 未建模。

观测是 `native SampleConcentration` 在连续坐标输出的 ppm，`preCalculateConcentrations=False`，不是 column footprint pixel。Hit threshold 0.1 ppm。Oracle preflight 每源需至少 3/4 有 ≥2 detectable sample；两种 inference family 各至少 3/4 正确且 p_true≥0.60。失败 -> `M0_OBSERVATION_HOLD`，不得改路线或 threshold。

运行数固定：**5 winds × 2 sources × 4 seeds = 40**。前 8 条 oracle baseline，后 32 条干预；同一预测库供两 inference 和 ensemble 使用，无额外 source sweep/MC。任何基础门失败都暂停，不自动花掉 32 条。40 为科学预算硬上限，失败基础设施尝试保留，不自动 retry/补 seed。R0 没有生成 wind、occupancy、launch 文件。

## 5. 三类 inference comparator 与无泄漏 LORO

每个测试 r，所有 wind、两个 candidate 都排除 seed r，只用另三个 seeds 建字典。避免模板直接包含当前 query realization。训练器输入仅有 candidate positions、wind ID、3 个训练浓度数组；真实 query 源标签仅交给独立 evaluator。

**HIT_FORWARD**：候选前向 Bernoulli likelihood。51 点 hit `h_i=1[C_i≥0.1 ppm]`；每个 wind/source 的训练 `p_i=(Σ_q h_i+0.5)/(3+1)`，采用 Jeffreys smoothing，冻结独立点 likelihood，均匀 source prior。它是 PMFS-compatible candidate-forward 小空间代理，不能报告成原生 PMFS 复现或 parity。

**LOG_GAUSSIAN**：simple Bayesian/source-term likelihood。`z_i=log1p(C_i / 1 ppm)`，用三个训练 seeds 计算均值和无偏方差（ddof=1），effective variance=`max(sample_var,0.25²)`，51 点 diagonal Gaussian log likelihood，均匀 source prior。Release 固定，不拟合未知 flux。

独立点假设是近似，四个 seed 无法支持 calibration/统计显著性主张；报告 posterior score，不声称 calibrated probability。

**WRONG_MODEL_BMA**：Many-Wrong-Models / transport-ensemble prior-art comparator。模型集合只含四个错误 winds，不含 U0；`p(s,m)=1/8`。每种 likelihood 分别计算 joint source/model evidence，用 logsumexp 排序并边缘化模型，得到 blended p(s|y)。权重不能用真实源、held-out 源标签或损伤分数调节。该 comparator 使用同一 40-run 库，无新 run，属于 generic Bayesian model averaging，不是新方法，也不声称是 Piro et al. 原始实现的精确复现。BMA 救回不改变单-model 的 primary gate。

## 6. 冻结损伤指标

每个源/seed/arm 分别计算，禁止只报 averaged template 的“识别率”：

1. **D_F**：ROI 2D column footprint 的 symmetric relative L2，`||F_m−F_0||₂ / [0.5(||F_m||₂+||F_0||₂)]`，合并 51×40×32 数组计算；两者都零时为零，baseline 总信号为零则 observation HOLD。
2. **D_Y**：`sqrt(mean((log1p(y_m)−log1p(y_0))²))`，51 点。
3. **D_B[f]**：`Brier(p_m,y_true)−Brier(p_U0,y_true)`，分别对应两种 likelihood。Scaled binary Brier=`0.5*Σ(p−onehot)²=(1−p_true)²`，小者更好。

Footprint 在原生 cell-centre grid 每两格采样（0.5 m；坐标偏移保留原生 cell centre），ROI 内 x/y 40×32，沿 **整个 simulation 的 Free 垂向 column** 离散积分 `Σ native_ppm*0.5 m`。是 ppm·m 的近似 column concentration，不是 box mass；真实边界门独立采用 Gaussian CDF/support/deletion。可用 3σ native cutoff 的局部 filament scatter 加速，必须保持原生单-filament函数/LOS/累加顺序，并在每 frame 与直接 native query 复核：25 个固定等距索引点及最多 25 个按有序索引取出的非零点，`abs_diff≤1e−5*(1+abs(native))`；无非零点也须记录。绝不能输出整批 full-3D time-volume bank 来扩大资源。

Secondary：每 fold/arm 的 posterior NLL、TV vs U0、posterior-mean position error、MAP error、rank、top1，arrival/detection times、centroid/spread、ROI mass、全 simulation 粗 column footprint。二候选 top2 恒等 1 无证据价值。|p0−p1|≤1e−12 为 tie：rank 1.5，top1 false，MAP 取 worst-case 2 m，不能让 source index tie-break 给出优势。NLL 对输出 p 以 floor 1e−15 仅防数值溢出，原始 posterior/log evidence 保留。Posterior-mean error 使用加权候选坐标欧氏距离。

## 7. PASS / HOLD / STOP：结果前冻结

Machine gate 为 `M0_GATE_CONTRACT.json`，执行逻辑参考 `gate_logic.py`。资格门优先，未知/失败不能算科学 STOP。所有参数、数据变换、所有 seeds 和 arms 的输出均报告，不事后移除 rescue run。

对每 pair 固定差 `arm1−arm2`。预先允许两种全局方向（+ 或 −）；一个 pair 必须选 **同一个方向** 同时覆盖两源、两 likelihood 和前向损伤，不能逐源/逐 baseline 换符号。每源同一 seed 必须同时达到：

- signed `ΔD_F≥0.10`；signed `ΔD_Y≥0.10` log1p units；
- 两 family 的 signed `ΔD_B≥0.10`；
- 被判为较差 arm 的两 family `D_B≥0.05`，确保是损伤差异而不只是一个 arm rescue。

上述交集在每源 **至少 3/4** seeds 满足，pair 才完整通过。不同 metrics 不允许各自挑三个 seeds。0.10 是预设 material-effect absolute margin：Brier 的量纲为 0–1；sensor margin 大致对应 1+ppm 尺度的 10% 差异；D_F 为 0–2 对称相对量纲。它们是有限预算筛查阈值，不是统计显著性或由旧结果拟合的效应阈值。单独登记零 harm、rescue、sign reversal。

| Verdict | 冻结含义与下一步 |
|---|---|
| `M0_PASS` | 两对均完整通过，或至少一对按上述规则在两源/两 family 完整复现。报告 TWO_PAIR 或 ONE_PAIR_REPLICATED tier。仅提交 surviving contrast 到 FSR pilot 设计；本轮不启动 FSR。 |
| `M0_PARTIAL_HOLD` | 未完整通过，但在某源/某 family 存在 ≥3/4 的 material forward→posterior 链，或两 source/baseline 方向分裂，或稳定 source damage 与 forward damage 链脱节。需审查，不能以 secondary 或 BMA rescue 升级。 |
| `M0_STOP` | 全 40 条有效、全部资格门通过，没有可复现 material source-posterior 差异。停止该冻结机制路线；不声称所有风况、复杂湖岸中的 transport structure 普遍无效。 |
| prerequisite HOLD | boundary、A relevance、native field readback、physical/RMSE、RNG、observation、sampling parity、provenance、resource 任一失败/未知，或 run 数不足。问题尚未被合法测试，禁止写科学 STOP。 |

一次 contrast 的双边选择只是预注册描述性重复门，无 p-value claim；完整 PASS 要求较 draft 更明确的同方向交集，在结果前收紧，未看任何 M0 plume。完整结果后自动停止，禁止补 seed、改窗口、找新 feature、跑公开数据或加 NN。当前只能给 `M0_R0_DESIGN_FROZEN`，**不是 M0_PASS**。

## 8. 冻结与 provenance

八份必需文件、machine inference/gate、static field audit、路线点、runlist、静态复核、native 源快照和 parent SHA256 一起冻结。`M0_R0_FREEZE.json` 记录各文件字节 hash，`M0_R0_FILES_SHA256.csv` 可独立复核；目录 `.gitattributes` 禁止文本换行转换导致 hash 变化。Builder 遇 freeze 文件拒绝覆盖。

旧 W0C GitHub 分支已包含原 archive，SHA256 `fcfb638f2c4a400b93f699249c95aa1ecc487042e3e8c49af0ce78e5feba712c`。新设计从最新 handoff 单独分支生成，不继承或改写旧 audit。未来实际 native input assets 及 decoder/runner需单独执行前 manifest，逐字节符合此合同；出现 formula-code contradiction 时先修设计、保留本冻结版并重新审查，不能悄悄换 runtime。
