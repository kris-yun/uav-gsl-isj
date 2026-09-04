# G2-M3 offline falsification：主动实验设计（动作选择）策略对比

日期：2026-09-04

## 一、当前 M3 实现的问题

读 CTPI.cpp 的 `evaluateCTPIActionInformation`，当前 M3 是：

1. **myopic（单步贪心）**：只评估当前动作的即时信息增益
2. **二值命中互信息**：`information = H(mixture) - Σ p_s H(pHit_s)`，基于 Gaussian plume 的"命中/未命中"二值概率——丢掉了浓度幅值
3. **手工后验调制 hack**：`score = information * (1 + 20 * posteriorMass)`，20 倍是手工调参（正是应避免的"调 beta"）

## 二、offline falsification 结果（4 策略，true-source rank 随采样步数）

用 M2 bank-free 数值解做环境（210 carrier 峰值场），动作 = 任意 free cell：

| 策略 | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 步 |
|---|---|---|---|---|---|---|---|---|
| random | 179 | 168 | 149 | 140 | 128 | 119 | 101 | 92 |
| **exploit（追后验峰值）** | **125** | **110** | **95** | **75** | **65** | **47** | **39** | **35** |
| myopic-EIG（当前 M3） | 119 | 103 | 92 | 72 | 55 | 45 | 39 | 37 |
| non-myopic（确定性前瞻） | 120 | 104 | 95 | 86 | 71 | 63 | 55 | 50 |

**结论**：
1. **exploit（追浓度峰值）最优**，myopic EIG ≈ exploit（略差），non-myopic 反而最差。
2. 这精确复现了 12-run 里 M3 不承重（F10 vs F00 无改善）的原因。

## 三、核心洞察（M3 不承重的根因）

**在"峰值场 + 持续源"的简单环境里，浓度峰值 = 源位置，追峰值（exploit）就是最优策略，EID 无额外信息价值。**

验证：单 wind it1（朝 +y）的瞬时场峰值仍在源 cell (23,16)——因为数值解用"持续源"（源 cell 浓度永远最高）。

**但真实 GSL 是"脉冲源 + 时变风 + 瞬时观测"**：
- GADEN filament 是脉冲释放（每个 iteration 释放一个 puff，随风飘走）
- 机器人测到的是"瞬时浓度"，其峰值在**当前风向的下游**，≠ 源位置
- 于是 exploit（追瞬时峰值）会追到下游（错误），EID（用输运预测区分源 vs 下游）才有价值

（早期 closed-loop 实证：观测 gas 浓度 max 仅 0.31 PPM，而源 cell 峰值 164 PPM——机器人采到的是下游羽流，不是源。）

## 四、non-myopic 反而最差的说明（诚实）

我的 non-myopic 用"确定性前瞻"（期望观测 ev = Σ p_s·C_s 更新后验），这是**伪 non-myopic**——它把后验拉向"期望"，丢失观测的不确定性。真正的 non-myopic 应做 `E_O[V(a)]`（对观测分布采样/积分取期望），而非确定性期望。此实现缺陷使 non-myopic 产生 bias。

## 五、M3 正确 redesign 方向

1. **瞬时观测环境**：脉冲源（filament puff）+ 时变风，观测 = 瞬时浓度 snapshot（峰值在下游）
2. **正确的 EIG**：`EIG(a) = E_O[KL(P(S|O,a)‖P(S))]`，对观测分布积分，而非二值命中互信息
3. **正确的 non-myopic**：采样前瞻（对观测 O 采样 rollout），而非确定性前瞻
4. **用 M2 输运预测**（时变 advection-diffusion）评估动作的期望观测，而非简单 Gaussian plume

这正好对应 2026 文献主线 3（Sequential BOED via Policy Gradient RL、non-myopic 优于 myopic、源定位需"源附近+略上游"采样）。
