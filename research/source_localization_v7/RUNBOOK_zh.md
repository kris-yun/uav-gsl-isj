# V7 中文运行指南

## 1. 安装与验证

在工程目录执行。Linux/macOS 使用下列 shell；Windows 可在 WSL 的相同目录运行。原始 GADEN 归档路径保留在原生接入合同中，不用替换全局 HOME 等环境变量。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install -e .
python scripts/run_tests.py --out results/my_tests
gsl-v7 --help
```

测试结果的判断依据是进程退出码、`pytest.log`、`junit.xml`，不是 README 中的预期数字。`TEST_RECEIPT.json` 保存依赖版本与所测源码哈希。

## 2. 跑完整闭环

```bash
gsl-v7 calibrate-control --variant secondary --blocks 32 --out results/my_model
gsl-v7 demo --model results/my_model --out results/my_demo --wrong-prior --budget 300
```

该后端是明确的解析构造：二维浓度均值、共享间歇扰动、受控传感器响应、三个固定机制。它用于检查历史→M1→联合后验→M2→M3→合法付费动作→新观测。不能将其成绩写成 GADEN、湖岸或真实飞行效果。

读取 `CONTROL_RESULT.json` 看最终状态，`online_steps.jsonl` 看每一步，`raw_ledger/events.jsonl` 与 NPZ 看实际读数，`source_probability_map.npz` 看二维源质量图。

## 3. 跑整个冻结矩阵

```bash
gsl-v7 control-matrix --config configs/control_matrix.yaml --out results/my_matrix
```

矩阵包含适配方差、raw-joint EIG、best-one、固定双通道、raw-joint 强基线、M2 独立消融、M3 成本/覆盖/审计消融及 full。首次写出配置冻结件；相同目录只允许按同配置接续，不覆盖已有 episode。

若比较方法需要不同动作，输入随机性按世界 seed/step 独立索引；这仍是受控模型的比较，不能代替在同一原生 plume realization 上执行不同策略。

## 4. 检查已经存在的 House/OCB 数据

```bash
python scripts/fetch_ocb_assets.py --output local_assets/ocb_x00
python scripts/check_native_assets.py --root local_assets/ocb_x00 --out results/ocb_input_audit.json
gsl-v7 qualify-ocb --root local_assets/ocb_x00 --out results/ocb_qualification.json
gsl-v7 static-pilot --root local_assets/ocb_x00 --out results/ocb_static_reproduction
```

下载脚本只读取固定提交、8 个已经开放的 discovery 世界、16 个已知文件。私有仓库认证由本地已有 GitHub 登录或 `GITHUB_TOKEN` 提供，脚本不打印 token。原始 arrays 不包含在科研 ZIP；同内容从固定版本恢复并逐个核对 SHA256/Git blob。

静态 pilot 保留旧 `legacy_per_cell` 设置用于复现原冻结结果；它不是当前默认 M1 平滑。禁止把此命令改成动态互相关试验；reader 会拒绝这种资格升级。

## 5. 原生窗口训练与固定回放

先按 `docs/NATIVE_INTEGRATION_CONTRACT.md` 完成坐标、occupancy、传感器、真实时钟和独立 realization 审查，并生成 `gsl-native-block-manifest-1` 清单。其字段见 `evaluation/block_pipeline.py`；能力证明必须为实质审查文件，不能仅把状态字符串改成 PASS。

```bash
gsl-v7 calibrate-blocks --manifest local_assets/native/train_dev_manifest.json --variant secondary --out results/native_model
gsl-v7 fit-geometry --manifest local_assets/native/train_dev_manifest.json --model results/native_model
gsl-v7 replay-blocks --manifest local_assets/native/train_dev_manifest.json --model results/native_model --split dev --out results/native_dev
```

`fit-geometry` 是普通 TRAIN-only RBF 响应拟合，为 M2 提供均值、梯度和协方差；不是新增创新。需要二维非共线中心、固定感测高度、完整 action catalog。独立世界上的空间线性化误差、梯度与协方差仍须检验。

后续 final 回放必须显式 `--split final`，且满足冻结合同。训练命令不会打开 final 观测文件。

## 6. 主动进程桥

先用已经实现的解析进程检查接口：

```bash
gsl-v7 live --model results/my_model --bridge '["python", "scripts/control_bridge_server.py", "--output", "results/bridge_backend"]' --out results/bridge_client --budget 60
```

实际执行使用无 shell 的命令数组。native executor 应实现 `describe` 和 `execute` 两个 JSONL 请求，返回原始块、实际时间/成本、运动历史与安全检查回执；客户端负责三模块和后验更新。`scripts/control_bridge_server.py` 是协议样例，不是 GADEN/ROS 的替身。真实本地 executor 尚需接入，具体任务与禁止 oracle 的边界见原生合同。

## 7. 原生 PMFS 算子回放

从官方运行导出 `measured_hit[T,C]`、`confidence[T,C]`、`predicted_hit[T,S,C]`、`source_xy[S,2]`，可附 `free_mask[C]`：

```bash
gsl-v7 pmfs-map-replay --maps local_assets/pmfs_maps.npz --out results/pmfs_operator
```

这条命令每帧重新计算并归一化地图相容分数，不乘旧后验。完整 PMFS 的感知、前向模拟与 ROS 导航仍应执行固定官方版本并单独保存日志。

## 8. 停止与续接

若缺数据、时钟不合格、action 契约变化、代价非有限、未覆盖机制、全部预测支持为零，程序应报错或输出 HOLD。先修输入合同或将相关科学结论降级，不能为完成矩阵填假值。每次运行用新目录；已冻结负结果保留。详细一次性研发计划见 `docs/CODEX_EXPERIMENT_CONTRACT_FINAL.md`。
