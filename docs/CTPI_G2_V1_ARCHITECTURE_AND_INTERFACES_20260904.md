# CTPI G2-v1 三模块统一架构 + 接口冻结

日期：2026-09-04
前置：`CTPI_M3_FASTTRACK_H01_3SEED_SCREEN_NO_GO_20260904.md`（frozen CREL–TSDC–PIP 正式 NO-GO）
性质：G2 failure-driven redesign 的第一步 —— 理论层一次性推导完整架构，冻结 M1→M2→M3 接口。

---

## 0. 为什么重设计（失败机制回顾）

12-run screen 显示 `posterior 更集中 但 定位更错`。从当前 M1（CPIR `applyCPIRPosterior`）源码定位到四个方法层缺陷：

1. **二值命中丢失浓度幅值**：`hits = count(physical > 0.1)` 只看"是否超阈值"，丢弃浓度幅值与梯度 —— 而浓度幅值/梯度才是定位源的核心物理量。
2. **source strength 与 transport nuisance 混淆**：一个二值命中率无法区分"强源远距离"与"弱源近距离"，源强度 q、风场输运 T、传感器动力学 E 全部压进一个 Laplace 平滑命中率 `qsb=(0.5+hits)/(8+1)`。
3. **carrier 粗化**：源候选是 2×2 quadtree（0.6m×0.6m，210 个），空间分辨率被粗化，而非 626 free cell 级。
4. **member 是经验命中率，不是 nuisance 边缘化**：8 个 member（`prediction_transport_keys=[101,211,307,401,503,601,701,809]`）是 8 个 transport regime，观测用独立 `2,4-1_fast` realization —— 观测 regime 大概率不在 8 个 member 内，命中率系统性偏差。

生成 site-specific bank 耗时 5.4h（19459s），这正是 G2-M2 要消除的成本。

---

## 1. 统一因果链

```
S = (θ, q)           源：位置 θ ∈ 626 free cells, 强度 q ∈ R+
  → T               输运 nuisance：时变风场 u(x,t), 扩散 D
    → C(x,t)        浓度场（advection-diffusion / filament）
      → E           传感器 nuisance：FOPDT (τ, dead_time, gain, noise)
        → O         观测：机器人位置上的浓度时间序列 y(t)
          → Belief  P(S | O)
            → do(a) 动作：导航到新位置
              → O'  新观测（重复）
```

三个模块严格对应因果链的三段，分别借鉴不同母领域（用户已定）。

---

## 2. G2-M1：源/干扰分离（因果表征 + 地球物理/统计逆问题）

**目标**：从观测正确反推 source posterior，显式分离 source strength / transport nuisance / sensor nuisance。

**观测模型**：
```
C(x,t) = F(S, T; x, t)              # 正演：advection-diffusion 解（GADEN filament 的连续化）
y(t)    = H_E( C(x_r(t), t) ) + ε   # 传感器：FOPDT 算子 H_E 作用在机器人轨迹浓度上
```

**贝叶斯逆问题（source posterior）**：
```
P(S | O) ∝ P(S) · ∫∫ P(O | S, T, E) P(T | T̂) P(E) dT dE
```

其中 `T̂` 是 online wind 观测（GMRF 估计场），`P(T|T̂)` 是 wind 后验，`P(E)` 是传感器参数先验。

**关键分离（这是当前 CREL 缺失的）**：
- `θ`（源位置）与 `q`（源强度）**分开**建模：`S=(θ,q)`，likelihood 对 q 连续敏感（用浓度幅值，非二值）。
- `T`（transport）作为 nuisance，用 `P(T|T̂)` 边缘化，而非 8 个固定 member 的经验平均。
- `E`（sensor）作为 nuisance，用 deconvolution 从观测 y 恢复真实浓度 C，再反推源。
- posterior 输出到 **626 free cell 级**，不做 2×2 carrier 粗化。

**因果表征视角**：不直接拟合 `O→S` 的黑盒，而是显式编码 `S→T→C→E→O` 的因果结构，使 nuisance 干预（见 §6 破坏性测试）可被识别并剔除，而不是污染 source 后验。

**接口（冻结）**：
```
G2M1::Update( observations: {(t, x, y, ppm)}, online_wind: {(t, wind_field)}, geometry )
       → P_S = source_posterior[626]        # log-prob over free cells（strength 已边缘化）
       → P_T = transport_posterior (可选)    # 供 G2-M2 使用
```

**对应现有代码**：替换 `PMFS::applyCPIRPosterior` 的似然核；`recordCPIRRawSample` 的 timestamp-pose 关联保留（它是正确的基础设施）。

---

## 3. G2-M2：bank-free 输运预测（非平衡统计物理 + 湍流/Lagrangian + committor + operator learning）

**目标**：替代 site-specific predictive bank，最终在 held-out House 上**禁止查询该 House 的 bank**。

