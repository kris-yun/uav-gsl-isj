# Codex 完整实验合同 V2：源证据投影、可撤销回放与主动反证

版本日期：2026-10-23。执行依据为本包实际 `src/gsl_recovery/v2_cli.py`、数据适配器和测试。本文不把命令存在、单元测试通过、工程演示或数值训练当作原生气源定位科学成绩。

## 0. 工作边界、版本与本轮交付判决

统一主线保持 M1/M2/M3：训练期的物理信息教师，向只接收合法观测的学生传递源间证据；M2 重算受影响的历史证据；M3 使用学生的联合预测进行风险约束的主动反证与候选恢复。

- V1 固定基线提交：`55117464617719760489a86ff8829a818d266257`。
- 新工作分支：`research/source-evidence-recovery-v2-distill`。不得直接改 main；发布状态及最终提交以交付时 `git rev-parse HEAD` 为准。
- GitHub 仓库内保留目录名 `research/source_evidence_recovery_v1/`，该目录内部新增 V2 代码与文档。独立压缩包的根目录名可以是 `source_evidence_recovery_v2/`；不要因为目录名含 V1 就调用旧命令代替 V2。
- 不改写 V1 的 `IMPLEMENTATION_AUDIT.md`、旧实验收据、原始负结果或原测试划分。V1 seed 0 的同容量 NLL Top-1 为 11/12、M1 B′+nominal M2 为 10/12、加入完整回放后恢复到 11/12，不能被 V2 文案改写为主创新已胜出。V1 source-aware 诊断提议也没有独立优势。
- 本轮已经核验 CPU PyTorch `2.7.1+cpu`；没有访问用户本地 RTX 5060、3090 或其他 GPU。后续 Codex 在本机执行 GPU 实验必须留下新的设备回执。
- 当前原生 3D teacher 的多源、独立 realization、完整外生风场和物理时间资产资格不齐：`BLOCKED_QUALIFIED_MULTI_SOURCE_BANK_MISSING`。该状态不能用一组 64 位字符串或人工改 metadata 解除。
- 原生 GADEN Malliavin/不连续边界导数没有接入：`BLOCKED_NATIVE_DERIVATIVE`。现有可微教师是神经代理，其导数不能宣称为原生模拟器的无偏导数。

当前真实 House02 NLL 学生已由 8 epoch 恢复到 40 epoch：20,139 参数、192 条训练序列、96 个原始 cube 组、CPU；后 32 epoch 阶段用时约 60.039 秒。依据 `artifacts/v2/house_student/training_receipt.json`，状态 `COMPLETE`、`scope=NUMERICAL_ONLY`、原 test 响应读取量为 0。192 条序列来自同一批 96 个 cube 的两种固定探针表，不是 192 个独立世界。它没有物理 teacher，不能把这条训练收据报告成蒸馏或湖岸提升。

## 1. 命令状态表：先区分可执行与待实现

| 项目 | 当前入口 | 状态和含义 |
|---|---|---|
| 环境诊断 | `python -m gsl_recovery.v2_cli doctor` | 可执行；读取当前 Python/Torch/CUDA |
| 工程数据与外生风场 bank | `prepare-engineering` | 可执行；制造环境，非 CFD/GADEN |
| 物理场条件教师 | `train-teacher` | 可训练工程 bank；原生物理训练被资产资格门阻断 |
| 投影目标 | `build-targets` | 可执行训练源端点及中点方向目标；代理导数 |
| 学生六个控制 | `train-student --variant ...` | `nll/distribution/privileged_pair/mean_log/projected_evidence/projected_no_anchor` |
| 去掉方向项 | `train-student --no-directional` | 可执行端点控制，不是 direction-only |
| 同架构容量控制 | `train-student --hidden ... --modes ...` | 可执行；参数量和训练预算须另记 |
| House 输入和训练清单 | `data.house_v2`、`prepare-house` | 可执行；只允许 record-index 数值任务 |
| 开发/冻结集评估 | `evaluate --split development/frozen_test` | 可执行，但当前 House 清单没有授权 frozen_test 响应；不能自行造这个 split |
| 失配诊断校准 | `calibrate-adequacy` | 可执行开发诊断；不是物理错误概率证书 |
| 神经闭环 | `demo` | 可执行制造环境闭环，非原生导航 |
| 持久在线会话 | `online-jsonl` | 可执行学生接口；真实 ROS 导航/时钟 supervisor 仍须本机接入 |
| S2 真实观测查询 | `python -m gsl_recovery.data.s2_v2` | 可执行原发布包的局地读取资格检查 |
| T1 场重建、T2 后验蒸馏、T4 动作蒸馏、HIB、direction-only | 无对应 CLI | `IMPLEMENTATION_TASK`，见第 8 节；不得编造子命令 |

## 2. 环境、分支与第一条科研执行命令

### 2.1 进入正确代码目录

在已经干净检出的项目中，若目标分支尚不存在，可从固定 base 建立独立工作分支：

```bash
git show --no-patch --format=%H 55117464617719760489a86ff8829a818d266257
git switch -c research/source-evidence-recovery-v2-distill 55117464617719760489a86ff8829a818d266257
cd research/source_evidence_recovery_v1
```

若交付分支已存在，直接检出该分支后进入上述目录；不要再次创建、重置或覆盖用户已有工作。若从 V1 base 新建分支，须先把本次交付的 V2 增量应用到该目录、保留旧证据并检查 diff，才能运行 V2 命令；V1 base 本身没有这些新入口。独立 ZIP 则直接进入解压后的工程根目录。

