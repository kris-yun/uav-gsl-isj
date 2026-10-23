# 源对辨识条件审计：复算入口

先读项目根目录 `SOURCE_PAIR_OBSERVABILITY_AUDIT.md`。本包保留上一轮V7负结果，不代表新算法通过。

## 不依赖原始气体归档的核验

使用Python 3.12以及根目录 `requirements-tested.txt` 的固定版本，在解压后的项目根目录执行：

```powershell
python native/observability_20261023/verify_audit.py
```

该命令读取包内已导出的四份TRAIN数组、唯一已冻结DEV窗口、原模型与旧结果，复算624项TRAIN标量分数、TRAIN门限统计及92项DEV评分。它不会打开本机原始气体世界，不会生成气体或运行ROS。它会在该解压副本内重新写入QA收据及描述性表。

ZIP内 `MANIFEST_SHA256.json` 记录每个载荷的SHA256；先验哈希应在复算前检查，核验命令可能改写自己生成的QA文件。`DELIVERY_RECEIPT.json` 记录交付提交和范围。

## 原始查询与评分的记录

`PROTOCOL.json` 是事前诊断规则；结果目录中的 `INPUT_FREEZE.json`、`SELECTION_FREEZE.json`、`DEV_MODEL_FREEZE.json` 分别固定输入、唯一测点组合和DEV前模型。`PRE_ANALYSIS_SCOPE_CORRECTION.json` 记录第一次TRAIN评分前对不适用增益控制的纠正。

- `extract_train.py`：只能读取原allowlist中的四个TRAIN世界，每帧先核对SHA。
- `analyze_train.py`：19个窗口、435个测点对，进行整实现交叉诊断与一次选择冻结。
- `check_selected_dev.py`：冻结普通模板；`evaluate`仅查询所选的一个窗口。旧DEV已经开放，不能称盲测。
- `m1_structure_audit.py`：原覆盖饱和、编码损失和数学反例诊断，不训练新M1。
- `verify_audit.py`：独立标量核验，建议外部复核只执行此入口。
- `finalize_audit.py`：整理已完成结果，不运行新物理。

原始完整气体帧未重复塞入ZIP。重新执行提取需要原本机归档、原占据图与已验收C++读出组件，路径和SHA均有收据。不要为了复算而替换气体生成器或悄悄扩大授权目录。

`NEXT_SINGLE_FROZEN_PROPOSAL.md` 只是同高三源的下一步提案，不含自动执行授权。本轮至此结束，不启动新世界、M2/M3或ROS。
