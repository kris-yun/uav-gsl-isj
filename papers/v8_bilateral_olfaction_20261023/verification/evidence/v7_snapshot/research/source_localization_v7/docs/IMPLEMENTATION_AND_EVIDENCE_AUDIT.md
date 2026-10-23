# V7 实现与证据审计

日期：2026-10-23。交付语义：三个可计算算法候选、统一概率定位闭环、可执行科研原型和冻结验证合同。没有将候选设计写成已建立的三项物理性能成果。

## 1. 完成状态

| 项目 | 实际产物与计算 | 已运行范围 | 状态 |
|---|---|---|---|
| M1 镜像通道与源对覆盖 | 因果物理时钟滤波、ReLU 镜像相减、共同强度保留、稳健源对 JS 覆盖、单个联合符号及 `[A,S,R,O]` 通道 | 数学测试、冻结静态 pilot、156 episode 控制矩阵 | IMPLEMENTED；物理独立增益未证 |
| M2 返回方向与判别几何 | 因果事件记忆、方向不确定管、双点均值/梯度/协方差评分、管外复测 | 21 项专用测试；控制闭环和消融；TRAIN-only RBF 接口构造测试 | IMPLEMENTED；原生几何/带宽资格 BLOCKED |
| M3 全候选反证审计 | 成本 LP、全源对付费覆盖、共享 nuisance 的新后缀审计、可恢复列表到下一动作反馈 | 18 项专用测试；控制矩阵，错误先验 full 共 7 次挑战触发 | IMPLEMENTED；条件风险性质已推导，原生风险与独立收益未证 |
| 源概率图与账本 | 联合源/机制更新；每原始块只更新一次；同 `(x,y)` 候选质量相加，保留候选支撑，不替代三维 occupancy 审查 | 去重/时间重叠/二维质量测试及完整循环 | IMPLEMENTED |
| 原生数据导入 | CSV/NPZ、原 hash、真实时钟、资格/单位/源/世界/动作合同、TRAIN/DEV/final 隔离 | 八个真实 OCB 世界静态读入；构造合格 manifest 标定与回放 | INPUT PATH RUN；动态资格 BLOCKED |
| 进程主动桥 | 独立 JSONL executor，过去观测返回、动作/成本/时钟检查，M1/M2/M3 和地图输出 | 最终版本 6 步、57 秒解析后端 | BRIDGE RUN；不是 ROS/GADEN |
| PMFS 对照 | 官方提交的 map 相容评分与方差选点算子移植 | 源码审查、构造算子检查；原 B4 证据复核 | OPERATOR ONLY；完整 native PMFS-1U/2U 未跑 |
| PPTX | 用户原图原生对象复用，三页总览/闭环/公式 | 实际导入、渲染、结构与字体检查 | DELIVERED EDITABLE |
| 科学收益 | 固定资源、强基线、分世界结果与负结论 | 真实静态及解析矩阵 | 未达到 L2–L4；不声称 ≥10% 定位提升 |

## 2. 软件范围与不是接口空壳的证据

主要计算位于：

- `src/gsl_discrimination/m1_opponent/`：算子、标定、原始窗口 VQ 强对照、模型持久化。
- `src/gsl_discrimination/m2_boundary/`：记忆、几何、TRAIN RBF 适配。
- `src/gsl_discrimination/m3_audit/`：成本规划、共享机制审计、列表状态与理论。
- `src/gsl_discrimination/channel.py`、`ledger.py`：源/机制后验和唯一账本。
- `src/gsl_discrimination/navigation/`：合法路径/编队、进入事件、真实进程桥。
- `src/gsl_discrimination/evaluation/`：资格化块标定/回放、PMFS 算子回放、地图、指标、静态 pilot、完整矩阵。
- `src/gsl_discrimination/engine.py` 与 `cli.py`：实际在线循环和命令，不是只有函数签名。

`native/gaden_executor/` 与既有归档提取器明确尚未实现，交由本地 Codex 按 [原生合同](NATIVE_INTEGRATION_CONTRACT.md) 接入。代码不会调用一个空实现并返回假成功。

## 3. 实际测试收据

最终 `scripts/run_tests.py` 运行结果：**71 passed in 2.24 s**，退出码 0。包括 M1 9、M2 21、M3 18、数据资格 8、跨模块集成 15 项。

