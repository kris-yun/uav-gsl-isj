# 新物理realization确认

判决：`FRESH_ENDPOINTS_COMPLETE`。

对象与干预：预测、接收计划、源和初态在气体输出前固定；6份原引擎。

结果：见FRESH_CONFIRMATION_RESULTS及Brier/MAE/RMSE完整表。

限制/反例：新初态同源同环境，不是新源、外部物理验证或完整方法增益。

证据：原生源码 `source/native/Simulations_native_with_state_access.cpp` 236–267评分、291–459输运、510–523模糊；`PMFSLib_frozen.cpp`19–86测量传播；`source/C/`同引擎插桩，全部SHA在清单。见同名主报告章节及CONTROLLED_FACTORIAL_CONTRASTS、SAME_BANK_READOUT_CONTRASTS、QUALIFIED_N_POINT、QUALIFIED_NATIVE、FRESH系列表。每张比较都固定源、观测、支持、评分，改变的算子单独标记；不得混用原生完整后验与五点候选权重。

下一步：先由PRO判定最小可否证完整原生候选对照，本轮不自动追加实验。
