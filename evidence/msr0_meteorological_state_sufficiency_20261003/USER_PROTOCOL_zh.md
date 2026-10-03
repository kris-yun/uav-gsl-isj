现在不要再验证第五个湖岸微机制。下一步直接做一个**“气象信息充分性”实验**，把科学问题压到最本质：

> **在跨风况气源定位中，传统二维风信息是否已经足够？如果不够，最少需要补充哪些三维气象结构，才能稳定恢复源坐标？**

这一步非常关键，因为它决定我们后面到底有没有资格做“Task-Sufficient Meteorological State”。如果二维风已经足够，就停止 3D/world-model 路线；如果确实存在“二维看起来相同、但产生完全不同源证据”的情况，再找 2026 母理论。

### 这次四类数据各司其职

**S2X/GADEN**负责回答“气象信息对源定位有没有因果价值”，因为它有干净源真值和固定 context；**WiscoDISCO**只负责回答“这些三维气象结构在真实湖岸是否存在”；**Svalbard/Mackenzie**后面做真实点源外部验证；**Lagoon**继续只做湖岸真实场景/羽流形态，不承担唯一点源定位误差。

真正的第一刀不是训练网络，而是找一种现象：

> 两个气象 context 在 PMFS 的二维风表征下几乎一样，  
> 但同一源、同一采样轨迹产生的气体证据明显不同。

我把这种情况叫 **meteorological aliasing（气象混叠）**。

如果连这种 collision 都找不到，说明 PMFS 压成二维并没有造成我们想象中的主要信息损失，直接 STOP。

如果找到了，再检查加入 \(w\)、垂直风切变等信息后能不能把 collision 解开。

给 Codex 直接发下面这版。

新建独立实验：

MSR0_METEOROLOGICAL_STATE_SUFFICIENCY

不要修改：
R1/R1A/R3/TIBL-R0/FRONT-LAG 的任何旧判定。

本轮不寻找新的湖岸微机制，不训练神经网络，不做 world model，不做闭环。

核心科学问题：

在跨气象状态的未知源定位中，PMFS/经典反演所使用的二维风信息是否存在任务相关的信息损失？
若存在，什么最小的三维气象描述足以恢复稳定的 source–receptor mapping？

最终目标仍然是：
source coordinate + localization uncertainty。

---

## A. 先做现有数据覆盖审计

优先只使用已经修复的 S2X/OCB-R2 数据。

固定主实验 context：
H01/s0
H01/s1
H02/s0
H02/s1

并检查其余 S2X context 是否具有合法输入。

每个 context 必须确认：

- wind lineage
- gas lineage
- source truth
- realization ID
- UAV/receptor trajectory
- observation clock
- 3-D GADEN wind availability
- PMFS 2-D wind availability
- candidate source grid
- candidate forward-bank coverage

输出：

MSR0_DATA_CONTRACT.json
MSR0_FORWARD_BANK_COVERAGE.csv

本阶段不得为了补齐数据直接生成 268k forward。

先报告现有 bank 到底够不够。

---

## B. 冻结气象表示阶梯

所有表示必须 source-blind，不能读取 source truth。

### Phi0：PMFS-style 2-D

仅：
u, v

使用当前 baseline 所能获得的二维风表示。

### Phi1：local 3-D

u, v, w

只增加垂直风分量。

### Phi2：vertical-structure state

在观测位置附近，从合法 3-D wind field 提取：

u,v,w
vertical differences / vertical shear
wind-direction shear
speed shear

只能使用冻结的固定高度偏移或固定高度层。

不得看定位结果后改高度。

### Phi3：local 3-D structural state

在固定局地邻域中加入：

horizontal wind gradients
vertical gradients
local directional variability
local speed variability

所有特征必须在 source truth 不可见时计算。

如果 wind_iteration_0..10 的物理时间语义不能证明，不得把 iteration variability 写成 turbulence 或 TKE。

### Phi_ORACLE

允许使用更大的 3-D wind patch 作为 oracle upper bound。

