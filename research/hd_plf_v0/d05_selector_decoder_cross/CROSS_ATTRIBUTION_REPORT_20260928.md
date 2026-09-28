# D0.5 选点器 × B2 解码器交叉归因

**状态：OPEN 历史数据只读归因。** 原结论
`HD_PLF_V0_ACTION_PROXY_NOT_VALIDATED_IN_OPEN_D05` 保持；AOD 既有的十点 B2
读出证据也不改写。本轮不启动 VGR、因果不变性实验、训练或新的效用函数。

## 数据和算法边界

输入只用已归档的 `D05_RESULT.json` 与 `GOAL_COUNTERFACTUALS.csv`。原始文件
SHA256 分别是 `baa871f020703f2d05e9dc1d71d036511c5d61ef5a00bc88ab31b643781f1e10`
和 `66a9a2e3f7244f88ed30d706bbab4a4abf26bf0757e83a460317241befb59c1f`。
来自用户 ZIP 的 `audit_and_cross.py` SHA256 为
`0bb6282fb7f36f99d01b80e23430b62a0f14acbc44dc9f58430c7e1be1dee252`；
ZIP 自身 SHA256 为 `d4b4a4630910579ba1193139ac4416e9834d9b25a09daaea65e68b97b81d233a`，
包内 8 项哈希和 6 项确定性测试均通过。

规范化输入的 `expected_rank` 直接复制已归档的 `rank_after_tie_aware` 文本；
另外核验 `before − after = gain`、每 episode 两臂选择点恰好各一个、
144 组 `episode × decoder` 的目标数与冻结 JSON 一致。72 个 episode、每个
目标各有两种解码结果，共 2,208 行。交叉程序输出 576 行
`episode × decoder × {两选择器、均匀可行点、真值 oracle}`；独立第二遍从原
CSV 与冻结 selected cell 直接计算，最大绝对差为 **0**。全部输出再次运行
逐字节一致。

## 完整交叉表

表内是六个源各四条 realization 的**源均衡平均真源期望 rank**，越低越好。
均匀列是枚举同一可行集的精确平均；oracle 列在看过真源之后选最佳点，
仅表示这组可行点的离线下界。

| OPEN 环境 | 固定 B2 解码器 | LF-u 选点 | LF-rawu 选点 | 均匀可行点 | 真值 oracle |
|---|---|---:|---:|---:|---:|
| H01 | u | 2.000 | 2.167 | 2.210 | 1.125 |
| H01 | rawu | 1.917 | **1.667** | 2.062 | 1.042 |
| H02 W0 | u | **1.583** | 1.750 | 2.713 | 1.167 |
| H02 W0 | rawu | **1.458** | 2.125 | 2.723 | 1.250 |
| H02 W2 | u | 2.417 | 2.750 | **2.325** | 1.333 |
| H02 W2 | rawu | 2.250 | 1.917 | **1.796** | 1.250 |

固定解码器看选点：

- H01/rawu-B2 中，LF-rawu 比 LF-u 平均低 0.250 rank；24 条为
  **6 改善、14 持平、4 恶化**。逐源平均差主要由 source 1 的 −4.0、
  source 3 的 +3.0 和 source 5 的 −0.5 构成。
- H02 W0/rawu-B2 中，LF-rawu 比 LF-u 平均**高 0.667 rank**；
  **0 改善、16 持平、8 恶化**。恶化集中在 source 0 和 1，
  两源各四条 realization 的平均差均为 +2.0。
- H02 W2/rawu-B2 中，LF-rawu 平均低 0.333 rank；
  **4 改善、20 持平、0 恶化**，四次改善均来自 source 1。

固定选点看解码器：用 LF-rawu 的同一个点，rawu-B2 相对 u-B2
在 H01 平均低 0.500 rank（6/18/0 改善／持平／恶化），在 H02 W0
反而高 0.375（4/15/5），在 H02 W2 低 0.833（13/8/3）。
用 LF-u 的同一个点，rawu-B2 在三个环境分别平均低
0.083、0.125、0.167 rank。完整逐 episode、逐源和全部对照计数分别保存于
`crossed_episode_results.csv`、`crossed_per_source.csv` 与
`CROSS_INDEPENDENT_CHECK_AND_CONTRASTS.json`。

H02 W2 的均匀可行点平均 rank 在两种解码器下均优于两种已冻结选择器，
而 oracle 仍明显更好。这里**有可利用的离线空间**，但目前选择器没有稳定
找到它。H02 W0 却是 LF-u 选点配 rawu-B2 最好；因此选点与幅度读出不能
捆成一个成败结论。

## 结论和限制

交叉表支持保留 AOD 的既有后端读出证据，同时继续停止 HD-PLF v0 动作
规则：同一解码器下 LF-rawu 选点的效果随环境、源位置改变，未形成稳定
收益。本轮只是**六候选、两点、OPEN、B2** 的有限归因；每个环境 24 个
episode 实际只有 3 个不同锚点，每个锚点对应 8 条 episode，并非 24 个独立
在线决策上下文。真值 oracle 是不可部署的上限。Native 的 sourceProbability
不使用本表的 B2 幅度分数，不能把这里的 rank 变化说成 Native 后验或闭环
已改善。

本轮到此结束，不从这张表反向调整 cost、半径、gain、EPS、候选集或动作
规则，也不自动启动新的方法路线。