本机新环境的安装命令：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
```

这是已验证的 CPU 路线。需要 GPU 时使用与本机驱动配套的官方 PyTorch wheel，记录 wheel/驱动版本后重新运行 doctor；不要把 CPU wheel 的安装成功当成 GPU 已可用。

本对话运行时已有 `/tmp/gsl_v6_torch` 和 `/tmp/gsl_v5_test_deps`，仅在这些实际目录存在时，可用以下环境替代重复安装：

```bash
export PYTHONPATH="/tmp/gsl_v6_torch:/tmp/gsl_v5_test_deps:$PWD/src"
```

### 2.2 冻结一次运行位置

以下命令从工程根目录执行。`GSL_RUN_ROOT` 必须是本轮新的输出目录；原 `artifacts/` 是历史证据，不能覆盖。

```bash
set -euo pipefail
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export GSL_RUN_ROOT="$PWD/runs/v2_contract_01"
export GSL_DEVICE=cpu
mkdir -p "$GSL_RUN_ROOT/receipts"

gsl_require_complete() {
  python - "$1" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / 'training_receipt.json'
receipt = json.loads(p.read_text())
if receipt.get('status') != 'COMPLETE':
    raise SystemExit('STOP: incomplete training; resume the last complete epoch before proceeding: ' + str(p))
print('COMPLETE:', p)
PY
}
```

**安装之后的首批科研命令固定为 doctor 和测试，不能先训练再补资格：**

```bash
python -m gsl_recovery.v2_cli doctor --out "$GSL_RUN_ROOT/receipts/doctor.json"
python -m pytest -q --junitxml="$GSL_RUN_ROOT/receipts/pytest.xml"
python -m gsl_recovery.v2_cli --help > "$GSL_RUN_ROOT/receipts/cli_help.txt"
python -m gsl_recovery.v2_cli train-student --help > "$GSL_RUN_ROOT/receipts/student_help.txt"
python -m pip freeze > "$GSL_RUN_ROOT/receipts/environment.txt"
```

测试必须包含 `test_v2_neural_audit.py`、`test_v2_projection.py`、`test_house_v2_adapter.py`、`test_v2_joint_eig.py`、`test_v2_planner_diagnostics.py` 及原 M1/M2/M3 测试。缺 Torch 导致的 skip 不能算神经部分通过。出现失败先修复并保留失败回执，再跑受影响测试及完整门禁；不得删测试、放宽数值门或把失败转换成 skip。

## 3. 先发现资产，再检查授权，再读取数值

本次资产目录是 `/workspace/scratch/f825a7b8b273/v6_work/data/`。在本机应设置实际挂载目录，不假设聊天环境路径存在：

```bash
export GSL_DATA_ROOT=/workspace/scratch/f825a7b8b273/v6_work/data
rg --files "$GSL_DATA_ROOT" -g '*.zip' -g '*MANIFEST*.json' -g '*manifest*.json' -g '*QUALIFICATION*.json' -g '*SCOPE*.json' > "$GSL_RUN_ROOT/receipts/asset_paths.txt"
```

此步骤只发现路径和读权限元数据。禁止为了“看看有没有信号”先打开 sealed test、owner-only 标签或候选真实未来响应库。发现多个同名包时按原 manifest/hash 识别，不按文件修改日期或包名中的 `VERIFIED` 判定资格。

数据身份必须包含：几何、源条件、风边界程序、模拟随机种子、plume realization、观测算子、时间语义、权限、原始文件 hash。不同时间窗、路径、观测掩码或导航随机种子不能伪装成独立 plume 世界。

### 3.1 House02 已授权数值包

原包名：`HOUSE02_3D_JOINT_EVIDENCE_SIX_CONTROLS_20261020_VERIFIED.zip`。

SHA256：`32a85615731c5003dfcc4f355d33bafda8028f0d7b5ba9f05ebff978f5d8a4f5`。

原 `ARCHIVE_DATA_SCOPE.json` 允许 benchmark/offline fit；原 `PREREGISTRATION.json` 的 12 train/6 test 源范围必须保留。执行适配器前不要手工读取响应向量：

```bash
export GSL_HOUSE_ARCHIVE="$GSL_DATA_ROOT/library_downloads/研究/HOUSE02_3D_JOINT_EVIDENCE_SIX_CONTROLS_20261020_VERIFIED.zip"
python -m gsl_recovery.data.house_v2 \
  --archive "$GSL_HOUSE_ARCHIVE" \
  --out "$GSL_RUN_ROOT/house_export" \
  --test-fold 0 --dev-fold 1
