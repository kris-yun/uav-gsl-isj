# R3：结构性传播不充分、可观测性与历史 placebo

最终判定：**R3_STOP**。R3-A=NOT_PASS；R3-B目标标签门=PASS；R3-C=STOP_HISTORY_ROUTE。没有执行R4、CFD/GADEN、神经网络、闭环或多无人机。

## Provenance与冻结

protocol_anchor_commit=17b31989e726b64ac95030a5b3f7dd635578af65。delivery_parent_commit与starting_commit均为5c1da8d824393119f5b2688486ebf759dd8ec0a2，对应上一轮实际交付HEAD。旧包SHA重新验证为2ecafd53e52be069e240af43aa7b5f8e580f804074c66e63865c9d9bfa3ed482，旧产物未改。此次不把协议锚点称作实际交付版本；当前R3最终commit在外部交付receipt中记录，避免自引用commit循环。

需要诚实区分：前一轮已公开源坐标及误差，人的先验知识无法撤销。本轮程序只读取无真源列的处理观测；配置、候选域、模型支持、窗口、抽样种子和门先保存。所有source-blind gates与decision保存以后，才读取坐标用于最后的误差CSV，误差不参与任何选择。不是声称研究者从未知道源位置。

## R3-A方法与冻结门

Svalbard两种ENU一致风×3背景×2 log sigma×3phase，共36配置；Mackenzie3风×2扩散支持×2作者背景×2平台，共24配置。phase3仅作negative control，不参与共同机制判定。Lagoon保持HOLD，没有新的解锁或评分。

使用已审计的源域与所有参数范围，无额外增加定位支持。Svalbard沿用条件风mirror forward，Q均匀0..10000g/h边缘积分后的source MAP；Mackenzie沿用共享Q、扩散格点profile RSS的source MAP。两者统计对象不同，不混称Bayesian posterior。

每个条件固定60s非重叠块、24次有放回分层block bootstrap；两条Mackenzie航线分别重采样，同一条件不同模型使用相同draw。source/Q以及Mackenzie dispersion重新拟合；风summary/covariates与候选域条件固定，不重估bootstrap mean/height regression。故within漂移是条件于已观测风表征的抽样漂移，不是包括全部气象误差的总不确定度。模型MAP离散网格的量化下限显式报告，避免零漂移导致无限ratio。

between与within都采用点估计对的欧氏距离中位数；within pairwise95是漂移分布的95分位，不是置信区间，也没有将276个pair当独立样本。normalized drift除以观测GPS包络对角线。

主门固定：wind-only、primary nuisance的between median / within median >=2，且between大于对应within pairwise95；primary wind arms不得靠源域边界。Svalbard phase1/2及Mackenzie CP/OP均须通过。不让background/noise变化或6m支撑通过；这个门是保守必要证据规则，不是从真源误差挑出的显著性检验。all-nuisance数值另报，不用来替换wind-only主门。边界invalid表示域/可辨识性限制，不等于证明缺失动态状态。

|条件|全部配置between m|全部配置within m|ratio|wind-only between m|wind-only within95 m|wind-only ratio|primary边界invalid|条件门|
|---|---:|---:|---:|---:|---:|---:|---|---|
|Svalbard_phase1|68.24|10.00|6.82|68.24|115.60|6.82|False|False|
|Svalbard_phase2|10.00|5.59|1.79|12.50|53.85|2.24|False|False|
|Svalbard_phase3|107.38|76.69|1.40|167.80|285.54|1.78|True|False|
|Mackenzie_CP|27.19|13.00|2.09|39.81|138.54|2.61|False|False|
|Mackenzie_OP|13.00|26.00|0.50|65.00|104.00|2.50|True|False|

四个primary条件的wind-only中位漂移比均超过2（6.82、2.24、2.61、2.50），但between漂移均小于同模型bootstrap pairwise95；Mackenzie OP另外有边界解。说明中位效应值得保留，却还不能排除长尾sampling不稳定。不能选择只报median ratio而忽略预注册的95分位条件来救门。R3_STOP意味着该预注册证据链未通过、R4不开，不是证明所有动态传播表示都无价值。

