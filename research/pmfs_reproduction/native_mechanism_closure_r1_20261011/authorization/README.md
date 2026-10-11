# RK2-B审查与原生机制闭合总计划

本包由本轮实际只读审查和下一轮未执行任务书组成。不修改原始证据，不重判旧主门。

阅读顺序：
1. 00_直接转发Codex.txt
2. 02_本轮独立审核与推导.md
3. 01_Codex_原生机制闭合连续任务书.md
4. 03_文献边界与条件母理论.md

code/review_rk2b.py：给定原CORE和包外新目录，独立哈希/事件/分项算术；需要NumPy，无拟合/生成。
code/contract_guard.py：检查干预只改变事先许可的JSON字段；不替代真实运行血统。
code/controlled_contrasts.py：同合同2×2条件效应及交互；非显著性检验。
code/test_diagnostics.py：7项单元测试，已实际通过。

复算例：
```text
python -B code/review_rk2b.py /path/to/CORE /path/to/NEW_OUTPUT
python -B -m unittest discover -s code -p test_diagnostics.py -v
python -B code/contract_guard.py baseline.json run.json --allow factors.D
python -B code/controlled_contrasts.py quartet.csv new_contrasts.json
```

原CORE与RAW仍由用户本次上传的两个ZIP提供；本包不重复嵌套它们。evidence中的verify日志是本轮实际运行产物，不是下一轮计划的执行结果。manifest不包括自身。