```

预期：原 fold2 的 6 源×16 realization=96 train；原训练范围内 fold1 的 96 dev；原 fold0 的 96 test 响应不读。授权原件、源划分、raw-cube/response hash 和导出 hash 都应留在输出中。适配器拒绝非空输出、权限缺失、跨分区原 cube 重复或响应哈希不符。

该数据只有 10 个保存记录×30 探针；气体为原四格池化数值，没有合格物理秒或局地风。风以缺失 mask 表达；占位 0 不是实际静风。不能把探针当障碍，不把 `record_index` 当秒，不把这批向量拼上单源 S2 就宣称已有多源三维 teacher 数据。

### 3.2 原生 teacher 合格门

只有实际原件支持以下全部条件，才能申请 `PHYSICALLY_QUALIFIED_TRAIN`：

1. 多个合法源与独立 plume realization，训练源/风/几何与最终测试分区固定。
2. 完整外生风场的三维位置、真实秒和三维速度可追溯；bank 是源无关外生世界，不能是真源 plume 快照库。
3. 世界几何、源高、边界、原生源强、传感器响应/积分/LOD/延迟与查询有效域通过独立资格检查。
4. `physics_qualification_sha256`、`readout_contract_sha256`、`world_lineage_sha256` 对应实际存在的原始资格文件；必须计算 hash 核对，而不是只满足字符串长度。
5. `teacher_train_only/`、`student_inputs/`、`evaluation_only/` 的访问边界可审计。学生部署加载器不能打开 teacher checkpoint、全场 bank、未来实测风或 evaluator 标签。

当前 House02 和 S2 均不能满足该联合门。缺一项就保存阻碍清单并继续独立工程任务，不伪造 bank、不把工程数据改名成物理数据。

## 4. 一轮完整可执行工程训练矩阵

本节是可复现实现验证，范围始终 `ENGINEERING_ONLY`。在同一个固定数据集上执行三个预注册优化种子，区别优化随机性；这些种子不增加真实物理世界数量。

### 4.1 一次准备制造环境

```bash
python -m gsl_recovery.v2_cli prepare-engineering \
  --out "$GSL_RUN_ROOT/engineering_data" \
  --episodes 48 --length 8 --seed 31
```

该命令产生 48 train、12 development、4 个制造外生风上下文。其三维坐标输入是工程 bank，不是原生 CFD。不要把生成函数重复调用到同一目录；参数、manifest 和数据 hash 一经冻结就不变。

### 4.2 教师、目标和同容量学生控制

```bash
for GSL_SEED in 23 29 37; do
  python -m gsl_recovery.v2_cli train-teacher \
    --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
    --bank "$GSL_RUN_ROOT/engineering_data/bank" \
    --out "$GSL_RUN_ROOT/seed_$GSL_SEED/teacher" \
    --epochs 8 --batch-size 8 --seed "$GSL_SEED" \
    --device "$GSL_DEVICE" --wall-seconds 175
  gsl_require_complete "$GSL_RUN_ROOT/seed_$GSL_SEED/teacher"

  python -m gsl_recovery.v2_cli build-targets \
    --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
    --teacher "$GSL_RUN_ROOT/seed_$GSL_SEED/teacher/model" \
    --out "$GSL_RUN_ROOT/seed_$GSL_SEED/targets" \
    --count 32 --seed "$GSL_SEED" --order 6

  python -m gsl_recovery.v2_cli train-student \
    --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
    --out "$GSL_RUN_ROOT/seed_$GSL_SEED/nll" \
    --variant nll --epochs 8 --batch-size 8 --seed "$GSL_SEED" \
    --device "$GSL_DEVICE" --wall-seconds 175
  gsl_require_complete "$GSL_RUN_ROOT/seed_$GSL_SEED/nll"

  for GSL_VARIANT in distribution privileged_pair mean_log projected_evidence projected_no_anchor; do
    python -m gsl_recovery.v2_cli train-student \
      --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
      --targets "$GSL_RUN_ROOT/seed_$GSL_SEED/targets" \
      --out "$GSL_RUN_ROOT/seed_$GSL_SEED/$GSL_VARIANT" \
      --variant "$GSL_VARIANT" --epochs 8 --batch-size 8 --seed "$GSL_SEED" \
      --device "$GSL_DEVICE" --wall-seconds 175
    gsl_require_complete "$GSL_RUN_ROOT/seed_$GSL_SEED/$GSL_VARIANT"
  done
done
```

每条训练命令结束后检查 `training_receipt.json`。状态不是 `COMPLETE` 时不得使用未完成模型继续建立正式目标/报告；按第 10 节恢复已完成 epoch 的 checkpoint，不把墙钟停止当成功。

控制的实际含义：

| 控制 | 代码实现 | 必须回答的问题 |
|---|---|---|
| 同容量 NLL | `nll`，不读取 teacher targets | 新监督是否优于同样学生和合法输入的标准生成模型 |
| 普通分布蒸馏 | `distribution` | 收益是否只是更多 teacher 样本/密度监督 |
| 特权原子直接迁移 | `privileged_pair` | 不消去特权世界状态，是否产生错误源证据 |
| 期望 log 控制 | `mean_log` | 把 `log E p` 换成 `E log p` 会否扭曲源间判断 |
| 源证据投影 | `projected_evidence` | 条件投影后的端点+中点方向目标是否产生独立收益 |
| 去分布锚 | `projected_no_anchor` | 只拟合证据而不约束发生频率会出现什么退化；此模型禁止部署主动预测 |

这些是 V2 明确定义的迁移与二次创新控制，不冒充 ICML/SIGGRAPH 原论文完整实现或原生模拟器导数。

实际端点消融与强容量基线：

```bash
for GSL_SEED in 23 29 37; do
  python -m gsl_recovery.v2_cli train-student \
    --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
    --targets "$GSL_RUN_ROOT/seed_$GSL_SEED/targets" \
    --out "$GSL_RUN_ROOT/seed_$GSL_SEED/projected_endpoint_only" \
    --variant projected_evidence --no-directional \
    --epochs 8 --batch-size 8 --seed "$GSL_SEED" \
    --device "$GSL_DEVICE" --wall-seconds 175
  gsl_require_complete "$GSL_RUN_ROOT/seed_$GSL_SEED/projected_endpoint_only"

  python -m gsl_recovery.v2_cli train-student \
    --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
    --out "$GSL_RUN_ROOT/seed_$GSL_SEED/nll_capacity96" \
    --variant nll --hidden 96 --modes 4 \
    --epochs 8 --batch-size 8 --seed "$GSL_SEED" \
    --device "$GSL_DEVICE" --wall-seconds 175
  gsl_require_complete "$GSL_RUN_ROOT/seed_$GSL_SEED/nll_capacity96"
