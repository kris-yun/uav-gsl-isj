# 审核包使用说明

先读`STATIC_AUDIT_REPORT_zh.md`，再看两份CSV、`MINIMAL_TWO_SCENARIO_PLAN.md`与`FAILURE_MECHANISM_TEST_CONTRACT.md`。本轮是静态筛选，无新定位或气体生成成绩。

在解压目录运行：

```text
python verify_static_inventory.py
```

需要NumPy、Pillow、PyYAML。默认只读取包内文件：重构20套二维支持、复算3份完整原始CFD、核验77份记录文件头和76份安装配置，再查SHA256清单；不启动VM、ROS、编译或模拟。

原始输入仍在本机对应路径时，可运行`python verify_static_inventory.py --recheck-local`重核812项本地/Git原始资产哈希。该选项不连接VM，也不生成文件；某原件已迁移时会明确失败，不拿缺失原件算PASS。

`SOURCE_ASSET_HASHES.json`是原始来源哈希；`SHA256_MANIFEST.json`是包内交付文件哈希，两者不可混用。`SELECTED_RAW_ASSET_INDEX.json`列E3/B4附带的原件。`BUNDLE_COMPACT_PATH_INDEX.json`将长配置/文件路径映射为较短包内文件名，以方便Windows解压；原始内容保持相同。

PMFS原件链接锚点：

- [PMFS配置，固定提交](https://github.com/MAPIRlab/GasSourceLocalization/tree/4e141e162551e674f2f30ddb8859136c72139aac/Environment_config/PMFS)
- [GADEN test_env，固定提交](https://github.com/MAPIRlab/gaden/tree/ccb02e959a45a188e4b6c78792e197633fc64f1c/test_env)

本次使用本地固定Git对象和现存数据，未下载任何新数据。已有VGR的来源在本地路径、原始文件头及哈希中逐项列示；不把旧适配器生成记录冒称作者原始定位实验。

`code/`保存审计过程脚本。它们用于追溯原始盘点，含本机路径；跨机器复核请使用上述默认只读验证器。SSH授权信息、私钥和remote helper均不在包内。R7/D0/D1没有再打包为新实验，其冻结保全结果见`FROZEN_RESULTS_PRESERVATION.json`。

结论：静态审核GO；新病例执行HOLD；物理机制HOLD。两场景方案等待独立审核，不自动产生新的realization或原生goal。