收据：[`TEST_RECEIPT.json`](../results/final_tests/TEST_RECEIPT.json)、[`pytest.log`](../results/final_tests/pytest.log)、[`junit.xml`](../results/final_tests/junit.xml)。收据保存实际 Python、依赖版本、测试/源码 SHA。测试集合覆盖实质错误风险：源对覆盖不是凭空信息增益、同块不重复计数、共享 nuisance 不逐帧重抽、时钟/滞后/风/空间门、成本 LP、反证列表、未授权 final 不读、单位/传感器错位、跨世界混用、完整消息超时等。

RBF 额外集成检查：三个非共线中心、两个源、18 个构造 TRAIN 块拟合成功，梯度源/空间轴和方向正确、协方差正定；sealed final 未打开；被重标的 manifest 在任何观测读取前拒绝。它证明软件行为，不证明真实梯度准确。

终审另保留三项修复前反例和修复后收据：[FINAL_THEORY_IMPLEMENTATION_REVIEW.md](FINAL_THEORY_IMPLEMENTATION_REVIEW.md)、`results/final_review/FINAL_REVIEW_RECEIPT.json`。修复包括：episode 固定源/机制/realization；ppm/ppb 和传感器顺序冻结；原生编队协方差取冻结 TRAIN 文件。审计代理没有把这些修复写成新的创新点。

最终进程桥：[`results/bridge_final/BRIDGE_RESULT.json`](../results/bridge_final/BRIDGE_RESULT.json)，6 步、57.0 秒，`CONTROLLED_LEVEL1`。实际主进程启动独立后端、请求动作、接收物理时间块并更新；后端拥有真源，策略接口没有真源标签。原生 GADEN/ROS 与真实 UAV 认证未完成。

## 4. 全矩阵结果与解释

[`configs/control_matrix.yaml`](../configs/control_matrix.yaml) 冻结 13 变体 × 6 指定 source/mechanism/seed 组合 × 正常/错误先验 = **156 episode**，两虚拟平台，每轮 300 秒预算；不是六源×三机制×多 seed 全交叉实验。配置 SHA256 为 `25d5d047a238c3c846179c3098e2f848ce5fd0d8df28b67cba37082d5053d303`。

[`CONTROL_MATRIX_RESULT.json`](../results/control_matrix_v7_frozen/CONTROL_MATRIX_RESULT.json) 与 `per_world.csv` 保存汇总和逐世界结果。episode 原始块、动作和成本完整保留在 ZIP。执行矩阵墙钟约 101.84 秒，不含此前模型标定；不能写成真实飞行时长。

| 代表方法 | 正常先验 Top-1 | 错误先验 Top-1 | 含义 |
|---|---:|---:|---|
| adapted variance | 4/6 | 3/6 | 仅迁移 PMFS 方差思想的 L1 对照，不是官方 PMFS |
| raw-joint + EIG | 6/6 | 6/6 | 强结构适配已解决本构造任务 |
| best-one / fixed-two / raw-joint 强表征 | 均 6/6 | 均 6/6 | 没有体现源对覆盖 B′ 的独立收益 |
| M2 独立消融、M3 EIG/成本/无覆盖/无反馈 | 均 6/6 | 均 6/6 | 当前任务最终 Top-1 饱和，不能支持必要性 |
| full | 6/6 | 6/6 | 闭环完整运行；错误先验共 7 次审计挑战反馈，不等于 7 次独立恢复成功 |

局限：解析校准和测试共享生成族；均匀随机相位能吸收所构造的源相位平移，因此该相位不能证明源判别；模型候选有限且已标定；后验只用 dwell，M2 另读 travel 事件；未测真实传感器下洗、湖岸流体或 native PMFS。保持这些限制，不能换一个叙述就升级为物理成果。

矩阵完成后只修接口资格/进程守卫和补导出，不调参追逐已见成绩。控制结果对应冻结配置与当时执行文件；最终测试收据记录最终修复源码。复现请使用新目录按同配置运行，不能覆写本次负结果。

## 5. 真实 House/OCB 联通结果

确实读取固定 pin 的八个开放世界，cube `(10,87,114)`、pool `(10,30)`；真实时间约 50.30–499.82 秒，相邻约 50 秒。已验证 2×2 空间池化和原始值，导出/重读 CSV/NPZ 位级相同；八世界×十帧×两固定探针共 160 标量读数。原始数据不随 ZIP 重复分发，提供精确 fetch manifest 和哈希收据。

冻结静态 pilot 每源两 TRAIN、两 DEV；只用 TRAIN 从 435 个 pair 选出探针 12/17，再评估四个 DEV 世界的 40 个相关快照。两点间距约 7 米，尚不是已验证的 UAV 编队尺度。

