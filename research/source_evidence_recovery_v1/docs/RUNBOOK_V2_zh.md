# V2 中文运行指南

## 1. 先运行什么

GitHub 分支为 `research/source-evidence-recovery-v2-distill`，在仓库内仍进入 `research/source_evidence_recovery_v1/`。ZIP 解压后直接进入工程根目录。V1 文件与负结果保留，V2 文档在 `docs/`，V2 新实验在 `artifacts/v2/`。

```bash
git fetch origin research/source-evidence-recovery-v2-distill
git switch research/source-evidence-recovery-v2-distill
cd research/source_evidence_recovery_v1
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
python -m gsl_recovery.v2_cli doctor --out runs/v2_doctor.json
python -m pytest -q --junitxml=runs/v2_tests.xml
```

这是本轮实际验证的 CPU 依赖路线。GPU 请按本机驱动与官方 PyTorch 安装选择器安装相容版本，先运行 doctor；当前没有访问 RTX 5060 或 3090，不提供未测显存/速度承诺。

## 2. 一条命令完整复跑工程流程

```bash
bash scripts/run_v2_reference.sh runs/v2_reference_01
```

它按次序执行环境诊断、全测试、明确标注的制造环境数据、物理场条件代理教师、投影目标、七组同容量学生控制、开发评价与 M1/M2/M3 主动闭环。输出目录须全新。该脚本是实现验证；它不会自动将数据改为物理合格，也不会自动读取原 House 测试响应。

本轮实际执行了对应单独命令、七组矩阵脚本和主动闭环，详见审计。不要将这个入口脚本的存在单独写成已在用户 GPU/ROS 上跑完。

## 3. 使用已有 checkpoint

ZIP 和分支包含制造环境教师/学生及小型 checkpoint。学生部署只需 `model/` 中的配置、几何与权重，不需要 teacher bank。

```bash
python -m gsl_recovery.v2_cli evaluate \
  --manifest artifacts/v2/engineering_data/manifest.json \
  --model artifacts/v2/engineering_matrix/projected_evidence/model \
  --out runs/v2_replay_development

python -m gsl_recovery.v2_cli demo \
  --model artifacts/v2/engineering_matrix/projected_evidence/model \
  --out runs/v2_active_replay --rounds 3 --draws 512 --eig-draws 16 \
  --variant Bprime --m2 Bprime
```

生成 `plan_00.json` 等计划在环境查询之前落盘；`events.json` 保存动作、回放、概率地图和反证判决。`receipt.json` 中的真源只属于评价器，不在规划输入。模型重载检查权重与配置哈希；训练恢复还检查数据、教师和目标绑定。

## 4. 真实 House 数据

House02 已按原授权读取96个训练 cube和96个开发 cube，原96个测试 cube未读。训练使用每个训练 cube两种预登记稀疏探针表，共192条训练序列；开发只用一条表。

这份资产缺少合格物理秒和局地风，因此只能进行 `NUMERICAL_ONLY` 数值学习。实际读出为原四格池化数值，连续模型在原第一阈值0.1处分为未检出质量与正浓度密度；不能解释为真实传感器已完成标定。学生 online 加载器会拒绝它。

原始/派生 House 响应文件不随公开源码重新分发。包内保留 manifest、协议、哈希、训练收据与开发结果；按完整合同第3和5节从获授权原ZIP重新导出即可。转换命令是：

```bash
python -m gsl_recovery.data.house_v2 --archive /实际路径/HOUSE02_3D_JOINT_EVIDENCE_SIX_CONTROLS_20261020_VERIFIED.zip --out runs/house_export --test-fold 0 --dev-fold 1
python -m gsl_recovery.v2_cli prepare-house --export-root runs/house_export --out runs/house_numerical
python -m gsl_recovery.v2_cli train-student --manifest runs/house_numerical/manifest.json --out runs/house_student --variant nll --epochs 40 --seed 23 --device cpu
python -m gsl_recovery.v2_cli evaluate --manifest runs/house_numerical/manifest.json --model runs/house_student/model --out runs/house_development
```

完整科学训练方案、有限新增物理世界、未见House/风/源和S2转移见 `CODEX_EXPERIMENT_CONTRACT_V2.md` 与 `data/HOUSE_TO_LAKESHORE_TRANSFER_CONTRACT.md`。记录编号不能改名为秒，缺失风不能补成实测静风。

## 5. M2/M3 单独消融与未知机制

M2：`demo --m2 Aprime` 为名义机制，`B` 只解释新因子，`Bprime`完整后缀回放。B分支回放完整重算误差为null，而不是伪造0。

M3：`--variant Aprime`使用完整风气联合EIG；`B`为动作相关聚类；`Bprime`为风险反证与列表恢复；原有其他气体词基线仍在planner层。没有净认证功效时，Bprime回退完整EIG，并明确保存回退原因，不能算反证成功。

```bash
python -m gsl_recovery.v2_cli calibrate-adequacy \
  --manifest artifacts/v2/engineering_data/manifest.json \
  --model artifacts/v2/engineering_matrix/projected_evidence/model \
  --out runs/adequacy.json --block-length 3
```

校准只用开发组，每个lineage一次；它是未知/失配诊断，不是跨域误报保证，不是新的似然因子。`online-jsonl` setup中填写 `guard_path` 才会启用；默认demo不自动加载。

## 6. 原生在线接口

`python -m gsl_recovery.v2_cli online-jsonl --model ... --setup ... --log ...` 从stdin逐行接收JSON。setup包含合法候选、固定机制、种子、样本数、M2/M3变体与可选guard。

先发送 `op=plan`、导航已资格化的 `action_blocks` 与 `navigation_qualified=true`，取得整个承诺动作块。执行之后发送 `op=observe` 与原始观测列表。一个block必须完整回传、ID唯一、时间顺序合法；session跨轮复用。输入不接受 `truth_source`、未来实测风、oracle响应库等额外字段。二维概率输出含 x/y轴、probability_mass与candidate_support。

ROS本机接入必须实际完成飞控/导航可达性、动作时间、坐标系、传感器响应和故障停车合同。Python字段为真不等于这些物理检查已经完成。当前S2适配器已读通实际发布包，但它只有单源20s冷态范围，不能直接把House数值学生部署上去宣称湖岸主动提升。

## 7. 完成与停止

读 `training_receipt.json` 的状态；进程退出0但 `STOP_WALL_BUDGET` 不是训练完成，先恢复最近完整epoch。非有限loss、数据血统冲突、原test越权访问、原生物理门失败立即停止对应科学结论并保留日志。

第一轮真实结果有负结果：工程M1监督没有优于普通NLL，House未见源数值任务未获得有效定位，M3完整演示全部回退EIG。不能通过更换开发集、缩小候选支持或放宽风险门把它们改写为成功。此工程的用途是可复现地检验候选算子并准备合格物理实验，不是现成可宣称SCI二区效果的模型。
