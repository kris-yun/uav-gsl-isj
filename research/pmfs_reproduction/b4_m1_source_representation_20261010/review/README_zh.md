# B4-M1 审核包

先读 `B4_M1_INDEPENDENT_REVIEW_zh.md`。实际新增6次二维候选前向、2次原生锚点完全一致；错误1×1候选评分优势仍在。物理根因HOLD，未生成任何新三维气体数据或后验。

在解压目录运行：

```text
python -B verify_m1.py
python -B verify_m0_portable.py
python -B analyse_m1.py
```

需要Python 3与numpy。默认全部只读，不连接虚拟机，不运行ROS/GADEN，不写文件。`analyse_m1.py --write-derived`仅供在新的无派生输出副本中显式生成新结果；审核原包请勿使用该选项。

`frozen_M0/`是原M0包未改动副本，原始CSV及清单字节保持一致；新容差检查在包根目录。`source/`为隔离入口与保持原生函数体的模拟源码；`evidence/forwards/`包含所有6次新图、释放点、评分与随机状态。旧输入解析失败单独留档。

`M1_A_FROZEN_FORWARD_BUDGET.json`和预算说明是执行前冻结文件，仍保留当时WAIT状态；随后批准见`M1_A_USER_BUDGET_APPROVAL.json`，实际执行见`M1_A_EXECUTION_LEDGER.json`。不得将历史预算状态误读为本轮尚未执行。原输入解析修复有独立记录，不改原科学合同。

新原始评分、1788行逐格对照与区域表见`M1_A_RAW_SCORES.csv`、`M1_A_PER_CELL_DIFFERENCES.csv`、`M1_A_REGION_DIFFERENCES.csv`。所有比值为评分诊断，不是新算法定位成绩或独立物理似然。

`M1_B_MINIMAL_3D_REFERENCE_PLAN_zh.md`仅为下一关方案，不授权自动运行。所有历史STOP/HOLD和冻结开题保持不变。
