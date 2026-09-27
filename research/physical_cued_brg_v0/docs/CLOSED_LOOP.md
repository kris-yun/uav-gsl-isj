# 下一次只做闭环方法比较

不再设置“有没有信号”的前置实验。软件单元/接口检查是防止跑坏程序，不是新的科学资格门。

## 固定两种问题

- 实用问题：BRG-PMFS最终比classic native PMFS更准确/更快吗？
- 增量归因：同模板、同事件、同训练预算的GRU和关闭反馈，能否解释全部改善？

一次活动同时跑四臂：Native PMFS / Candidate-GRU / BRG / BRG-ungated。不先跑赢弱基线再决定是否加GRU。AOD+B2作为已有组件基础；本包没有为了加一个对照临时把未校准SSE强行softmax成概率。

## 默认开发合同（数字在VM执行前一次明确）

先用已有OPEN plume的连续回放，从同一source/seed/起点开始，每个算法自行选点，不强制轨迹相同。对既有数据的重放属于开发闭环，不冒称fresh独立确认。

建议最大500s，主要成功定义为最终源位置估计在0.5m内；若主线程已有有效closedloop合同，则用原值并填入campaign，不从结果挑0.5/1m。精确cell rank、源图熵和NLL作为诊断，不替代最终定位成功。错误声明、无hit、超时和导航失败都记录。模型服务故障需要与科学失败分开标记，但不能只汇总幸存任务。

同一次case所有臂使用相同：source/plume id、初始位姿、真实传输背景、模拟时钟、sensor响应/平均窗口、候选集合、prior、运动控制器、安全约束和最大预算。采用完全独立reset，不能让上一臂状态/缓存/随机游标传到下一臂。

Native预测本来不需要与训练银行同样多的先验数据，因此报告两层比较：
1. vs经典原生PMFS：包含额外PMFS forward准备成本的端到端资源；
2. vs同银行GRU/ungated：隔离网络结构价值。

不允许用target source标签适应模型，不从真实全场GADEN查询未访问位置给网络。全候选模型预测可离线缓存，但其生成输入是否真实可得要另列，不能写成未知环境few-context世界模型。

## 跑法

`configs/campaign.example.json`中留空的是VM现有runner路径和case列表，本环境不知道其真实CLI，不能发明一个。Codex只需把现有可用runner封装成`harness_argv`约定，并回写一行JSON结果。

```json
{"case_id":"case001","arm":"brg","source_id":"pmfs_i_j","plume_id":"seed...","budget_s":500,"initial_pose_id":"startA","observation_contract_id":"...","candidate_support_id":"...","truth_xy":[0,0],"estimate_xy":[0.4,0.1],"status":"completed"}
```

上面truth只在评估器；TCP侧只接受运行ID、事件ID、时间、实际位置和浓度。若real robot安全控制触发，应取消导航并由宿主记录，不自动回退成另一算法继续累计成绩。

```bash
python tools/run_campaign.py --campaign configs/campaign.json      # 显示锁定argv
python tools/run_campaign.py --campaign configs/campaign.json --execute
python tools/evaluate_closed_loop.py --jsonl runs/closed_loop/all_results.jsonl \
 --arms native_pmfs candidate_gru brg brg_ungated --radius-m 0.5 \
 --out runs/closed_loop/comparison.json
```

统计默认固定source面板，源内独立plume成组。多个起点来自同一plume时先合并成一个组；不能当作独立样本。模型选择/early stopping只读OPEN dev；闭环评估一旦用于调整，后续结果就明确是另一个开发版本，不是fresh确认。

## 怎样才算推进

下一次应交付四臂路径、源图、最终定位成功数、距离、耗时与失败案例。不要求BRG先取得某个离线signal才能运行，但也不因最新网络和服务跑通就提前授予主创新资格。

如果BRG不胜classic，当前版本不完成目标；若胜classic但与GRU相当，保留学习器收益而不夸大反馈机制。开发可以迭代，但要明确版本，不无限新增诊断实验来维持一个结论。
