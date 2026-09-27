# 2026-09-27文献选择：只选一个母算法

## 选中：双向循环门控（BRG）

Salehi S, Lei J, Benjamin AS, Müller KR, Kording KP. **Modeling attention and binding in the brain through bidirectional recurrent gating.** Nature Communications 17, 4072 (2026). Published 5 May 2026.
DOI: https://doi.org/10.1038/s41467-026-72146-9
作者代码: https://github.com/ssnio/bio-attention
已查看源码: https://raw.githubusercontent.com/ssnio/bio-attention/main/src/model.py

原论文：视觉系统中的bottom-up、top-down、lateral与memory，使用有界乘性调制；训练识别/分割等任务，不是已有GSL网络，也不以优于全部通用AI架构为结论。作者仓库GPL-3.0。本包没有复制该网络源码，而是独立实现小型候选匹配器；不可写成已复现作者全部实验。

我们的适配：把高层视觉任务cue替换为对每个候选都可计算的PMFS物理预测；网络共享参数，不输入真源提示或候选ID embedding；递归门控只发生在过去/当前可见信息内；完整源图再驱动原planner的候选分歧缓存。源定位中的有效性与二次创新仍待闭环比较。

## 为什么没选另外两篇更新的生物导航论文

1. Siliciano et al. **A vector-based strategy for olfactory navigation in Drosophila.** Nature 657, 443–454 (2026), published 22 July.
   https://doi.org/10.1038/s41586-026-10827-7
   研究气味走廊边界追踪、方向记忆与FC2。它很新，但不是完整源后验；直接迁移会改planner任务，离目前可比较的PMFS源图接口更远。不能声称它已解决房间内气源定位。
2. Ou et al. **Efficient robot navigation inspired by honeybee learning flights.** Nature 653, 1039–1046 (2026), published 13 May.
   https://doi.org/10.1038/s41586-026-10461-3
   https://github.com/tudelft/Bee-Nav
   小型神经网络与视觉归巢，已有真实机器人代码。它利用已知家位置/path integration提供训练目标；未知泄漏位置没有相同监督，不作为当前源推断首选。

## 不能忽略的邻近研究

- **Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference (DGSE-S).** 2026 preprint, submitted to T-RO, not verified accepted.
  https://arxiv.org/abs/2608.16221
  已有稀疏移动观测、概率wind/concentration/source序贯推断。因此“神经网络+概率源图”并非首次；本包不宣称首创这套框架。
- **PMFS: Particle Map for Source Localization.** 原始论文及实现。
  https://arxiv.org/abs/2304.08879
  https://github.com/MAPIRlab/GasSourceLocalization
  PMFS已有物理模拟、候选源概率和主动运动。新方法只改变源证据形成，不能把输出概率图或主动选择测点本身认领创新。

## 已核对的接口源码位置

公开humble分支：
- `.../PMFS/PMFS.cpp`: `processGasAndWindMeasurements`，native forward之后、`chooseGoalAndMove()`之前。
- `.../PMFS/MovingStatePMFS.cpp`: `informationValue`使用`simulations.varianceOfHitProb`；`calculateMutualInformationGas`使用coarse `resultsFirstLevel`，在该版本主要为可视化。
- `.../PMFS/internal/Simulations.hpp`: source map、variance与coarse缓存接口。
- `.../Common/Grid2D.hpp`: x+width*y、origin、cellSize、坐标变换。

这些是本次从公开源码核对的接口，不代表已与用户frozen fork逐行合并。完整ROS编译与实际闭环由Codex在原VM完成。

## 不预支创新

主创新成立需要：相同输入与物理forward预算下，闭环优于普通GRU/反馈关闭，并说明候选cue→反馈→证据整合的独立作用。仅胜classic PMFS可能含更丰富输入的收益；仅有最新发表年份不构成贡献。
