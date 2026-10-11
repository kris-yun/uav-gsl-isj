# PMFS研究审查与最小实验交接包

先读`研究决策与证据边界_20261010.md`，再读`下一轮Codex最小鉴别实验_待执行.md`。

`probability_semantics_counterexample.py`是公式级、单测点、独立Bernoulli观测反例，不是B4复现。运行：

```bash
python probability_semantics_counterexample.py --out ./counterexample_output
```

CSV/JSON给出已实际计算的结果。`b4_block_observation_check.json`是本次对B4块事件的读取核查。

特别注意：`original_package_verifier_stdout.json`是用户原M1核验脚本输出，其中`new_forward_calls=6`指历史M1包中的计算，不指本次新运行。以`execution_scope.json`区分本次实际执行范围。

本包不包含新GADEN参考、不包含新定位成绩或已验证主创新。没有改动原论文/开题报告、原GitHub或旧停止判决。
