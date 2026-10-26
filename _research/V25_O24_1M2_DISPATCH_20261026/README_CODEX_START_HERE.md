# V25 O24 原配置派发入口

**先执行 `CODEX_O24_RUN_CONTRACT_ZH.md`。** 当前基线为准确冻结 O24：D=.2、局地风/GMRF、全后验方差严格 <1 m²。

现有 SCREEN12 已登记全部12槽，不先盲跑12次。使用 `export_o24_protocol.py` 只读核对实际本地冻结目录，再用 `export_existing_screen12.py` 验证/导出已有完整运行档案。确有无法恢复的必要缺口才按合同新开原配置运行，并保留全部历史结果。

本目录包括：

- `O24_BASELINE_PROTOCOL_LOCK.json`：读取真实镜像后生成的完整配置/来源/指标协议，所有角色实际参数，不是人工猜值。
- `export_o24_protocol.py`：本机只读封存核验与独立收据导出。
- `export_existing_screen12.py`：原ZIP哈希验证和流式导出，不启动ROS。
- `CODEX_O24_RUN_CONTRACT_ZH.md`：本机执行顺序、必要补跑条件、完整回传接口及公平约束。
- `PROTOCOL_DIFFERENCES_ZH.md`：论文/作者公开启动/本地冻结的三种身份。
- `DISPATCH_MANIFEST.json`：文件哈希和派发状态。
- `VALIDATION_RECEIPT.json`：本轮廉价门检验记录，明确没有新增原生运行。

`execution_ready=false` 只表示 ChatGPT 当前没有核验本机Windows/VM资产和实时ROS状态，不能据此宣称已跑。Codex有用户授权，按合同完成本机门后继续即可。

公开仓库仅保存已授权的运行协议与工具；不在此发布新算法、未发表稿件或新原始数据。
