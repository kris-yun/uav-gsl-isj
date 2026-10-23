# V7：竞争源判别与主动反证定位

本工程按用户最新 V7 建议重新组织：先独立发现跨领域机制，再比较候选 X，最后形成 **一个主创新候选 + 两个辅助候选**。它保留二维源概率图与主动闭环，没有继续调参 V2 的 SBI/微分教师蒸馏。

## 已交付的算法

| 模块 | 具体运算 | 来源与本工程变化 |
|---|---|---|
| M1 源对覆盖镜像嗅觉通道 | 两侧因果滤波、整流、镜像相减；训练源对覆盖选通道；一个原始窗口只生成一个联合符号 | PNAS 2026 的双侧嗅觉计算；将中心线侧别任务改成多个竞争源的联合分布区分 |
| M2 返回方向管与双点几何 | 真实进入事件更新相对方向；不确定管约束动作中心；均值/梯度差与联合协方差确定双点间距、方向 | Nature 2026 的动态返回方向；新增面向竞争源的观测几何及管外复测 |
| M3 全候选付费反证审计 | 成对 KL/真实成本分配、后验独立覆盖、新后缀审计、可恢复列表反馈 | TIT 2025、非等成本 ASHT 与可预测似然审计；不删除低后验真源、不重复计数审计量 |

这是可运行研究原型，不是已证实三项独立定位增益的论文成果。真实静态 pilot 没有超过 raw-joint；156 个可控 episode 中，强基线与大多数消融都饱和。已知负结果完整保留。

## 从这里开始

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install -e .
python scripts/run_tests.py --out results/local_tests
gsl-v7 calibrate-control --out results/local_model --variant secondary --blocks 32
gsl-v7 demo --model results/local_model --out results/local_demo --wrong-prior --budget 300
```

没有 GPU 依赖。支持 Python ≥3.10；交付验证环境为 Python 3.12。若使用严格复现依赖，优先 Python 3.12。

完整冻结矩阵：

```bash
gsl-v7 control-matrix --config configs/control_matrix.yaml --out results/local_matrix
```

完整原生实验入口见 [CODEX_EXPERIMENT_CONTRACT_FINAL.md](docs/CODEX_EXPERIMENT_CONTRACT_FINAL.md)，中文操作见 [RUNBOOK_zh.md](RUNBOOK_zh.md)。

## 结果与边界

- `results/control_matrix_v7_frozen/`：13 变体 × 6 个解析世界 × 两种先验 = 156 episode；300 秒、相同两机，含逐世界 CSV 和原始观测账本。
- `results/ocb_static_v1/`：4 个开放开发世界、40 个相关快照；同一 TRAIN 冻结探针对，原始 joint Gaussian 40/40，新静态直方图 31/40。
- `results/bridge_demo/`：实际 JSONL 进程接口运行 6 步、57 秒，仍是解析 Level 1 后端。
- `results/final_tests/`：实际测试日志、JUnit、版本与源码 SHA256。
- `docs/METHOD_FRAMEWORK_FINAL.pptx`：基于用户原 PMFS 图元改造的三页原生可编辑图，非位图。

**BLOCKED 的是物理资格和原生 executor，不是把这些块假装成原生试验。**现有 OCB 切片约每 50 秒一帧，不支持高速双侧运动线索；House01 occupancy 原字节和局地风向量仍缺；ROS/GADEN 原生主动执行没有在本机跑通。详见 [NATIVE_INTEGRATION_CONTRACT.md](docs/NATIVE_INTEGRATION_CONTRACT.md)。

## 文件与接口

核心代码在 `src/gsl_discrimination/`：数据合同、M1、M2、M3、联合后验、导航与 JSONL 桥、评价、原始账本。`SynchronousBlock` 接收实际 CSV/NPZ；`calibrate-blocks`、`fit-geometry`、`replay-blocks` 在合格数据上可执行。`pmfs-map-replay` 是固定官方提交下的相容评分/方差算子移植，不冒称完整 PMFS/ROS 复现。

所有候选源坐标都出现在二维概率图输出中；同一 `(x,y)` 的候选质量会相加。不作空间插值，不把离散质量写成连续面积密度。

工程及理论边界详见 [IMPLEMENTATION_AND_EVIDENCE_AUDIT.md](docs/IMPLEMENTATION_AND_EVIDENCE_AUDIT.md)。