done
```

主比较保持原相同容量；`nll_capacity96` 单列参数量和成本，不混称同容量。不根据哪个 seed 表现好来删选其他 seed。

### 4.3 离线评价：先看逐例 margin/排名，再看汇总

```bash
for GSL_SEED in 23 29 37; do
  for GSL_VARIANT in nll distribution privileged_pair mean_log projected_evidence projected_no_anchor projected_endpoint_only nll_capacity96; do
    python -m gsl_recovery.v2_cli evaluate \
      --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
      --model "$GSL_RUN_ROOT/seed_$GSL_SEED/$GSL_VARIANT/model" \
      --split development \
      --out "$GSL_RUN_ROOT/seed_$GSL_SEED/evaluate_$GSL_VARIANT"
  done
done
```

`evaluation.json` 保存逐例真源排名、最大竞争源 margin、Top-1、MAP、Top-5% 质心误差、源后验 NLL、Brier 和错误高置信计数。当前 evaluator 的机制比较是 nominal 离线比较，不冒充完整 M2 消融；M2 分支在闭环中独立运行。Top-5% 当前按候选后验排序取前 ceil(5%N) 的概率加权质心；原生 C++ 的 tie/float/栅格语义需要最终原程序对齐，不能把此参考公式自动当作原生等价。

## 5. 真实 House02 数值训练：独立执行，不借工程 teacher 冒充物理监督

```bash
python -m gsl_recovery.v2_cli prepare-house \
  --export-root "$GSL_RUN_ROOT/house_export" \
  --out "$GSL_RUN_ROOT/house_numerical_data" \
  --paths 2 --hidden 48 --modes 4

for GSL_SEED in 23 29 37; do
  python -m gsl_recovery.v2_cli train-student \
    --manifest "$GSL_RUN_ROOT/house_numerical_data/manifest.json" \
    --out "$GSL_RUN_ROOT/house_seed_$GSL_SEED/nll" \
    --variant nll --epochs 40 --batch-size 8 --seed "$GSL_SEED" \
    --device "$GSL_DEVICE" --wall-seconds 175
  gsl_require_complete "$GSL_RUN_ROOT/house_seed_$GSL_SEED/nll"

  python -m gsl_recovery.v2_cli evaluate \
    --manifest "$GSL_RUN_ROOT/house_numerical_data/manifest.json" \
    --model "$GSL_RUN_ROOT/house_seed_$GSL_SEED/nll/model" \
    --split development \
    --out "$GSL_RUN_ROOT/house_seed_$GSL_SEED/evaluation"
done
```

输出应为 192 train sequences / 96 independent cube groups / 96 development sequences，原 test 值仍为 0。两种训练探针表在读响应前固定；开发只使用第一种固定表。它们不是可飞行航线。浓度按原数值协议 0.1 ppm 边界做删失读出，不能为了胜率改变阈值。

已经交付的 40 epoch 记录可用于复核，不需要因合同而覆盖重训。同一源域内数值开发结果不能称为最终未见场景验证。`load_online_model` 会拒绝这个 record-index/no-wind 模型；该拒绝是预期资格行为，不应删除。

当前禁止以下行为：把 `engineering_data/bank` 作为 House 物理 teacher；用原 test 实际响应制作源条件预测表；把保留测试源重新标记 train；为追求分类成绩把探针响应时刻当成连续飞行时间。

## 6. M2/M3 完整主动闭环与公平消融

### 6.1 可执行制造环境闭环

固定学生，改变 M2；固定 M2，改变 M3。不能通过每个组合重新训练不同 M1 混淆模块贡献。

```bash
for GSL_SEED in 23 29 37; do
  for GSL_M2 in Aprime B Bprime; do
    python -m gsl_recovery.v2_cli demo \
      --model "$GSL_RUN_ROOT/seed_$GSL_SEED/projected_evidence/model" \
      --out "$GSL_RUN_ROOT/seed_$GSL_SEED/active_m2_$GSL_M2" \
      --rounds 3 --draws 256 --eig-draws 8 --seed 42 \
      --m2 "$GSL_M2" --variant Bprime
  done

  for GSL_M3 in Aprime B Bprime min_hamming robust_eig channel_eig; do
    python -m gsl_recovery.v2_cli demo \
      --model "$GSL_RUN_ROOT/seed_$GSL_SEED/projected_evidence/model" \
      --out "$GSL_RUN_ROOT/seed_$GSL_SEED/active_m3_$GSL_M3" \
      --rounds 3 --draws 256 --eig-draws 8 --seed 42 \
      --m2 Bprime --variant "$GSL_M3"
  done

  python -m gsl_recovery.v2_cli demo \
    --model "$GSL_RUN_ROOT/seed_$GSL_SEED/nll/model" \
    --out "$GSL_RUN_ROOT/seed_$GSL_SEED/active_nll_joint_eig" \
    --rounds 3 --draws 256 --eig-draws 8 --seed 42 \
    --m2 Bprime --variant Aprime
