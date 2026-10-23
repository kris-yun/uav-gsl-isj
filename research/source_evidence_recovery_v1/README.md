# Source Evidence Recovery V1

可执行的无人机气源概率定位研究候选，冻结三个模块：

- **M1 主创新候选**：源证据微分监督的联合观测生成器。
- **M2 辅助创新候选**：机制差分诊断与可撤销证据回放。
- **M3 辅助创新候选**：容错反证观测与可恢复列表规划。

目标是竞争源可辨识性和可靠证据驱动的主动纠错，输出保留二维源概率地图。这里交付可运行参考工程和可执行验证合同，不声称已取得新的 House / 湖岸定位提升。

## 开始运行

Python 3.12 推荐；参考实现只需要 CPU。进入本目录后：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
bash scripts/run_reference_suite.sh
```

该脚本实际运行单元/集成测试、原生 B4 快照复算、M1/M2 训练、离线概率定位、三模块主动闭环和消融矩阵。已有测试收据在 `artifacts/`。完整主动消融矩阵另用：

```bash
python -m gsl_recovery matrix --manifest runs/reference_v1/data/manifest.json --config configs/controlled_matrix.yaml --out runs/full_active_matrix --active
```

## 必读文件

| 文件 | 用途 |
|---|---|
| `RUNBOOK_zh.md` | 中文安装、命令、输入格式和接入说明 |
| `CODEX_EXPERIMENT_CONTRACT.md` | 冻结实验链、权限、指标、停止条件及最终判决 |
| `THEORY_AND_PROOFS.md` | 完整方法和条件性理论证明 |
| `IMPLEMENTATION_AUDIT.md` | 实际完成状态、真实运行收据与 BLOCKED 位置 |
| `docs/METHOD_FRAMEWORK_V1.pptx` | 基于原 PMFS 图修改的两页可编辑图 |
| `docs/INDEPENDENT_NOVELTY_REVIEW.md` | 跨领域迁移、两轮质疑、设计评分 |
| `docs/FINAL_REDTEAM_REVIEW.md` | 独立源码及数据资格审查 |

## 工程范围

`src/gsl_recovery/` 下包含 `data`、`m1_teacher`、`m1_generator`、`m2_diagnosis`、`m2_replay`、`m3_codebook`、`m3_planner`、`posterior`、`navigation`、`evaluation`。`examples/native_b4` 是从公开冻结项目提交读取并验证 Git blob SHA 的真实 PMFS B4 最终更新快照。它不是新生成的 plume，也不是新的实验胜利。

M1 教师目前在可解析受控传播/读出后端上完成：风保持提升、散度项、自然噪声分支边界、可训练弱 score 损失均有代码和测试。原生 GADEN 的候选条件潜状态、自然噪声 JVP/VJP、分支轨迹和高维提升尚未接通；真实数据 B/B′ 训练会显式停止，不能自动改用受控教师。

M2 精确枚举是正确性参照，诊断提议的计算增益必须在同预算实验中证明。M3 使用整块联合软码本、风险约束和全源挑战，不靠事后真值选点；当没有可证明净反证功效时，会弃权并退回联合 EIG。擦除 LP 已实现，但原始缺测读数进入 M1 的完整闭环尚未实现。

## 外部文献和代码范围

代码为本任务实现的研究适配器，并非四篇母论文官方代码的完整复现。母来源依次为随机分析/扩散条件控制、物理逆图形学、生物扰动靶点识别、信息论主动假设检验。具体题录、原算子和二次创新见理论文档及独立审核；普通 NLL、贝叶斯归一化、积分和 replay 恒等式不单独声称原创。

## 数据与证据

训练、开发、校准、工程留出及最终科学留出必须区分。这里受控留出仅用于工程和算法诊断；已经在本轮查看，不是未来论文的盲测集。真实 House/湖岸最终集不得由这些参考测试结果反向调整。禁止把 `evaluation_only`、未来真实风、真实源标签或实际未来响应库传给规划器。
