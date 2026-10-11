# RK2-B/B+审核包读取说明

这是一次已结束的24份固定物理实现连续验证。原B主门FAIL，全部登记分支均完成。详细机制组成因素已有算术证据；原始PMFS物理缺陷尚未由本轮证明。

推荐阅读顺序：

1. `SEND_TO_PRO_zh.txt`：可直接发送PRO的说明和三个决策问题。
2. `READOUT_TRANSFER_FAILURE_COMPONENT_zh.md`：11例物理零支持破坏的代码与分项证据。
3. `RK2B_CONTINUOUS_RESEARCH_REPORT_zh.md`：全部分支、物理合同、成本及反例。
4. `ORIGINAL_B_GATE_FINAL.json`、`SUMMARY_METRICS.csv`、`reference_transfer_error_attribution.csv`：精确数值。
5. `authorization`与`PREPHYSICAL_SOURCE_SHA256.json`：运行前合同与冻结源；`technical_repairs`保留技术错误及修复。

两个ZIP解压到不同目录。需要Python 3、NumPy、SciPy（原始环境版本写在PREFLIGHT.json）；独立复核不启动ROS、GADEN，不生成物理数据或拟合模型：

```
python CORE/source/verify_b.py CORE
python CORE/source/verify_raw_support_b.py CORE RAW
```

CORE含全部预测、标量观测、模型、原始参数与时间索引。RAW含1200份主查询原字节快照、600份参考phi缓存、24份原生查询/时间/RNG日志、3D占据和风场。完整43272帧银行留在FULL_BANK_PRESERVATION.json指定目录；本任务不删除未装包数据。

每包MANIFEST_SHA256.json纳入除自身之外全部文件，CSV复算采用数值容差；ZIP另有SHA256与解压验证结果。已有父RK2-A、RK1和历史STOP/HOLD不被覆盖。

本包生产脚本为环境绑定的完整运行血统，不是鼓励重复执行科学试验的一键入口。已冻结生产模块的SHA保持不变；最终报告/打包与独立复核脚本在运行后完善，未更改模型或端点。受控仿真的物理生成资格与主门统计成绩分别判定。
