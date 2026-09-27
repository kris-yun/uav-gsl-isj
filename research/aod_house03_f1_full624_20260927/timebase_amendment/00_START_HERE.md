# AOD F1 时间阻断：独立复核与单次修订建议

日期：2026-09-27。

**原状态保留：AOD_F1_HOLD_TIMEBASE；科学判决为空。**

本包给出一种明确的继续方式：不改 GADEN 动力学或时钟，不重做 54,912 条 PMFS forward，在未读 target 浓度时，签署一次有记录的原生保存状态采样修订。该建议尚未被主线程批准，本包不授权生成 plume 或读取气体值。

先读 `01_REVIEW.pdf` 或 `01_REVIEW.docx`，然后看 `02_TIMEBASE_AMENDMENT_PROPOSED.md`。`03_CODEX_ONE_PASS_RESUME.txt` 是批准后的一次执行任务，不是新的科学 gate。

## 本次实做
- 核对原 ZIP SHA256 与 147 项文件哈希。
- 核对 54,912 个 bank 清单记录与原冻结 seed/key；未读取 VM 上的 1.90 GiB 原始 bank 本体。
- 用独立 Python 二进制32位时钟递推，逐项复现 986 个保存记录的时间、步号与风索引；零随机抽样。
- 检查完整 5,100 个积分时钟值，十个理想请求时间均无 1e-9 s 内的精确匹配。
- 复算原 HOLD，并给出一张明确标为待批准的十状态采样表；按已有路段长度核对新时刻的运动可行性。
- 没有运行 GADEN/PMFS、重训练网络、加载科学数组或计算定位分数与 CI。

## 运行只读复核
```bash
python 04_READONLY_AUDIT.py /path/to/AOD_HOUSE03_F1_FULL624_REVIEW_20260927.zip --out audit_output
```

该脚本只读取文本元数据和清单；科学数组只被流式哈希，不被解码。需要原上传 ZIP；本包不重复附入约32 MB的原包，不包含 unread House03 gas。

## 文件
- `01_REVIEW.pdf` / `.docx`：整合报告。
- `02_TIMEBASE_AMENDMENT_PROPOSED.md`：唯一建议的、尚未签署的时间合同修订。
- `03_CODEX_ONE_PASS_RESUME.txt`：审批与执行边界。
- `04_READONLY_AUDIT.py`：标准库可运行的只读复核。
- `05_AUDIT_OUTPUT/`：实算输出及草案采样表。
- `06_SOURCE_EXCERPTS.txt`：原包关键文件的带行号摘录。
- `07_INPUT_PROVENANCE.json`：输入哈希与范围。

**不将小于一秒的时间偏移说成物理上必然无影响；不将新采样定义追认为旧“精确50–500秒”合同已满足。**
