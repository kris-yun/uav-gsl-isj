# 中文操作指南：SOURCE_EVIDENCE_RECOVERY_V1

## 1. 先知道本工程能做什么

本工程已实现可训练模型、完整概率推断、机制回放、主动观测规划和真实 PMFS 快照输入。参考后端是带局地风 AR、间歇检出、硬分支和传感器状态的可控随机系统。它用于验证算法算子与工程闭环；它不是 CFD / GADEN 的替代品。

三模块数据流：原始观测按唯一 ID 入账 → M1 对每个源和机制给出历史联合似然 → M2 撤销名义后缀并替换为机制后缀 → 源—机制联合后验边缘化为二维源地图 → M1 为合法动作块生成未来联合响应 → M3 生成软码本、选择反证/探索动作并预提交整块 → 实际执行并获取新局地风及气体观测 → 回到账本。

## 2. 安装和第一条命令

建议 Python 3.12。无需 CUDA、PyTorch、ROS 才能运行参考套件。

```bash
cd source_evidence_recovery_v1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
bash scripts/run_reference_suite.sh
```

如果从 GitHub 独立分支进入，目录是 `research/source_evidence_recovery_v1`。默认输出 `runs/reference_v1`，不会覆盖交付的 `artifacts/`。输出目录参数可自定义，例如 `bash scripts/run_reference_suite.sh runs/my_reference`。测试日志在指定运行目录。

未安装 editable package 时，也可 `export PYTHONPATH="$PWD/src"` 后执行 `python -m gsl_recovery ...`；pytest 仍需安装。交付环境中临时依赖目录仅供测试收据说明，不是用户安装要求。

## 3. 分步命令

### 3.1 环境与三层测试

```bash
python -m gsl_recovery doctor --out runs/environment.json
python -m pytest -q --junitxml=runs/tests.xml
python -m gsl_recovery native-replay --root examples/native_b4 --out runs/native_b4
```

`native-replay` 读取真实保存的 B4 50 个观测块、最终更新的 128 个候选预测图和 447 个自由格后验。它逐候选复算原生兼容评分，按最终四叉树叶覆盖展开并归一化，不把旧源后验再乘一次。输出不是新定位成绩。保存的评分比也不称为物理似然比。

### 3.2 创建受控训练集并资格检查

```bash
python -m gsl_recovery generate-controlled --out runs/data --episodes 64 --length 10 --seed 11
python -m gsl_recovery audit-data --manifest runs/data/manifest.json --training --out runs/data_qualification.json
```

训练源与机制采用交叉覆盖，不能让源 ID 与故障类别一一绑定。所有 episode 有场景、源组、风组、realization、split、坐标系、单位和读出定义；清单逐文件 SHA256。这里的 `frozen_test` 是生成后冻结的工程留出；用于论文时必须另建没有被查看的科学留出。

### 3.3 M1 训练和消融

```bash
python -m gsl_recovery train --manifest runs/data/manifest.json --variant Aprime --out runs/m1_aprime
python -m gsl_recovery train --manifest runs/data/manifest.json --variant B --out runs/m1_mother
python -m gsl_recovery train --manifest runs/data/manifest.json --variant Bprime --out runs/m1_secondary
python -m gsl_recovery train --manifest runs/data/manifest.json --variant Bprime_no_boundary --out runs/m1_no_boundary
python -m gsl_recovery train --manifest runs/data/manifest.json --variant Bprime_no_wind_constraint --out runs/m1_no_wind_constraint
```

A′ 为同容量 NLL；B 为无风约束的积分分部教师直接迁移；B′ 加风保持约束与分支补偿；两个强消融分别去掉其中一项。B 的假设不足不能成为唯一获胜对照。模型以 34 个非线性可微特征及可训练参数实现正规化 AR 分布，源—参数混合导数采用解析梯度。风参数只用训练集拟合。它不是尚未写出的“神经网络接口”。

真实 manifest 可以用于 A′ 的资格化训练；B/B′ 若没有合格原生教师，命令明确返回 `BLOCKED_NATIVE_TEACHER`。严禁把真实数据送给受控 toy 教师打标签。

### 3.4 M2 训练、离线推断

```bash
python -m gsl_recovery train-diagnosis --manifest runs/data/manifest.json --model runs/m1_secondary/model.npz --out runs/diagnosis --maxiter 300
python -m gsl_recovery evaluate --manifest runs/data/manifest.json --model runs/m1_secondary/model.npz --out runs/offline --split frozen_test --m2 Bprime
```

诊断 checkpoint 绑定完整机制目录，包括类别顺序、类型、起点、持续期和幅度。相同类别数量不代表可以互换。默认在线后验使用精确枚举；诊断仅用于有限预算提议路径，不能乘成第二份观测证据。达到优化迭代上限但未收敛会如实写入收据。

同回放规则下的独立诊断预算对照已经实现：