done
```

本 demo 固定制造环境、四个源及固定实际真源，作用是检查闭环和归因；不是多世界性能基准。三次优化 seed 也不能替代独立环境 seed。任何一项失败保留日志；不要略过失败 arm 后只汇报成功 arm。

M2 分支的实际意义：A′ 使用 nominal 历史似然；B 只把新机制用于最新条件项；B′ 撤销旧后缀并按新机制重算。B 无“完整回放误差”定义，报告 null/NOT_APPLICABLE，不用 0 暗示已与整段重算一致。差分诊断输出仅决定计算/复查，不作为第二个似然因子。

M3 的 A′ 使用完整 gas+wind 联合 EIG；B 为当前可执行的聚类分离控制；B′ 为风险约束反证及恢复列表；另有 min-Hamming、共同污染通道 minimax-EIG 和 uniform-channel-EIG。`A` 仅为原 PMFS 方差项的有限参考，不是完整原生 PMFS；不能在论文表中把该分支写成 official PMFS。

当前 `sensor_offset` 在二值模型中是 logit 偏移，在连续模型中是 log-concentration 偏移，即 ppm 上的乘性变化；它不是原 ppm 的加性零点误差。`onset/duration` 目前按观测索引生效。真实仪器的加性偏置、延迟、响应积分和物理持续时间必须另行适配并校验，不能沿用同一名称冒充已经实现。

### 6.2 诊断四层反证功效，不能靠放宽风险得到触发

每个已选 action block 保留同一 null、竞争源和 α，记录：

1. nominal mechanism，无额外污染，无 TV；
2. 所有机制，无额外污染，无 TV；
3. 所有机制+原声明污染预算，无 TV；
4. 所有机制+原污染预算+原 MC/TV 半径。

实际入口 `m3_planner/diagnostics.py::diagnose_counterevidence_layers` 已在 V2 在线会话中调用。分别报告 LP 保守目标和独立有限 TV 重算的风险/功效；解释 fallback 是哪一层引起。TV 集合重叠或响应重合只能说明当前模型歧义集合中功效受限，不能证明真实气源物理不可辨识。

禁止降低污染预算、增大 α、删掉不利机制、删掉低后验合法源或在看过真实未来响应后换 action 以获得反证事件。默认动态 MC 预算仍为 `.01/((round+1)*(round+2))`；原风险账本预算不变。自适应加 draws 尚未实现，其未来版本必须预先登记各阶段及总 union δ，不能复用固定样本量证书。

### 6.3 持久在线服务

先对选定学生运行开发诊断校准：

```bash
python -m gsl_recovery.v2_cli calibrate-adequacy \
  --manifest "$GSL_RUN_ROOT/engineering_data/manifest.json" \
  --model "$GSL_RUN_ROOT/seed_23/projected_evidence/model" \
  --out "$GSL_RUN_ROOT/adequacy.json" --block-length 3
```

`online-jsonl` 已实现，但 setup 和请求必须来自通过碰撞/时钟资格的 supervisor。一个持久进程保持 plan→完整 observe→下一 plan，不能每次请求重新启动从而清空风险账本。启动命令为：

```bash
python -m gsl_recovery.v2_cli online-jsonl \
  --model "$GSL_RUN_ROOT/seed_23/projected_evidence/model" \
  --setup "$GSL_RUN_ROOT/online_setup.json" \
  --log "$GSL_RUN_ROOT/online_events.jsonl"
```

这里 `online_setup.json` 不是已有生成命令的输出。Codex supervisor 必须按 `run_jsonl_v2` 的实际 schema 写入候选坐标、机制、seed、draws、eig_draws、wall_seconds、variant、m2_variant、guard_path、max_flips、require_physical；工程会话 `require_physical=false`，原生会话必须为 true。请求只允许 `op/action_blocks/navigation_qualified/observations/costs`。不得加入真源、未来完整风场或实际候选响应库。未准备 setup/supervisor 时，此命令属于接口接入任务，不伪称原生 ROS 已运行。

## 7. S2：实际查询资格与后续原生接入

最新原始包 `FSR_S2_CH4_DAY_NIGHT_PRO_REVIEW_20261022.zip` 大小 423,444,765 字节，SHA256：

`2a53659d5d50918cb4588aae3f7089432776d22a3ec6de9133a6004781966d55`

其已解压发布根目录在当前环境可执行：

```bash
export GSL_S2_RELEASE_ROOT="$GSL_DATA_ROOT/s2_review/FSR_S2_CH4_DAY_NIGHT_PRO_REVIEW_20261022/evidence/01_current_stage/NIGHT_RELEASE_ONLY_COLDQA"
python -m gsl_recovery.data.s2_v2 \
  --release-root "$GSL_S2_RELEASE_ROOT" \
  --out "$GSL_RUN_ROOT/s2_interface"
