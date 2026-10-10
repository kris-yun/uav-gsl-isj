# 给独立分析者的阅读顺序

1. `REPORT_zh.md`：全部结果、分流、限制与资源偏差。
2. `SOURCE_DISCRIMINATION_PER_REALIZATION.csv`、`SAME_3D_BANK_UNMATCHED_ALIGNED_COMPARISON.csv`：核心数值。
3. `frozen_contract.json`、`SOURCE_BLIND_PRE_SCORE_LOCK.json`、`POST_SCORE_PRE_UNBLIND_SHA256.json`：预注册和评分冻结。
4. `OBSERVATION_AND_PREDICTION_DEFINITIONS_zh.md`、`observation_lineage/final_contract_delivery/`：精确观测血统。
5. `semantic_anchor/`、`event_map_anchor/`、`native_reference_evidence/`、`native_aligned_maps/`：原生记录和快照。
6. `verify_m2.py`：默认只读复算；使用 Python 3.10+、numpy即可，无ROS/VM要求。运行 `python -B verify_m2.py --root .`。

`execution_scripts/` 是实际执行的记录材料，不是审核入口；它包含会启动生成器的脚本，**复核时不要运行**。没有向外部人士发送消息，本ZIP由用户自行交给PRO。

包内 `SHA256_MANIFEST.json` 为最终文件清单；ZIP自身哈希在旁边的 `.sha256.txt`。轻量包仅含392个实际使用原始快照，全部14424帧哈希/时间已保存，完整银行仍在原VM。所有压缩内容按原字节保留，复核派生CSV使用数值容差而非平台换行字节假设。

当前结论是机制HOLD，而不是方法有效PASS；本轮已停止，没有自动追加试验。
