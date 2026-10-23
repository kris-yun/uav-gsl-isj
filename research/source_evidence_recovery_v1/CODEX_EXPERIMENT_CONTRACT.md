# Codex 完整实验合同：Source Evidence Recovery V1

版本：2026-10-23。本合同冻结 M1 源证据微分监督联合生成、M2 机制差分诊断与撤销回放、M3 容错反证与恢复列表。执行目标是完成一轮可追溯的工程与科研验证，不再根据少量好看案例临时更换主题或重写指标。

## 0. 交付边界与判决原则

当前源码提供可训练的 CPU 参考实现、原生 B4 数据回放、有限源集主动闭环、持久 JSONL 接口和消融矩阵。受控闭环通过不等于 House 或真实无人机定位收益。原生 GADEN 微分教师、完整候选支持的在线时延、原生 ROS 闭环、真实飞行分别设门槛，不以虚构结果填补。

必须保护旧项目：在 `research/source-evidence-recovery-v1` 分支操作，工程放在仓库 `research/source_evidence_recovery_v1/`；不得改 main、已冻结 TNQC/旧路线证据、历史真源、旧评测脚本或既有留出集。独立 ZIP 可直接解压进入工程目录执行。已有同名分支应检查后继续，不覆盖他人修改。

四篇母论文对应的是具体算子迁移：随机分析中的条件微分与高斯提升、可微渲染的跳变边界采样、计算生物学的共享编码差分诊断、信息理论的分阶段主动假设检验。**B 为这些算子的可执行移植，未宣称完整复现四篇作者架构；NLL、读出适配、标准积分与贝叶斯归一化均不计原创。**理论与详细出处见 `THEORY_AND_PROOFS.md` 和模块文档。

## 1. 环境与第一条整轮执行命令

