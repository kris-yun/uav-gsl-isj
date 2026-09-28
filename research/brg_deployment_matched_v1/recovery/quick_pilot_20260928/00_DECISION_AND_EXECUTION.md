# BRG V1：暂停额外采集，先做三个案例的闭环开发 pilot

**状态：供主线程签署的缩减版开发方案。本包未训练、未运行ROS/VGR、未生成plume。**

## 直接决定

1. 旧V2移动中采样记录继续隔离；不进训练。
2. V3停点采样在当前检查范围内是合法的训练覆盖策略，不是正式主动搜索策略。保留已完成4条，不再补采剩余44条。
3. 先仅使用已经完成的48条Native事件日志：40 train、8 dev，原6/2个物理源划分不变。覆盖数据本身没有被判无效，只是不作为这次快速pilot的前置条件。
4. 不先执行120条模型自身回灌；先做原十轮预算的初训，三种网络同数据同预算、从新随机权重开始，dev选择checkpoint。
5. 冻结这次初训权重，运行已有eval8清单中第009、021、065号：3个不同物理源、每源1条，四臂共12次真实交互闭环。先完成第一个case的四臂就输出结果，最终到12次停止；不自动扩跑32/384次。
6. 这是 `NATIVE_ONLY_INITIAL_PILOT_NOT_FULL_V1`，不是原完整V1完成，不具有统计确认身份。原HOLD、原计划与原记录保留。

## 预定目标与主动采集的区别

V3仅在训练覆盖模式下改写NavigateToPose目标，其目的是让观测历史不同于Native，不让未训练网络决定训练路线。正式四臂必须关闭该目标替换分支：

当前已观测历史 -> 各自的源概率图 -> 原PMFS planner -> 当前导航目标 -> 到点后按原流程采样 -> 后续更新。

“先决定本段目的地再飞过去”不等于固定整条路线。主动选择地点与停点采样不矛盾。当前网络训练的是候选源判断，不是模仿V3的目的地标签；Native训练日志也不是把Native的源估计作为真值，监督标签仍为模拟任务的真实源。

如欲移动采样，需要对每条原始读数使用其实际位置的前向预测及传感器历史，这属于新的观测模型，不能用旧的单停点block接口硬装。本轮不作该修改。

## 一次source update不等于一条样本

包内训练代码对每个event前缀计算训练损失，只在dev中用source_update_mask筛选部署更新时刻。四条V3分别25/28/27/26个event；48条Native为51–69个event。当前冻结调度在第20、35、50、65个event等位置形成source-update前缀。V3不到35条，因此只有1个更新前缀；不能据此声称网络只会训练一次，也不能人为复制或补造更新。

读取现有数组得到：Native训练2510个event、开发441个event。它们来自40/8条plume，不是2951条独立plume。

## 三案例

按原eval8顺序，选最先出现的三个不同(house,source_id)，取其首条已登记realization，不读浓度或成绩：

| ordinal | house / wind | source | historical seed |
|---|---|---|---:|
|009|House01 / 1,3-2,4_fast|pmfs_26_36|1453872|
|021|House01 / 1,3-2,4_fast|pmfs_27_36|127015129|
|065|House02 / 4,5-3_slow|pmfs_2_37|20702800|

这不是三个环境各一个。用户另附三环境原生样本为001(dev)、025(train)、049(train)，后两条还属于同一物理源，不能直接当成三条留出评测。

四臂：native_pmfs、candidate_gru、brg、brg_ungated。保持原候选支持、原起点、传感器、300秒上限、0.5m几何成功、原Native源图位置估计器及停止规则。提前声明按原规则结束，不强制每次都跑满300秒。超时末态满足几何成功的处理亦沿用原eval8。

## 可直接实施的代码范围

- `train_v1_native_pilot.py`是现有冻结trainer的显式新模式副本；放到原recovery目录，与`v0_reference`同级。
- `--phase native_pilot`只允许每条train/dev plume有Native策略；保持40/8 plume、6/2源、文件hash、完整候选标签、数据有限性及不泄漏检查。
- warm/final原分支的coverage要求仍保留。不能全局删除policy检查。
- 十轮初训，原seed、结构、optimizer、prefix损失、dev source-update NLL选择保持。三种模型同预算；不得使用V0权重热启动。
- Native-only初训的trainer state不能伪装为原完整warm/final。代码已阻止其直接作为原final阶段的warm输入。
- 现有freeze/eval脚本硬编码“final三模型、32次”。Codex需增加独立`PILOT_CHECKPOINT_FREEZE.json`及12次调度入口，匹配本包manifest；不能伪造原final完成标签，也不能直接执行原`full`入口。
- 最终评测必须检查`training_collection=false`、`fixed_source_blind_coverage=false`，且目标替换文件为空。采集模式中禁用成功停止的设置不能泄露到评测。
- Native13早期记录metadata中的`native`别名，使用原库存已记录的`policy=native_pmfs, recorded_policy=native`，不改原文件字节。

示例（路径由Codex绑定，不代表本包已在用户GPU运行）：

```bash
python recovery/train_v1_native_pilot.py \
  --manifest recovery/NATIVE_OPEN_EPISODE_INVENTORY_FROZEN.json \
  --out <新输出目录>/brg --phase native_pilot --variant brg
# gru、ungated各自同样运行一次；禁止依pilot成绩重选模型或追加轮数。
```

## 结果解释

先看逐case的几何成功、终点误差、错误声明、耗时/路程、实际源图安装及goal链。BRG、GRU与ungated允许选出相同目标；轨迹没有分叉不自动等于软件错误。

三例好坏只决定开发投入，不作科学显著性/PASS。若改模型或回灌数据，已查看的三例即为开发诊断，不能重新包装为未触碰确认；继续保留其他未看eval案例的身份。同版本结果可以计入后续同版本扩展，不重复运行。

## 为什么能够更快

原计划248次VGR含采集和评测，不是32次；其300秒累计模拟预算20小时40分。当前还差44条coverage+120条self+32条eval=196次。快速版只剩训练和12次闭环，0条额外coverage/self/GADEN/forward。

同一包47个Native采集receipt记录的核心wall time为74.97–84.97秒，中位78.05秒；入口传入realtime_factor=5。这不含全部归档/恢复时间，且不能代表学习臂GPU/ROS服务成本。因此不要把模拟秒当墙钟秒，也不要承诺固定半小时。用第一个案例各臂实际耗时汇报后续预算，沿用已检查的时钟速率，不再额外加速或并发。

## 局限

Native-only初训仍有自己策略的访问分布偏移，且只有6个训练位置。我们没有声称训练充分；取消大批回灌是为了先获得低成本行为证据，而不是认为回灌无用。本次没有引入PP、换网络或恢复任何STOP路线。
