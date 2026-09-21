# TNQC：终点决议建议与下一代闭环理论路线

这是对本轮八个问题及主创新定位的技术交付，不是导师签字，不是 V7 已通过，不是新算法闭环成绩。

先读 `docs/01_终点与证据规则.md`，再读 `docs/02_理论与闭环创新路线.md`。
`endpoint_contract_proposal.json` 是故意保留待核实字段的合同草案；不能把空字段填成猜测后标记通过。

## 本轮实际执行

- 精确枚举两个有限状态实验设计例子；单步源信息贪心与两步终端风险的差别是数学例子，不是 PMFS 成绩。
- 1,000 组局部 profile / Fisher Schur 恒等式数值检查。
- 共享 nuisance 与逐 cell 独立拟合的反例。

运行：

```bash
python -m pip install -r requirements.txt
python src/exact_identifiability_tests.py --out results/reproduced_exact_tests.json
python verify_package.py
```

没有执行：ROS/C++、当前 V7 replay、恢复 launch 的原始性核验、六例 300s、真实闭环。

当前 GitHub 获取失败；本轮 runtime 细节以用户提供的信息为条件。出处与文献状态在两份文档末尾。本包不重新打包上一轮 22 MB 合成数据，避免混淆新旧执行范围。