要求 Python ≥3.10，NumPy、SciPy、PyYAML、pytest。参考实现不依赖 PyTorch、CUDA 或 ROS。以下命令均在工程根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
bash scripts/run_reference_suite.sh runs/reference_v1
```

最后一条是安装后的**首条完整研发执行命令**，顺序完成环境诊断、全测试、真实 B4 冻结输入回放、受控数据资格检查、M1 训练、诊断训练、离线评测、带诊断审计的主动闭环、三种子 × 十一行的离线矩阵。任何非零退出都先保存日志并修复具体失败；不得跳过失败行生成总成功结论。矩阵的主动部分另见第 5 节。

分开检查环境或测试：

```bash
python -m gsl_recovery doctor --out runs/environment.json
python -m pytest -q --junitxml=runs/tests.xml
python -m gsl_recovery --help
```

`doctor` 只记录资产存在性与运行环境，不能证明数据物理合格。`audit-data` 的 JSON `status` 也必须检查；不得仅凭命令退出或文件存在判为资格通过。

## 2. 数据资产发现、权限和资格

先限定项目根/已知挂载目录发现，禁止扫描整台机器或自动打开 owner-only 真值：

```bash
rg --files -g '*manifest*' -g '*.npz' -g '*.csv' -g '*PROVENANCE*' -g '*.yaml' .
rg --files /mnt/hgfs/workspace/GADEN_files/scenarios/House01 /mnt/hgfs/workspace/GADEN_files/scenarios/House02 /mnt/hgfs/workspace/GADEN_files/scenarios/House03
python -m gsl_recovery doctor --asset-root /mnt/hgfs/workspace/GADEN_files/scenarios/House01 --asset-root /mnt/hgfs/workspace/GADEN_files/scenarios/House02 --asset-root /mnt/hgfs/workspace/GADEN_files/scenarios/House03 --out runs/asset_discovery.json
```

第二条仅在这些挂载存在时执行；不存在记 `BLOCKED_ASSET_MISSING`，继续受控与 B4 回放。建立资产表：路径、SHA256、场景、坐标系/单位、传播资格、传感器读出、用途权限、源组、风组、独立 realization、许可证/来源。历史摘要不是原始证据的替代品。

| 分区 | 可以做什么 | 不可以做什么 |
|---|---|---|
| train | 拟合模型、训练标签与教师监督 | 混入同一 realization 的留出片段 |
| development | 冻结前选择结构、超参和计算预算 | 选择最终冻结测试中的成功子集 |
| calibration | 冻结读出/通道误差/可靠性参数 | 用最终测试真值校准 |
| frozen_test | 冻结后一次主验收；独立 evaluator 看真值 | 反向训练、筛选测点、重设阈值 |
| legacy_evaluation | 获准接口审计及指定既有评分回放 | 默认训练、默认代表 House 留出 |

未见源、未见风、未见场景必须分别建分层报告；House01/02/03 是三个场景，不能随机拆窗口冒充跨场景。独立 plume realization 不跨分区；同源不同 seed 不等于未见源。训练局地风是当时可测输入，完整仿真风只可用于明确标记的 oracle 诊断列，不能进入实际方法。

参考生成器仅证明“受控、源留出、不同 realization”能力；**它不证明未见风/未见场景**。训练源 × 机制现在按交叉组合产生，修正的是数据混淆，不是看测试分数调参。更改生成逻辑必须升版本、保留旧收据，不比较不同数据版本的收益。

## 3. 数据生成、真实接口与输入拒绝

```bash
python -m gsl_recovery generate-controlled --out runs/data_v1 --episodes 64 --length 10 --seed 11
python -m gsl_recovery audit-data --manifest runs/data_v1/manifest.json --training --out runs/data_v1/qualification.json
python -m gsl_recovery native-replay --root examples/native_b4 --out runs/native_b4
```

原生 B4 fixture 来自提交 `c2aacbac7fb2ef7be4be3c9c7dcfce20c11f823c`；官方基线提交固定为 `4e141e162551e674f2f30ddb8859136c72139aac`。`native-replay` 验证真实冻结测量、候选分数与概率地图的数值一致性；错误/真源邻近评分比属于源码兼容评分，不能称物理似然比。它不是新模型的原生定位性能测试。

历史获准包的入口为：

```bash
python -m gsl_recovery legacy-audit --root /path/to/FAULT_TOLERANT_FINGERPRINT_QUALIFICATION --out runs/legacy_audit
```

该入口只读取获准 `inputs/UNSEEN_SOURCE` 中的三份 NPZ，检查接口和已有密度归一化；不自动打开 owner truth/`evaluation_only`，不把它标为训练数据。

外部观测 CSV 的真实导入命令为：

```bash
python -m gsl_recovery import-csv --csv assets/flight.csv --metadata assets/metadata.json --candidates assets/candidates.json --threshold 0.5 --out assets/episode.json
```

`0.5` 仅展示命令格式，实际阈值必须在开发/传感器校准阶段确定并冻结，不能直接套用。CSV 必需列：`time,x,y,z,gas,wind_x,wind_y`，可选 `uid,dwell`。metadata 参照 `examples/external_metadata_template.json`，至少包含 scene、source_group、wind_group、realization_id、split、frame、units、readout 及三个 qualification 字段。candidate JSON 为完整合法 XY 源集合，不能围绕真源裁剪。导入后用相对 episode 路径组成 `{"episodes":[{"path":"episode.json"}]}` manifest，再执行 `audit-data`。训练真值只存在 train 文件及离线 evaluator；在线请求不含它。

资格检查能发现格式/支持声明等错误，不自动证明传播收敛、几何坐标一致、传感器标定真实成立。须附独立证明。二值 readout 以外、缺测、时序不合法、非有限数值、重复 UID、未来真风或未经资格的训练数据均停止相应任务；不可静默补零。

## 4. 五个 M1 训练分支与诊断训练

```bash
for variant in Aprime B Bprime Bprime_no_boundary Bprime_no_wind_constraint
do
  python -m gsl_recovery train --manifest runs/data_v1/manifest.json --variant "$variant" --seed 0 --maxiter 200 --out "runs/models/$variant"