```

预期是 `PASS_ACTUAL_S2_LOCAL_QUERY_INTERFACE`，检查实际 DAY/NIGHT 局地点 gas/wind、NULL、域外和超过 20 秒拒绝。该程序不会读取 private_labels，也不重跑模拟器。原包 `verify_review.py` 的保存数值重算收据另在 `docs/data/`。

当前是一几何一源、DAY/NIGHT 两种静态诊断风条件各 20 秒，不是多源或两个独立 plume seed。热风空间速度 RMSE 约 0.02315/0.02851 m/s，超过原 0.02 门；全域动量、外域等门未通过。因此禁止把这项接口收据写成湖岸迁移、热力湖陆风或主动定位科学验证。

## 8. T1–T4 与进一步消融：必须补齐的实现任务

| 类别 | 要比较的监督 | 当前完成状态 | Codex 后续具体交付 |
|---|---|---|---|
| T1 | 全场/三维状态重建或辅助状态目标 | 有 field-conditioned teacher；没有全场重建损失/decoder CLI | 只从 train 全场建立目标；补 decoder 与观测域资格；与同容量学生按公平预算比较，不在线读取全场 |
| T2 | 教师源后验 KL 蒸馏 | 尚无独立 T2 训练 arm | 固定源先验和支持，按同一正确联合模型条件化教师后验；比较校准、排名与换先验后行为，不误称未来生成器 |
| T3 | 源对证据及方向监督 | 已有六种控制与 endpoint-only | 先执行第 4 节；再实现纯 direction-only、错误方向/打乱源配对负控制，仍有密度锚 |
| T4 | 教师动作或价值蒸馏 | 已有学生 M3/EIG；没有教师动作蒸馏 loss | 比较合法信念条件下的教师价值，不模仿看到未来真风或真源的 oracle 动作 |
| HIB/高级层次信息瓶颈 | 候选信息表示控制 | `IMPLEMENTATION_TASK` | 先锁定具体母论文、随机变量、可计算算子与代码；没有方法级资格前不加入主贡献或虚写命令 |
| 原生导数 | Malliavin/边界事件项 | `BLOCKED_NATIVE_DERIVATIVE` | 在合格原生模拟器上插桩、验证失败边界和无偏/偏差合同；不能用代理自动微分替代该验收 |

T1/T2/T4 不是先验判负。其比较要回答“全场拟合、后验蒸馏、证据蒸馏、动作蒸馏各自保留了什么任务信息”，不能因为主选 T3 而故意给其他控制更小模型、更少数据或更差训练预算。

当前投影训练使用端点和一个中点方向项；Gauss–Legendre 路径计算用于目标一致性检查，不等于训练时已执行全路径密集微分监督。新方向消融应分别比较端点、端点+中点、端点+预注册多点，且加入后仍保持归一化分布锚。

## 9. 物理科学阶段：固定上限，先 3 个成本资格世界，再完整冻结

详见 `docs/data/HOUSE_TO_LAKESHORE_TRANSFER_CONTRACT.md`。当前没有 `prepare-native`、`generate-72-worlds` 或 ROS 自动部署子命令；这些是本地资产转换和调度实现任务，不得在回执中声称已经执行。

### 9.1 有限数据生成合同

总上限 72 个世界：3 个 House 几何×4 个地图预选源×2 个合格风程序×3 个独立 plume seed。复用已合格完整风序列，优先只重新生成 plume，不无期限追加 CFD。

先固定源点/风程序/seed/时间长度和读出协议，再生成 3 个成本资格 pilot，检查物理有效域、单位、时钟、恢复和存储成本；3 个计入 72，不额外膨胀样本。pilot 不用于选择最易定位的源或调定位阈值。涉及 House03 的 pilot 由独立 evaluator 做物理资格，只输出 pass/fail、成本和哈希，不把测试响应交给模型研发。

成本资格通过后冻结整个矩阵、目标与算力预算，一次性执行已登记批次：

- House01/02：各 2 源 train、1 源 development、1 源 source-holdout。
- train 源各风 seed0/1 用于拟合，seed2 检查未见 realization。
- House03 全部 24 世界保留为 geometry-holdout。
- 未见风最多另立 18 世界，模型冻结后独立评价。
- S2 只有 R19 的物理门通过才启动最多 24 个小区域世界；zero-shot、few-shot 和目标域从零训练分开报告。

72 个世界不是效果保证，也未必能为稀有退化事件给出足够窄的区间。结果无效或置信不足时结束该批次并如实判定，不不断加数据直到显著。

### 9.2 原生适配器必须交付的内容

Codex 先实现从合格原始资产到 `gsl_v2_dataset` 的单向转换器。输出包含已授权 episodes、候选支持、geometry、真实时钟/单位/读出协议、原始身份哈希；仅 train 的 world_index 可关联源无关外生 bank。转换器必须通过路径逃逸、错误单位、源依赖 bank、测试数据打开、realization 跨划分、缺局地风、越界查询与真假零混淆的拒绝测试。

物理 teacher 的每个 bank 原子必须由真实训练风程序/随机实现支撑；不能用绝对源标签、world ID 单热或实际真源气体场代替外生状态。低阶几何/时间抽样或压缩要记录误差资格，不把任意稀疏点集合宣传成已验证完整物理场。

只有这些资产门通过，才用相同 `train-teacher/build-targets/train-student/evaluate` 命令替换为物理 manifest；命令可复用不等于数据已具备资格。方向/路径穿越墙面、水面或其他源条件边界时，先做合法域与分段事件处理；未完成的路径明确 BLOCKED。

## 10. 资源保护与 checkpoint 恢复

每次运行前保留至少 4 GiB 主机 RAM、8 GiB 磁盘、2 GiB GPU 空闲余量；本机共享 GPU 更严格时采用更高余量。原训练代码的 CUDA 启动最低 512 MiB 检查不是合同全部资源保护；默认每进程 75% 显存限制也不能保证共享 GPU 无 OOM。Codex 调度器必须监控实际峰值和外部占用，串行运行大模型 arm，不自行并发多个 GPU 任务。

训练命令显式 `--wall-seconds 175`，检查在 batch 边界执行，不能称硬实时中断。必要时由本机 runner 施加额外进程上限；终止后只恢复最近完整 epoch 的 `resume/`。不得看到训练未完就抬高内存配额或删除其他任务。

现有 checkpoint 保存模型、Adam 状态、Torch/CUDA/NumPy RNG、完成 epoch、dual、manifest hash、target/teacher/bank binding。`--resume` 指向含 `trainer.pt/trainer.json` 的目录；只增加总 epoch cap 或墙钟 cap，不能改变数据、seed、目标、batch size、学习率、方向项或模型架构。恢复不兼容即停止，不能静默从权重重新开始却称连续训练。

可执行恢复示例：

```bash
python -m gsl_recovery.v2_cli train-student \
  --manifest "$GSL_RUN_ROOT/house_numerical_data/manifest.json" \
  --out "$GSL_RUN_ROOT/house_seed_23/nll" \
  --variant nll --epochs 40 --batch-size 8 --seed 23 \
  --device "$GSL_DEVICE" --wall-seconds 175 \
  --resume "$GSL_RUN_ROOT/house_seed_23/nll/resume"
