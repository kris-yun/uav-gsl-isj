# M2 独立只读收尾核验

判决：`INDEPENDENT_ARITHMETIC_PASS / TWO_CANDIDATE_DISCRIMINATION_PASS_SMALL_BUDGET / E1_NOT_ESTABLISHED / E2_HOLD / MAIN_INNOVATION_HOLD`。

本复核独立读取已保存的八份查询结果、匿名输入与评分、原生对齐地图、物理时间血统和合同，使用另写的标量代码重算Bernoulli/Brier、447格比较及成员分支；同时只读运行`analyse_discrimination.analyse()`核查六份派生CSV。没有启动GADEN、ROS、前向、导航或新定位实验，没有更改已有证据。

## 数值结果

原B4的O0全正检出事件下，C7/K2对数评分分别为−9.1160778397 / −30.9834609077，Brier为0.0277777778 / 0.21；两者均选C7。四个独立RNG留出实现的两评分均4/4正确。参考只用rep0/1，留出只用rep2/3；Jeffreys平滑固定为`(k+.5)/3`。五任务的全部逐块、逐停留及总评分均独立复算通过。匿名输入不含源坐标/角色；输入、评分脚本和解盲前输出SHA均匹配保存锁。

同一3D参考bank的未对齐相似度：C7为0.1319982933，K2为0.0023978733；对齐map MSE为0 / 0.0514899247。**未对齐与对齐都选C7，没有发生E1要求的错误候选→正确候选翻转。** 原生2D占用频率缺少同定义PID算子，本轮没有额外二维前向，因此不能将原M1错源偏好与本轮3D结果差异直接解释成二维或高度的因果根因，E2继续HOLD。

八份bank各22848查询行均有限非负；两个成员分支在八份bank的受体与完整网格上均相同。逐条检查真实物理目标处于选择帧与下一帧header时间之间，风索引均10。原生观测地图锚点1530格的logOdds/omega/confidence最大绝对差均0。六份派生CSV共1314行重新计算与保存数值完全一致；另外800行分支化源条件块预测的PID、阈值事件、帧号和XYZ均与原查询记录一致。

## 必须保留的解释限制

- 这里只检验两个事后选择候选在同一B4轨迹上的区别；4份留出不能证明统计显著性、完整源空间定位收益或未选任务迁移。没有新的PMFS定位成绩。
- 八份是同一GADEN模型的独立随机实现，不是独立物理模型/真实传感器验证。定位时风静态10，不是时变传播验证。
- C7对齐map MSE=0来自两份reference的50块全正事件，与原B4相同，经固定确定性地图算子得到同一map；**这不表示三维浓度逐值预测完美。**
- `REALIZATION_EVENT_COUNTS.csv`中`independent_stops=10`列名宜解释为“10个不同且相关的停留位置”，不能计为10次独立物理实验。
- 分析中的H101/H102→rep2、H103/H104→rep3是固定映射；已由独立核验逐项与匿名任务事件确认。匿名化限定为评分程序输入隔离，准备合同公开坐标且分析人员知晓角色，不应宣称分析人员双盲。
- 未对齐控制在生成前冻结为`concentration>0.1ppm`的时间频率，区别于累计belief-map；不能把它叫原生二维羽丝占格频率或独立格联合似然。

## 子任务交付复制覆盖

五份关键schedule/recovery/map共变量文件已复制到`observation_lineage`，SHA一致。`score_source_blind.py`已在输出根目录、与子任务原文件一致，但不在`observation_lineage`。该子目录未复制的补充件为：`SCORING_ALIGNMENT_DEFINITION.json`、`SCORING_AND_ALIGNMENT_CONTRACT_zh.md`、`SCORING_CONTRACT_SHA256.json`、`SOURCE_BLIND_SCORE_CODE_UNIT_CHECK.json`，另评分脚本不在该子目录；本目录JSON保存逐项覆盖状态。最终实际实验合同以root的生成前冻结合同为准，这些建议稿不替代实验合同。

本轮适当结论是：在当前两个候选、冻结轨迹和小参考预算下，源条件原始事件提供可重复候选判别信息；所提观测对齐导致排序翻转机制未被本实验确认，二维/三维前向区别仍未被可比算子隔离。继续保留主创新与物理根因HOLD，不自动开发方法或追加样本。