done
python -m gsl_recovery train-diagnosis --manifest runs/data_v1/manifest.json --model runs/models/Bprime/model.npz --out runs/diagnosis --seed 0 --maxiter 300
python -m gsl_recovery evaluate --manifest runs/data_v1/manifest.json --model runs/models/Bprime/model.npz --m2 Bprime --split frozen_test --out runs/offline
```

训练读取 train；完整 manifest 的资格检查读取分区元数据，但 frozen_test 不参与梯度和超参选择。模型、机制目录与诊断 checkpoint 的语义哈希必须匹配。预先固定全部种子/迭代次数；记录优化器收敛标志，不把达到迭代上限包装成收敛。

外部 native M1 的 B/B′ 需要条件潜状态或正确整段轨迹教师、源方向 JVP/VJP、分支事件 trace 与强制重放、可验证提议分布/coarea 权重，以及保持同一外生风的源响应提升。缺任何项即 `BLOCKED_NATIVE_TEACHER`，禁止悄悄退化为 NLL 后仍称 B′。先交付 A′、接口、回放与规划结果；后续在原生 simulator 提供这些算子及独立有限差分验证后解锁 B/B′。

## 5. A → A′ → A′+B → A′+B′ 的真实实验链

| 模块 | A：原生 | A′：结构适配 | A′+B：直接算子迁移 | A′+B′：二次创新 |
|---|---|---|---|---|
| M1 | PMFS 原始前向/地图评分 | 同读出、合法联合分布、NLL | 普通提升微分教师 | 同风约束源微分 + 跳变边界项 |
| M2 | 原生更新 | nominal 联合似然 | 诊断/新机制解释最新证据 | 源条件诊断 + 后缀撤销替换 + 防御提议 |
| M3 | 原生主动效用与闭环 | 普通联合 EIG | 分阶段聚类 ASHT | 软联合码本 + 风险约束反证 + 恢复列表 |

```bash
python -m gsl_recovery matrix --manifest runs/data_v1/manifest.json --config configs/controlled_matrix.yaml --out runs/matrix_offline
python -m gsl_recovery matrix --manifest runs/data_v1/manifest.json --config configs/controlled_matrix.yaml --out runs/matrix_active --active
python -m gsl_recovery demo --model runs/models/Bprime/model.npz --diagnosis runs/diagnosis/diagnosis.npz --out runs/active --rounds 3 --draws 128 --block-length 5 --planner Bprime --m2 Bprime
```

配置固定三种子、十一行，共 33 个配对结果：三种 M1、去边界、去风约束、M2 母算子/二次创新、M3 母算子/二次创新、普通码距、噪声通道 EIG。`--active` 才实际检验选点差异；离线相同预测器下的 M3 行不构成规划收益证据。受控 `planner=A` 只实现原生效用核心，不等于完整原生 PMFS；A 必须单独运行冻结原生可执行程序。不得用 Python 代理曲线冒充 A。

### M2 必做的独立诊断计算实验

矩阵默认 exact enumeration，因此它隔离的是“是否撤销回放”，并未证明诊断网络必要。另在相同历史、生成器、机制目录、源支持与预算上比较：源无关 B、源条件 B′、先验/均匀提议、exact。使用已经实现的：

```python
result = engine.infer_budgeted(history, diagnosis, rng,
    draws=4, reference_draws=4, epsilon=0.1, variant="Bprime")
