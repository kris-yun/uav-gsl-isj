# 垂向状态与接收器高度

判决：`CONDITIONAL_FACTOR_SUPPORTED`。

对象与干预：V0取消所有垂向位移并保留原随机消耗；V1原生三维。

结果：B4 O1提高5.29696/4.95329；真实源事件Brier由.80/.60降至.19/0。

限制/反例：浮力、垂向风和噪声共同取消；没有单独证明浮力是根因。共享初态不是逐粒子配对噪声。

证据：原生源码 `source/native/Simulations_native_with_state_access.cpp` 236–267评分、291–459输运、510–523模糊；`PMFSLib_frozen.cpp`19–86测量传播；`source/C/`同引擎插桩，全部SHA在清单。见同名主报告章节及CONTROLLED_FACTORIAL_CONTRASTS、SAME_BANK_READOUT_CONTRASTS、QUALIFIED_N_POINT、QUALIFIED_NATIVE、FRESH系列表。每张比较都固定源、观测、支持、评分，改变的算子单独标记；不得混用原生完整后验与五点候选权重。

下一步：先由PRO判定最小可否证完整原生候选对照，本轮不自动追加实验。
