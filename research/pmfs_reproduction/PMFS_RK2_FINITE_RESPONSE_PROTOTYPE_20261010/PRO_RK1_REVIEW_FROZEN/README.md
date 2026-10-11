# RK1独立审核与有限原型建议

先读 `RK1_独立审核与研究决策.md`；下一步方案见 `RK2_有限原型与单任务否证_待执行.md`。

本包没有新算法性能结果：只有已完成的独立数值复算、事后误差恒等式分析，以及尚未执行的原型方案。原RK1 ZIP不重复附带。

复算需用户原始RK1解压目录，NumPy；脚本不会导入producer或执行物理查询：

```sh
python -B independent_rk1_audit.py --root /path/to/extracted_RK1 --out /path/to/new_external_output
```

包内验证结果包括原版核验器的 `--deep --parent-deep` 输出以及第二个独立实现的重算。其作用是核查缓存到响应核、预测和指标，不等于重演CFD或气体传播物理真值。

原始输入：GitHub commit `210b94e5de0ab7e906136fd0765c3639f10103b2`；
RK1 ZIP SHA256 `c56daec4117cedf2503c8467402e78a852cc3d0f3bdca753830838a91b78c979`。

新原型、新任务及新增物理生成均未执行；没有写入GitHub。
