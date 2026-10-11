# 原始观测与预测定义

|对象|定义/单位|信息来源|允许用途|
|---|---|---|---|
|气体物理状态|native filament位置、sigma、源强，3D世界米/cm/摩尔参数按GADEN源码|新源条件bank原始快照|受控模拟参考；不是真实实验验证|
|PID原始读数|GADEN SampleConcentration，3σ和LOS，单gas float累加，ppm|实际受体时刻/高度|相同响应和阈值的原始观测预测|
|测量块|该次实际消费的1条gas float均值；2条wind共变量|消费者/CDR/原生block|严格 `>0.1 ppm`事件|
|事件概率p|每源2个reference的逐块检出预测，(k+0.5)/3|独立源条件实现|边缘复合log及Brier；非联合后验|
|累计信念图|native inverse sensor model累计logOdds和confidence|50块同一covariates|相同PMFSLib输出；非检出频率|
|3D全格命中频率|实际50时刻每自由格nativeppm>0.1的均值|诊断oracle全场查询|故意未对齐对照；非2D占用频率|
|原生2D hitMap|每模拟步至少一丝团占据该格的频率|冻结B4/M1历史|原生基线；不能随意转ppm|
|对齐参考图|源条件受体事件通过同一native建图后，2reference平均|相同轨迹、图核、占据和TO风|447相关格的描述MSE|
|连续浓度条件|额外保存原始ppm逐块值|同一8bank|仅信息增强档案，未选新的连续评分|

所有8bank共用原B4传感器位置和风共变量。没有在新源条件下重新模拟运动或改变风测量；这是条件于已有轨迹/TO风的比较，不是新闭环预测。源高−0.5m，受体高−0.20000000298m；PMFS二维图在水平坐标上，不能用图z占位代替真实传感器高度。

原始成员49块唯一，block40两候选并行核验，分支一致不代表原生成员身份已被恢复。native图只回放测量更新，无候选随机模拟/自适应细分/后验更新。

`REALIZATION_EVENT_COUNTS.csv` 使用distinct_stops字段，表示10处不同停留，**不是10个独立统计样本**。statistical unit为整份物理随机实现；8份中4份reference、4份holdout。

未对齐与对齐的数值尺度不同，不能相减为效果量。合成Bernoulli、B4原生2D、当前3D两源参考属于不同层级，不拼成一个所谓定位准确率表。
