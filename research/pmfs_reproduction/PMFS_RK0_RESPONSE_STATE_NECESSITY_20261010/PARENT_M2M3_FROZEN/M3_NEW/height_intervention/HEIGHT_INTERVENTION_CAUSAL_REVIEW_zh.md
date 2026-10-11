# M3 补充：输入-only 风高度/二维柱闭合对照

## 完成结论

在相同冻结 B4 观测图、原生评分、两个 exactpoint 源和 native rollback 壁面规则下，仅替换二维候选模拟的 u/v 字段。原生 sensorplane 四份预测直接复用；本轮执行 sourceplane 与 free-column mean 共8份新预测，全部正常返回。

**两种先声明的替换均未纠正源偏好，反而部分加大错源优势。** 因而“只把风平面改到释放高度”或“只按整个自由柱均匀平均”不能解释掉本次主要判别错误。这个否证只针对所定义的两种候选无关闭合，不否定任意3D垂向输运模型。

| u/v输入 | T 错/真评分比 | W 错/真评分比 | 判别 |
|---|---:|---:|---|
| NATIVE_SENSOR_PLANE | 6604.960 | 10006.261 | 两状态均偏向错误 K2 |
| SOURCE_PLANE | 14715.081 | 10227.809 | 两状态均偏向错误 K2 |
| COLUMN_FREE_UNIFORM_MEAN | 21729.753 | 25553.938 | 两状态均偏向错误 K2 |

## 为什么不是简单的风输入工程错误

已有原生 u/v 与实际 sensorheight CFD10 场在447个自由格逐值最大差为0；两新字段均从同一冻结 CFD10 资产取出，不生成CFD、不选新风索引。SOURCE_PLANE固定z=-0.5m，是两候选共同的已知释放高度，未依据评分挑平面；其447个二维自由格中心均位于3D自由空间。COLUMN_FREE_UNIFORM_MEAN在每个固定XY位置上对全部既存自由CFD体素高度作均匀平均，候选无关，未用真源羽流给高度加权。

输入-only检查逐行核实：除u/v外，1530行所有列的字符串完全一致，地图占据、logOdds、omega、confidence、源候选、prior_posterior、坐标与格式值均不变。元数据、模拟参数、高斯2500表及随机初态也不变，运行使用原M3可执行文件，不重新编译、不改变壁面实现。

## 动力学与预算边界

录制步数仍为200，min/max warmup仍为200/500。源码按是否有粒子出界决定warmup是否稳定，这个实际终止行为可能随u/v变化。SOURCE_PLANE真源两状态达到maxwarmup=500，释放点3500，而其余10份对比预测为200步warmup、2000点。**没有人为改warmup，但不能把这些分支当作相同逐粒子数量/逐步随机数配对。** 这正是原生二维输运在指定风平面下的实际响应，已保存全部释放点与初末高斯相位。

两固定RNG bundle仅是冻结原生随机计算状态，不是独立3D实验。exactpoint使用已知真源/错峰，是oracle对照；sourceplane也用已知共同释放高度，不能宣称部署性能。柱平均是明确的近似闭合，不是3D气体分布的精确边缘化。所有比值均来自同一二维地图评分，不能解释为经校准物理似然比。

运行8/8完成，合计2.557109秒，峰值RSS 139,644,928字节，低于60秒/512MiB。baseline_reruns=0，new_GADEN/new_CFD/ROS_init/new_navigation=0。本轮后停止所有前向，不追加其他高度、平均权重、种子或阈值。

## 对根因判定的意义

1. sourceplane将真源预测raw自由格平均hit从约0.138降至0.065/0.062，而错误候选仍有约0.143/0.144，不能改善真源。
2. 柱平均将真源覆盖提高，但同时更强地提高错误源评分：错/真比分别约21730、25554。扩大预测并不自动改善判别。
3. 本轮排除了两个最直接、低成本的单平面闭合修正作为足以翻转B4错误偏好的解释。下一根因判断应结合相同三维粒子库的中心格事件/原生浓度核读出以及评分语义，不能事后再挑新的风平面制造正信号。

## 可复核文件

`HEIGHT_FORWARD_SCORES.csv`列出12条件(4复用+8新)的评分/覆盖/释放点/相位；`HEIGHT_PAIRED_COMPARISONS.csv`为6个两源配对；`HEIGHT_PER_CELL_CONTRIBUTIONS.csv`为逐自由格差分。`snapshots/`保存每个分支实际加载的全部输入，`forward_calls/`保存原生blurred/unblurred图、全部点、统计与RESULT。冻结父合同hash和字段SHA在`HEIGHT_INPUT_FIELD_QUALIFICATION.json`，前向绑定合同在`HEIGHT_EXECUTION_CONTRACT.json`，实际执行清单在`HEIGHT_EXECUTION_LEDGER.json`。

执行前第一次生成SSH文本时，通用token替换碰到了文件名，代码在本机compile()阶段拒绝，未发送远端、未启动forward；已换唯一占位符后只实际执行了一轮8次。采集时本地与远端ledger仅换行/末尾格式不同，保留`HEIGHT_EXECUTION_LEDGER_REMOTE_EXACT.json`，JSON内容一致，未覆盖原文件或重运行。