```

仅在此前完成 epoch 小于 40 时执行；已完成 40 的运行不用重启。同目录恢复前复制已有 `training_curve.json` 和 `training_receipt.json` 到带段号的证据目录，因为续训会更新同目录曲线/回执；自动拼接旧曲线也不能代替原始分段证据。发生 batch 中途墙钟停止时，最终临时模型可能含部分 epoch 更新，只有 `resume/` 中完整 epoch 可作为一致恢复基点；不得把二者混用。

`build-targets/evaluate/demo` 暂无通用 CLI checkpoint；外层 runner 按完成的固定独立任务分块，保留不完整目录并重新运行该完整块。不能把部分 target 清单拼接后不更新 hash，也不能跨 active block 重用已消费计划或观测。

## 11. 评价矩阵、科学门槛与停止条件

### 11.1 A→A′→A′+B→A′+B′ 必须逐级对照

| 模块 | A | A′ | A′+B | A′+B′ |
|---|---|---|---|---|
| M1 | 冻结官方 PMFS 原前向/比较 | 合法 readout+同容量联合 NLL | 同学生的普通 teacher 分布迁移；加特权原子直接迁移控制 | 条件投影的源对证据+方向监督 |
| M2 | 官方原生更新 | nominal 历史联合推断 | 机制解释只用于新项 | 源—机制联合后验+撤销后缀重放 |
| M3 | 官方原生完整选点 | 相同学生的完整联合 EIG | 当前聚类分离迁移参考；母论文独立复现另列 | 风险约束反证+恢复列表+无功效 fallback |

官方 A 需要冻结 MAPIR/PMFS commit、配置、候选支持、观测轨迹和原生指标代码；现有 Python 方差核心、兼容分数或归一化概率不能替代整条原生 A。所有后续比较保留相同合法输入、观测预算和路径/动作执行约束。

模块归因顺序固定：先 M1 对同容量 NLL 和普通蒸馏取得独立证据；再固定 M1 比 M2；最后固定 M1/M2 比 M3。M2 把 M1 的损失救回不能写成 M1 已优于 NLL。所有 M3 基线记录实际模型调用数、完整 gas+wind EIG 抽样、码本抽样、规划耗时、航程与耗电代理；不能只比较同名 `draws` 而忽略不同隐藏成本。

### 11.2 冻结集与统计单位

最终留出在模型、阈值、候选支持、航线预算和停止规则冻结后只运行一次。每个物理世界下所有方法配对；窗口和不同导航访问不当独立样本。至少按 `(geometry, source, wind program)` 分层/成簇，对簇内独立 plume seed 保留配对结构，报告簇数和世界数；不能以海量时间窗制造窄区间。

评价主指标：真源 Top-1、MAP 误差、原协议 Top-5% 误差、真源对最强竞争源 margin、排名、后验 NLL/Brier/覆盖、错误高置信、原正确案例退化、未见源/风/几何分组。普通浓度 MSE 是辅助指标。

相对 MAP 改善定义为 `(baseline_mean - method_mean) / baseline_mean`；baseline_mean 为 0 时不报告相对改善，改报配对绝对误差。预注册物理科学成功门：

1. 相对完整原生 PMFS 的平均 MAP 误差下降至少 10%，配对簇级 95% CI 的改善下界大于 0。
2. 相对同容量 NLL 和普通分布蒸馏，主 M1 至少在预注册源间判别/定位指标上有独立正收益，不能只有 teacher-target MSE 改善。
3. 未见源与未见 realization 改善方向一致；单列未见风、未见几何，不能让一个室内案例的巨大收益掩盖湖岸/新几何退化。
4. 原方法 Top-1 正确的固定子集上，新增错误率的配对单侧 95% 上界不得超过预注册非劣界；本合同默认 5 个百分点。样本量不足以证明非劣就记 `INCONCLUSIVE`，不能将 `p>0.05` 写成无伤害。任何改变非劣界必须发生在冻结测试打开之前并说明科学依据。
5. 源后验可靠性、错误高置信和实际导航合法性不能出现未解释的严重退化。M2/M3 的辅助贡献必须各自超过更简单控制，且风险保证只在已核验适用条件内陈述。

当前 `evaluate` 输出逐例数据，但没有完整层次 bootstrap/多重比较报告命令。Codex 必须实现独立统计汇总器，固定重采样 seed、10,000 次配对簇重采样、原始 rows hash、主要比较和同时报告规则，评估后不可改主要指标。该统计实现属于必须补齐的分析任务，不伪造 `bootstrap-evaluate` 子命令。

### 11.3 一票停止条件

- 权限不明确、sealed test 被训练或目标生成打开、源/realization 跨 split、原始 hash 不符。
- 原生资格失败，真实源不在合法支持，坐标/几何/时钟/读出未对齐，缺风被伪造成静风。
- teacher 仅拟合浓度而在留出源的观测分布和源排序上不合格；不能继续用 M2/M3 复杂化掩盖。
- 标签、完整未来风或实际候选响应进入在线输入；诊断输出重复加入似然；计划看到真实未来后重选；旧证据重复消费。
- full-support rollout/延迟预算超限。不得通过删除低后验合法源或缩小真源可达域通过门；应优化实现或报告 `BLOCKED_FULL_SUPPORT_LATENCY`。
- 非有限损失/梯度、OOM、磁盘/RAM/GPU 保护失效、checkpoint/target binding 不符。
- 为追求触发而改变 α、污染预算、阈值、动作集合、评测源或评测窗口。

停止一个不合格科学分支不妨碍完成其他独立工程交付；所有失败仍进入最终表，不删掉以形成正结果。

## 12. 日志、证据和最终判决格式

每个 run 留存：代码 commit/dirty diff、命令原文、开始/结束 UTC、环境锁、设备、配置、授权原件、数据/划分/target/teacher/model hash、完整训练曲线及恢复段、逐例评估 rows、资源峰值、失败栈和停止原因。工程包不携带大量 evaluator 响应或 private_labels；共享小型收据和可复现实验身份。

每个主动 block 留存：查询前的历史账本 hash、模型/机制版本、候选支持、源—机制后验、完整预提交动作与时钟、风险账本、MC δ、污染预算、四层功效、恢复列表、实际观测 ID、被撤销和替换的后缀贡献、全量重算误差、fallback 原因。test/diagnosis 结果只作为动作与计算事件，不是新观测因子。

最终报告按以下独立层级判定，不合成一个“全部通过”：

| 判决 | 通过条件 | 当前可主张范围 |
|---|---|---|
| E1 工程算子 | 测试、归一化/投影/回放/风险算子检查通过 | 已有实现可核验；不是有效性结论 |
| E2 完整工程闭环 | 神经 M1→M2→M3→实际后端查询→账本循环 | 制造环境可执行 |
| D1 真实输入资格 | 授权/哈希/缺失/时钟/接口全部清楚 | House 数值训练、S2 真实局地读取分别报告 |
| P1 原生物理 teacher | 多源外生 bank、独立实现、读出与物理门通过 | 当前 BLOCKED |
| S1 冻结离线科学效果 | 主创新超过强控制，满足预注册统计门 | 当前未成立 |
| S2 冻结主动定位效果 | 公平原生闭环、至少 10% 稳定定位收益、无显著正确案例伤害 | 当前未成立 |
| F1 实飞 | 独立飞行安全/传感/时钟与现场协议 | 本合同没有声称已经执行 |

Codex 的第一轮完成条件是：E1/E2/D1 的所有可执行任务有真实收据；P1 的缺口定位到具体文件和字段；T1/T2/T4/HIB 等未实现项有明确代码任务与验收测试；不把尚未通过的科学门填成 PASS。达到工程完成后，按固定有限物理批次推进；结果可以是正、负或证据不足，不能靠修改问题和评测规则把它变成成功。

## 13. 交接末页：真实可执行基线与待补实现

**当前真实可执行：** 同容量 NLL、加大 hidden 的 NLL 容量控制、普通分布蒸馏、特权原子源对直接迁移、mean-log 控制、projected-evidence、去密度锚、endpoint-only；M2 的 Aprime/B/Bprime；M3 的完整联合 EIG、当前聚类分离参考、风险约束反证、min-Hamming、共同污染通道 minimax-EIG、uniform-channel-EIG。工程与数值数据上的执行不等于原生科学比较。

**需要新增实现或原生接入：** T1 全场重建监督、T2 独立后验蒸馏、T4 教师动作/价值蒸馏、HIB、direction-only/多路径方向负控制、原生 GADEN Malliavin/边界导数、合格物理 bank 自动转换、真实 ROS/GADEN supervisor、独立簇级统计汇总器和完整原生 A 的公平联跑。母论文完整复现与本包的有限迁移参考必须分列，不能以同名 `B` 声称全文算法已复现。


## 14. 本轮交付后的执行修订：先读真实结果再调度

`artifacts/v2/tests_final.xml` 为97 passed；七组M1、真实House两容量和六组主动配置的结果已写入 `IMPLEMENTATION_AUDIT_V2.md`。当前M1没有优于NLL，House未见源数值定位不合格，M3未触发。`target_degeneracy_audit.json` 显示工程bank被历史风识别到ESS近1，三种teacher证据标签几乎相同。

第4节三seed工程命令仍可用于环境移植复现，但**没有新代码/环境风险时不要自动把它重复作为科研实验**。不继续在此toy调超参数或生成另一toy追求正结果。实际后续工作从第3/7节物理资格与第8节缺失强基线开始；按有限物理批次合同推进。保留原评测的全候选支持、全部开发例和原sealed test权限。

快速完整工程入口为 `bash scripts/run_v2_reference.sh runs/v2_reference_01`；新active控制入口为 `python scripts/run_v2_active_controls.py --help`。它们只补足可复现性，不解除原生teacher或科学效果的BLOCKED/FAIL状态。
