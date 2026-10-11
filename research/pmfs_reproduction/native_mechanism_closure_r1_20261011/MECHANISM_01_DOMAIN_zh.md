# 活动域与物理可达性

判决：`CONDITIONAL_FACTOR_SUPPORTED`。

对象与干预：D0/D1同引擎干预；固定V0/V1、源、观测、读出和评分。

结果：B4 O1 C7−K2提高4.83370/4.49003；两参考方向一致。

限制/反例：D0是人为附加导航限制而非新CFD环境，不能当真实风场扰动；原生与参考其他差异未全部匹配。

证据：原生源码 `source/native/Simulations_native_with_state_access.cpp` 236–267评分、291–459输运、510–523模糊；`PMFSLib_frozen.cpp`19–86测量传播；`source/C/`同引擎插桩，全部SHA在清单。见同名主报告章节及CONTROLLED_FACTORIAL_CONTRASTS、SAME_BANK_READOUT_CONTRASTS、QUALIFIED_N_POINT、QUALIFIED_NATIVE、FRESH系列表。每张比较都固定源、观测、支持、评分，改变的算子单独标记；不得混用原生完整后验与五点候选权重。

下一步：先由PRO判定最小可否证完整原生候选对照，本轮不自动追加实验。
