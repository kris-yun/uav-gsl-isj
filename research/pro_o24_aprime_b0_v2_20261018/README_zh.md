# PMFS O24 第二轮独立研究——使用方法

本目录全部文件只读运行，不写入/修改用户 O24 冻结源码，来源提交 `631145657461c41840f6844f118de57d1e747ea4`。下述实验均没有新气体世界、ROS 导航、PMFS 前向调用、模型训练或云端 Codex 任务。

## 文件

- `DECISION_zh.md`：最新量化裁决、正反证据及科学边界。
- `ASSET_LINEAGE_AND_ELIGIBILITY_zh.md`：旧 OCB S2X、E2、E2C 数据的状态与原始 GitHub 来源。
- `E2_OPEN_EXPORT_ONLY_HANDOFF_zh.md`：只导出 OPEN 旧数据的严格合同；用户可按需交给 Codex，不包含任何自动执行动作。
- `o24_cross_update_holdout.py`、`CROSS_UPDATE_HOLDOUT.json`：原生 O24 首次候选响应训练、后续更新留出测试。目录同时包含从上一轮逐字复制的 `o24_parity.py`，可独立读取原保存图。
- `o24_support_shift_ablation.py`、`SUPPORT_SHIFT_ABLATION.json`：普通新支持原生回退消融。
- `e2_open_response_adapter.py`：真正物理数据的接收门与旧 E2 开放发现集普通三臂评估；没有收到 E2 真实浓度时不得声称运行完成。
- `test_e2_contract.py`：完全隔离的合成数据+非法角色/时钟/哈希/单位测试，不会打开用户资产。

## 复算

```bash
# 本目录包含同一份 o24_parity.py，无需安装 ROS/GADEN
OPENBLAS_NUM_THREADS=2 python o24_cross_update_holdout.py \
    --zip /PATH/PMFS_O24_最终冻结_A2隔离补跑与五回合完整证据_V2_20261018.zip \
    --out CROSS_UPDATE_HOLDOUT_recomputed.json
OPENBLAS_NUM_THREADS=2 python o24_support_shift_ablation.py \
    --zip /PATH/PMFS_O24_最终冻结_A2隔离补跑与五回合完整证据_V2_20261018.zip \
    --out SUPPORT_SHIFT_ABLATION_recomputed.json
python test_e2_contract.py

# 仅当获得经审计的 E2 OPEN discovery ppm、完整时钟、放出率和校准值后
python e2_open_response_adapter.py \
    --manifest /E2_OPEN_EXPORT/manifest.csv \
    --probes /E2_OPEN_EXPORT/probes.csv \
    --timebase /E2_OPEN_EXPORT/timebase.csv \
    --root /E2_OPEN_EXPORT/ \
    --sigma-ppm CALIBRATED_VALUE \
    --out E2_ORDINARY_BASELINES.json
```

## 限制

此轮没有可用 E2 真实 ppm 数组，最后一个命令不是执行记录。GitHub 中已有的 O24 冻结代码未做改动。适配器需要外部验证 SHA 对应的真实原始求解器、2×2 采样算子和单位；仅校验字符串哈希本身不能证明科学物理正确。
