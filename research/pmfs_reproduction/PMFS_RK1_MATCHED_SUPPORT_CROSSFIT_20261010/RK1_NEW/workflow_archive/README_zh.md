# 工作流存档：不用重新运行生产器

实际实验入口已执行一次，权威文件为RK1_NEW/contract.json、PRE_RUN_CONTRACT_SHA256.txt、source/冻结源码及EXECUTION_LEDGER.json。此目录保留冻结、报告/图生成和打包代码，使用原Windows工作目录，不是包内新的实验入口。

报告/图脚本只读取结果。repair_figure_layout.py修复图C标签重叠，没有改核或预测。独立复算入口为包根verify_rk1_review_bundle.py；不要重新执行source/run_rk1.py、supervise_rk1.py或打包脚本。pre_execution_static_feasibility/与PRE_EXECUTION_SCIENTIFIC_REVIEW_zh.md是执行前原样文件，状态尚未执行的文字属于历史记录，不覆盖实际完成结果。
