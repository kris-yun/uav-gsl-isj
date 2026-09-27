# ME-D0 后的具体改进：把幅度读出与 hit-map blur 分开

## 首先读
`ME_D0_幅度读出改进与证据报告.pdf`（9页，另附可编辑Word）。
然后看 `CODEX_NEXT_ACTION.txt`。本包不是新冻结实验，也不是一份继续寻找理论的任务书。

## 本轮结论
原判决 `ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE` 不变。
以下均为已经揭盲的 OPEN 数据上开展的**事后方法开发与机制诊断**。
原包中的普通B2已经显示连续幅度信息可用。本轮保持B2不变、仅使用已保存的rawu而非复用hit-map的模糊u，三个环境mean rank为1.333333 / 1.291667 / 1.208333；唯一Top-1为75% / 79.1667% / 79.1667%。
相对原B2多找对10/72条，未损害原B2正确target；改善集中4/18个environment–source单元。
2×2完整比较表明，当前排名改善来自去掉额外blur，不是footprint平均单独带来的收益。没有搜索sigma，没有删target。

## 包含内容
- PDF＋Word整合报告。
- `code/readout.py`：确定性平均计数、矩形采样区投影和原B2评分；不是已校准的后验。
- `code/test_readout.py`：8项确定性检查。
- `code/reproduce.py`：对原review ZIP检查hash、解压、执行全部事后诊断。不会启动ROS、GADEN、随机模拟或模型训练。
- `results/`：原评分复核、全部事后尝试、四格候选分数、源级结果、几何权重、独立整包重放检查。未成功的诊断同样保留。
- `evidence/`：原判决、原环境与target结果、带行号的源码与probe合同。
- `SHA256SUMS`：本包文件清单。

## 复现
需要Python 3.10+、numpy、pandas。原review ZIP不重复装入本包。
原ZIP SHA256必须是：
`7a3e436900ab2696c2d7148215cd58b6632a017e447583f77c9c864b56f9c56c`

```bash
python code/test_readout.py
python code/reproduce.py --review-zip /path/MARKED_ENCOUNTER_PMFS_D0_REVIEW_20260927.zip --out replay_out
```

已执行完整重放；12个主要CSV逐字节一致。原review的12,979项文件哈希均通过。
本轮新增plume=0、新forward=0、新训练=0、新随机抽样=0；未读取封存环境。

## 不允许的推论
- 不是将旧M的失败改成PASS。
- 不是证明二维粒子计数已经等于真实ppm。
- 不是证明“blur越少越好”、已获得全屋／新House泛化或概率校准。
- 不是主创新已确认；这是一个真实可实现且在OPEN数据有改善的方法构造。
- 不得直接将负SSE做未经标定的softmax并宣称可信后验，也不得与使用同一观测的B0任意相加。

所有读出尝试在结果揭盲后提出；四格分解在初步组合改善后补做。报告没有把它们包装成target-blind确认。
