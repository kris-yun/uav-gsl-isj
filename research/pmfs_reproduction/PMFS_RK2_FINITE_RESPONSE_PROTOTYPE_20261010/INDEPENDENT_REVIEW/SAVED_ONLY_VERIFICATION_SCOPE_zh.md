# 只解压本轮 RK2 包的复核入口

`verify_rk2_saved_only.py` 不依赖父包、不导入原型代码、不运行拟合或 φ/LOS。命令：

```text
python -B verify_rk2_saved_only.py --root <本轮RK2实验目录> --out <新的外部QA目录>
```

输出目录必须尚不存在且位于实验目录之外。完整示例：

```text
python -B verify_rk2_saved_only.py --root ./RK2_NEW --out ../rk2_saved_only_qa
```

也可以由包总检查器调用此独立脚本自身的 `verify(root)`，返回 `(result, tables)`；无需导入任何 producer、模型或 infer 模块。

该检查会重算：7 项冻结源码 SHA、18 项准备输入 SHA、模型与候选预测冻结 SHA、30 个最终保存模型目标/梯度/KKT、72 项训练划分日志择优与容量、200 行候选响应与文件对应、16 个二值复合源评分/规范化/NLL/Top1、600 行压缩误差、1600 行成本汇总、模型容量及原注册 A 门。

其 PASS 仅表示**本轮保存数值与规范一致**。它不读取或验证 642 项外部父资产，不由 196 份参考缓存重建 X 和先验，不重新执行物理读出、信息隔离测试、方法拟合或运行测速。保存的 X/先验作为待审数值输入，不能因为其 KKT 成立就认定外部训练血统正确。

本轮另有 `verify_rk2.py --root <RK2目录> --parent <冻结RK1完整父包> --out <新外部目录>`，用于父输入 642 项 SHA 与 196 缓存→路由→X/先验的完整核验。两种检查的结果不得混写为同一复核范围。

本地已仅用本轮实验目录执行 saved-only 检查，判决 `PASS_SAVED_ONLY_RK2_NUMERICAL_RECOMPUTATION`；结果位于 `independent_rk2_saved_only_validation/`。