它只回答：
“完整局地三维气象是否含有二维表示遗漏的定位相关信息？”

不得把 ORACLE 当成最终可部署算法。

---

## C. 第一门：Meteorological Aliasing

这是本轮最重要的实验。

对所有合法 context pairs：

1. 计算二维气象距离

d_2D(i,j)

2. 计算 Phi1/Phi2/Phi3 距离

d_3D(i,j)

3. 对相同 source、相同或严格可比较 receptor path，计算 transport/gas response distance

D_gas(i,j)

若轨迹不同，不得直接比较原始 gas trace。
必须使用：
- common receptor set，
或
- 已存在 candidate forward field，
或
- 空间上严格匹配的采样点。

不得用轨迹差异制造气象差异。

---

## D. 用 within-context stochastic variability 做自然噪声底

不要再人为指定一个 JSD=0.01 式的绝对物理门。

先利用每个 fixed context 中的多个 gas realization 计算：

D_within

即：
同一 source
同一 wind context
不同 stochastic gas realization

产生的 gas-response distance。

得到：
median
q90
q95

然后定义：

alias_ratio(i,j)
=
D_between_context(i,j)
/ q95(D_within)

所谓 2-D meteorological collision 必须满足：

1. 在 Phi0 下属于相近 context；
2. D_between_context > q95 within-context variability；
3. 相同 source/trajectory contract；
4. 该差异不能由 gas realization 本身解释。

优先寻找：

二维风很相似
但三维结构明显不同
同时 plume/source evidence 差异超出随机 plume variability

的 context pair。

---

## E. 核心判据：更丰富的气象是否解除 collision

对每一种 Phi：

使用完全相同的 context/source 数据，计算：

meteorology-distance
vs.
gas-response-distance

的关系。

至少报告：

- nearest-neighbor transport mismatch
- Spearman correlation
- context retrieval accuracy
- alias collision count
- false-neighbor count

核心不是追求分类准确率。

要回答：

Phi1/Phi2/Phi3 是否能够把 Phi0 错误认为“相似”的气象状态正确分开？

如果：
Phi0 已经足够解释 transport differences

则：

MSR0_STOP_2D_MET_SUFFICIENT

停止三维气象主创新。

---

## F. 第二门：直接进入源坐标，而不是停留在 plume difference

只有 Meteorological Aliasing Gate 出现正信号才执行。

优先使用现有 candidate forward bank。

构造一个不训练深度网络的：

meteorology-conditioned forward-bank retrieval / mixture baseline。

对 held-out context：

根据 Phi0/Phi1/Phi2/Phi3 与已有 forward contexts 的距离，
选择或加权 source candidate forward likelihood。

所有权重规则在 source truth 不可见条件下冻结。

输出 source probability map。

从同一概率图同时计算：

1. MAP candidate coordinate
2. posterior-weighted coordinate estimate
3. localization uncertainty/spread

真实连续 source coordinate直接用于 meter error。

必须单独报告：
candidate-grid quantization floor

不能把候选格中心误差混成算法误差。

---

## G. Split contract

严禁 observation-level random split。

至少执行：

leave-one-context-out

并分别报告：

H01
H02

若数据允许，再执行：

leave-one-house-out。

两个固定 source 必须分别报告，不允许只平均后隐藏某一 source 失败。

gas realization 必须整条留出。

---

## H. source localization Gate

比较：

Phi0
Phi1
Phi2
Phi3
Phi_ORACLE

Primary：
localization error m

Secondary：
true-source rank
MAP
mean rank
posterior spread / uncertainty

建议预冻结以下工程 GO 条件：

相对 Phi0：

- median localization error 改善 >=15%
- 至少 3/4 主固定 cases 同方向
- 两个 source 都不能系统退化
- paired context-level bootstrap/error difference 不跨明显反方向
- Phi2/Phi3 至少一个接近 Phi_ORACLE 的主要收益