| 观测模型 | Top-1 | 平均 MAP 误差 | 结论 |
|---|---:|---:|---|
| mean-only Gaussian | 31/40 | 1.092177 m | 静态平均丢失部分空间联合信息 |
| raw-joint Gaussian | 40/40 | 0 m | 当前强对照；小样本尖后验不表示校准已证 |
| 可逆 even/odd Gaussian | 40/40 | 0 m | 与 raw-joint 后验最大差约 `4.51e-17`，坐标变换不创造信息 |
| M1 静态联合直方图 | 31/40 | 1.092177 m | **未胜出**；不能把动态设计的希望记作已取得收益 |

收据 [`STATIC_PILOT_RESULT.json`](../results/ocb_static_v1/STATIC_PILOT_RESULT.json)，当时代码和 SHA 在同目录 `code_at_run/`。旧每单元平滑仅为冻结复现，新默认固定总平滑质量不被用来回写旧成绩。

当前占据原字节、源出生邻域、局地风向量、连续原生窗、传感器带宽与编队资格仍不完整，故此 pilot 是真实数据路径与静态开发，不是完整 Level 2。House02 缺合格时间/局地风的记录只能静态用；S2 DAY/NIGHT 单源短窗口仅接口用；H03/confirmation 数值未开放。

## 6. 数学完成与未完成

已给出并交叉审核的条件结论：

1. 可逆 even/odd 不增加信息；确定性编码服从数据处理不等式。M1 只可能在受限表示/标定预算下更有效，或通过 M2/M3 取得新的物理观测。
2. 保留已有联合符号并增加观测坐标时，真实源对 JS 不降；经验估计/贪心选择不自动继承总体增益，也无一般次模最优保证。固定总 Dirichlet 避免特征多即凭平滑质量取胜。
3. M2 的一阶双点响应差与余项条件、最优方向非零梯度条件成立；梯度差为零时方向全部并列。真实流场非光滑/协方差失配会破坏局部评分。
4. 非等成本信息率 LP 与动作概率的换算正确；资源份额不能直接当动作频率。
5. 若完整共享 nuisance 观测族覆盖真实过程，且备择预测在观测前冻结，新后缀审计受真实参数似然比超鞅支配，给出相应 anytime 风险界。经验通道和未知真实 plume 不能据此直接承诺误删概率。

详证见 [THREE_INNOVATIONS_AND_THEORY.md](THREE_INNOVATIONS_AND_THEORY.md)。尚不能证明原生真源排序必然上升、10% 性能提升、未见源泛化、未知风覆盖或固定五次观测纠错。源在所有合法动作和允许 nuisance 下分布相同，即不可辨识。

## 7. PPTX 实际对象审计

确实取得用户原始 `pmfs原方法图.pptx` 的工作副本 `docs/source/PMFS_ORIGINAL.pptx`，SHA256 `95cb24f31f63a7003d598f20896c1207d95eb14f77a378dc80915c9491984af6`。最终 `METHOD_FRAMEWORK_FINAL.pptx` SHA256 `331f19a297498547ff24ca8ad44bf2cb4b9936f48870f375610410423d3152d2`。

三页 16:9：原 PMFS 与改造关系；新方法输入—三模块—二维源图—下一动作闭环；内部算子/公式/资格。第一页保留原 720 个可编辑图元，第二页复用 176 个；总计 **1068 原生可编辑对象、2 原生表格、0 图片对象/嵌入媒体**。原 16 个组容器在导入时展开，不声称分组层级完全保持。

实际 finalizer 的包完整性、字体、表格、布局通过；两项连接线/文字框包围盒警告经逐页渲染核查，线处于文本框空白而未遮挡文字。不是在 Microsoft PowerPoint 中执行验证。逐页 PNG 与 `PPTX_EDITABILITY_AUDIT.md/.json` 同包提供。

## 8. 独立审查与下一阶段

实际执行是主代理与三个研究代理，以七个专家职责进行四轮独立发现/条件审查/候选比较/综合重构。未声称真实教授参与或七个独立模型一致赞成。原始独立稿及 SHA、反对意见和可实施修改保留在 [会议记录](EXPERT_MEETING_AND_DECISION.md) 和 `evidence/discovery/`。

下一阶段按 [Codex 合同](CODEX_EXPERIMENT_CONTRACT_FINAL.md) 恢复既有原生连续数据，完成物理资格及 executor；先进行同轨迹强基线判别试验，独立收益成立后再跑资源公平主动矩阵。SCI 分区/接受可能性没有由本包验证，当前不以人为“7/10”替代真实增益证据。