**映射**：
```
(geometry, online wind T̂, S, a, M_t) → P(O_future)
```

**方法**：
- **operator learning**：学习 advection-diffusion 解算子 `Ĉ = N_θ(geometry, wind, source)`（FNO / DeepONet / 神经算子），从 (geometry, wind, source) 直接预测浓度场，替代"每个 source×transport 跑一遍 GADEN 存 bank"。
- **committor（rare-event）**：源检测本质是 low-concentration 区域的 rare event；用 committor function `q(x,t)=P(未来在 x 处超阈 | 当前 wind, source)` 直接建模命中概率，规避逐点 PPM 回归的方差。
- **非平衡/Lagrangian transport**：用 Lagrangian 视角（随流体质点输运）替代欧拉稳态假设，捕捉湍流羽流的间歇性。

**部署约束（冻结）**：
- held-out House 上**禁止查询该 House 的 predictive bank**。
- 旧 bank（H01 等）只可作为 DEV_SPENT 的训练/验证数据；最终部署接口 `N_θ` 不查表。
- 输入只允许：geometry/SLAM、online wind、online gas、机器人位置、传感器状态、跨环境一次性训练好的模型。

**接口（冻结）**：
```
G2M2::Predict( geometry, online_wind T̂, source_hypothesis S, action a, belief M_t )
        → P_O_future = future observation distribution（浓度预测 + 不确定性）
```

---

## 4. G2-M3：主动实验设计（Bayesian experimental design + information geometry + autonomous science）

**目标**：选动作真正提高 source resolution，而非"内部 MI 高但机器人走错"。

**方法**：Bayesian optimal experimental design，最大化 **expected information gain (EIG)** 直接作用在 M1 的 source posterior 上：
```
a* = argmax_a  EIG(a)
EIG(a) = E_{O_future ~ P(O_future | a)} [ KL( P(S | O_future, a)  ‖  P(S) ) ]
```
（或等价的 Fisher information `det F(P(S|O,a))`，用 information geometry 在 source posterior 流形上度量。）

**与当前 PIP 的本质区别**：当前 `evaluateCTPIActionInformation` 用 8-member 命中率的 `H(mixture)-H(conditional)` 作为 MI，与真实 source resolution 脱节。G2-M3 的 EIG 直接在 G2-M1 输出的 `P_S` 上算，且 future observation 来自 G2-M2 的 `P_O_future`。

**接口（冻结）**：
```
G2M3::Score( P_S = source_posterior, candidate_actions, P_O_future )
       → scores[action]  # EIG，降序即动作优先级
```

---

## 5. Ablation 定义（冻结）

```
A0   = classic PMFS（无任何 G2 模块）
G100 = G2-M1 + native planner（M1 替换 CREL，planner 用原生，不用 G2-M3）
G110 = G2-M1 + transferable baseline prediction + G2-M3
G111 = G2-M1 + bank-free G2-M2 + 同一个 G2-M3
```

分解：
```
M1  = G100 − A0
M3  = G110 − G100
M2  = G111 − G110
Full = G111 − A0
```

最终验收（冻结，不变）：
```
Full G2 vs classic PMFS ≥ 10%（预注册主指标：240s localization error AUC）
且该优势必须在 bank-free held-out environment 上成立（禁止 House 专属 bank）
三模块各自 downstream load-bearing。
```

---

## 6. M1 破坏性测试清单（冻结，用户写死）

1. **source strength intervention**：干预源强度 q，检查 source posterior 是否随 q 正确移动，且不误伤 θ。
2. **transport regime intervention**：干预风场 regime（换 transport key），检查 transport nuisance 是否被边缘化掉，θ 后验不变形。
3. **sensor dynamics intervention**：干预 FOPDT 参数（τ/dead_time/gain），检查 sensor nuisance 是否被分离，θ 后验不漂移。
4. **House holdout**：在 held-out House 上验证 θ 定位不依赖 site-specific 假设。
5. **关键判据（反"越自信越错"）**：当 entropy/support 变小时，**true-source rank / error 必须单调变好**；若"后验越尖但尖在错误源上"，M1 直接判失败，禁止把"更自信"当优点。

---

## 7. 验证顺序（冻结）

```
1. 完整推导三模块架构（本文档）           ← 当前
2. 冻结 M1→M2→M3 接口（§2/§3/§4）
3. 先攻 M1：实现 + 破坏性测试（§6），单独通过才继续
4. 再攻 bank-free M2：held-out 预测通过
5. 再攻 M3：证明动作提高 source resolution
6. 最后 fresh closed-loop 联合验证（A0/G100/G110/G111）
7. 达到 Full ≥10% 且 bank-free held-out 成立，或出现外部资源 blocker
```

每个模块独立开发、独立确认数据；失败则冻结该版本，从失败机制推新版本，禁止"调参调到有效"。
