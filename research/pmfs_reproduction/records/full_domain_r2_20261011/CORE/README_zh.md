# PMFS R2 一次性交付

先读 `FINAL_METHOD_NECESSITY_DECISION_zh.md` 和 `SEND_TO_PRO_zh.md`。本轮完成32几何粗源区域全覆盖、64三维参考、64原生点源前向、19已见观测与6预登记新观测，所有普通评分头及负例。没有新CFD、导航goal、网络训练、L修复或额外seed。原VM保持运行，原始R1/E3/B4冻结。

## 复核

解压CORE和RAW到短目录；安装Python+NumPy后运行：
```
python -B CORE/source/verify_r2.py --core CORE --raw RAW
```
只提供CORE也可复算1125份源后验、概率质量、源损失、覆盖与判决；提供RAW增加所有包内哈希、6580个已用/代表帧和280个固定实际受体PID查询的独立浮点复算。它不会连接VM、启动GADEN、ROS或新更新。`source/`其他文件是执行血统，**不要为复核运行生成脚本**。

## 数据组织

- `inference_inputs/`及`future_inference_inputs/`：冻结候选预测、过去观测与native测量地图；不含真源映射。两个目录共享同一预测SHA。
- `evaluation_only/`：真源、种子角色及事前未来选择；仅评价使用。
- `development_inference/`、`future_inference/`：1125份普通后验及真实native位置/方差，另75份N0快照。N0原生树结果不可与统一点源作纯读出效应相减。
- `PAIRED_SOURCE_METRICS.csv`、`FUTURE_PAIRED_SOURCE_METRICS.csv`：全部单源/区域损失、rank/ties、MAP、官方Top-5%、均值、1m邻域、最强错误区域。前缀20/35/50。区域NLL主端点和细格NLL明确分开。
- `RECEPTOR_METRICS`、`REFERENCE_SENSITIVITY`、`EVENT_EQUIVALENCE`及其FUTURE版本：受体预测、两参考敏感性和有限等价类。
- RAW `references/`、`observations/`：每银行94个实际使用/代表帧、全部1803帧的SHA/时间索引、完整45000数值查询、物理/RNG/参数与时间日志。未携带从未使用帧的原始字节，详见RAW_COVERAGE。
- RAW `N_POINT_ALL/`及`observations/*/N0/`：native随机状态、候选图、树、评分和后验；RAW `diagnostics/`逐源逐评分格贡献。
- `EXTERNAL_TASK_ARTIFACT_SHA256.csv`：外部本轮完整工件索引；未携带实际二进制/旧父银行的边界显式标记，不暗示它们可由ZIP独立重建。

源码差分合同只允许P3主配对的`readout`改变。576张图的独立普通logscore与真实native评分最大差1.95e−14；原生Top5的并列排序结果保留，不能假设跨实现完全相同。三项盲性及前缀测试均通过。

32粗源不等于447逐格源预测。447主要是地图评分/回填格；94个实际帧不等于完整1803原始帧全部装包。50测量块来自10停留位置，时间相关，未作为独立实验。所有0检出银行保留。