exact = engine.infer(history, variant="Bprime")
```

`demo --diagnosis` 会实际调用预算推断并保存与 exact 的 L1 误差；其主地图仍使用 exact，不能声称预算网络已驱动控制。以下独立预算基准也已实现并实际执行，固定 Bprime 完整回放，比较 uniform、source-blind、source-aware 三种提议：

```bash
python -m gsl_recovery.m2_diagnosis.benchmark --manifest runs/data_v1/manifest.json --model runs/models/Bprime/model.npz --diagnosis runs/diagnosis/diagnosis.npz --out runs/diagnosis_budget
```

默认使用 4 条 development 历史、R=2/4/8、5 次重复，共 180 次推断。报告模型 likelihood 次数、生成参考轨迹次数、总时间、后验 L1、平方概率误差及提议/抽样机制。当前小基准没有支持 source-aware 独立优势，负结果须保留。科学阶段还需扩展预注册历史、真源 margin/rank 和物理独立重复。B 与 B′ 含不同回放规则时，还须固定同一回放规则比较提议，不能将全部收益归因诊断。重要性权重只保证未归一证据的适当无偏性，有限样本归一化后验不作无偏承诺。

### 母算子与三模块的独立必要性

M1 须胜过同架构 NLL，并用去边界/去风约束区分增益来源；只改善浓度或 NLL 不算定位创新。M2 须在预定义故障和无故障集同时报告错误恢复与原正确案例退化，不得把诊断输出再乘一次当证据。M3 须与相同模型的联合 EIG、通道 EIG、普通码距及 ASHT 配对比较，报告无功效回退比例、列表恢复和低概率候选覆盖。风险测试不通过也要完整保留结果。

## 6. 持久主动桥接协议与本地接入

执行真实在线桥接前，native supervisor 提供通过碰撞/高度/时序/能量检查的整段 action blocks。未来 wind 由模型采样，不能由 supervisor 输入。单架次只启动一个持久进程：

```bash
python -m gsl_recovery online-jsonl --model runs/models/Bprime/model.npz --setup assets/online_setup.json --log runs/online/ledger.jsonl
```

setup 仅允许 `candidates,mechanisms,seed,draws,wall_seconds`，例如：

```json
{"candidates":[[0.5,0.5],[2.5,0.5],[0.5,2.5],[2.5,2.5]],"mechanisms":[{"kind":"nominal"},{"kind":"sensor_offset","onset":3,"magnitude":1.0},{"kind":"sensor_offset","onset":3,"magnitude":-1.0}],"seed":0,"draws":128,"wall_seconds":10.0}
```

stdin 每行一个 JSON，stdout 每行一个响应。先 `plan`：

```json
{"op":"plan","navigation_qualified":true,"action_blocks":[[{"x":1.0,"y":1.0,"z":1.0,"time":1.0,"dwell":1.0},{"x":1.5,"y":1.0,"z":1.0,"time":2.0,"dwell":1.0}]],"costs":[0.5]}
```

响应包含动作、plan_id、源图、版本与风险支出。仅实际执行被选中的完整动作块，再回传 `observe`：

```json
{"op":"observe","observations":[{"uid":"flight1-001","action":{"x":1.0,"y":1.0,"z":1.0,"time":1.0,"dwell":1.0},"wind":[0.8,0.1],"gas":0.0},{"uid":"flight1-002","action":{"x":1.5,"y":1.0,"z":1.0,"time":2.0,"dwell":1.0},"wind":[0.7,0.1],"gas":1.0}]}
```

以上只定义协议，不是实飞数据。action 必须与已提交计划一致，UID 唯一，时间递增；尚有 pending block 时拒绝新 plan。服务保存同一 risk ledger 与恢复列表，不能每块重启以重置 alpha。日志支持审计；当前不提供断电自动恢复，进程崩溃后本架次停测，完成状态恢复校验后才续飞。

`bridge-request` 是无状态 A′ 选点接口，**不能替代 M3 持久风险闭环**。在线 erasure 缺 mask 与边缘化实现：传感器漏测、半块或中断不得伪填 0；停止该块并标 `BLOCKED_ONLINE_ERASURE`。通道层擦除测试通过不等于真实在线擦除链路已通。

## 7. 资源保护与完整支持约束

CPU 参考限制 2–4 线程；建议 8 GiB 内存上限，无 GPU。若后续更换 GPU 网络，显存峰值不得超过可用显存 70%，训练与规划分开。设置：

```bash
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
```

码本默认 block length 5，精确枚举上限 8；默认 rollout-observation 上限 2,000,000，码本上限 512 MiB。矩阵默认墙钟上限 3600 秒；该检查位于行边界，原生长任务另由 supervisor/watchdog 强制限时并保留未完成收据。不得把未跑行算成功。

超预算依次调整开发期冻结的 action 数、批处理和采样预算，记录相应 MC 不确定性；不删除低概率源、不裁剪成 Top-K、不利用真源位置减少支持。全源支持的时延与内存不达标就是 `BLOCKED_FULL_SUPPORT_LATENCY`，不是允许丢失真源的理由。在线候选源条件机制概率使用对数域计算；显示概率下溢不能把该源永久从恢复列表删除。

## 8. 科学验收与停止条件

在打开 final freeze 前保存预注册：主假设、源集合、场景/风/realization 划分、故障强度、阈值、固定路线离线集、主动动作预算、停止规则、种子、主指标、统计方法和计算资源。后续改动形成新版本、新留出；不得继续解释成同一次冻结验收。

主指标同时报告真源 Top-1/rank、真源对最强竞争源 log-score margin、MAP 米误差、原生 Top-5% 米误差、真源 log score/Brier/覆盖可靠性、原本正确案例退化率、达到成功条件的观测数/飞行距离/时间。原生 Top-5% 是最高 `ceil(0.05*N_free)` 个自由栅格的概率加权质心误差，不能替换为其中最小距离。边界 tie/float 以冻结官方 `ExpectedValue(...,0.05)` 程序输出为最终基准。

目标为原生主误差至少 10% 稳定相对下降，同时 Top-1、可靠性与原正确退化满足预注册约束；还必须优于强 A′ 基线，区分结构适配收益。该 10% 是研发目标，不是已达结果或可通过调指标保证的下限。对独立 episode/realization 做配对分层 bootstrap 95% CI，不能把相邻观测当独立样本；报告逐场景与总体效应，种子是训练随机性重复，不替代物理独立重复。CI 宽则结论为证据不足，不能凭点估计称稳定。

立即停止相应科学链的条件：数据泄漏、源/机制标签混淆、oracle 输入、训练资格不合格、无合法真源支持、教师梯度/边界验证失败、证据重复计数、回放与整段重算不一致、风险重复使用、模型版本变更未恢复列表、重要性权重无支持、非有限概率或归一化错误。停止后先纠正实现并重新冻结；不得继续加权补救旧曲线。若 B′ 在预注册外推任务不胜同架构 NLL，或 M3 不胜联合 EIG，则该创新结论不成立，保留有效工程与负结果，不包装新名字。

## 9. 证据保存和最终判决

每次保存命令/退出码、环境、源码 commit、配置及数据 SHA256、模型/机制版本、训练日志、原始逐 episode 指标、动作执行前计划、观测 UID、回放移除/替换因子、源机制后验、风险及 MC 预算、候选列表变化、退化案例和资源峰值。计划必须先保存后获得新观测。模型目录、数据与 evaluation-only 真值分权限保存，公开包不复制未授权资产。

```bash
python scripts/freeze_evidence.py .
```

生成 `ARTIFACT_MANIFEST.json` 后核对全部关键文件，打包不得只留汇总表。收据应明确：

1. **ENGINEERING_PASS**：测试、训练、受控闭环、真实 B4 回放、接口执行成立；不带物理性能承诺。
2. **PHYSICAL_QUALIFIED**：House/湖岸传播、几何、读出、支持及 native teacher 资格成立。
3. **INDEPENDENT_MODULE_EFFICACY**：三模块分别通过 A′/B/强消融、相同预算、未见源验证；诊断与回放收益分开。
4. **NATIVE_CLOSED_LOOP_PASS**：冻结原生 PMFS 对照、真实动作预算、全支持延迟与无 oracle 闭环成立。
5. **PAPER_READY**：冻结留出稳定收益、完整失败分析、统计不确定性、物理解释与复现实验材料足够。

只能晋级已满足的等级。当前 ROS/GADEN 和真实飞行不标已运行；缺口准确标 BLOCKED 并附接口、所需资产与下一条可执行命令。设计自评分与实证准备度分别报告，不为达到“7 分”修改成绩或宣称论文已经通过。
