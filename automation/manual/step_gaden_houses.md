已完成House01的GADEN验证。现在请执行以下步骤：

**Step 1**: 运行House02 GADEN实验
修改run_iter11_gaden.py中的SCENARIOS，只保留House02的配置，然后运行。
命令: D:\Anaconda\python.exe scripts\run_iter11_gaden.py
输出: automation/results/iter11_gaden_house02.csv

**Step 2**: 运行House03 GADEN实验
同上，只保留House03配置。
输出: automation/results/iter11_gaden_house03.csv

**Step 3**: 生成汇总
运行完成后，脚本会自动生成iter11_gaden_summary.md。

**注意**:
- 每个house用1个种子(seed=0, start=-5,-5)快速验证
- 如果DQA_AS_V2表现不如DQA_AS，诚实记录，不要调参
- 重点关注median final error和success@2m

开始执行Step 1。
