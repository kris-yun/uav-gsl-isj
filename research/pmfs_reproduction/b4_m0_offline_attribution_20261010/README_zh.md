# B4-M0冻结空间证据审核包

仅使用已完成B4的三次原生更新。包内保留所有388张候选的模糊前后命中图、释放采样点、RNG状态、原始评分、粗/细树和后验，以及50块原始测量记录。

- `B4_M0_EVIDENCE_ATTRIBUTION_zh.md`：中文结论、评分公式、分区及配对评分边界。
- `derived/`：全部逐格/分区贡献、三次树路径、测量覆盖、3×3条件评分与结果JSON。
- `figures/`：真实冻结网格上的PNG/PDF诊断图。
- `evidence/`：原始证据字节副本；父清单完整保留，但该目录是父包子集，不应直接对其运行父包全量核验程序。
- `INPUT_PROVENANCE.csv`：每个复制文件与父证据SHA256的对应。
- `verify_m0.py`、`independent_scalar_check.py`：默认只读，不启动ROS、VM、GADEN或训练，不写缓存。

复核（Python+NumPy）：

```powershell
python -X utf8 verify_m0.py
python -X utf8 independent_scalar_check.py
```

主脚本验证包清单、重算388评分/3后验、逐项比较JSON和15份CSV；标量脚本不导入主脚本，以45位Decimal独立验证评分。若需重新导出算术结果，显式指定包外新目录：`--write-derived <新目录>`。不要改动冻结证据。

官方B4已收敛于错误位置的事实保持；本轮物理根因HOLD。3×3表是条件评分，不是新原生分支、不产生新定位成绩。

本B4-M0与历史已经STOP的M0机制无关。结束后不继续新的实验。