```bash
python -m gsl_recovery.m2_diagnosis.benchmark --manifest runs/data/manifest.json --model runs/m1_secondary/model.npz --diagnosis runs/diagnosis/diagnosis.npz --out runs/diagnosis_budget
```

它比较 uniform / source-blind / source-aware，保存 180 次推断与 exact 的差异，计入参考生成成本。交付结果未显示 source-aware 优势，不能据此宣称诊断加速或定位增益。

### 3.5 主动闭环和完整矩阵

```bash
python -m gsl_recovery demo --model runs/m1_secondary/model.npz --diagnosis runs/diagnosis/diagnosis.npz --out runs/active --rounds 3 --draws 128 --block-length 5
python -m gsl_recovery matrix --manifest runs/data/manifest.json --config configs/controlled_matrix.yaml --out runs/full_matrix --active
```

每轮先写 `round_*_plan.json`，再获取观测；完整执行承诺的块后才能使用其检验。随后写 update、原始历史、风险账本与 summary。`fallback_rounds` 必须报告；若等于总轮数，不能宣称该次运行证明了 M3 独立反证收益。

M3 支持 `Aprime` 联合 EIG、`B` 分簇选点、`Bprime` 风险功效规划、`min_hamming` 和 `robust_eig`。`A` 只是原生方差选点核心的算子对照，不是完整原生 PMFS；完整 A 使用原生运行或冻结快照。

## 4. 接入真实 House / PMFS

### 4.1 标准 CSV

必须具有列：`time,x,y,z,gas,wind_x,wind_y`；可选 `uid,dwell`。时间和位置为真实测量块，不能用未来帧替代历史局地风。先准备：

- metadata JSON：参照 `examples/external_metadata_template.json`，实际证明资格后再设置三类资格标志；
- candidates JSON：`[[x0,y0], ...]`，保留全部合法候选，不依真源定制；
- 传感器阈值：来自冻结的原生配置，不能看结果选择。

```bash
python -m gsl_recovery import-csv --csv /absolute/data/measurements.csv --metadata /absolute/data/metadata.json --candidates /absolute/data/candidates.json --threshold 0.1 --out runs/imported_episode.json
```

这里 `0.1` 仅为命令语法示例，实际数值必须来自原配置；不允许直接当作默认物理阈值。训练还需要训练源监督、manifest、独立 split 和原生条件教师。

既有指纹审计包可通过：

```bash
python -m gsl_recovery legacy-audit --root /absolute/path/to/fault_evidence --out runs/legacy_audit
```

它只审计/回放 DEV 的保存预测，不打开 `evaluation_only` 真值所有者，不把该包自动变成训练资格。正值读出仅用于接口连通，不改变原实验判决。

### 4.2 持久在线 JSONL 桥接

`online-jsonl` 真正保留账本、风险预算、待执行 Plan 和恢复列表，可用于本地 ROS/GADEN supervisor 调用。它不是每次重启的无状态脚本。

```bash
python -m gsl_recovery online-jsonl --model runs/m1_secondary/model.npz --setup examples/online_setup.json --log runs/native_session.jsonl
```

setup 包含 `candidates`、`mechanisms`、`seed`、`draws`、`wall_seconds`。禁止真源/未来真实风/响应库字段。

输入一行 `{"op":"plan","navigation_qualified":true,"action_blocks":[...],"costs":[...]}`。动作字段是 `x,y,z,time,dwell`；原生 supervisor 必须已校验碰撞、飞行状态和时序。输出承诺动作。执行完整块后送入 `{"op":"observe","observations":[...]}`，每条含唯一 `uid`、原样 `action`、二维 `wind`、二值 `gas`。程序返回源概率地图与机制后验。不能换动作或复用 Plan；缺测 gas 当前需先停止该块并实现合法缺测适配，不能用 0 填补。

原生 ROS 消息类型/时间同步/Nav2 航点转换需要本地 supervisor 接入，本交付没有声称 ROS 节点或实飞已跑通。`bridge-request` 是保留的无状态联合 EIG 动作提案工具；它关闭正式风险检验，不能代替持久 M3 会话。

## 5. 状态文件和错误处理

- `training_receipt.json`：优化目标、收敛状态、教师残差、训练清单和模型哈希。
- `matrix_receipts.json`：每个 seed/消融/离线与主动结果，不能只筛选改善例。
- `risk_ledger.json`：风险预约与执行；MC 误差预算与物理失配分开。
- `ARTIFACT_MANIFEST.json`：交付文件 SHA256。
- `BLOCKED_NATIVE_TEACHER`：缺少原生条件潜状态/JVP/分支资格；按合同补齐，不替换模型冒充。
- `BLOCKED_CODEBOOK_BUDGET` / `BLOCKED_CODEBOOK_WALL_TIME`：全源支持下超预算；不得通过删除低概率源绕过。

所有工程结果最终以 `IMPLEMENTATION_AUDIT.md` 为准。真实源 Top-1、MAP、原生 Top-5%、可靠性、原正确案例退化及未知源泛化，都必须在新的合格科学测试中判决。