即使某个ratio大，也不能独自证明“缺失动态记忆”是原因：受体风、模型稳态假设、参数补偿、有限路径和网格/先验均可能参与。R3只尝试冻结真实逆问题不稳定这个现象；机制归因仍须后续受控因果实验。NOT_PASS/STOP不等于数学上证明不存在任何transport memory。

## R3-B不使用truth的可观测性门

仅用primary current-local模型。七条规则同时满足才更新位置：增强观测比例>=5%（threshold=background*exp(log sigma)）；归一化posterior entropy<0.85；95%条件后验面积占候选域<25%；Q=0 posterior<0.5且MAP Q>0；边界概率<10%；两次互补60s块训练的source split drift小于观测长度25%。阈值按内部无量纲规则冻结，没有依据目标标签或定位真值调节。

Q=0概率对所有source/Q联合模型积分，并非只检查Q_MAP。面积、熵及边界质量是模型条件量，未做独立覆盖率校准。phase1/2预注册目标informative，phase3预注册目标abstain；若未满足，报告门失败，不修阈值。

|条件|增强比例|entropy fraction|area fraction|Q_MAP|P(Q=0)|boundary mass|split drift/domain|判定|
|---|---:|---:|---:|---:|---:|---:|---:|---|
|Svalbard_phase1|0.173|0.156|0.000|2000|0.000|0.000|0.009|INFORMATIVE|
|Svalbard_phase2|0.109|0.080|0.000|1375|0.000|0.000|0.247|INFORMATIVE|
|Svalbard_phase3|0.009|0.936|0.800|0|0.086|0.067|0.216|INSUFFICIENT_ABSTAIN|

phase2的split漂移占域0.247，接近0.25冻结阈值；标签通过不能称为稳健阈值验证。仅三个同场景phase不是独立验证集，模型条件posterior很窄也不能抵消block bootstrap长尾。R3-B仅是这一轮不读真值的negative-control gate示范，没有据此升级正式辅助创新。

## R3-C历史只作falsification

固定10/30/60s窗口，不包含当前风；past严格过去，future严格未来，各自仅限同一架次。所有窗口和baseline统一采用同时有完整past/future窗的子集，不跨缺失窗口插值。采用互补交替60s blocks的源/释放率训练与held-out prediction，primary nuisance固定。Svalbard评价held-out log Gaussian NLL（越低越好），Mackenzie评价held-out等航线权重RSS（越低越好）；不跨数据集直接比较分值尺度。

预定义要求每个窗口在每个primary condition中past相对current与matched future均改善至少5%，而不是选最有利窗口。Mackenzie仅有近似相对采样时钟，上游sensor lag没有核验；Svalbard公开预处理也没有另立气体动态lag合同。future效果可以说明smoothing/协变量关联，不能变成可部署的causal predictor。C门若没有跨数据集一致优势或lag前提缺失，则STOP_HISTORY_ROUTE，不训练history模块。

|条件|current score|mean score|10s past/future|30s past/future|60s past/future|
|---|---:|---:|---|---|---|
|Mackenzie_CP|0.9264|1.326|1.045/1.322|1.274/1.069|1.204/2.158|
|Mackenzie_OP|1.094|1.138|1.284/1.164|1.148/1.066|1.213/0.9351|
|Svalbard_phase1|1.236|1.958|0.6043/1.385|1.436/1.377|1.512/1.276|
|Svalbard_phase2|1.223|1.522|1.254/1.734|1.577/2.468|1.425/1.759|

## 交付与解释边界

R3_STRUCTURAL_DRIFT.csv、R3_BOOTSTRAP_DRIFT.csv及SUMMARY、R3_OBSERVABILITY.csv、R3_HISTORY_PLACEBO.csv及GATE、R3_SUPPORT_AREA.csv、R3_SPLIT_CONSISTENCY.csv、配置、source-blind decision、所有posterior/RSS profile与最后才算的R3_LOCALIZATION_POSTHOC_ONLY.csv均保存。旧数据审计中的不可复现ground-only及Lagoon合同缺项保持，不用其他文件补猜。

本轮不以“某种风定位误差最低”为目标，不把局地风固化成修复模块，也不把结构性不稳定直接等同于最小充分latent已存在、已可学习。若共同机制门没过，R4保持关闭；若过，也只能冻结问题，等待下一次明确的R4授权与预注册。
