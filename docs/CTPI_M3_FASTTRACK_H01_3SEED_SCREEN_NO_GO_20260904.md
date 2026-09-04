# CTPI M3 FASTTRACK — H01 3-SEED SCREEN NO-GO 证据冻结

日期：2026-09-04
结论：`CTPI_FASTTRACK_H01_3SEED_SCREEN = NO_GO`
冻结性质：frozen CREL–TSDC–PIP 三模块首次正式 closed-loop 性能筛选，科学上未通过。

---

## 1. Screen Gate 结果

| 检查项 | 判定 |
|---|---|
| M1_screen（F00 − A0，CREL 源/干扰分离） | **false** |
| M3_screen（F10 − F00，PIP 主动实验设计） | **false** |
| M2_downstream_screen（F11 − F10，TSDC 输运预测） | **false** |
| formal_crosshouse_authorized | false |
| verdict | **CTPI_FASTTRACK_H01_3SEED_SCREEN=NO_GO** |

说明：12 个 run（seeds 0/1/2 × A0/F00/F10/F11）全部**正常跑完**（terminal PASS、M3 action sanity PASS、causal chain PASS），工程闭环无故障。失败是**性能无增量**，不是运行失败。

---

## 2. 核心失败机制

**整体规律：模块叠加 = 越加越差，后验越集中到错误位置。**

error_auc（越低越好）单调递增：

```
A0(1341) → F00(1584) → F10(1880) → F11(1878)
```

estimate_points（后验有效点数）单调递减：

```
A0(~108) → F00(~78) → F10/F11(~32)
```

即：每叠加一个模块，后验更"自信"（更集中），但集中到了错误位置，误差反而上升。

| 模块 | 对照 | error_auc_m_s (3seed mean) | final_error_m (3seed mean) | estimate_points | 失败机制 |
|---|---|---|---|---|---|
| A0（baseline PMFS） | — | 1340.9 | 4.40 | ~108 | — |
| M1 CREL | F00−A0 | 1583.8（**+18%**，3/3 恶化） | 6.91（**+57%**，3/3 恶化） | ~78 | 源/干扰分离把概率质量错误转移到非源 cell |
| M3 PIP | F10−F00 | 1879.9（**+19%**，3/3 恶化） | 6.55（1 胜 2 负） | ~32 | MI 动作选择在 CPIR 离散化 + GMRF 风场近似下不反映真实信息增益，选错 goal |
| M2 TSDC | F11−F10 | 1877.7（持平，1 胜 1 负 1 平） | 6.46（持平） | ~34 | bank-based 输运预测在 240s 短时域无下游转化 |

### 3.1 M1（CREL）失败机制
源/干扰分离把后验从 ~108 点压到 ~78 点，但压缩方向错误——把真源的概率质量转移到了错误 cell，final_error 从 4.40 恶化到 6.91（+57%）。当前 CREL 的 nuisance 分离模型在 H01 GADEN 数据上，未能正确区分 source strength / transport nuisance / sensor nuisance。

### 3.2 M3（PIP）失败机制
主动实验设计把后验进一步压到 ~32 点，但选出的动作（goal）没有带来信息增益，error_auc 从 1584 升到 1880（+19%）。当前 PIP 的 mutual-information 估计在 CPIR 离散化 + GMRF 风场近似下，无法正确反映"哪个动作最能区分剩余源假设"。

### 3.3 M2（TSDC）失败机制
TSDC 的输运预测在 F11 上没有带来任何下游增量（error_auc 1878 vs 1880 持平）。当前 TSDC 依赖 H01 bank 的输运预测，在 240s 短时域 + 3 seed 下没有转化为定位增益。

### 3.4 收敛性
time_to_2m 在 12 个 run 中 11 个 = 240.0s（未在预算内进入源 2m 内）。整个系统（含 A0 baseline）在 H01 上普遍难以在 240s 内精确收敛。

---

## 4. 结论与 G2 方向

这是**方法层失败**（三模块假设在 H01 GADEN 数据上不成立/未校准），不是参数问题，不能通过调参修复。

按预注册决策树：screen NO-GO → 冻结本失败机制 → 转入 **G2 failure-driven redesign**。

G2 三个模块分别借鉴不同母领域（对应上述失败机制）：

| G2 模块 | 母领域 | 解决的失败机制 |
|---|---|---|
| G2-M1 | Causal Representation Learning + Geophysical Inverse Problems | 正确分离 source / source strength / transport nuisance / sensor nuisance（修复 CREL 的分离错误） |
| G2-M2 | Non-equilibrium Statistical Physics + Turbulence/Lagrangian Transport + Rare-event/Committor + Operator Learning | bank-free 未来输运预测（修复 TSDC 依赖 bank、无泛化增益） |
| G2-M3 | Bayesian Experimental Design + Information Geometry + Autonomous Science | 真正区分剩余源假设的动作选择（修复 PIP 选错动作） |

最终目标：bank-free G2 在 unseen environment 上相对 classic PMFS 的预注册主指标（240s localization error AUC）≥ 10%。

---

## 5. 数据位置

- RUN_ROOT：`/dev/shm/ctpi_m3_h01_3seed_screen_c4445ee`
- 完整 12-run 数据：`H01_3SEED_PERFORMANCE.json`
- Screen gate：`H01_3SEED_SCREEN_GATE.json`
- 每个 run 的 trace：`H01_seed{0,1,2}_{A0,F00,F10,F11}/`