若只有 ORACLE 有收益、低维表示都没有：
HOLD_HIGH_DIMENSIONAL_ONLY

若 Phi1/Phi2/Phi3 均无稳定收益：
STOP_2D_MET_SUFFICIENT

不得因为 Top1 改善而忽略 meter localization error。

---

## I. 如果现有 forward bank 不够

只有：

Meteorological Aliasing Gate 已通过

但 candidate bank coverage 不足

时，才允许补生成最小 source bank。

不要直接补完整 268,224 次。

优先：

H01 + H02
已确认最有信息的 4 个 meteorological contexts
固定 common receptor path
7x7 或现有合法候选网格中的最小覆盖子集
至少多个 source positions
两个 independent gas realizations

先验证 source-coordinate signal。

若最小 bank 不通过：
STOP。

---

## J. WiscoDISCO：真实湖岸桥接，不做定位评分

仅在 S2X 中找到有效 Phi 后执行。

使用已经通过合同的数据检查：

Wisco lake-breeze PRE / TRANSITION / POST

在 Phi0 和通过的 PhiX 中是否表现不同。

问题是：

真实湖岸中是否存在
“二维平均/局地风看起来相近，但垂直/三维状态明显不同”
的可观测状态？

禁止：

- 使用 source localization error
- 使用气体真值
- 重新解释弱 42/59 m lidar retrieval
- 为了支持 S2X 结果重新选择事件

如果 S2X 有信号，但真实 Wisco 看不到对应的气象结构：

MSR0_HOLD_NO_LAKESHORE_BRIDGE

---

## K. 本轮只允许三个主结论

1.
MSR0_STOP_2D_MET_SUFFICIENT

含义：
没有证据说明二维风压缩是当前源定位的主要瓶颈。
停止 3-D/task-sufficient meteorology 主路线。

2.
MSR0_HOLD_SIM_SIGNAL_NO_LAKESHORE_BRIDGE

含义：
仿真中存在额外气象信息价值，但尚不能证明与真实湖岸相关。

3.
MSR0_PASS_TASK_RELEVANT_MET_STATE

必须同时满足：

- 存在超出 within-context plume stochasticity 的 2-D meteorological aliasing；
- 更丰富但低维的气象表示可以解除 aliasing；
- source-coordinate localization 在 held-out context 稳定改善；
- Wisco 真实湖岸中存在对应的可观测气象结构。

只有 PASS 后，才设计正式主创新：
Task-Sufficient Meteorological Transport State。

---

## L. 输出文件

MSR0_FROZEN_CONFIG.json
MSR0_DATA_CONTRACT.json
MSR0_FORWARD_BANK_COVERAGE.csv
MSR0_WITHIN_CONTEXT_VARIABILITY.csv
MSR0_CONTEXT_DISTANCES.csv
MSR0_ALIASING_PAIRS.csv
MSR0_REPRESENTATION_SCORE.csv
MSR0_LOCALIZATION.csv
MSR0_QUANTIZATION_FLOOR.csv
MSR0_WISCO_BRIDGE.csv
MSR0_DECISION.json
REPORT_MSR0_zh.md

所有输入、SHA256、代码版本、branch、commit 完整保存并推送。

不得修改任何旧 STOP/HOLD 结论。

我现在最希望看到的不是“Phi3 比 Phi0 高 2%”，而是一个非常明确的结果：

> **两个风场在 PMFS 的二维表示里几乎无法区分，但真实 forward plume/source evidence 明显不同；加入某一个很小的三维状态量后，这种混叠消失，而且源坐标误差下降。**

如果真能找到这个，我们的科学问题和主创新就都顺了：

**场景问题：湖岸复杂低空气象被二维风压缩后发生任务相关信息混叠。**

**科学问题：什么最小气象状态足以维持源—羽流映射的可辨识性？**

**方法创新：Task-Sufficient Meteorological Transport State。**

如果找不到，也很好——我们就终于可以有证据地停止“3D 气象是第一篇核心瓶颈”这条路线，不再继续烧时间。