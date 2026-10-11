# RK2-A新增结果审核包

**开发门PASS，收益小；B没有执行。**

先读 `SEND_TO_PRO_zh.txt` 和 `RK2_FINITE_PROTOTYPE_REPORT_zh.md`。源NLL约改善1.10%/1.22%，Top1均4/4，O03相对U有退化；L恢复F的二值候选读出，没有超越完整物理。原始结果、失败和回退全部保留。

- `RK2_NEW/`：完整一次修复后运行、模型、实际候选预测、冻结标量观测、原始表/日志。
- `FIRST_NUMERICAL_ATTEMPT_FROZEN/`：测试前KKT停止的第一次运行及原始源码，未覆盖。
- `INDEPENDENT_REVIEW/`：独立矩阵与源评分复核、实际源盲进程审计及审计初始化失败记录。
- `B_DESIGN_ONLY/`：只读几何设计和12份待批方案，生成数0。
- `PRO_RK1_REVIEW_FROZEN/`：用户Pro本次任务书原件。
- `verification/`：独立只读数值验证器，不导入原型、不拟合或生成物理。
- `workflow_source/`：准备、冻结、唯一数值修复、报告与打包代码。

旧RK1原始物理库没有再次复制。父ZIP与根清单SHA见 `PARENT_REFERENCE.json`。本新包可以自包含复算最终代数/分数；原始输入血统重验仍需旧RK1包。

仅本包（Python3+NumPy，psutil可选；输出目录须不存在）：

```text
python -B verify_bundle.py --root . --out ../rk2_saved_check
```

加旧父包复算196缓存路由/矩阵/先验及642外部SHA：

```text
python -B verify_bundle.py --root . --parent <旧RK1包解压目录> --out ../rk2_full_check
```

验证只读包文件；跨平台表格按数值容差比较，字节SHA仍严格。上面入口检查记录的源盲进程证据，不重新执行隔离审计。可选实际独立推断重验（只推断已有标量输入，不调用物理或训练，Windows本地运行库依赖可能不同）：

```text
python -B verification/audit_infer_process.py --package RK2_NEW --out ../rk2_infer_check
```

不要运行 `RK2_NEW/source/run_rk2.py` 来审核现有结果；它会重新拟合，超出本次一次A范围。没有正式闭环新结果或新独立物理任务；本包不是发表用的主创新确认。
